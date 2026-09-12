"""Tests de l'application web Savoirthèque (grille + fiche d'item).

Reprend les mêmes fixtures que test_library_index.py : une
bibliothèque jetable construite dans un dossier temporaire, scannée
avant chaque test.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from library_index import scan_library  # noqa: E402
from savoiritheque import create_app  # noqa: E402


def make_file(path: Path, content: bytes = b"x") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


@pytest.fixture
def library(tmp_path: Path) -> Path:
    root = tmp_path / "library"

    book = root / "Adobe Illustrator CS6 (Adobe Press)"
    make_file(book / "920 - Adobe Illustrator CS6 - Adobe Press.pdf")
    make_file(book / "Exercices.zip")
    make_file(book / "000 - presentation.html")

    deep = root / "Motion Design - la formation complete (TUTO.com)"
    make_file(deep / "01 - Bases" / "001 - Interface.mp4")
    make_file(deep / "01 - Bases" / "002 - Calques.mp4")
    make_file(deep / "02 - Animation" / "003 - Keyframes.mp4")
    make_file(deep / "Ressources" / "projets.zip")

    return root


@pytest.fixture
def db(tmp_path: Path) -> Path:
    return tmp_path / "data" / "savoiritheque.db"


@pytest.fixture
def client(library: Path, db: Path):
    scan_library(library, db, verbose=False)
    app = create_app(library, db)
    app.config["TESTING"] = True

    with app.test_client() as test_client:
        yield test_client


def item_id_by_title(client, title: str) -> int:
    import sqlite3

    db_path = client.application.config["DB_PATH"]
    conn = sqlite3.connect(db_path)

    try:
        row = conn.execute(
            "SELECT id FROM items WHERE title = ?", (title,)
        ).fetchone()
    finally:
        conn.close()

    return row[0]


def test_grille_liste_les_items(client) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert b"Adobe Illustrator CS6" in response.data
    assert b"Motion Design" in response.data


def test_fiche_item_liste_les_chapitres_en_ordre(client) -> None:
    item_id = item_id_by_title(client, "Motion Design - la formation complete (TUTO.com)")

    response = client.get(f"/item/{item_id}")
    data = response.data.decode()

    assert response.status_code == 200
    assert "01 - Bases" in data
    assert "02 - Animation" in data
    assert data.index("01 - Bases") < data.index("02 - Animation")
    assert "Interface" in data
    assert "Keyframes" in data


def test_fiche_item_liste_les_ressources(client) -> None:
    item_id = item_id_by_title(client, "Adobe Illustrator CS6 (Adobe Press)")

    response = client.get(f"/item/{item_id}")
    data = response.data.decode()

    assert response.status_code == 200
    assert "Exercices.zip" in data


def test_fiche_item_inconnu_renvoie_404(client) -> None:
    response = client.get("/item/999")

    assert response.status_code == 404
