# Savoirthèque

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

## Environnement

    Poste          gautier@gautierPC, développement exclusivement local
    Dépôt          /home/gautier/dev/offlineu-lab
    Branche        offlineu-lab
    Remote origin  github.com/gautier-cmd/savoiritheque (le sien)
    Remote upstream github.com/WhiskeyCoder/OfflineU (projet d'origine, lecture seule)
    Venv           .venv (à activer : source .venv/bin/activate)
    Bibliothèque   /home/gautier/offlineu-test-library
    Données        /home/gautier/offlineu-test-data/savoiritheque.db
    Flask          3.1.1
    ffprobe        /usr/bin/ffprobe

## État actuel

### Fichiers

    offlineu_core.py    application OfflineU d'origine, 1003 lignes, INTACTE
    library_index.py    scanner SQLite de Savoirthèque
    tests/test_library_index.py   17 tests pytest
    templates/          templates OfflineU (course_dashboard, lesson_view,
                        select_course) — réutilisables pour le CSS seulement

### Modèle de données

Item (un dossier de premier niveau) contient des Media et des Resources.
Le concept Lesson d'OfflineU est abandonné.

Tables SQLite, schéma version 2 :
schema_info, users, items, media, resources, progress.

    media       item_id, relative_path, parent_path, sort_order,
                media_type, extension, size_bytes,
                duration_seconds, probed_at, created_at
                UNIQUE(item_id, relative_path)
    resources   mêmes colonnes sans durée
    progress    UNIQUE(user_id, media_id) — jamais media_id seul

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

## Objectif suivant

Une application web locale mono-utilisateur lisant SQLite :
grille de couvertures -> fiche d'un item -> lecteurs -> progression.

Décision prise : écrire une nouvelle application (savoiritheque.py) à côté
d'OfflineU plutôt que de modifier offlineu_core.py, dont les 154
occurrences de « lesson » et l'état global current_course sont
incompatibles avec le modèle. Le CSS des templates existants est
réutilisable comme point de départ.

Lecteurs prévus, dans cet ordre : vidéo, audio/M4B avec chapitres,
PDF (PDF.js). EPUB plus tard.

Progression selon le type : secondes pour vidéo et audio, page pour PDF,
position pour EPUB.

## Backlog (ne pas traiter sans demande explicite)

- Fichier renommé = nouvel id = progression perdue. Appariement par
  empreinte à prévoir.
- Le compteur « sans durée » du résumé compte aussi les PDF, qui n'en ont
  pas. Affichage à corriger.
- Chapitres internes des M4B (ffprobe -show_chapters), distincts des
  chapitres par sous-dossier.
- Nombre de pages des PDF.
- Couvertures : aucun des quatre cas n'a de fichier image. À extraire
  (première page PDF, pochette M4B, image de vidéo) ou à récupérer en ligne.
- Métadonnées enrichies, quatre sources par ordre de priorité :
  1. Moissonnage des pages de vente des plateformes commerciales
     (TUTO.com, Udemy, LinkedIn, Elephorm...).
  2. Fichiers locaux : pour les formations achetées, la page
     000 - Presentation.html livrée avec le contenu s'affiche telle
     quelle en tête de fiche ; plus les faits lisibles dans les fichiers
     (durée, chapitres, nombre de médias).
  3. APIs publiques pour les livres (Google Books, Open Library) :
     titre, auteur, ISBN, éditeur, année, couverture — champs factuels
     uniquement.
  4. Saisie manuelle, pour les contenus créés par Gautier et pour
     corriger ou compléter n'importe quelle fiche. Ces champs-là ne
     sont jamais écrasés par un rescan.
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
