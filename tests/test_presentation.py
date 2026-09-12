"""Tests du parseur de pages de présentation (presentation.py).

Les quatre pages réelles de la bibliothèque de test utilisent deux
mises en page différentes (tableau, ou lignes en div avec couverture) ;
ces tests couvrent les deux, plus le filtrage des blocs qui ne
contiennent que des liens de téléchargement.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from presentation import parse_presentation  # noqa: E402

TABLE_STYLE_HTML = """
<html><head><style>body{color:red}</style></head><body>
<h1>Titre</h1>
<table>
<tr><td class="k">Source</td><td><a href="https://example.com">Exemple</a></td></tr>
<tr><td class="k">Durée</td><td>5h00</td></tr>
</table>
<div class="dl-block"><a class="dl" href="fichier.pdf">Télécharger</a></div>
<h2>Sujet</h2>
<p>Un paragraphe de présentation.</p>
<ul><li>Item un</li><li>Item deux</li></ul>
</body></html>
"""

FICHE_STYLE_HTML = """
<html><head><style>body{color:red}</style></head><body>
<h1>Titre Livre</h1>
<div class="fiche">
<img src="data:image/png;base64,AAAA" alt="Couverture">
<div class="meta">
<div class="row"><span class="k">Auteur</span><span>Jean Dupont</span></div>
</div>
</div>
<h2>Description</h2>
<p>Un livre.</p>
</body></html>
"""


def test_structure_tableau_extrait_faits_et_blocs() -> None:
    result = parse_presentation(TABLE_STYLE_HTML)

    assert result["cover_data_uri"] is None

    facts = {f["label"]: f["runs"] for f in result["facts"]}
    assert facts["Source"] == [{"text": "Exemple", "href": "https://example.com"}]
    assert facts["Durée"] == [{"text": "5h00", "href": None}]

    assert result["blocks"] == [
        {"type": "heading", "text": "Sujet"},
        {"type": "paragraph", "text": "Un paragraphe de présentation."},
        {"type": "list", "items": ["Item un", "Item deux"]},
    ]


def test_structure_fiche_extrait_couverture_et_faits() -> None:
    result = parse_presentation(FICHE_STYLE_HTML)

    assert result["cover_data_uri"] == "data:image/png;base64,AAAA"

    facts = {f["label"]: f["runs"] for f in result["facts"]}
    assert facts["Auteur"] == [{"text": "Jean Dupont", "href": None}]

    assert result["blocks"] == [
        {"type": "heading", "text": "Description"},
        {"type": "paragraph", "text": "Un livre."},
    ]


def test_bloc_ne_contenant_que_des_liens_est_filtre() -> None:
    # Le bloc "dl-block" de TABLE_STYLE_HTML ne contient qu'un lien de
    # telechargement, deja couvert par la liste des medias/ressources
    # de la fiche : il ne doit pas apparaitre parmi les blocs de texte.
    result = parse_presentation(TABLE_STYLE_HTML)

    textes = [b.get("text", "") for b in result["blocks"]]
    assert not any("Télécharger" in t for t in textes)


def test_bloc_avec_texte_et_lien_est_conserve_comme_note() -> None:
    html = """
    <html><body>
    <h1>Titre</h1>
    <div class="note">Attention ceci est important. <a href="x">lien</a></div>
    </body></html>
    """

    result = parse_presentation(html)

    assert result["blocks"] == [
        {"type": "note", "text": "Attention ceci est important. lien"}
    ]
