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

from flask import Flask, abort, render_template, send_file

from library_index import connect_database, format_duration


def fetch_video_media(conn, media_id: int):
    """Media de type vidéo avec le chemin de bibliothèque de son item.

    None si l'id n'existe pas ou si ce n'est pas une vidéo : cette
    fonction sert de garde commune aux deux routes vidéo.
    """

    return conn.execute(
        """
        SELECT
            media.id,
            media.relative_path,
            media.extension,
            items.library_path
        FROM media
        JOIN items ON items.id = media.item_id
        WHERE media.id = ? AND media.media_type = 'video'
        """,
        (media_id,),
    ).fetchone()


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
                "SELECT id, title, item_type FROM items WHERE id = ?",
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

        chapters_by_parent: dict[str, list] = {}
        for row in media_rows:
            chapters_by_parent.setdefault(row["parent_path"], []).append(row)

        chapters = list(chapters_by_parent.items())

        return render_template(
            "item_detail.html",
            item=item,
            chapters=chapters,
            resources=resources,
            format_duration=format_duration,
        )

    @app.route("/watch/<int:media_id>")
    def watch_video(media_id: int):
        conn = connect_database(app.config["DB_PATH"])

        try:
            media = fetch_video_media(conn, media_id)
        finally:
            conn.close()

        if media is None:
            abort(404)

        return render_template("video_player.html", media=media)

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
