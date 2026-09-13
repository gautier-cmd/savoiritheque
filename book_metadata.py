"""Recherche de métadonnées de livres sur Google Books et Open Library.

Ne remplit jamais une fiche automatiquement : ces fonctions renvoient
des candidats, à valider ou rejeter humainement (voir les routes
book_* de savoiritheque.py). Une fiche vide vaut mieux qu'une fiche
fausse.

La clé Google Books vient uniquement de la variable d'environnement
GOOGLE_BOOKS_API_KEY (jamais écrite dans le code ni le dépôt). Sans
elle, Google Books est simplement ignoré — ce n'est pas une erreur.
"""

from __future__ import annotations

import json
import os
import re
import urllib.parse
import urllib.request
from urllib.error import URLError

REQUEST_TIMEOUT_SECONDS = 8
MAX_CANDIDATES_PER_SOURCE = 5

_ISBN_TOKEN = re.compile(r"(?<!\d)(\d[\d\-\s]{8,16}[\dXx])(?!\d)")


def _isbn13_checksum_valid(digits: str) -> bool:
    total = sum((1 if i % 2 == 0 else 3) * int(d) for i, d in enumerate(digits[:12]))
    return (10 - total % 10) % 10 == int(digits[12])


def _isbn10_checksum_valid(digits: str) -> bool:
    total = 0
    for i, ch in enumerate(digits):
        value = 10 if ch.upper() == "X" else int(ch)
        total += (10 - i) * value
    return total % 11 == 0


def find_isbn(*texts: str) -> str | None:
    """Cherche un ISBN-10 ou ISBN-13 valide (somme de contrôle) dans un
    ou plusieurs textes (nom de dossier, noms de fichiers...).

    La somme de contrôle évite de confondre un vrai ISBN avec une
    autre suite de chiffres (taille de fichier, résolution...).
    """

    for text in texts:
        for raw in _ISBN_TOKEN.findall(text):
            digits = re.sub(r"[-\s]", "", raw)

            if len(digits) == 13 and digits.isdigit() and _isbn13_checksum_valid(digits):
                return digits

            if (
                len(digits) == 10
                and digits[:-1].isdigit()
                and digits[-1].upper() in "0123456789X"
                and _isbn10_checksum_valid(digits)
            ):
                return digits.upper()

    return None


def default_query(item_title: str) -> str:
    """Requête de recherche proposée à partir du nom de dossier.

    Les noms de dossiers de cette bibliothèque suivent souvent le
    motif "Titre (Éditeur ou plateforme)" : on retire ce suffixe entre
    parenthèses. Les accents ou apostrophes déjà perdus dans le nom de
    dossier ne peuvent pas être restitués automatiquement — la requête
    reste modifiable pour ça.
    """

    return re.sub(r"\s*\([^)]*\)\s*$", "", item_title).strip()


def _http_get_json(url: str) -> dict | None:
    """Requête GET renvoyant du JSON, ou None en cas d'échec.

    Le réseau, un site indisponible ou une réponse invalide ne
    doivent jamais faire planter une fiche : on renvoie juste
    "aucun résultat" dans ce cas.
    """

    try:
        with urllib.request.urlopen(url, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            return json.loads(response.read().decode("utf-8"))
    except (URLError, TimeoutError, json.JSONDecodeError, ValueError, OSError):
        return None


def search_google_books(query: str, isbn: str | None = None) -> list[dict]:
    """Candidats Google Books, ou liste vide sans clé ou sans résultat."""

    api_key = os.environ.get("GOOGLE_BOOKS_API_KEY")

    if not api_key:
        return []

    search_term = f"isbn:{isbn}" if isbn else query

    url = (
        "https://www.googleapis.com/books/v1/volumes?"
        + urllib.parse.urlencode({"q": search_term, "key": api_key, "maxResults": MAX_CANDIDATES_PER_SOURCE})
    )

    data = _http_get_json(url)

    if not data:
        return []

    candidates = []

    for entry in data.get("items", [])[:MAX_CANDIDATES_PER_SOURCE]:
        info = entry.get("volumeInfo", {})
        identifiers = info.get("industryIdentifiers", [])
        found_isbn = next(
            (i["identifier"] for i in identifiers if i.get("type") in ("ISBN_13", "ISBN_10")),
            None,
        )

        candidates.append(
            {
                "source": "google_books",
                "source_id": entry.get("id", ""),
                "title": info.get("title"),
                "authors": ", ".join(info.get("authors", [])) or None,
                "publisher": info.get("publisher"),
                "published_year": (info.get("publishedDate") or "")[:4] or None,
                "isbn": found_isbn,
                "cover_url": info.get("imageLinks", {}).get("thumbnail"),
            }
        )

    return candidates


def search_open_library(query: str, isbn: str | None = None) -> list[dict]:
    """Candidats Open Library, ou liste vide sans résultat."""

    if isbn:
        url = (
            "https://openlibrary.org/api/books?"
            + urllib.parse.urlencode(
                {"bibkeys": f"ISBN:{isbn}", "format": "json", "jscmd": "data"}
            )
        )

        data = _http_get_json(url)
        entry = (data or {}).get(f"ISBN:{isbn}")

        if not entry:
            return []

        return [
            {
                "source": "open_library",
                "source_id": f"isbn:{isbn}",
                "title": entry.get("title"),
                "authors": ", ".join(a["name"] for a in entry.get("authors", [])) or None,
                "publisher": ", ".join(p["name"] for p in entry.get("publishers", [])) or None,
                "published_year": (entry.get("publish_date") or "")[-4:] or None,
                "isbn": isbn,
                "cover_url": (entry.get("cover") or {}).get("medium"),
            }
        ]

    url = "https://openlibrary.org/search.json?" + urllib.parse.urlencode(
        {"q": query, "limit": MAX_CANDIDATES_PER_SOURCE}
    )

    data = _http_get_json(url)

    if not data:
        return []

    candidates = []

    for doc in data.get("docs", [])[:MAX_CANDIDATES_PER_SOURCE]:
        cover_id = doc.get("cover_i")
        candidates.append(
            {
                "source": "open_library",
                "source_id": doc.get("key", ""),
                "title": doc.get("title"),
                "authors": ", ".join(doc.get("author_name", [])) or None,
                "publisher": ", ".join(doc.get("publisher", [])[:1]) or None,
                "published_year": str(doc.get("first_publish_year") or "") or None,
                "isbn": (doc.get("isbn") or [None])[0],
                "cover_url": (
                    f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg"
                    if cover_id
                    else None
                ),
            }
        )

    return candidates


def search_candidates(query: str, isbn: str | None = None) -> list[dict]:
    """Interroge les deux sources et renvoie tous les candidats bruts.

    Ni fusion ni tri par confiance : les deux sources sont montrées
    côte à côte, c'est à l'humain de comparer et choisir.
    """

    return search_google_books(query, isbn) + search_open_library(query, isbn)
