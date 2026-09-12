"""Extraction structurée des pages de présentation HTML des formations.

Chaque item peut fournir une page "000 - Presentation....html", livrée
telle quelle par la source d'achat. Sa mise en forme (classes CSS,
structure des balises) varie d'un fichier à l'autre car ces pages ne
sont pas produites par un outil commun. Plutôt que de l'afficher telle
quelle dans le navigateur (avec sa propre feuille de style), cette
fonction en extrait la matière utile — couverture, fiche technique,
texte — pour la réafficher avec le gabarit de Savoirthèque.

Convention observée sur les quatre fichiers de test, quelle que soit
la mise en page (tableau ou lignes en div) : le libellé de chaque
donnée de fiche technique porte la classe CSS "k".
"""

from __future__ import annotations

from bs4 import BeautifulSoup, Tag


def _extract_runs(el: Tag) -> list[dict]:
    """Texte d'un élément, en gardant les liens comme des liens.

    Une valeur de fiche technique est parfois un simple texte, parfois
    un ou plusieurs liens (source, ISBN...). On les affichera avec le
    style de Savoirthèque, mais il faut d'abord distinguer ce qui est
    cliquable de ce qui ne l'est pas.
    """

    runs: list[dict] = []

    for child in el.children:
        if isinstance(child, Tag) and child.name == "a":
            text = child.get_text(strip=True)
            if text:
                runs.append({"text": text, "href": child.get("href")})
        else:
            text = (
                child.get_text(strip=True)
                if isinstance(child, Tag)
                else str(child).strip()
            )
            if text:
                runs.append({"text": text, "href": None})

    return runs


def _is_link_only(el: Tag) -> bool:
    """Vrai pour un bloc qui ne contient que des liens.

    Ce sont des raccourcis de téléchargement vers les fichiers de
    l'item, déjà listés ailleurs sur la fiche : ce bloc n'apporte rien
    de plus une fois réaffiché avec nos propres moyens.
    """

    if el.find("a") is None:
        return False

    texte_hors_liens = "".join(
        node
        for node in el.find_all(string=True, recursive=True)
        if not (node.parent and node.parent.name == "a")
    ).strip()

    return not texte_hors_liens


def parse_presentation(html_text: str) -> dict:
    """Renvoie {"cover_data_uri", "facts", "blocks"} depuis le HTML brut.

    facts : liste de {"label", "runs"} (fiche technique).
    blocks : liste ordonnée de paragraphes/titres/listes/notes,
    chacun {"type": ..., ...}.
    """

    soup = BeautifulSoup(html_text, "html.parser")

    for tag in soup.find_all(["script", "style"]):
        tag.decompose()

    cover_data_uri = None
    img = soup.find("img")
    if img and (img.get("src") or "").startswith("data:image"):
        cover_data_uri = img["src"]

    facts = []
    for key_el in soup.select(".k"):
        value_el = key_el.find_next_sibling()
        if value_el is not None:
            runs = _extract_runs(value_el)
            if runs:
                facts.append({"label": key_el.get_text(strip=True), "runs": runs})

    body = soup.body or soup

    for el in body.select("table, .fiche"):
        el.decompose()

    blocks: list[dict] = []

    for el in body.find_all(["h2", "h3", "p", "ul", "div"], recursive=False):
        if el.name in ("h2", "h3"):
            text = el.get_text(strip=True)
            if text:
                blocks.append({"type": "heading", "text": text})

        elif el.name == "p":
            text = el.get_text(" ", strip=True)
            if text:
                blocks.append({"type": "paragraph", "text": text})

        elif el.name == "ul":
            items = [
                item
                for li in el.find_all("li", recursive=False)
                if (item := li.get_text(" ", strip=True))
            ]
            if items:
                blocks.append({"type": "list", "items": items})

        elif el.name == "div":
            if _is_link_only(el):
                continue

            text = el.get_text(" ", strip=True)
            if text:
                blocks.append({"type": "note", "text": text})

    return {"cover_data_uri": cover_data_uri, "facts": facts, "blocks": blocks}
