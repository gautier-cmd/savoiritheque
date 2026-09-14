"""Tests du module covers.py.

Les extractions réelles (ffmpeg sur une vraie vidéo/M4B) ne sont pas
testées ici : elles ont été vérifiées à la main sur la vraie
bibliothèque de test. Ces tests couvrent la logique qui ne dépend pas
d'un binaire externe (cache, priorité, repli) avec des extracteurs
remplacés, plus un cas réel avec un PDF minimal — pdftoppm est rapide
et sans dépendance externe au-delà du paquet système déjà requis.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import covers  # noqa: E402

MINIMAL_PDF = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] /Resources << >> /Contents 4 0 R >>
endobj
4 0 obj
<< /Length 44 >>
stream
1 0 0 RG 10 10 180 180 re S
endstream
endobj
trailer
<< /Size 5 /Root 1 0 R >>
%%EOF
"""


def make_item(item_id=1, item_type="course", library_path="Item"):
    return {"id": item_id, "item_type": item_type, "library_path": library_path}


def test_extract_pdf_first_page_avec_un_vrai_pdf(tmp_path: Path) -> None:
    pdf_path = tmp_path / "livre.pdf"
    pdf_path.write_bytes(MINIMAL_PDF)
    out_path = tmp_path / "cover.jpg"

    assert covers.extract_pdf_first_page(pdf_path, out_path) is True
    assert out_path.is_file()
    assert out_path.stat().st_size > 0


def test_extract_pdf_first_page_echoue_proprement_sur_fichier_invalide(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "pas-un-pdf.pdf"
    pdf_path.write_bytes(b"ceci n'est pas un PDF")
    out_path = tmp_path / "cover.jpg"

    assert covers.extract_pdf_first_page(pdf_path, out_path) is False
    assert not out_path.exists()


def test_extract_video_frame_sur_fichier_invalide_ne_leve_pas(tmp_path: Path) -> None:
    video_path = tmp_path / "video.mp4"
    video_path.write_bytes(b"pas une vraie video")
    out_path = tmp_path / "cover.jpg"

    assert covers.extract_video_frame(video_path, out_path, 120.0) is False
    assert not out_path.exists()


def test_ensure_cover_reutilise_le_cache_existant(tmp_path: Path, monkeypatch) -> None:
    cache_dir = tmp_path / "covers"
    cache_dir.mkdir()
    item = make_item()
    out_path = covers.cover_cache_path(cache_dir, item["id"])
    out_path.write_bytes(b"deja-la")

    def fail_if_called(*args, **kwargs):
        raise AssertionError("ne doit pas re-extraire si le cache existe deja")

    monkeypatch.setattr(covers, "extract_video_frame", fail_if_called)

    result = covers.ensure_cover(tmp_path, cache_dir, item, [], [])

    assert result == out_path
    assert out_path.read_bytes() == b"deja-la"


def test_ensure_cover_force_reextrait_meme_si_cache_existe(
    tmp_path: Path, monkeypatch
) -> None:
    cache_dir = tmp_path / "covers"
    cache_dir.mkdir()
    item = make_item(item_type="course")
    out_path = covers.cover_cache_path(cache_dir, item["id"])
    out_path.write_bytes(b"ancienne-version")

    (tmp_path / item["library_path"]).mkdir()
    video_path = tmp_path / item["library_path"] / "video.mp4"
    video_path.write_bytes(b"x")

    def fake_extract(source, out, duration):
        out.write_bytes(b"nouvelle-version")
        return True

    monkeypatch.setattr(covers, "extract_video_frame", fake_extract)

    media_rows = [
        {"relative_path": "video.mp4", "media_type": "video", "extension": ".mp4", "duration_seconds": 60}
    ]

    result = covers.ensure_cover(
        tmp_path, cache_dir, item, media_rows, [], force=True
    )

    assert result == out_path
    assert out_path.read_bytes() == b"nouvelle-version"


def test_ensure_cover_priorise_une_image_deja_presente(
    tmp_path: Path, monkeypatch
) -> None:
    cache_dir = tmp_path / "covers"
    item = make_item(item_type="book")
    (tmp_path / item["library_path"]).mkdir()
    (tmp_path / item["library_path"] / "cover.png").write_bytes(b"x")

    def fake_copy(source, out):
        out.write_bytes(b"depuis-image-existante")
        return True

    def fail_if_called(*args, **kwargs):
        raise AssertionError("ne doit pas extraire le PDF si une image existe deja")

    monkeypatch.setattr(covers, "copy_existing_image", fake_copy)
    monkeypatch.setattr(covers, "extract_pdf_first_page", fail_if_called)

    resources = [{"relative_path": "cover.png", "resource_type": "image"}]
    media_rows = [{"relative_path": "livre.pdf", "media_type": "book", "extension": ".pdf", "duration_seconds": None}]

    result = covers.ensure_cover(tmp_path, cache_dir, item, media_rows, resources)

    assert result is not None
    assert result.read_bytes() == b"depuis-image-existante"


def test_ensure_cover_retombe_sur_extraction_si_image_existante_illisible(
    tmp_path: Path, monkeypatch
) -> None:
    cache_dir = tmp_path / "covers"
    item = make_item(item_type="book")
    (tmp_path / item["library_path"]).mkdir()
    (tmp_path / item["library_path"] / "livre.pdf").write_bytes(b"x")

    def fake_copy_fails(source, out):
        return False

    def fake_pdf_extract(source, out):
        out.write_bytes(b"depuis-le-pdf")
        return True

    monkeypatch.setattr(covers, "copy_existing_image", fake_copy_fails)
    monkeypatch.setattr(covers, "extract_pdf_first_page", fake_pdf_extract)

    resources = [{"relative_path": "cover.png", "resource_type": "image"}]
    media_rows = [{"relative_path": "livre.pdf", "media_type": "book", "extension": ".pdf", "duration_seconds": None}]

    result = covers.ensure_cover(tmp_path, cache_dir, item, media_rows, resources)

    assert result is not None
    assert result.read_bytes() == b"depuis-le-pdf"


def test_ensure_cover_renvoie_none_sans_rien_de_coverable(tmp_path: Path) -> None:
    cache_dir = tmp_path / "covers"
    item = make_item(item_type="document")

    result = covers.ensure_cover(tmp_path, cache_dir, item, [], [])

    assert result is None


def test_ensure_cover_renvoie_none_si_extraction_echoue(
    tmp_path: Path, monkeypatch
) -> None:
    cache_dir = tmp_path / "covers"
    item = make_item(item_type="course")
    (tmp_path / item["library_path"]).mkdir()
    (tmp_path / item["library_path"] / "video.mp4").write_bytes(b"x")

    monkeypatch.setattr(
        covers, "extract_video_frame", lambda source, out, duration: False
    )

    media_rows = [{"relative_path": "video.mp4", "media_type": "video", "extension": ".mp4", "duration_seconds": 60}]

    result = covers.ensure_cover(tmp_path, cache_dir, item, media_rows, [])

    assert result is None
    assert not covers.cover_cache_path(cache_dir, item["id"]).exists()


def test_extract_all_covers_compte_reussites_et_total(tmp_path: Path, monkeypatch) -> None:
    import sqlite3

    from library_index import create_schema, migrate_schema, now_iso

    db_path = tmp_path / "data" / "studia.db"
    db_path.parent.mkdir(parents=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    create_schema(conn)
    migrate_schema(conn)

    now = now_iso()
    conn.execute(
        "INSERT INTO items(library_path, title, item_type, created_at, updated_at) "
        "VALUES ('A', 'A', 'document', ?, ?)",
        (now, now),
    )
    conn.execute(
        "INSERT INTO items(library_path, title, item_type, created_at, updated_at) "
        "VALUES ('B', 'B', 'course', ?, ?)",
        (now, now),
    )
    conn.commit()

    cache_dir = tmp_path / "covers"

    reussites, total = covers.extract_all_covers(
        conn, tmp_path, cache_dir, verbose=False
    )

    conn.close()

    assert total == 2
    assert reussites == 0  # aucun media reel, aucune extraction possible
