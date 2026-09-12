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


def media_id_by_relative_path(client, relative_path: str) -> int:
    import sqlite3

    db_path = client.application.config["DB_PATH"]
    conn = sqlite3.connect(db_path)

    try:
        row = conn.execute(
            "SELECT id FROM media WHERE relative_path = ?", (relative_path,)
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


def test_chapitre_racine_non_consecutif_reste_un_seul_groupe(
    tmp_path: Path, db: Path
) -> None:
    """Des médias à la racine avant et après un sous-dossier ne doivent
    former qu'un seul groupe "Racine", pas deux.

    Les noms sont choisis pour que le tri naturel place les deux
    fichiers de racine de part et d'autre du sous-dossier : media_rows
    n'est alors plus consécutif par parent_path, ce que groupby()
    traiterait à tort comme deux chapitres "" distincts.
    """

    root = tmp_path / "library"
    item = root / "Item entrelace"

    make_file(item / "1 - Root A.mp4")
    make_file(item / "2 - Chapitre" / "1 - Video B.mp4")
    make_file(item / "3 - Root C.mp4")

    scan_library(root, db, verbose=False)

    app = create_app(root, db)
    app.config["TESTING"] = True

    with app.test_client() as test_client:
        item_id = item_id_by_title(test_client, "Item entrelace")
        response = test_client.get(f"/item/{item_id}")
        data = response.data.decode()

    assert response.status_code == 200
    # Un seul groupe "Racine", pas un par plage consecutive de fichiers.
    assert data.count(">Racine<") == 1
    assert data.count("<h3>") == 2
    # A l'interieur du groupe, l'ordre sort_order des deux fichiers de
    # racine est respecte malgre le sous-dossier intercale entre eux.
    assert data.index("Root A") < data.index("Root C")
    assert "Video B" in data


def test_page_lecteur_video_affiche_le_lecteur(client) -> None:
    media_id = media_id_by_relative_path(
        client, "01 - Bases/001 - Interface.mp4"
    )

    response = client.get(f"/watch/{media_id}")

    assert response.status_code == 200
    assert b"<video" in response.data


def test_fichier_video_supporte_les_requetes_range(client) -> None:
    media_id = media_id_by_relative_path(
        client, "01 - Bases/001 - Interface.mp4"
    )

    response = client.get(
        f"/media/{media_id}/file", headers={"Range": "bytes=0-0"}
    )

    assert response.status_code == 206
    assert response.headers["Content-Type"] == "video/mp4"


def test_media_non_video_renvoie_404_sur_lecteur_et_fichier(client) -> None:
    media_id = media_id_by_relative_path(
        client, "920 - Adobe Illustrator CS6 - Adobe Press.pdf"
    )

    assert client.get(f"/watch/{media_id}").status_code == 404
    assert client.get(f"/media/{media_id}/file").status_code == 404
