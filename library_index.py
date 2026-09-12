#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from offlineu_core import (
    VIDEO_EXTENSIONS,
    AUDIO_EXTENSIONS,
    BOOK_EXTENSIONS,
    DOCUMENT_EXTENSIONS,
    IMAGE_EXTENSIONS,
    RESOURCE_EXTENSIONS,
    SUBTITLE_EXTENSIONS,
)

SCHEMA_VERSION = 1


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def connect_database(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    return conn


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS schema_info (
            version INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            display_name TEXT NOT NULL,
            is_admin INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            library_path TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            item_type TEXT NOT NULL DEFAULT 'unknown',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS media (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL,
            relative_path TEXT NOT NULL,
            media_type TEXT NOT NULL,
            extension TEXT NOT NULL,
            size_bytes INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(item_id, relative_path),
            FOREIGN KEY(item_id) REFERENCES items(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL,
            relative_path TEXT NOT NULL,
            resource_type TEXT NOT NULL,
            extension TEXT NOT NULL,
            size_bytes INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(item_id, relative_path),
            FOREIGN KEY(item_id) REFERENCES items(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            media_id INTEGER NOT NULL,
            position_seconds REAL,
            page_number INTEGER,
            completed INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL,
            UNIQUE(user_id, media_id),
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY(media_id) REFERENCES media(id) ON DELETE CASCADE
        );
        """
    )

    row = conn.execute("SELECT COUNT(*) AS n FROM schema_info").fetchone()

    if row["n"] == 0:
        conn.execute(
            "INSERT INTO schema_info(version) VALUES (?)",
            (SCHEMA_VERSION,),
        )

    conn.execute(
        """
        INSERT OR IGNORE INTO users(
            username,
            display_name,
            is_admin,
            created_at
        )
        VALUES (?, ?, ?, ?)
        """,
        ("local", "Utilisateur local", 1, now_iso()),
    )

    conn.commit()


def create_scan_workspace(conn: sqlite3.Connection) -> None:
    """Table temporaire listant les chemins vus pendant le scan d'un item.

    Elle n'existe que le temps de la connexion et n'est jamais ecrite
    dans le fichier de base de donnees.
    """

    conn.executescript(
        """
        CREATE TEMP TABLE IF NOT EXISTS seen_paths (
            kind TEXT NOT NULL,
            relative_path TEXT NOT NULL
        );
        """
    )


def classify_item(files: list[Path]) -> str:
    extensions = {f.suffix.lower() for f in files}

    has_video = bool(extensions & VIDEO_EXTENSIONS)
    has_audio = bool(extensions & AUDIO_EXTENSIONS)
    has_book = bool(extensions & BOOK_EXTENSIONS)

    if has_video:
        return "course"

    if has_book and has_audio:
        return "book_audio"

    if has_book:
        return "book"

    if has_audio:
        return "audiobook"

    return "document"


def classify_file(
    file_path: Path,
    item_type: str,
) -> tuple[str, str] | None:

    ext = file_path.suffix.lower()
    name_lower = file_path.name.lower()

    # OfflineU helper pages are metadata/resources, not primary media.
    if (
        ext in {".html", ".htm"}
        and name_lower.startswith("000")
        and "presentation" in name_lower
    ):
        return ("resource", "presentation")

    if (
        ext in {".html", ".htm"}
        and name_lower.startswith("000")
        and "ressource" in name_lower
    ):
        return ("resource", "resource_index")

    if ext in VIDEO_EXTENSIONS:
        return ("media", "video")

    if ext in AUDIO_EXTENSIONS:
        return ("media", "audio")

    if ext in BOOK_EXTENSIONS:
        # Important first heuristic:
        # in a video course, PDFs/ebooks are usually supporting resources.
        # In a book/audiobook item, they are primary media.
        if item_type == "course":
            return ("resource", "document")

        return ("media", "book")

    if ext in SUBTITLE_EXTENSIONS:
        return ("resource", "subtitle")

    if ext in IMAGE_EXTENSIONS:
        return ("resource", "image")

    if ext in RESOURCE_EXTENSIONS:
        return ("resource", "file")

    if ext in DOCUMENT_EXTENSIONS:
        return ("resource", "document")

    return None


def upsert_media(
    conn: sqlite3.Connection,
    item_id: int,
    relative_path: str,
    media_type: str,
    extension: str,
    size_bytes: int,
    timestamp: str,
) -> None:
    """Insere ou met a jour un media sans changer son id.

    L'id stable est ce qui permet a progress.media_id de survivre
    a un rescan.
    """

    conn.execute(
        """
        INSERT INTO media(
            item_id,
            relative_path,
            media_type,
            extension,
            size_bytes,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(item_id, relative_path)
        DO UPDATE SET
            media_type = excluded.media_type,
            extension = excluded.extension,
            size_bytes = excluded.size_bytes
        """,
        (
            item_id,
            relative_path,
            media_type,
            extension,
            size_bytes,
            timestamp,
        ),
    )


def upsert_resource(
    conn: sqlite3.Connection,
    item_id: int,
    relative_path: str,
    resource_type: str,
    extension: str,
    size_bytes: int,
    timestamp: str,
) -> None:

    conn.execute(
        """
        INSERT INTO resources(
            item_id,
            relative_path,
            resource_type,
            extension,
            size_bytes,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(item_id, relative_path)
        DO UPDATE SET
            resource_type = excluded.resource_type,
            extension = excluded.extension,
            size_bytes = excluded.size_bytes
        """,
        (
            item_id,
            relative_path,
            resource_type,
            extension,
            size_bytes,
            timestamp,
        ),
    )


def delete_vanished_rows(conn: sqlite3.Connection, item_id: int) -> None:
    """Supprime les lignes dont le fichier n'existe plus.

    Seules ces lignes disparaissent : la progression attachee aux
    fichiers toujours presents n'est jamais touchee.
    """

    conn.execute(
        """
        DELETE FROM media
        WHERE item_id = ?
          AND relative_path NOT IN (
              SELECT relative_path FROM seen_paths WHERE kind = 'media'
          )
        """,
        (item_id,),
    )

    conn.execute(
        """
        DELETE FROM resources
        WHERE item_id = ?
          AND relative_path NOT IN (
              SELECT relative_path FROM seen_paths WHERE kind = 'resource'
          )
        """,
        (item_id,),
    )


def scan_item(
    conn: sqlite3.Connection,
    library_root: Path,
    item_path: Path,
) -> None:

    all_files = sorted(
        file
        for file in item_path.rglob("*")
        if file.is_file() and not file.name.startswith(".")
    )

    item_type = classify_item(all_files)

    library_path = item_path.relative_to(library_root).as_posix()
    timestamp = now_iso()

    conn.execute(
        """
        INSERT INTO items(
            library_path,
            title,
            item_type,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(library_path)
        DO UPDATE SET
            title = excluded.title,
            item_type = excluded.item_type,
            updated_at = excluded.updated_at
        """,
        (
            library_path,
            item_path.name,
            item_type,
            timestamp,
            timestamp,
        ),
    )

    item = conn.execute(
        "SELECT id FROM items WHERE library_path = ?",
        (library_path,),
    ).fetchone()

    item_id = item["id"]

    conn.execute("DELETE FROM seen_paths")

    for file_path in all_files:
        classification = classify_file(file_path, item_type)

        if classification is None:
            continue

        category, subtype = classification

        relative_path = file_path.relative_to(item_path).as_posix()
        ext = file_path.suffix.lower()
        size = file_path.stat().st_size

        conn.execute(
            "INSERT INTO seen_paths(kind, relative_path) VALUES (?, ?)",
            (category, relative_path),
        )

        if category == "media":
            upsert_media(
                conn,
                item_id,
                relative_path,
                subtype,
                ext,
                size,
                timestamp,
            )

        else:
            upsert_resource(
                conn,
                item_id,
                relative_path,
                subtype,
                ext,
                size,
                timestamp,
            )

    delete_vanished_rows(conn, item_id)


def scan_library(library_root: Path, db_path: Path) -> None:
    library_root = library_root.resolve()

    if not library_root.is_dir():
        raise SystemExit(
            f"Bibliothèque introuvable : {library_root}"
        )

    conn = connect_database(db_path)

    try:
        create_schema(conn)
        create_scan_workspace(conn)

        current_items = {
            path.relative_to(library_root).as_posix()
            for path in library_root.iterdir()
            if path.is_dir() and not path.name.startswith(".")
        }

        existing_items = {
            row["library_path"]
            for row in conn.execute(
                "SELECT library_path FROM items"
            )
        }

        removed_items = existing_items - current_items

        for removed in removed_items:
            conn.execute(
                "DELETE FROM items WHERE library_path = ?",
                (removed,),
            )

        for item_path in sorted(
            path
            for path in library_root.iterdir()
            if path.is_dir() and not path.name.startswith(".")
        ):
            scan_item(conn, library_root, item_path)

        conn.commit()

    finally:
        conn.close()


def print_summary(db_path: Path) -> None:
    conn = connect_database(db_path)

    try:
        print()
        print("=== INDEX SAVOIRTHEQUE ===")

        rows = conn.execute(
            """
            SELECT
                i.title,
                i.item_type,
                COUNT(DISTINCT m.id) AS media_count,
                COUNT(DISTINCT r.id) AS resource_count
            FROM items i
            LEFT JOIN media m ON m.item_id = i.id
            LEFT JOIN resources r ON r.item_id = i.id
            GROUP BY i.id
            ORDER BY i.title
            """
        ).fetchall()

        for row in rows:
            print(
                f"{row['title']}\n"
                f"  type       : {row['item_type']}\n"
                f"  médias     : {row['media_count']}\n"
                f"  ressources : {row['resource_count']}"
            )

        print()
        print("=== DETAIL DES MEDIAS ===")

        rows = conn.execute(
            """
            SELECT
                i.title,
                m.media_type,
                m.relative_path
            FROM media m
            JOIN items i ON i.id = m.item_id
            ORDER BY i.title, m.relative_path
            """
        ).fetchall()

        for row in rows:
            print(
                f"[{row['media_type']:5}] "
                f"{row['title']} :: {row['relative_path']}"
            )

    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--library",
        required=True,
        type=Path,
    )

    parser.add_argument(
        "--database",
        required=True,
        type=Path,
    )

    args = parser.parse_args()

    scan_library(args.library, args.database)
    print_summary(args.database)


if __name__ == "__main__":
    main()
