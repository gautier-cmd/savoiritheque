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
    covers.py           extraction des couvertures (PDF, M4B, vidéo),
                        cache à côté de la base — jamais écrit dans la
                        bibliothèque, voir "Tranche 3"
    tests/              test_library_index.py, test_studia.py,
                        test_presentation.py, test_book_metadata.py,
                        test_notes.py, test_covers.py — 70 tests pytest
    templates/          course_dashboard, lesson_view, select_course
                        (OfflineU, CSS repris comme point de départ) +
                        _base.html, library_grid, item_detail,
                        video_player, orphan_notes, _note_widget
                        (Studia — héritent de _base.html)
    static/tokens.css   seul endroit où sont déclarés couleurs,
                        typographie, espacements, rayons, transitions,
                        breakpoints (voir "Refonte visuelle")
    static/style.css    styles des composants, consomme uniquement
                        tokens.css — pas de :root propre à part
                        quelques compléments sans équivalent officiel
                        (danger, fond sélectionné), clairement isolés
                        en tête de fichier
    static/fonts/       Inter, deux variable fonts (romain, italique)
                        au format woff2 — jamais Google Fonts, jamais
                        de .ttf dans le dépôt (2 à 2,5x plus lourd)
    static/images/      copies de travail des logos (logo.png,
                        logo-picto.png), servies par Flask — design/
                        garde les fichiers d'origine de Gautier
    design/             specification.md (spec de la refonte, source de
                        vérité — voir ci-dessous), 3 maquettes PNG,
                        2 logos (LOGO.png, LOGO-Picto.png)

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

    GET /cover/<item_id>                    sert la couverture en cache (404 sinon)

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

### CSS et gabarits

Toutes les pages de Studia héritent de templates/_base.html (squelette
HTML, `<link>` vers tokens.css puis style.css, blocs title/body_class/
active_nav/header/content/print/scripts) plutôt que de recopier
`<html><head>...` et leur propre `<style>`.

Certaines pages ont de vraies différences (largeur de `.container`,
taille du `<h1>` d'en-tête, marge du `.card` sur le lecteur, taille des
boutons sur la page des notes orphelines) : plutôt que de les fondre en
une seule règle au risque de changer un peu chacune, chaque `<body>`
porte une classe (page-grid, page-item, page-player, page-orphans) et
le fichier CSS a une règle scopée par page pour chaque différence
réelle — repérable en cherchant "body.page-" dans static/style.css.

Le bloc `print` (pas `content`) est le seul endroit où appeler
`render_print_block(...)` : il doit rester un enfant direct de
`<body>`, en dehors de `.app-shell`, sinon l'impression (qui masque
tout sauf `#print-only`) ne peut plus l'atteindre — un ancêtre caché
cache aussi ses enfants, même ceux qu'on voudrait montrer.

## Refonte visuelle

Source de vérité : `design/specification.md`. En cas de doute sur une
question de design, la relire plutôt que deviner. Deux écarts assumés
par rapport à ce document :

- Section 34 (notes individuelles avec timestamp, éditer/supprimer)
  est obsolète — on garde une seule note Markdown par formation (voir
  "Bloc-notes" ci-dessus et "Format des notes" ci-dessous).
- Les breakpoints (section 8) ne sont pas dans la spec : dérivés
  ci-dessous, voir "Tranche 1".

### Contraintes absolues de la refonte

- **Logos** : utiliser `design/LOGO.png` et `design/LOGO-Picto.png` tels
  quels. Ne jamais les redessiner, ni les recréer en CSS ou en SVG
  inline. Le wordmark a "Stud" en blanc : si un fond clair apparaît
  quelque part sous le logo, le signaler à Gautier plutôt que modifier
  le fichier.
- **Aucune donnée fictive.** Ce qui existe réellement en base : titre
  (= nom de dossier), item_type, médias (chemin/type/extension/taille/
  durée), ressources, chapitres (parent_path/sort_order), notes,
  progression. Les maquettes montrent en plus : couvertures,
  formateurs, année, tags, descriptions, libellés de chapitres
  nettoyés, pourcentages de progression, favoris, notifications, avatar,
  compteurs par type — rien de tout ça n'existe aujourd'hui. Si une
  donnée manque, appliquer l'état vide prévu par la spec (section 49)
  ou retirer l'élément, jamais la remplir avec un exemple ou un chiffre
  inventé.
- **Libellés de chapitre.** Les vrais dossiers s'appellent
  "0100 - Introduction au Motion Design", pas "01 - ...". Nettoyage à
  l'affichage uniquement (ex. retirer le préfixe numérique technique,
  reformater) — ne jamais renommer les dossiers ou fichiers réels
  (interdit n°3).
- **Pas de compte utilisateur en V1.** Favoris, cloche de notifications,
  avatar : retirés des écrans plutôt que simulés, jusqu'à un vrai compte
  (V2, déjà au backlog).
- **Polices hors-ligne.** Inter est servie depuis `static/fonts/`
  (@font-face), jamais depuis Google Fonts — l'appli doit fonctionner
  sans connexion internet.

### Format des notes

Markdown, stocké brut (colonne `notes.text` inchangée). V1 : champ
texte simple (pas d'éditeur visuel) avec une barre d'outils qui insère
la syntaxe — gras, italique, titres 1 à 3, liste, bloc de code, plus le
bouton "Insérer un repère" déjà en place — et une bascule aperçu qui
rend le Markdown. Pas de bouton souligné : ça n'existe pas en Markdown
standard, et pas de HTML dans les notes. Les repères horodatés restent
cliquables dans l'aperçu et à l'impression.

V2 (backlog) : éditeur enrichi (le gras et les titres s'affichent
directement), toujours sur le même Markdown stocké — le stockage brut
dès la V1 est justement ce qui permet ce changement plus tard sans nouvelle
migration.

### Ordre de travail (une tranche à la fois, arrêt entre chaque)

1. Design tokens — fait, voir ci-dessous.
2. Layout global et sidebar — fait, voir ci-dessous.
3. Extraction des couvertures (PDF, M4B, vidéo), cache hors bibliothèque,
   jamais écrites dedans ; placeholder par type sinon — fait, voir
   ci-dessous.
4. Écran Bibliothèque : recherche, filtres, grille, cartes.
5. Responsive.
6. Fiche de contenu — fait, voir ci-dessous.
7. Lecteur vidéo et programme.
8. Notes.
9. États vides et erreurs.

### Tranche 1 — design tokens (fait)

`static/tokens.css`, chargé avant `static/style.css` dans
`templates/_base.html`. Couleurs : palette officielle de la spec
(section 4), recopiée sans ré-estimation. Typographie : Inter en
`@font-face` (variable font, une seule plage de graisse 100–900 par
style plutôt qu'un fichier par graisse), échelle et graisses de la
section 6 avec le point choisi dans chaque plage documenté en
commentaire. Espacements et rayons : aucune valeur n'est imposée par la
spec (elle demande seulement qu'ils soient centralisés) — échelle de 4px
et trois rayons choisis, à ajuster librement. Transitions : valeurs
sobres par défaut, marquées "à ajuster" dans le fichier — rien à cet
égard dans la spec.

**Breakpoints**, dérivés (spec section 8 : pas de valeurs arbitraires,
doivent venir du moment où le contenu se comprime) — raisonnement :
largeur minimale de carte choisie à 260px (vignette 16:9 + 2 lignes de
titre + une ligne de métadonnées, section 13/14), espacement de grille
24px, empreinte de sidebar estimée à chaque palier (240px complète,
200px réduite, 72px icônes seules, 0 en drawer), plus le remplissage de
page. Seuil = empreinte sidebar + remplissage + N×260 + (N-1)×24,
arrondi :

    720px   -> 2 colonnes devient confortable (tablette)
    1120px  -> 3 colonnes devient confortable (desktop intermédiaire)
    1440px  -> 4 colonnes devient confortable (desktop large)

Le CSS ne permet pas d'utiliser une variable dans une condition
`@media` : ces tokens documentent et justifient les valeurs, mais les
futures règles `@media` devront répéter ces mêmes nombres en dur — à
garder synchronisés à la main si on retouche le raisonnement.

### Tranche 2 — layout global et sidebar (fait)

Avant de commencer, deux nettoyages demandés par Gautier :

- **Une seule feuille de style.** `static/style.css` avait son propre
  `:root` (ancienne palette bleue d'OfflineU) qui l'emportait sur
  `tokens.css` pour les noms en commun — deux sources pour la même
  valeur, source de confusion dès qu'on toucherait à la mise en page.
  Supprimé : `style.css` ne déclare plus que les quelques compléments
  sans équivalent officiel (voir "Fichiers"), tout le reste vient de
  `tokens.css`. Résultat direct et voulu : les pages existantes ont
  changé de couleurs et de police d'un coup (thème bleu -> palette
  officielle) avant même que leur mise en page soit reconstruite —
  normal, ce sont deux choses différentes qui se font l'une après
  l'autre, pas un rendu à moitié fini.
- **Polices en woff2.** Les .ttf déposés par Gautier ont été convertis
  (fonttools) puis retirés du dépôt ; `tokens.css` charge les .woff2
  (2 à 2,5 fois plus légers, format standard du web).

**Sidebar**, dans `_base.html`, identique sur toutes les pages :
- Logo (`static/images/logo.png`) en haut.
- Navigation (section 7.1, Favoris et Notifications retirés — pas de
  compte utilisateur en V1, voir "Contraintes absolues"). Seule
  "Bibliothèque" a une vraie destination aujourd'hui ; Continuer,
  Formations, Livres, Audiobooks, Notes, Paramètres s'affichent mais
  sont désactivés (`.disabled`, sans lien) tant que leur écran n'existe
  pas — pas de lien qui mène nulle part, pas de fonctionnalité simulée.
  Notes existe déjà comme page séparée (/notes-orphelines) mais n'est
  pas la même chose qu'"toutes mes notes" : pas relié pour ne pas
  créer une confusion entre les deux.
- Item actif marqué via `{% block active_nav %}` (une chaîne : library,
  notes...), lu dans `_base.html` avec `self.active_nav()` et comparé
  au `key` de chaque item de nav.
- Signature en bas ("Apprendre / Explorer / Progresser / Pour un
  meilleur / Demain") : texte de la maquette, repris tel quel — c'est
  une signature de marque, pas une donnée fabriquée.

Icônes de nav : SVG simples écrites à la main (pas de librairie
d'icônes, pas de CDN — cohérent avec l'appli hors-ligne). Ce n'est pas
le logo, donc pas concerné par l'interdiction de recréer le logo en SVG.

Contenu de chaque page (grille, fiche, lecteur, notes orphelines) :
inchangé dans cette tranche, simplement replacé à côté de la sidebar
dans `.app-main`. Leur reconstruction vient avec les tranches 4, 6 et 7.

### Tranche 3 — extraction des couvertures (fait)

`covers.py`, aucune nouvelle dépendance : `ffmpeg` et `pdftoppm`
(poppler-utils) étaient déjà installés sur la machine, appelés en
sous-processus comme `ffprobe` l'est déjà dans library_index.py.

Cache dans `<dossier de la base>/covers/<item_id>.jpg` — jamais dans la
bibliothèque, jamais suivi par git (déjà hors du dépôt de toute façon,
entrée `.gitignore` ajoutée par précaution). Ordre de priorité par
item :

1. Une image déjà présente dans le dossier de l'item (`resources` avec
   `resource_type = 'image'`) — recopiée en JPEG à taille plafonnée
   (480px) plutôt qu'utilisée telle quelle, pour un format uniforme.
2. book/book_audio : première page du PDF (`pdftoppm -singlefile`,
   évite le suffixe de page qu'il ajoute sinon).
3. audiobook/book_audio : pochette intégrée au M4B (`ffmpeg`, réencodée
   en JPEG — le flux copié tel quel donnerait un format variable selon
   le fichier).
4. course : une frame de la première vidéo, à 10% de sa durée (plafond
   15s, jamais avant 1s) — jamais la première seconde, souvent un écran
   noir ou un générique.

Si rien de tout ça n'aboutit (pas de média du bon type, outil en échec,
fichier illisible) : aucune erreur, aucun fichier en cache, l'item
reste dans la grille avec le badge de couleur par type déjà existant —
vérifié avec le livre audio de test, qui n'a pas de pochette intégrée.

Ni le scan ni la web app ne déclenchent d'extraction : c'est un choix
explicite, `library_index.py --covers` (manquantes) ou `--recovers`
(tout, même déjà en cache) — mêmes noms de logique que `--probe`/
`--reprobe`. L'app web se contente de lire le cache (`GET /cover/<id>`,
404 si absent) ; `library_grid.html` affiche l'image si elle existe,
sinon retombe sur l'emoji par type comme avant.

Non testé en pytest (nécessiterait des fichiers M4B/vidéo valides
synthétisés) : l'extraction M4B et vidéo, vérifiées à la main sur la
vraie bibliothèque de test à la place. Testé en pytest : l'extraction
PDF (avec un PDF minimal écrit à la main, `pdftoppm` s'en accommode
sans xref complet), et toute la logique de cache/priorité/repli avec
des extracteurs remplacés.

La carte de la grille n'est pas encore celle de la spec (16:9, badge,
auteur...) — seul le remplacement emoji -> image a été branché pour
vérifier le mécanisme. La vraie carte vient en tranche 4.

### Tranche 6 — fiche de contenu (fait)

Reprise de la fiche (`templates/item_detail.html`) selon les sections
20 à 28 de la spec : elle s'était éloignée en pile verticale de cartes.
Nouvelle structure : hero horizontal (couverture ~30-35% à gauche ;
badge, titre, auteur/formateur, durée, nombre de médias, chapitres,
année, boutons d'action à droite — `extract_hero_fields()` dans
studia.py, qui choisit auteur/année parmi la présentation locale puis
les métadonnées de livre validées), suivi de trois onglets À propos /
Programme / Ressources (bascule en JS pur, `data-tab-target` /
`data-panel`, pas de bibliothèque).

Cinq corrections demandées par Gautier :

1. **Logo.** La fenêtre principale (grille) affichait `<h1>Studia</h1>` ;
   remplacé par `static/images/logo.png` (picto + texte), comme la
   sidebar.
2. **Redondances supprimées :**
   - La table des matières que certaines présentations répètent en fin
     de texte (ex. Copywriter : "Table des matières" ; Motion Design :
     "Les vingt-sept chapitres", sans le mot "sommaire") duplique le
     programme réel tiré du scan. `presentation.py` la coupe désormais
     à l'affichage (`_drop_table_of_contents`, repérage par mot-clé de
     titre — "table des matières", "sommaire", "chapitre", "programme"
     — jamais par position, donc un contenu qui n'a pas ce genre de
     titre n'est jamais tronqué). Le programme réel reste seul, dans
     l'onglet Programme, en accordéon (`<details>`) replié par défaut.
   - Sur Adobe Illustrator, Auteur/Éditeur apparaissaient à la fois
     dans les faits extraits de la présentation et dans la carte
     Métadonnées validée. `filter_duplicated_presentation_facts()`
     (studia.py) retire des faits de présentation les libellés que la
     carte Métadonnées affiche déjà, une fois validée — **correctif
     provisoire** : la vraie solution (traçabilité de la source de
     chaque champ) est la prochaine tranche demandée par Gautier, pas
     encore commencée.
3. **Bouton d'action principal** du hero : lien direct vers la première
   vidéo (`first_video_id`) si l'item en a une, sinon un bouton désactivé
   pour livre/livre audio/audiobook (pas encore de lecteur audio/PDF).
   Le libellé "Reprendre" (au lieu de "Regarder") suppose une
   progression enregistrée : pas encore le cas (voir backlog "sauvegarde
   de la position de lecture"), donc seul "Regarder" est atteignable
   pour l'instant — pas un bug, une conséquence attendue.
4. **Lecteur vidéo** (`templates/video_player.html`) : la note
   (`render_note`) est remontée juste sous les boutons précédent/
   suivant, dans la même colonne que la vidéo, au lieu d'une ligne
   pleine largeur séparée en dessous. La playlist (`.playlist`) est
   maintenant calée sur la hauteur de cette colonne par un script
   (`ResizeObserver` sur `.main`, hauteur recopiée sur `.playlist`) —
   préféré à un `align-items: stretch` en CSS, dont le comportement
   avec une liste très longue (258 vidéos sur Motion Design) et un
   `overflow-y: auto` était incertain sans test réel.
5. **Badges en français** : BOOK/COURSE/AUDIOBOOK → LIVRE/FORMATION/
   AUDIOBOOK (`BADGE_LABELS` dans studia.py, fonction `badge_label()`).

Vérifié à l'œil sur les 4 items de la bibliothèque de test (grille et
fiches), `pytest tests/` (73 tests) au vert.

### Traçabilité des métadonnées — règle actée, pas encore implémentée

Décidé avec Gautier, à mettre en œuvre dans une tranche séparée (pas
commencée) : **aucun champ de métadonnée sans source identifiée.**

- Chaque champ stocke sa source : scanner, présentation locale
  (`000 - Presentation....html`), Google Books, Open Library, saisie
  manuelle, ou une source fournie explicitement par Gautier lui-même
  (à nommer comme telle, pas confondue avec le scanner).
- Sources autorisées pour les livres et audiobooks : Google Books et
  Open Library, uniquement après validation d'un candidat par Gautier
  (voir "Métadonnées de livres" ci-dessus, déjà le cas).
- Sources autorisées pour les formations vidéo : tuto.com, elephorm,
  udemy, LinkedIn Learning, etc. (moissonnage, voir backlog), le fichier
  `000 - Presentation....html` livré avec la formation, les faits lus
  par le scanner (durée, nombre de médias, chapitres), et une source
  fournie explicitement par Gautier.
- Saisie manuelle : autorisée dans tous les cas, toujours comme source
  déclarée.
- Un rescan ne doit jamais remplacer un champ dont la source n'est pas
  le scanner.
- Les fiches déjà en base seront reprises pour y inscrire la bonne
  source, sans rien supprimer.

Le correctif provisoire de la Tranche 6 (`filter_duplicated_presentation_facts`)
disparaîtra probablement à ce moment-là, remplacé par un vrai choix par
source plutôt qu'un masquage de libellés.

### Priorité des couvertures — ordre acté, pas encore implémenté

Décidé avec Gautier, remplace l'ordre de la Tranche 3 ci-dessus le jour
où l'import manuel et la couverture Google Books seront ajoutés (tranche
séparée, pas commencée) :

1. image importée manuellement — priorité absolue, jamais écrasée par
   un rescan ni par `--recovers`.
2. image déjà présente dans le dossier de l'item.
3. première page du PDF ou de l'ebook (EPUB : couverture généralement
   intégrée au fichier ; si extraite, même rang que le PDF).
4. pochette intégrée du M4B.
5. couverture Google Books, si des métadonnées ont été validées.
6. image extraite de la vidéo.
7. placeholder par type.

Raison donnée par Gautier pour placer le PDF/l'ebook avant Google
Books : la première page vient de l'exemplaire qu'il possède
réellement, pas d'une autre édition que Google Books pourrait renvoyer.

L'import manuel lui-même (bouton sur la fiche, chargement depuis le
disque ou collage presse-papiers, stocké dans le cache des couvertures
— jamais dans la bibliothèque —, suppression possible pour revenir à
l'extraction automatique) n'est pas encore implémenté.

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

- Les fichiers .mp4 des formations portent un tag `title` contenant le
  vrai titre éditorial, avec accents et apostrophes (vérifié : 307/307
  sur Copywriter et Motion Design). Ce titre diffère du nom de fichier
  au-delà de la ponctuation et n'est pas toujours plus complet (ex.
  004, dont le nom de fichier porte un sous-titre absent du tag). À
  prévoir : lecture du tag par le scanner, stockage à côté du nom de
  fichier sans le remplacer, règle de choix du titre affiché, et
  comportement pour les fichiers sans tag. Aucun renommage de fichier.
- `extract_hero_fields` retrouve l'auteur par correspondance sur le
  texte du libellé ("Auteur" ou "Formateur(s)"). Un libellé est un
  texte d'affichage, pas un identifiant : renommer `author_label` dans
  `resolve_metadata_fields` ferait disparaître l'auteur du hero
  silencieusement. À remplacer par une clé stable indépendante du
  libellé affiché.
- `accept_book_candidate` et `save_manual_candidate` écrasent
  silencieusement un candidat accepté d'origine manuelle — une saisie
  manuelle ne doit jamais être remplacée par une source automatique
  sans confirmation explicite. Découvert en écrivant la résolution des
  champs de métadonnées (tranche "restructuration visuelle des
  métadonnées") : `resolve_metadata_fields` ne fait que lire le seul
  candidat `accepted` existant, il n'y a rien à arbitrer à son niveau —
  le problème est dans le workflow d'acceptation, pas l'affichage.
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
- Multi-utilisateur réel, authentification, rôles, HTTPS : V2 — dont
  dépendent aussi favoris, notifications et avatar (retirés des écrans
  en V1, voir "Refonte visuelle").
- Éditeur de notes enrichi (le Markdown s'affiche mis en forme au lieu
  d'être tapé) : V2. Le stockage reste le même Markdown brut, posé dès
  la V1 pour ne rien casser au passage.

## Méthode de travail

- Petits commits cohérents et testables, messages en anglais.
- pytest tests/ doit passer avant chaque commit.
- git push après chaque commit : c'est la seule sauvegarde du projet.
- Les médias ne sont jamais touchés, la base de données est un index
  reconstructible.
