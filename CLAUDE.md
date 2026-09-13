# Studia

Bibliothèque personnelle et plateforme d'apprentissage multi-supports,
dérivée d'OfflineU (MIT, WhiskeyCoder).

## Avec qui tu travailles

Gautier, graphiste, pas administrateur système. Il comprend les concepts
mais n'écrit pas de code et ne corrige pas une commande lui-même.

- Réponds en français.
- Explique ce que fait chaque changement et pourquoi, avant de l'appliquer.
- Définis les termes techniques au passage, sans qu'il ait à demander.
- Une chose à la fois. Pas de « il faudrait aussi » qui ouvre trois chantiers.
- Pas de félicitations ni d'enthousiasme de façade.
- Ne suppose rien sur la machine : vérifie, ou demande.

## Interdits absolus

1. Ne jamais modifier l'OfflineU de production.
2. Ne jamais écrire dans /srv/disk1/Media/Formations (serveur maisonsrv,
   192.168.31.33). Cette bibliothèque sert uniquement de source de copie.
3. Ne jamais modifier ni renommer les fichiers médias de l'utilisateur,
   en particulier pas pour contourner un problème d'Unicode.
4. Ne jamais rendre le projet dépendant de Calibre. Les fichiers Calibre
   existants servent au plus de référence pour vérifier un résultat.
5. Ne rien documenter qui n'existe pas encore : ça va dans le backlog.
6. Ne jamais écrire une clé API (GOOGLE_BOOKS_API_KEY ou une autre) dans
   le code, un fichier du dépôt ou un message de commit. Elle vient
   uniquement de la variable d'environnement, propre à chaque
   installation ; l'application doit fonctionner sans (la source
   correspondante devient juste indisponible, pas une erreur).

## Environnement

    Poste          gautier@gautierPC, développement exclusivement local
    Dépôt          /home/gautier/dev/offlineu-lab
    Branche        offlineu-lab
    Remote origin  github.com/gautier-cmd/studia (le sien)
    Remote upstream github.com/WhiskeyCoder/OfflineU (projet d'origine, lecture seule)
    Venv           .venv (à activer : source .venv/bin/activate)
    Bibliothèque   /home/gautier/offlineu-test-library
    Données        /home/gautier/offlineu-test-data/studia.db
    Flask          3.1.1
    ffprobe        /usr/bin/ffprobe
    GOOGLE_BOOKS_API_KEY   variable d'environnement, propre à chaque
                           installation (jamais dans le dépôt, voir
                           interdit n°6). Absente ici en développement :
                           Google Books est alors simplement ignoré.

## État actuel

### Fichiers

    offlineu_core.py    application OfflineU d'origine, 1003 lignes, INTACTE
    library_index.py    scanner SQLite de Studia
    studia.py           application web de consultation (Flask) : grille,
                        fiche d'item, lecteur vidéo
    presentation.py     extrait couverture/fiche technique/texte des pages
                        "000 - Presentation....html" (BeautifulSoup) pour
                        les réafficher avec le gabarit de Studia
                        plutôt que telles quelles
    book_metadata.py    recherche de métadonnées de livres sur Google
                        Books et Open Library, détection d'ISBN
    tests/              test_library_index.py, test_studia.py,
                        test_presentation.py, test_book_metadata.py,
                        test_notes.py — 60 tests pytest
    templates/          course_dashboard, lesson_view, select_course
                        (OfflineU, CSS repris comme point de départ) +
                        _base.html, library_grid, item_detail,
                        video_player, orphan_notes, _note_widget
                        (Studia — héritent de _base.html)
    static/style.css    seule feuille de style de Studia, variables CSS
                        en haut (couleurs, espacements, rayons, tailles
                        de police, police)
    design/             maquettes PNG de Gautier — pas encore de
                        contenu, rien n'en dépend

### Modèle de données

Item (un dossier de premier niveau) contient des Media et des Resources.
Le concept Lesson d'OfflineU est abandonné.

Tables SQLite, schéma version 4 :
schema_info, users, items, media, resources, progress, book_search,
book_candidates, notes.

    media       item_id, relative_path, parent_path, sort_order,
                media_type, extension, size_bytes,
                duration_seconds, probed_at, created_at
                UNIQUE(item_id, relative_path)
    resources   mêmes colonnes sans durée
    progress    UNIQUE(user_id, media_id) — jamais media_id seul

    book_search      item_id (clé), query, searched_at — dernière
                     recherche lancée pour un item livre
    book_candidates  item_id, source ('google_books'|'open_library'
                     |'manual'), source_id, champs bibliographiques,
                     decision ('proposed'|'accepted'|'rejected')
                     UNIQUE(item_id, source, source_id)

book_search et book_candidates ne sont jamais touchées par scan_library :
un rescan ne peut donc pas défaire une métadonnée validée ni faire
réapparaître un candidat rejeté.

    notes   library_path (clé), text, updated_at — pas de clé
            étrangère du tout vers items

notes est rattachée au chemin de bibliothèque, pas à item_id, et le
scanner n'est pas modifié : quand un dossier disparaît, scan_library
supprime l'item comme avant, la note reste simplement en base, non
liée à rien. Si le même chemin revient, elle se retrouve automatiquement.
Si le dossier a été renommé (chemin différent), la note devient
orpheline — visible et récupérable sur /notes-orphelines (voir
"Bloc-notes" ci-dessous), jamais perdue.

parent_path est le sous-dossier du fichier, vide à la racine : c'est ce
qui représente les chapitres. sort_order est le rang dans l'item, calculé
par tri naturel (10 après 9).

### Garanties du scanner, protégées par les tests

- Les ids de media sont stables entre deux scans : upsert sur
  (item_id, relative_path), jamais DELETE puis INSERT. C'est ce qui
  empêche ON DELETE CASCADE d'effacer la progression.
- Seules les lignes dont le fichier a réellement disparu sont supprimées.
- La durée est conservée tant que size_bytes ne change pas, remise à NULL
  sinon.
- Une base au schéma v1 est migrée sur place par ALTER TABLE, sans perdre
  d'id.
- Unicode, accents et apostrophes typographiques traités sans renommage.

### Classification actuelle (heuristique, à améliorer)

    contient vidéo        -> course
    livre + audio         -> book_audio
    livre                 -> book
    audio                 -> audiobook
    sinon                 -> document

    PDF dans un course    -> resource
    PDF dans un book      -> media

### Bibliothèque de test

    Adobe Illustrator CS6 (Adobe Press)    book,  1 média, 2 ressources
    Devenez Copywriter avec les IA         course, 49 médias, 5h44
    Motion Design - la formation complete  course, 258 médias, 27 chapitres, 55h10
    S organiser pour reussir (David Allen) audiobook, 1 M4B, 3h05

### Application web (studia.py)

    /                       grille des items (type, durée, nb de médias)
    /item/<id>              fiche : présentation extraite (si le fichier
                            existe), chapitres/médias, ressources
    /watch/<media_id>       lecteur vidéo : playlist par chapitre,
                            précédent/suivant, enchaînement automatique
    /media/<media_id>/file  sert le fichier vidéo (Range HTTP géré par
                            Flask, permet d'avancer/reculer)

    POST /item/<id>/book-search                        lance une recherche
    POST /item/<id>/book-candidate/<id>/accept          valide un candidat
    POST /item/<id>/book-candidate/<id>/reject          rejette un candidat
    POST /item/<id>/book-candidate/<id>/unreject        annule un rejet
    POST /item/<id>/book-manual                         saisie manuelle

    POST /item/<id>/note                    enregistre la note (JSON)
    GET  /notes-orphelines                  notes dont le dossier a disparu
    POST /notes-orphelines/reattach         rattache une note à un autre item

Chaque page de présentation a sa propre mise en page HTML (tableau, ou
lignes en div avec couverture) selon l'item : presentation.py ne dépend
d'aucune des deux en particulier, il repère les libellés de fiche
technique par leur classe CSS commune ("k") et les blocs de texte par
leur position dans le corps de page.

### Métadonnées de livres (book_metadata.py)

Sur la fiche d'un item de type book/book_audio/audiobook, une carte
"Métadonnées" propose une recherche sur Google Books (avec
GOOGLE_BOOKS_API_KEY) et Open Library, en priorisant un ISBN détecté
dans les noms de fichiers/dossier (somme de contrôle vérifiée) sur une
requête par titre (nettoyée du suffixe entre parenthèses, modifiable
avant de lancer la recherche).

Ni fusion ni tri par confiance entre les deux sources : les candidats
sont montrés côte à côte, à valider ou rejeter à la main. Rien n'est
jamais rempli automatiquement — une fiche vide vaut mieux qu'une fiche
fausse. Un candidat rejeté reste mémorisé (consultable, réversible) et
n'est jamais re-proposé. La saisie manuelle est traitée comme une
source de plus, immédiatement validée.

Cette tranche couvre les livres. Les formations restent couvertes par
la page de présentation locale (ci-dessus) : les deux mécanismes
coexistent, aucun n'est un repli pour l'autre.

### Bloc-notes (une note par item)

Un seul champ texte par item, affiché à deux endroits qui pointent
vers la même donnée : en bas de la fiche (/item/<id>, pour tous les
types) et en bas du lecteur vidéo (/watch/<media_id>, pour les
courses). Modifier la note d'un côté la met à jour de l'autre au
prochain chargement de page.

- Enregistrement automatique après une pause de frappe (900 ms), et
  immédiatement si l'onglet est masqué ou fermé (navigator.sendBeacon,
  pensé pour aboutir même pendant un déchargement de page). Un filet
  local (localStorage) garde aussi chaque frappe : si une version plus
  récente que celle du serveur est retrouvée au chargement (crash juste
  avant l'envoi différé), la page propose de la restaurer.
- Le bouton "Insérer un repère" (uniquement sur le lecteur) écrit une
  ligne texte au format "Vidéo N — titre — mm:ss (/watch/id?t=secondes)"
  à la position du curseur. Ces lignes sont aussi détectées par une
  expression régulière côté navigateur et affichées comme une petite
  liste cliquable au-dessus du champ — pas de zone de texte enrichi,
  juste un motif reconnu dans le texte brut.
- La reprise de position (?t=secondes) se fait par script sur
  l'évènement loadedmetadata du lecteur, pas par le fragment d'URL
  #t=secondes : ce fragment (pourtant standard, "Media Fragments URI")
  s'est révélé peu fiable ici pour positionner une vidéo servie
  localement — vérifié en pratique, currentTime restait à 0.
- Bouton Imprimer : une feuille de style @media print masque tout sauf
  le titre de l'item, la date du jour et le texte de la note.

Pas encore fait : sauvegarde de la position de lecture (progress),
lecteur audio/PDF.

### CSS et gabarits (réorganisation, aucun changement visuel)

Toutes les pages de Studia héritent de templates/_base.html
(squelette HTML, `<link>` vers static/style.css, blocs title/body_class
/header/content/scripts) plutôt que de recopier `<html><head>...`
et leur propre `<style>`. static/style.css est la seule feuille de
style, avec les couleurs, espacements, rayons et tailles de police en
variables CSS (`:root`) en haut du fichier.

Certaines pages ont de vraies différences (largeur de `.container`,
taille du `<h1>` d'en-tête, marge du `.card` sur le lecteur, taille des
boutons sur la page des notes orphelines) : plutôt que de les fondre en
une seule règle au risque de changer un peu chacune, chaque `<body>`
porte une classe (page-grid, page-item, page-player, page-orphans) et
le fichier CSS a une règle scopée par page pour chaque différence
réelle — repérable en cherchant "body.page-" dans static/style.css.

## Objectif suivant

Une application web locale mono-utilisateur lisant SQLite :
grille de couvertures -> fiche d'un item -> lecteurs -> progression.

Décision prise : écrire une nouvelle application (studia.py) à côté
d'OfflineU plutôt que de modifier offlineu_core.py, dont les 154
occurrences de « lesson » et l'état global current_course sont
incompatibles avec le modèle. Le CSS des templates existants est
réutilisable comme point de départ.

Lecteurs prévus, dans cet ordre : vidéo (fait), audio/M4B avec chapitres,
PDF (PDF.js). EPUB plus tard.

Progression selon le type : secondes pour vidéo et audio, page pour PDF,
position pour EPUB.

## Backlog (ne pas traiter sans demande explicite)

- Fichier renommé = nouvel id = progression perdue. Appariement par
  empreinte à prévoir. (Ne concerne plus les notes : elles survivent à
  un renommage de dossier en devenant orphelines et récupérables, voir
  "Bloc-notes" — reste vrai pour la progression de lecture par média.)
- Le compteur « sans durée » du résumé compte aussi les PDF, qui n'en ont
  pas. Affichage à corriger.
- Chapitres internes des M4B (ffprobe -show_chapters), distincts des
  chapitres par sous-dossier.
- Nombre de pages des PDF.
- Couvertures dans la grille : aucun fichier image dédié dans les
  quatre cas de test, mais deux d'entre eux (les books) ont déjà une
  couverture intégrée dans leur page de présentation, que presentation.py
  extrait déjà pour la fiche — reste à la réutiliser aussi dans la
  grille. Pour les deux autres (les courses, sans page de présentation
  avec image) : à extraire autrement (première page PDF, pochette M4B,
  image de vidéo) ou à récupérer en ligne.
- Métadonnées de formations par moissonnage des plateformes commerciales
  (TUTO.com, Udemy, LinkedIn, Elephorm...). Autorisé (usage strictement
  personnel, décision explicite de Gautier), mais pas encore fait : pas
  d'API publique sur ces sites, donc un scraper par plateforme, plus
  fragile qu'un appel d'API (casse si le site change sa page). À
  cadrer dans un plan séparé le moment venu. Pour les livres, voir
  "Métadonnées de livres" ci-dessus (fait). Restent aussi, pour toutes
  les fiches : les faits déjà lisibles par le scanner (durée, chapitres,
  nombre de médias) à afficher en tête de fiche, et une saisie manuelle
  générique pour les contenus de Gautier lui-même.
- Si un moissonnage de plateforme ne trouve rien : donner le nom de
  l'item à Gautier et soit attendre une URL (pour retenter le
  moissonnage dessus), soit proposer la saisie manuelle — même logique
  que "Aucune ne convient" côté livres.
- requirements-dev.txt pour pytest.
- Clé SSH GitHub à la place du token en clair dans ~/.git-credentials.
- Watcher automatique — seulement après un scanner manuel fiable.
- Multi-utilisateur réel, authentification, rôles, HTTPS : V2.

## Méthode de travail

- Petits commits cohérents et testables, messages en anglais.
- pytest tests/ doit passer avant chaque commit.
- git push après chaque commit : c'est la seule sauvegarde du projet.
- Les médias ne sont jamais touchés, la base de données est un index
  reconstructible.
