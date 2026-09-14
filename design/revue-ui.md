# Revue UI/UX — corrections à apporter à Studia

## 1. Normaliser complètement la gestion des métadonnées

Le principal point à corriger est la séparation entre trois niveaux d'information qui sont encore mélangés :

**Résumé du contenu**

- affiché dans le hero ;
- doit contenir uniquement les informations immédiatement utiles ;
- exemple formation : formateur, durée, nombre de vidéos, chapitres, année ;
- exemple livre : auteur, éditeur, année, langue ;
- exemple audiobook : auteur, durée, année, langue.

**Métadonnées éditoriales détaillées**

- affichées dans l'onglet « À propos » ;
- doivent suivre un composant visuel unique et cohérent ;
- labels secondaires, valeurs principales ;
- éviter les répétitions avec le hero.

**Gestion technique des métadonnées**

- source des métadonnées ;
- saisie manuelle ;
- candidats rejetés ;
- identifiants internes ou externes ;
- actions Modifier / Rechercher ;
- doivent être visuellement secondaires et séparées des informations éditoriales.

## 2. Supprimer les répétitions d'information

Éviter d'afficher plusieurs fois la même donnée sur la même fiche.

Exemples à corriger :

- date dans le hero + dans « À propos » + dans le bloc Métadonnées ;
- auteur dans le hero + dans le bloc détaillé sans valeur ajoutée ;
- nombre de médias dans plusieurs zones.

Règle recommandée :

- hero = version synthétique ;
- « À propos » = version détaillée ;
- technique = uniquement dans un sous-bloc dédié.

## 3. Uniformiser le vocabulaire métier

Définir des libellés stables selon le type de contenu.

**Pour les formations :** Formateur(s), Durée, Année, Vidéos, Chapitres, Logiciels, Source.

**Pour les livres :** Auteur, Éditeur, Langue, Date de publication, ISBN, Source des métadonnées.

**Pour les audiobooks :** Auteur, Narrateur si disponible, Éditeur, Langue, Date de publication, Durée, ISBN, Source des métadonnées.

Éviter d'alterner sans raison entre :

- Auteur / Autrice
- Publié / Date de publication
- média(s) / vidéos / fichiers
- Structure / chapitres

## 4. Ne pas exposer le modèle technique à l'utilisateur

Remplacer les formulations techniques par des formulations métier.

| Actuel | Attendu |
|---|---|
| `49 média(s)` | `49 vidéos` |
| `1 média(s)` sur un PDF | ne rien afficher, ou `1 PDF` |
| `resource_index` | Page de ressources |
| `document` | PDF ou Document |
| `file` | Fichier |
| `.mp4`, `.pdf`, `.zip` dans les titres visibles | masquer l'extension sauf si elle apporte une vraie information |

## 5. Revoir le hero des fiches

Le hero doit rester synthétique.

**Pour une formation :** badge type ; titre ; formateur(s) ; durée ; nombre de vidéos ; nombre de chapitres ; année ; CTA principal ; CTA secondaire.

**Pour un livre :** badge type ; titre ; auteur ; éditeur ; année ; langue ; CTA Lire ; CTA Ressources.

**Pour un audiobook :** badge type ; titre ; auteur ; durée ; année ; langue ; CTA Lire/Écouter ; CTA Ressources.

Éviter d'y mettre : identifiants techniques ; source API ; nombre générique de « médias » ; détails de gestion.

## 6. Repenser le composant « Informations / Métadonnées »

Le bloc actuel ressemble encore trop à un tableau brut.

Créer un composant réutilisable :

- label plus petit et plus discret ;
- valeur plus contrastée ;
- espacement vertical régulier ;
- alignement cohérent ;
- grille 2 colonnes sur desktop si possible ;
- 1 colonne sur mobile.

Exemple conceptuel :

    Auteur          David Allen
    Éditeur         Leduc.s éditions
    Publication     8 octobre 2015
    Langue          Français
    ISBN            9791092928136

## 7. Séparer « Informations bibliographiques » et « Gestion des métadonnées »

Ne pas mélanger dans un même bloc : Auteur, Éditeur, ISBN, Source, Modifier, Candidats rejetés.

Créer deux zones :

**Informations bibliographiques** — Auteur, Éditeur, ISBN, Année, Langue.

**Gestion des métadonnées** — Source, Rechercher, Modifier, Candidats rejetés, Saisie manuelle.

## 8. Hiérarchiser les sources et identifiants

Les informations comme TUTO.com, ID source, Google Books, Open Library, ISBN doivent être secondaires.

Pour une formation : afficher TUTO.com comme source ; déplacer l'ID dans un détail secondaire.

Pour un livre : afficher l'ISBN dans la fiche ; source de métadonnées plus discrète.

## 9. Revoir les listes de programme

Les listes affichent encore les noms de fichiers.

À corriger :

- masquer `.mp4` ;
- masquer `.pdf` ;
- masquer les préfixes purement techniques s'ils ne servent pas à l'utilisateur ;
- conserver uniquement un numéro pédagogique si utile.

Exemple :

    001 - Presentation de l intervenante et du programme.mp4

devient :

    001 — Présentation de l'intervenante et du programme

## 10. Gérer les titres longs dans le programme

Dans les listes :

- garder une colonne fixe pour la durée ;
- le titre prend l'espace restant ;
- troncature sur une ligne si nécessaire ;
- tooltip ou `title` complet au survol/focus.

Ne jamais laisser un titre long décaler la durée ou casser l'alignement.

## 11. Revoir les types de ressources

Les ressources doivent afficher un type compréhensible : PDF, Archive ZIP, Page de ressources, Document, Fichier source.

Éviter : `resource_index`, `document`, `file`.

## 12. Revoir la grille Bibliothèque

La grille actuelle est propre mais encore incomplète par rapport au design cible.

À ajouter ou finaliser : auteur/créateur ; progression si le contenu a commencé ; pourcentage ; métadonnées compactes ; menu `⋮` toujours visible ; titre limité à 2 lignes ; auteur limité à 1 ligne ; cartes de hauteur uniforme.

## 13. Différencier clairement « Continuer » de « Bibliothèque »

La section Continuer doit être plus orientée action. Elle doit montrer : bouton play ; point de reprise ; progression ; prochain chapitre ou étape.

La bibliothèque doit montrer : type ; titre ; auteur ; métadonnées ; progression si disponible.

Les deux cartes ne doivent pas être quasi identiques.

## 14. Corriger l'état des entrées de sidebar

Les entrées non actives sont trop grisées. Elles ressemblent à des éléments désactivés.

À faire : augmenter légèrement le contraste ; garder l'actif en orange ; conserver un hover clair ; prévoir un focus clavier visible.

## 15. Alléger le trait orange horizontal sous le header

Le trait orange attire beaucoup trop l'œil.

Options : le supprimer ; le rendre plus fin/discret ; ou le réserver uniquement à certains états actifs.

L'accent orange doit rester fonctionnel, pas décoratif en permanence.

## 16. Revoir la hiérarchie des CTA

CTA principal : orange plein ; plus visible ; texte orienté action.

CTA secondaire : fond sombre ; contraste plus faible.

Uniformiser les libellés : Regarder, Lire, Écouter, Reprendre — selon le type et l'état.

## 17. Rendre les libellés d'action cohérents

Éviter une logique différente selon les écrans sans raison.

- formation jamais commencée : **Regarder**
- formation commencée : **Reprendre**
- livre : **Lire**
- audiobook : **Écouter**

## 18. Revoir le lecteur vidéo

Le lecteur est fonctionnel mais doit encore évoluer.

À corriger : masquer les extensions de fichiers ; organiser les médias par chapitre ; améliorer la hiérarchie de la playlist ; maintenir la durée toujours visible ; limiter les titres à une ligne dans la playlist ; conserver les chapitres ouverts ; panneau Programme repliable.

## 19. Améliorer l'état actif dans la playlist

La leçon courante doit être plus évidente.

Utiliser : accent orange ; fond teinté ; icône play ; texte plus contrasté.

Les leçons terminées peuvent avoir une coche. Les non commencées restent neutres.

## 20. Le bouton « Insérer un repère »

Il doit créer directement un repère au timestamp courant dans la note, générer automatiquement la référence temporelle, et permettre l'édition ensuite.

## 21. Revoir le bloc Notes sur les fiches

Sur les fiches, le bloc Notes est visuellement très lourd.

Améliorations : réduire son contraste de fond ; limiter la hauteur initiale ; laisser la zone grandir si besoin ; bouton Imprimer moins visible ; espacement plus cohérent avec les autres sections.

## 22. Harmoniser les largeurs de contenu

Certaines pages ont une grande zone vide à droite.

Créer une largeur de contenu cohérente : hero et contenu principal alignés ; paragraphes avec largeur de lecture limitée ; listes plus larges que les paragraphes si nécessaire.

## 23. Réduire la longueur des lignes de texte

Les descriptions deviennent parfois trop larges.

Limiter la largeur de lecture : environ 60 à 85 caractères par ligne, surtout pour les longues descriptions.

## 24. Uniformiser les espacements verticaux

Définir une échelle d'espacement commune : petit, moyen, grand, section.

Les fiches ont actuellement des espacements irréguliers entre hero, onglets, description, encadrés et notes.

## 25. Uniformiser les blocs surélevés

Les blocs Métadonnées et Notes utilisent des cartes sombres avec bord gauche orange.

Décider quels blocs méritent ce traitement, et ne pas l'utiliser partout. Le réserver aux blocs secondaires importants ou aux encadrés.

## 26. Harmoniser les badges

Créer une couleur par type : Formation, Livre, Audiobook — avec une saturation modérée.

Le badge ne doit pas attirer autant que le titre ou le CTA.

## 27. Placeholder d'image

Si aucune image n'est disponible :

- Formation : motif play / média ;
- Livre : couverture abstraite ;
- Audiobook : casque / waveform.

Le placeholder doit être cohérent avec la palette Studia.

## 28. Responsive sidebar

- Desktop : sidebar complète.
- Largeur intermédiaire : sidebar plus étroite.
- Tablette : sidebar compacte / icônes.
- Smartphone : drawer.

Ne pas laisser la sidebar écraser le contenu.

## 29. Responsive fiche

- Desktop : image à gauche, informations à droite.
- Tablette : réduire l'image et les espacements.
- Mobile : image au-dessus, texte dessous, CTA pleine largeur si nécessaire.

## 30. Responsive lecteur

- Desktop : vidéo à gauche, programme à droite.
- Tablette : programme repliable.
- Mobile : vidéo pleine largeur, programme en panneau secondaire ou sous la vidéo.

## 31. Recherche instantanée

Prévoir : recherche instantanée ; debounce ; conservation de la saisie après navigation si possible.

## 32. Persistance d'état

Conserver : filtres ; tri ; vue grille/liste ; scroll si possible ; état du panneau Programme ; chapitres ouverts.

## 33. États vides

Prévoir des écrans propres pour : aucune ressource ; aucune note ; aucun résultat ; aucune couverture ; aucun média ; contenu indisponible.

## 34. Accessibilité

Prévoir : contraste WCAG AA ; focus clavier visible ; navigation clavier ; tooltips pour texte tronqué ; `aria-label` pour icônes ; cibles de clic suffisamment grandes ; états actifs compréhensibles sans dépendre uniquement de la couleur.

## 35. Ne pas réduire excessivement la typo sur petit écran

Quand ça ne tient plus : changer de grille ; empiler ; replier ; tronquer.

Ne pas compresser la typographie jusqu'à perdre la lisibilité.

## 36. Supprimer les informations inutiles dans le hero

Exemples : `1 média(s)` pour un livre ; identifiant source ; type de fichier ; nombre de ressources si secondaire.

Le hero doit servir à comprendre le contenu, pas son stockage.

## 37. Harmoniser les dates

- Dans le hero : année seule.
- Dans À propos : date complète.

Exemple — hero : `2015` ; détail : `8 octobre 2015`.

## 38. Harmoniser les durées

Utiliser une même convention partout : `5 h 44`, `55 h 08`, `3 h 05`.

Éviter d'alterner avec `5h44`, `55h10`, `3h05` selon les endroits.

## 39. Harmoniser les pluriels

Éviter l'affichage brut `1 média(s)`, `27 chapitre(s)`.

Utiliser : `1 média`, `2 médias`, `1 chapitre`, `27 chapitres`.

## 40. Harmoniser la casse et la ponctuation

Utiliser systématiquement : phrase case pour les titres ; capitales uniquement pour les badges ; séparateur `·` pour les métadonnées courtes.

Exemple : `5 h 44 · 49 vidéos · 2023`

## 41. Uniformiser les breadcrumbs

Format conseillé : `Bibliothèque › Motion Design › Titre`

Texte secondaire. Le dernier élément peut être plus contrasté.

## 42. Revoir le slogan de sidebar

Le slogan en bas fonctionne, mais doit rester décoratif. Il ne doit pas entrer en concurrence avec la navigation.

## 43. Réduire les termes administratifs

L'application doit parler comme une bibliothèque, pas comme une base de données.

Éviter : `média(s)`, `resource_index`, `file`, `document`, `source_id`, `candidats` — sauf dans une zone explicitement technique.

## 44. Créer des composants réutilisables

À factoriser : HeroItem, MetadataSummary, MetadataDetails, MetadataManagement, TypeBadge, MediaCard, ContinueCard, ProgramList, ResourceList, NotesPanel, Sidebar, Breadcrumbs.

L'objectif est d'éviter les variations d'un écran à l'autre.

## 45. Définir les priorités visuelles

Ordre général : titre ; action principale ; visuel ; informations essentielles ; progression ; description ; métadonnées secondaires ; informations techniques.

Actuellement, certaines métadonnées techniques remontent trop haut dans la hiérarchie.

## 46. Garder une logique commune entre Livre, Formation et Audiobook

Même squelette : hero ; CTA ; onglets ; À propos ; Programme/Fichiers ; Ressources ; Notes.

Seul le contenu des métadonnées change selon le type.

## 47. Ne pas dupliquer les données entre onglets

Chaque information doit avoir un emplacement clair :

- résumé dans le hero ;
- détail dans À propos ;
- fichiers dans Programme ;
- fichiers annexes dans Ressources ;
- gestion des sources dans Métadonnées techniques.

## 48. Rendre les onglets plus signifiants

- **À propos** = description + métadonnées éditoriales
- **Programme** = médias / chapitres / fichier principal
- **Ressources** = fichiers annexes

## 49. Critère de validation final

Une fiche doit pouvoir être comprise en quelques secondes sans voir : nom de fichier brut ; extension ; terme technique de base de données ; information répétée trois fois.

L'utilisateur doit pouvoir identifier immédiatement :

- ce que c'est ;
- qui l'a créé ;
- combien de temps ça dure ;
- où reprendre ;
- comment lire / regarder / écouter ;
- quels sont les chapitres ;
- quelles ressources sont disponibles.

C'est la ligne directrice à utiliser pour la prochaine itération.
