"""Tests du module book_metadata.py (recherche de métadonnées de livres).

Les appels réseau réels sont remplacés par des réponses fixes : les
tests doivent passer sans connexion internet et sans clé API.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import book_metadata  # noqa: E402


# --------------------------------------------------------------------
# find_isbn / default_query
# --------------------------------------------------------------------


def test_find_isbn_reconnait_un_isbn13_valide() -> None:
    assert book_metadata.find_isbn("Livre 9782744025488.pdf") == "9782744025488"


def test_find_isbn_reconnait_un_isbn10_valide() -> None:
    assert book_metadata.find_isbn("Livre 2744025488.pdf") == "2744025488"


def test_find_isbn_ignore_un_nombre_a_treize_chiffres_invalide() -> None:
    # Meme longueur qu'un ISBN-13, mais somme de controle fausse :
    # ne doit pas etre pris pour un ISBN (ex : une taille de fichier).
    assert book_metadata.find_isbn("Fichier 1234567890123.pdf") is None


def test_find_isbn_cherche_dans_plusieurs_textes() -> None:
    assert (
        book_metadata.find_isbn("dossier sans isbn", "920 - 9782744025488.pdf")
        == "9782744025488"
    )


def test_default_query_retire_la_parenthese_finale() -> None:
    assert (
        book_metadata.default_query("Adobe Illustrator CS6 (Adobe Press)")
        == "Adobe Illustrator CS6"
    )
    assert book_metadata.default_query("Sans parenthese") == "Sans parenthese"


# --------------------------------------------------------------------
# search_google_books / search_open_library (réseau simulé)
# --------------------------------------------------------------------


def test_google_books_sans_cle_ne_cherche_pas(monkeypatch) -> None:
    monkeypatch.delenv("GOOGLE_BOOKS_API_KEY", raising=False)

    def fake_get(_url):
        raise AssertionError("ne doit pas etre appele sans cle API")

    monkeypatch.setattr(book_metadata, "_http_get_json", fake_get)

    assert book_metadata.search_google_books("titre") == []


def test_google_books_avec_cle_normalise_les_resultats(monkeypatch) -> None:
    monkeypatch.setenv("GOOGLE_BOOKS_API_KEY", "clef-de-test")

    reponse = {
        "items": [
            {
                "id": "abc123",
                "volumeInfo": {
                    "title": "Adobe Illustrator CS6",
                    "authors": ["Adobe Press"],
                    "publisher": "Pearson",
                    "publishedDate": "2012-09-20",
                    "industryIdentifiers": [
                        {"type": "ISBN_13", "identifier": "9782744025488"}
                    ],
                    "imageLinks": {"thumbnail": "https://example.com/cover.jpg"},
                },
            }
        ]
    }

    monkeypatch.setattr(book_metadata, "_http_get_json", lambda url: reponse)

    candidates = book_metadata.search_google_books("Adobe Illustrator CS6")

    assert candidates == [
        {
            "source": "google_books",
            "source_id": "abc123",
            "title": "Adobe Illustrator CS6",
            "authors": "Adobe Press",
            "publisher": "Pearson",
            "published_year": "2012",
            "isbn": "9782744025488",
            "cover_url": "https://example.com/cover.jpg",
        }
    ]


def test_open_library_isbn_sans_resultat(monkeypatch) -> None:
    monkeypatch.setattr(book_metadata, "_http_get_json", lambda url: {})

    assert book_metadata.search_open_library("", isbn="9782744025488") == []


def test_open_library_titre_normalise_les_resultats(monkeypatch) -> None:
    reponse = {
        "docs": [
            {
                "key": "/works/OL123W",
                "title": "Adobe Illustrator CS6",
                "author_name": ["Adobe Press"],
                "publisher": ["Pearson"],
                "first_publish_year": 2012,
                "isbn": ["9782744025488"],
                "cover_i": 42,
            }
        ]
    }

    monkeypatch.setattr(book_metadata, "_http_get_json", lambda url: reponse)

    candidates = book_metadata.search_open_library("Adobe Illustrator CS6")

    assert candidates == [
        {
            "source": "open_library",
            "source_id": "/works/OL123W",
            "title": "Adobe Illustrator CS6",
            "authors": "Adobe Press",
            "publisher": "Pearson",
            "published_year": "2012",
            "isbn": "9782744025488",
            "cover_url": "https://covers.openlibrary.org/b/id/42-M.jpg",
        }
    ]


def test_http_get_json_echec_reseau_ne_leve_pas(monkeypatch) -> None:
    def fake_urlopen(*args, **kwargs):
        raise OSError("reseau indisponible")

    monkeypatch.setattr(book_metadata.urllib.request, "urlopen", fake_urlopen)

    assert book_metadata._http_get_json("https://example.com") is None
