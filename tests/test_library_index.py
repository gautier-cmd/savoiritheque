"""Tests du scanner SQLite de Savoirtheque.

Chaque test construit une bibliotheque jetable dans un dossier
temporaire fourni par pytest (tmp_path), la scanne, puis verifie
l'etat de la base. Aucun fichier reel de la bibliotheque de test
n'est touche.
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from library_index import scan_library  # noqa: E402


def make_file(path: Path, content: bytes = b"x") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def query(db_path: Path, sql: str, params: tuple = ()) -> list[tuple]:
    conn = sqlite3.connect(db_path)

    try:
        return conn.execute(sql, params).fetchall()

    finally:
        conn.close()


def set_progress(db_path: Path, media_id: int, seconds: float) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")

    try:
        conn.execute(
            """
            INSERT OR REPLACE INTO progress(
                user_id, media_id, position_seconds, completed, updated_at
            )
            VALUES (1, ?, ?, 0, datetime('now'))
            """,
            (media_id, seconds),
        )
        conn.commit()

    finally:
        conn.close()


@pytest.fixture
def library(tmp_path: Path) -> Path:
    """Une bibliotheque miniature couvrant les quatre cas de test reels."""

    root = tmp_path / "library"

    # Cas 1 : livre PDF + ressource ZIP + page de presentation.
    book = root / "Adobe Illustrator CS6 (Adobe Press)"
    make_file(book / "920 - Adobe Illustrator CS6 - Adobe Press.pdf")
    make_file(book / "Exercices.zip")
    make_file(book / "000 - presentation.html")

    # Cas 2 : livre audio M4B.
    audiobook = root / "S organiser pour reussir (David Allen)"
    make_file(audiobook / "S organiser pour reussir.m4b")
    make_file(audiobook / "Ressources.zip")

    # Cas 3 : formation video a plat, avec des PDF qui sont
    # des ressources et non des livres.
    course = root / "Devenez Copywriter avec les IA (TUTO.com)"
    make_file(course / "001 - Presentation.mp4")
    make_file(course / "002 - Le metier.mp4")
    make_file(course / "Support de cours.pdf")
    make_file(course / "Modeles.zip")

    # Cas 4 : hierarchie profonde.
    deep = root / "Motion Design - la formation complete (TUTO.com)"
    make_file(deep / "01 - Bases" / "001 - Interface.mp4")
    make_file(deep / "01 - Bases" / "002 - Calques.mp4")
    make_file(deep / "02 - Animation" / "003 - Keyframes.mp4")
    make_file(deep / "Ressources" / "projets.zip")

    return root


@pytest.fixture
def db(tmp_path: Path) -> Path:
    return tmp_path / "data" / "savoiritheque.db"


def test_classification_des_items(library: Path, db: Path) -> None:
    scan_library(library, db)

    types = dict(
        query(db, "SELECT title, item_type FROM items")
    )

    assert types["Adobe Illustrator CS6 (Adobe Press)"] == "book"
    assert types["S organiser pour reussir (David Allen)"] == "audiobook"
    assert types["Devenez Copywriter avec les IA (TUTO.com)"] == "course"
    assert types["Motion Design - la formation complete (TUTO.com)"] == "course"


def test_pdf_de_formation_est_une_ressource(library: Path, db: Path) -> None:
    scan_library(library, db)

    medias = query(
        db,
        """
        SELECT m.relative_path FROM media m
        JOIN items i ON i.id = m.item_id
        WHERE i.item_type = 'course'
        """,
    )
    chemins = {row[0] for row in medias}

    # Les PDF d'une formation video ne doivent pas etre des medias.
    assert "Support de cours.pdf" not in chemins

    ressources = query(
        db,
        """
        SELECT r.relative_path FROM resources r
        JOIN items i ON i.id = r.item_id
        WHERE i.title LIKE 'Devenez Copywriter%'
        """,
    )

    assert "Support de cours.pdf" in {row[0] for row in ressources}

    # A l'inverse, le PDF d'un livre reste un media.
    livres = query(
        db,
        """
        SELECT m.media_type FROM media m
        JOIN items i ON i.id = m.item_id
        WHERE i.title LIKE 'Adobe Illustrator%'
        """,
    )

    assert livres == [("book",)]


def test_hierarchie_profonde(library: Path, db: Path) -> None:
    scan_library(library, db)

    chemins = {
        row[0]
        for row in query(
            db,
            """
            SELECT m.relative_path FROM media m
            JOIN items i ON i.id = m.item_id
            WHERE i.title LIKE 'Motion Design%'
            """,
        )
    }

    assert chemins == {
        "01 - Bases/001 - Interface.mp4",
        "01 - Bases/002 - Calques.mp4",
        "02 - Animation/003 - Keyframes.mp4",
    }


def test_rescan_preserve_ids_et_progression(library: Path, db: Path) -> None:
    scan_library(library, db)

    avant = query(db, "SELECT id, relative_path FROM media ORDER BY id")
    set_progress(db, avant[0][0], 123.4)

    scan_library(library, db)

    apres = query(db, "SELECT id, relative_path FROM media ORDER BY id")

    assert apres == avant

    progression = query(
        db, "SELECT media_id, position_seconds FROM progress"
    )

    assert progression == [(avant[0][0], 123.4)]


def test_fichier_supprime_disparait_sans_toucher_aux_voisins(
    library: Path, db: Path
) -> None:
    scan_library(library, db)

    item = "Devenez Copywriter avec les IA (TUTO.com)"

    medias = query(
        db,
        """
        SELECT m.id, m.relative_path FROM media m
        JOIN items i ON i.id = m.item_id
        WHERE i.title = ?
        ORDER BY m.relative_path
        """,
        (item,),
    )

    garde_id, garde_path = medias[0]
    supprime_id, supprime_path = medias[1]

    set_progress(db, garde_id, 42.0)
    set_progress(db, supprime_id, 99.0)

    (library / item / supprime_path).unlink()

    scan_library(library, db)

    restants = {
        row[0]
        for row in query(db, "SELECT id FROM media")
    }

    assert garde_id in restants
    assert supprime_id not in restants

    progression = query(
        db, "SELECT media_id, position_seconds FROM progress"
    )

    assert progression == [(garde_id, 42.0)]


def test_unicode_et_apostrophes(tmp_path: Path, db: Path) -> None:
    root = tmp_path / "library"
    item = root / "Formation accentuée"

    noms = [
        "Leçon 1 - l'apostrophe droite.mp4",
        "Leçon 2 — l\u2019œuvre (été).mp4",
        "Fichier ÀÉÎÔÙ çæœ.mp4",
    ]

    for nom in noms:
        make_file(item / nom)

    scan_library(root, db)

    chemins = {
        row[0]
        for row in query(db, "SELECT relative_path FROM media")
    }

    assert chemins == set(noms)


def test_item_supprime_disparait_de_lindex(library: Path, db: Path) -> None:
    import shutil

    scan_library(library, db)

    assert len(query(db, "SELECT id FROM items")) == 4

    shutil.rmtree(library / "Adobe Illustrator CS6 (Adobe Press)")

    scan_library(library, db)

    titres = {row[0] for row in query(db, "SELECT title FROM items")}

    assert "Adobe Illustrator CS6 (Adobe Press)" not in titres
    assert len(titres) == 3
