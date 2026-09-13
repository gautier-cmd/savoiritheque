#!/usr/bin/env python3
"""Application web de consultation de la bibliothèque Savoirthèque.

Lecture seule pour l'instant : grille des items puis fiche d'un item.
Les lecteurs (vidéo, audio, PDF) et l'écriture de la progression
viennent dans des tranches suivantes.
"""

from __future__ import annotations

import argparse
import mimetypes
from pathlib import Path

from flask import Flask, abort, redirect, render_template, request, send_file, url_for

from library_index import connect_database, format_duration, now_iso
from presentation import parse_presentation
from book_metadata import default_query, find_isbn, search_candidates

BOOK_ITEM_TYPES = ("book", "book_audio", "audiobook")


def fetch_video_media(conn, media_id: int):
    """Media de type vidéo, avec le chemin de bibliothèque et le titre
    de son item.

    None si l'id n'existe pas ou si ce n'est pas une vidéo : cette
    fonction sert de garde commune aux deux routes vidéo.
    """

    return conn.execute(
        """
        SELECT
            media.id,
            media.item_id,
            media.relative_path,
            media.extension,
            items.title AS item_title,
            items.library_path
        FROM media
        JOIN items ON items.id = media.item_id
        WHERE media.id = ? AND media.media_type = 'video'
        """,
        (media_id,),
    ).fetchone()


def fetch_video_playlist(conn, item_id: int):
    """Toutes les vidéos d'un item, dans l'ordre de sort_order."""

    return conn.execute(
        """
        SELECT id, relative_path, parent_path, sort_order
        FROM media
        WHERE item_id = ? AND media_type = 'video'
        ORDER BY sort_order
        """,
        (item_id,),
    ).fetchall()


def read_presentation(library_root: Path, library_path: str, relative_path: str):
    """Lit et analyse la page de présentation HTML d'un item.

    None si le fichier a disparu du disque depuis le scan : une fiche
    ne doit pas planter pour autant, elle s'affiche juste sans
    présentation.
    """

    file_path = (library_root / library_path / relative_path).resolve()

    if library_root not in file_path.parents:
        return None

    try:
        html_text = file_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None

    return parse_presentation(html_text)


def fetch_book_candidates(conn, item_id: int):
    return conn.execute(
        """
        SELECT id, source, source_id, title, authors, publisher,
               published_year, isbn, cover_url, decision
        FROM book_candidates
        WHERE item_id = ?
        ORDER BY id
        """,
        (item_id,),
    ).fetchall()


def fetch_book_state(conn, item_id: int) -> dict:
    """État de la recherche de métadonnées pour un item livre.

    Le statut n'est pas stocké : il est déduit des candidats présents,
    pour ne jamais désynchroniser un champ "statut" du contenu réel de
    book_candidates.
    """

    search_row = conn.execute(
        "SELECT query, searched_at FROM book_search WHERE item_id = ?",
        (item_id,),
    ).fetchone()

    candidates = fetch_book_candidates(conn, item_id)
    accepted = next((c for c in candidates if c["decision"] == "accepted"), None)
    proposed = [c for c in candidates if c["decision"] == "proposed"]
    rejected = [c for c in candidates if c["decision"] == "rejected"]

    if accepted is not None:
        status = "validated"
    elif proposed:
        status = "has_candidates"
    elif search_row is not None:
        status = "searched_no_match"
    else:
        status = "never_searched"

    return {
        "status": status,
        "query": search_row["query"] if search_row else None,
        "accepted": accepted,
        "proposed": proposed,
        "rejected": rejected,
    }


def detect_isbn_for_item(conn, item) -> str | None:
    texts = [item["title"]]
    texts += [
        row["relative_path"]
        for row in conn.execute(
            """
            SELECT relative_path FROM media WHERE item_id = ?
            UNION ALL
            SELECT relative_path FROM resources WHERE item_id = ?
            """,
            (item["id"], item["id"]),
        )
    ]
    return find_isbn(*texts)


def run_book_search(conn, item_id: int, raw_query: str) -> None:
    """Lance une recherche et enregistre les candidats trouvés.

    Une recherche par ISBN écrase toujours une recherche par titre :
    si la requête contient un ISBN valide, c'est lui qui est utilisé
    (identifiant fiable), le reste du texte est ignoré pour la requête
    envoyée aux deux sources.
    """

    isbn = find_isbn(raw_query)
    candidates = search_candidates(query=raw_query.strip(), isbn=isbn)
    now = now_iso()

    conn.execute(
        """
        INSERT INTO book_search(item_id, query, searched_at)
        VALUES (?, ?, ?)
        ON CONFLICT(item_id) DO UPDATE SET query = excluded.query, searched_at = excluded.searched_at
        """,
        (item_id, raw_query.strip(), now),
    )

    for candidate in candidates:
        conn.execute(
            """
            INSERT INTO book_candidates(
                item_id, source, source_id, title, authors, publisher,
                published_year, isbn, cover_url, decision, found_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'proposed', ?)
            ON CONFLICT(item_id, source, source_id) DO NOTHING
            """,
            (
                item_id,
                candidate["source"],
                candidate["source_id"],
                candidate["title"],
                candidate["authors"],
                candidate["publisher"],
                candidate["published_year"],
                candidate["isbn"],
                candidate["cover_url"],
                now,
            ),
        )


def demote_accepted_candidate(conn, item_id: int, except_id: int = -1) -> None:
    """Repasse à "proposé" l'éventuel candidat déjà validé de l'item.

    Appelé avant d'en valider un autre : changer d'avis ne doit rien
    effacer, l'ancien choix reste consultable comme un candidat parmi
    d'autres.
    """

    conn.execute(
        """
        UPDATE book_candidates SET decision = 'proposed', decided_at = NULL
        WHERE item_id = ? AND decision = 'accepted' AND id != ?
        """,
        (item_id, except_id),
    )


def accept_book_candidate(conn, item_id: int, candidate_id: int) -> None:
    demote_accepted_candidate(conn, item_id, except_id=candidate_id)

    conn.execute(
        """
        UPDATE book_candidates SET decision = 'accepted', decided_at = ?
        WHERE id = ? AND item_id = ?
        """,
        (now_iso(), candidate_id, item_id),
    )


def save_manual_candidate(conn, item_id: int, fields: dict) -> None:
    """Enregistre une saisie manuelle comme métadonnées validées.

    source_id fixe ("manual") : une seule fiche saisie à la main par
    item, une nouvelle saisie remplace la précédente plutôt que d'en
    accumuler.
    """

    demote_accepted_candidate(conn, item_id)
    now = now_iso()

    conn.execute(
        """
        INSERT INTO book_candidates(
            item_id, source, source_id, title, authors, publisher,
            published_year, isbn, cover_url, decision, found_at, decided_at
        )
        VALUES (?, 'manual', 'manual', ?, ?, ?, ?, ?, NULL, 'accepted', ?, ?)
        ON CONFLICT(item_id, source, source_id) DO UPDATE SET
            title = excluded.title,
            authors = excluded.authors,
            publisher = excluded.publisher,
            published_year = excluded.published_year,
            isbn = excluded.isbn,
            decision = 'accepted',
            decided_at = excluded.decided_at
        """,
        (
            item_id,
            fields.get("title") or None,
            fields.get("authors") or None,
            fields.get("publisher") or None,
            fields.get("published_year") or None,
            fields.get("isbn") or None,
            now,
            now,
        ),
    )


def group_by_parent(rows):
    """Regroupe des lignes media/resource par parent_path.

    Un dict garde l'ordre de première apparition de chaque
    parent_path, contrairement à itertools.groupby qui ne fusionne
    que des lignes déjà consécutives.
    """

    grouped: dict[str, list] = {}
    for row in rows:
        grouped.setdefault(row["parent_path"], []).append(row)

    return list(grouped.items())


def create_app(library_root: Path, db_path: Path) -> Flask:
    app = Flask(__name__)
    app.config["LIBRARY_ROOT"] = library_root.resolve()
    app.config["DB_PATH"] = db_path

    @app.route("/")
    def library_grid():
        conn = connect_database(app.config["DB_PATH"])

        try:
            items = conn.execute(
                """
                SELECT
                    i.id,
                    i.title,
                    i.item_type,
                    (SELECT COUNT(*) FROM media m
                     WHERE m.item_id = i.id) AS media_count,
                    (SELECT COUNT(*) FROM resources r
                     WHERE r.item_id = i.id) AS resource_count,
                    (SELECT COUNT(DISTINCT parent_path) FROM media m
                     WHERE m.item_id = i.id
                       AND m.parent_path <> '') AS chapter_count,
                    (SELECT SUM(duration_seconds) FROM media m
                     WHERE m.item_id = i.id) AS total_duration
                FROM items i
                ORDER BY i.title
                """
            ).fetchall()
        finally:
            conn.close()

        return render_template(
            "library_grid.html",
            items=items,
            format_duration=format_duration,
        )

    @app.route("/item/<int:item_id>")
    def item_detail(item_id: int):
        conn = connect_database(app.config["DB_PATH"])

        try:
            item = conn.execute(
                """
                SELECT id, title, item_type, library_path
                FROM items WHERE id = ?
                """,
                (item_id,),
            ).fetchone()

            if item is None:
                abort(404)

            media_rows = conn.execute(
                """
                SELECT
                    id, relative_path, parent_path, sort_order,
                    media_type, extension, size_bytes, duration_seconds
                FROM media
                WHERE item_id = ?
                ORDER BY sort_order
                """,
                (item_id,),
            ).fetchall()

            resources = conn.execute(
                """
                SELECT
                    id, relative_path, parent_path, sort_order,
                    resource_type, extension, size_bytes
                FROM resources
                WHERE item_id = ?
                ORDER BY sort_order
                """,
                (item_id,),
            ).fetchall()
        finally:
            conn.close()

        chapters = group_by_parent(media_rows)

        presentation_resource = next(
            (r for r in resources if r["resource_type"] == "presentation"),
            None,
        )
        resources = [
            r for r in resources if r["resource_type"] != "presentation"
        ]

        presentation = None
        if presentation_resource is not None:
            presentation = read_presentation(
                app.config["LIBRARY_ROOT"],
                item["library_path"],
                presentation_resource["relative_path"],
            )

        book = None
        if item["item_type"] in BOOK_ITEM_TYPES:
            conn = connect_database(app.config["DB_PATH"])
            try:
                book = fetch_book_state(conn, item_id)
                if book["query"] is None:
                    isbn = detect_isbn_for_item(conn, item)
                    book["suggested_query"] = isbn or default_query(item["title"])
                    book["isbn_detected"] = isbn
            finally:
                conn.close()

        return render_template(
            "item_detail.html",
            item=item,
            chapters=chapters,
            resources=resources,
            presentation=presentation,
            book=book,
            format_duration=format_duration,
        )

    def fetch_book_item_or_404(conn, item_id: int):
        item = conn.execute(
            "SELECT id, item_type FROM items WHERE id = ?", (item_id,)
        ).fetchone()

        if item is None or item["item_type"] not in BOOK_ITEM_TYPES:
            abort(404)

        return item

    @app.route("/item/<int:item_id>/book-search", methods=["POST"])
    def book_search(item_id: int):
        conn = connect_database(app.config["DB_PATH"])

        try:
            fetch_book_item_or_404(conn, item_id)
            raw_query = request.form.get("query", "").strip()

            if raw_query:
                run_book_search(conn, item_id, raw_query)
                conn.commit()
        finally:
            conn.close()

        return redirect(url_for("item_detail", item_id=item_id) + "#metadonnees")

    @app.route("/item/<int:item_id>/book-candidate/<int:candidate_id>/accept", methods=["POST"])
    def book_candidate_accept(item_id: int, candidate_id: int):
        conn = connect_database(app.config["DB_PATH"])

        try:
            fetch_book_item_or_404(conn, item_id)
            accept_book_candidate(conn, item_id, candidate_id)
            conn.commit()
        finally:
            conn.close()

        return redirect(url_for("item_detail", item_id=item_id) + "#metadonnees")

    @app.route("/item/<int:item_id>/book-candidate/<int:candidate_id>/reject", methods=["POST"])
    def book_candidate_reject(item_id: int, candidate_id: int):
        conn = connect_database(app.config["DB_PATH"])

        try:
            fetch_book_item_or_404(conn, item_id)
            conn.execute(
                """
                UPDATE book_candidates SET decision = 'rejected', decided_at = ?
                WHERE id = ? AND item_id = ?
                """,
                (now_iso(), candidate_id, item_id),
            )
            conn.commit()
        finally:
            conn.close()

        return redirect(url_for("item_detail", item_id=item_id) + "#metadonnees")

    @app.route("/item/<int:item_id>/book-candidate/<int:candidate_id>/unreject", methods=["POST"])
    def book_candidate_unreject(item_id: int, candidate_id: int):
        conn = connect_database(app.config["DB_PATH"])

        try:
            fetch_book_item_or_404(conn, item_id)
            conn.execute(
                """
                UPDATE book_candidates SET decision = 'proposed', decided_at = NULL
                WHERE id = ? AND item_id = ? AND decision = 'rejected'
                """,
                (candidate_id, item_id),
            )
            conn.commit()
        finally:
            conn.close()

        return redirect(url_for("item_detail", item_id=item_id) + "#metadonnees")

    @app.route("/item/<int:item_id>/book-manual", methods=["POST"])
    def book_manual(item_id: int):
        conn = connect_database(app.config["DB_PATH"])

        try:
            fetch_book_item_or_404(conn, item_id)
            save_manual_candidate(
                conn,
                item_id,
                {
                    "title": request.form.get("title", "").strip(),
                    "authors": request.form.get("authors", "").strip(),
                    "publisher": request.form.get("publisher", "").strip(),
                    "published_year": request.form.get("published_year", "").strip(),
                    "isbn": request.form.get("isbn", "").strip(),
                },
            )
            conn.commit()
        finally:
            conn.close()

        return redirect(url_for("item_detail", item_id=item_id) + "#metadonnees")

    @app.route("/watch/<int:media_id>")
    def watch_video(media_id: int):
        conn = connect_database(app.config["DB_PATH"])

        try:
            media = fetch_video_media(conn, media_id)

            if media is None:
                abort(404)

            playlist = fetch_video_playlist(conn, media["item_id"])
        finally:
            conn.close()

        chapters = group_by_parent(playlist)

        flat_ids = [row["id"] for row in playlist]
        position = flat_ids.index(media_id)
        prev_id = flat_ids[position - 1] if position > 0 else None
        next_id = (
            flat_ids[position + 1] if position + 1 < len(flat_ids) else None
        )

        return render_template(
            "video_player.html",
            media=media,
            chapters=chapters,
            current_media_id=media_id,
            prev_id=prev_id,
            next_id=next_id,
        )

    @app.route("/media/<int:media_id>/file")
    def media_file(media_id: int):
        conn = connect_database(app.config["DB_PATH"])

        try:
            media = fetch_video_media(conn, media_id)
        finally:
            conn.close()

        if media is None:
            abort(404)

        library_root = app.config["LIBRARY_ROOT"]
        file_path = (
            library_root / media["library_path"] / media["relative_path"]
        ).resolve()

        if library_root not in file_path.parents or not file_path.is_file():
            abort(404)

        mimetype, _ = mimetypes.guess_type(file_path.name)

        return send_file(file_path, mimetype=mimetype)

    return app


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument("--library", required=True, type=Path)
    parser.add_argument("--database", required=True, type=Path)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=5000, type=int)

    args = parser.parse_args()

    app = create_app(args.library, args.database)
    app.run(host=args.host, port=args.port, debug=False)


if __name__ == "__main__":
    main()
