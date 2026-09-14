"""Extraction des couvertures — première page de PDF, pochette de M4B,
image de vidéo.

Jamais rien n'est écrit dans la bibliothèque : chaque couverture est
produite dans un cache séparé (à côté de la base de données), qui peut
être supprimé et reconstruit sans perte — voir cover_cache_dir().

Rien ici ne se déclenche tout seul pendant un scan : l'appelant
(library_index.py, via --covers/--recovers) décide quand extraire.
Une extraction ratée n'est jamais une erreur qui remonte : elle renvoie
simplement False, l'appelant retombe sur un remplacement visuel par
type plutôt que de faire disparaître l'item.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

EXTRACT_TIMEOUT_SECONDS = 30
COVER_MAX_WIDTH = 480

# Priorité pour les items qui ont à la fois un PDF et un M4B
# (item_type book_audio) : le livre passe avant l'audio.
COVER_ITEM_TYPES = ("book", "book_audio", "audiobook", "course")


def cover_cache_dir(db_path: Path) -> Path:
    """Dossier de cache, à côté de la base — jamais dans la bibliothèque."""

    return db_path.parent / "covers"


def cover_cache_path(cache_dir: Path, item_id: int) -> Path:
    return cache_dir / f"{item_id}.jpg"


def _run(cmd: list[str]) -> bool:
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=EXTRACT_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False

    return result.returncode == 0


def _produced(out_path: Path) -> bool:
    """Un exécutable qui renvoie 0 ne garantit pas toujours un fichier
    utilisable (ex. ffmpeg sans flux vidéo à extraire) : on vérifie."""

    return out_path.is_file() and out_path.stat().st_size > 0


def _scale_filter() -> str:
    # N'agrandit jamais une image plus petite que COVER_MAX_WIDTH.
    return f"scale='min({COVER_MAX_WIDTH},iw)':-2"


def copy_existing_image(source_path: Path, out_path: Path) -> bool:
    """Réutilise une image déjà présente dans le dossier de l'item.

    Repasse par ffmpeg pour uniformiser en JPEG à taille plafonnée,
    plutôt que de copier le fichier tel quel (qui pourrait être un PNG,
    un WebP, ou une image bien plus grande que nécessaire).
    """

    ok = _run(
        [
            "ffmpeg", "-y",
            "-i", str(source_path),
            "-vf", _scale_filter(),
            "-frames:v", "1",
            str(out_path),
        ]
    )
    return ok and _produced(out_path)


def extract_pdf_first_page(pdf_path: Path, out_path: Path) -> bool:
    # -singlefile evite le suffixe de page que pdftoppm ajoute sinon
    # (prefix-1.jpg) : la sortie porte exactement le nom demandé.
    prefix = str(out_path.with_suffix(""))

    ok = _run(
        [
            "pdftoppm", "-jpeg",
            "-f", "1", "-l", "1",
            "-singlefile",
            "-scale-to", str(COVER_MAX_WIDTH),
            str(pdf_path), prefix,
        ]
    )
    return ok and _produced(out_path)


def extract_m4b_cover(m4b_path: Path, out_path: Path) -> bool:
    ok = _run(
        [
            "ffmpeg", "-y",
            "-i", str(m4b_path),
            "-an",
            "-vf", _scale_filter(),
            "-frames:v", "1",
            str(out_path),
        ]
    )
    return ok and _produced(out_path)


def extract_video_frame(
    video_path: Path, out_path: Path, duration_seconds: float | None
) -> bool:
    """Une frame prise plus loin que la première seconde (souvent un
    écran noir ou un générique) : 10% de la durée, plafonné à 15s,
    jamais avant 1s."""

    offset = 5.0
    if duration_seconds:
        offset = min(15.0, duration_seconds * 0.1)
        offset = max(offset, 1.0)

    ok = _run(
        [
            "ffmpeg", "-y",
            "-ss", str(offset),
            "-i", str(video_path),
            "-vf", _scale_filter(),
            "-frames:v", "1",
            str(out_path),
        ]
    )
    return ok and _produced(out_path)


def ensure_cover(
    library_root: Path,
    cache_dir: Path,
    item,
    media_rows,
    resources,
    force: bool = False,
) -> Path | None:
    """Couverture en cache pour un item, en l'extrayant si besoin.

    Renvoie le chemin du fichier en cache, ou None si rien n'a pu être
    produit (aucune extraction n'est alors tentée à nouveau tant que
    force n'est pas demandé).
    """

    out_path = cover_cache_path(cache_dir, item["id"])

    if out_path.is_file() and not force:
        return out_path

    if item["item_type"] not in COVER_ITEM_TYPES:
        return None

    cache_dir.mkdir(parents=True, exist_ok=True)
    item_dir = library_root / item["library_path"]

    existing_image = next(
        (r for r in resources if r["resource_type"] == "image"), None
    )
    if existing_image is not None:
        source = item_dir / existing_image["relative_path"]
        if source.is_file() and copy_existing_image(source, out_path):
            return out_path

    if item["item_type"] in ("book", "book_audio"):
        pdf_media = next(
            (m for m in media_rows if m["extension"] == ".pdf"), None
        )
        if pdf_media is not None:
            source = item_dir / pdf_media["relative_path"]
            if source.is_file() and extract_pdf_first_page(source, out_path):
                return out_path

    if item["item_type"] in ("audiobook", "book_audio"):
        m4b_media = next(
            (m for m in media_rows if m["extension"] == ".m4b"), None
        )
        if m4b_media is not None:
            source = item_dir / m4b_media["relative_path"]
            if source.is_file() and extract_m4b_cover(source, out_path):
                return out_path

    if item["item_type"] == "course":
        video_media = next(
            (m for m in media_rows if m["media_type"] == "video"), None
        )
        if video_media is not None:
            source = item_dir / video_media["relative_path"]
            if source.is_file() and extract_video_frame(
                source, out_path, video_media["duration_seconds"]
            ):
                return out_path

    return None


def extract_all_covers(
    conn, library_root: Path, cache_dir: Path, force: bool = False, verbose: bool = True
) -> tuple[int, int]:
    """Couvertures de tous les items. Renvoie (réussies, total)."""

    items = conn.execute(
        "SELECT id, title, item_type, library_path FROM items ORDER BY title"
    ).fetchall()

    reussites = 0

    for item in items:
        media_rows = conn.execute(
            """
            SELECT relative_path, media_type, extension, duration_seconds
            FROM media WHERE item_id = ? ORDER BY sort_order
            """,
            (item["id"],),
        ).fetchall()

        resources = conn.execute(
            """
            SELECT relative_path, resource_type
            FROM resources WHERE item_id = ? ORDER BY sort_order
            """,
            (item["id"],),
        ).fetchall()

        result = ensure_cover(
            library_root, cache_dir, item, media_rows, resources, force=force
        )

        if result is not None:
            reussites += 1
        elif verbose:
            print(f"  pas de couverture : {item['title']}")

    return reussites, len(items)
