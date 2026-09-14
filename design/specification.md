# Fiche technique complète — Studia

## 1. Présentation du produit

Studia est une bibliothèque personnelle et une plateforme d'apprentissage multi-supports conçue pour centraliser plusieurs types de contenus dans une seule interface cohérente :

- formations vidéo ;
- livres et documents ;
- audiobooks ;
- notes associées aux contenus ;
- progression de lecture ou de visionnage.

Le parcours principal est :

    Bibliothèque → Fiche de contenu → Lecteur → Progression

L'interface est pensée en priorité pour ordinateur, tout en restant pleinement responsive sur tablette et smartphone.

## 2. Direction artistique

### 2.1 Positionnement visuel

Le design doit être :

- professionnel ;
- sobre ;
- sombre ;
- moderne ;
- lisible ;
- peu décoratif ;
- orienté contenu.

L'interface ne doit pas ressembler à un dashboard SaaS chargé. Le contenu reste l'élément principal : couverture, formation, vidéo, chapitre, livre ou audiobook.

L'inspiration générale reprend les qualités ergonomiques de bibliothèques multimédia modernes, avec un langage visuel propre à Studia.

## 3. Identité visuelle

### 3.1 Logo

Le logo Studia est composé de deux éléments :

- un symbole ;
- un wordmark.

**Symbole**

Le symbole associe :

- trois barres verticales arrondies et ascendantes ;
- une forme triangulaire de lecture ;
- un triangle plein "play".

Le symbole évoque simultanément :

- progression ;
- audio ;
- vidéo ;
- bibliothèque multimédia ;
- apprentissage.

**Wordmark**

Le mot **Studia** est traité avec :

- `Stud` en blanc ;
- `ia` dans la couleur d'accent orange/corail.

**Fichiers**

- Logo horizontal SVG
- Symbole seul SVG

## 4. Palette officielle

Les couleurs suivantes constituent la palette officielle du projet.

| Rôle | Couleur |
|---|---|
| Fond principal | `#081015` |
| Fond sidebar | `#0C141A` |
| Surface principale | `#101920` |
| Surface secondaire | `#121D24` |
| Texte principal | `#F2F4F5` |
| Texte secondaire | `#B8C0C5` |
| Texte tertiaire | `#87929A` |
| Accent principal | `#FF6847` |
| Accent sombre | `#D95A3C` |
| Bordure discrète | `#26323A` |
| Progression inactive | `#29343B` |

### 4.1 Utilisation de l'accent

L'orange/corail doit être réservé à :

- bouton principal ;
- progression ;
- sélection ;
- état actif ;
- focus ;
- élément courant ;
- timestamps ;
- logo.

Il ne doit pas devenir une couleur de fond dominante.

## 5. Couleurs par type de contenu

Les badges de type utilisent des variantes distinctes.

**Formation** — teinte chaude, dérivée de l'accent Studia. Usage : `FORMATION`

**Livre** — teinte ocre / ambre légèrement désaturée. Usage : `LIVRE`

**Audiobook** — teinte vert / teal sombre et désaturée. Usage : `AUDIOBOOK`

Les badges restent secondaires par rapport au titre. Ils ne doivent pas rivaliser visuellement avec les CTA.

## 6. Typographie

### 6.1 Police

Police principale : **Inter**

Fallback :

- system-ui ;
- -apple-system ;
- Segoe UI ;
- sans-serif.

### 6.2 Échelle typographique

La taille du texte courant est la référence 1.

| Rôle | Rapport |
|---|---|
| Annotation | 0,8–0,9 |
| Métadonnée | 0,85–0,9 |
| Navigation | 0,9–1 |
| Corps | 1 |
| Titre de carte | 1,05–1,15 |
| Titre de section | 1,45–1,65 |
| Titre de page | 1,8–2,2 |
| Titre principal de contenu | jusqu'à 2,3 |

### 6.3 Graisses

- Corps : Regular
- Métadonnées : Regular
- Navigation : Medium
- Titre de carte : Medium / Semibold
- Titre de section : Semibold
- Titre de page : Semibold / Bold

### 6.4 Interlignage

- Titres : 1,15 à 1,25
- Corps : 1,45 à 1,6
- Métadonnées : 1,3 à 1,4

## 7. Architecture globale

L'application est organisée autour d'une sidebar permanente sur desktop.

### 7.1 Sidebar

Navigation :

- Bibliothèque
- Continuer
- Formations
- Livres
- Audiobooks
- Notes
- Favoris
- Paramètres

Structure :

- logo en haut ;
- navigation au centre ;
- slogan ou signature en bas.

L'élément actif utilise :

- fond légèrement teinté ;
- accent orange ;
- contraste renforcé.

## 8. Responsive design

Studia doit fonctionner sur desktop, ordinateur portable, tablette et smartphone.

Les breakpoints ne doivent pas être définis uniquement selon des valeurs arbitraires. La mise en page doit changer lorsque le contenu commence réellement à être comprimé.

**Desktop large** — sidebar complète ; grille 4 colonnes ; lecteur avec programme à droite.

**Desktop intermédiaire** — sidebar plus étroite ; grille 3 colonnes ; programme lecteur plus compact.

**Tablette** — sidebar compacte ou icônes seules ; grille 2 colonnes ; programme vidéo repliable.

**Smartphone** — navigation dans un drawer ; grille 1 colonne ; hero de fiche vertical ; programme lecteur replié ; actions empilées si nécessaire.

## 9. Écran Bibliothèque

### 9.1 Structure

Ordre vertical :

1. barre de recherche ;
2. filtres ;
3. section Continuer ;
4. section Ma bibliothèque.

## 10. Barre de recherche

Le champ de recherche est prioritaire. Il occupe environ **50 à 65 % de la largeur utile** sur desktop large.

À droite : filtre type ; tri ; avatar utilisateur.

**Comportement**

Recherche instantanée si techniquement raisonnable.

La recherche doit idéalement fonctionner sur : titre ; auteur ; formateur ; sujet ; logiciel ; type.

Filtres et tri doivent être conservés lorsqu'un utilisateur ouvre une fiche puis revient à la bibliothèque.

## 11. Section "Continuer"

### 11.1 Objectif

Cette section répond à : *Où en étais-je et comment reprendre immédiatement ?*

Elle n'a donc pas le même rôle que la grille principale.

### 11.2 Nombre d'éléments

Afficher **3 ou 4 éléments maximum**, puis « Tout voir ».

### 11.3 Carte Continuer

Structure : image ; badge type ; bouton lecture ; titre ; point de reprise ; progression ; chapitre ou étape actuelle.

Exemple :

    Motion Design - la formation complète
    Reprendre à 12:43
    58 %
    Chapitre 8 · Animations avancées

**Action**

Le bouton lecture lance immédiatement le média. Le clic sur le reste de la carte ouvre la fiche.

**Texte long**

- Titre : maximum 2 lignes ; ellipse au-delà.
- Chapitre : 1 ligne ; ellipse.
- Timestamp : jamais tronqué.

## 12. Section "Ma bibliothèque"

### 12.1 Filtres

Filtres : Tous, Formations, Livres, Audiobooks.

Le filtre actif utilise l'accent principal.

À droite : tri ; bascule grille / liste.

## 13. Grille de bibliothèque

- Desktop : 4 colonnes.
- Largeur plus faible : 3 colonnes.
- Tablette : 2 colonnes.
- Smartphone : 1 colonne.

La largeur minimale exacte d'une carte sera déterminée pendant l'intégration.

## 14. Carte de bibliothèque

Toutes les cartes d'une même grille ont exactement la même hauteur.

**Structure verticale** : image 16:9 ; badge ; titre ; auteur ; espace flexible ; progression si disponible ; métadonnées.

**Image** — ratio 16:9.

Si aucune image n'existe : utiliser une image générique par type.

- formation : motif play / vidéo ;
- livre : couverture abstraite ;
- audiobook : casque / waveform.

## 15. Titre de carte

Hauteur réservée : **2 lignes maximum**. Au-delà : ellipse.

Exemple :

    Initiation complète à Adobe
    After Effects pour la création…

Le texte complet doit être disponible : au survol ; au focus clavier ; dans la fiche.

## 16. Auteur

Maximum **1 ligne**. Au-delà : ellipse.

Exemple :

    Jean-Christophe Van den Berghe & Alexan…

## 17. Progression

La progression n'est affichée que si le contenu a déjà été commencé.

**Non commencé** — ne rien afficher. Pas de `0 %`, pas de « Non commencé », pas de barre vide.

**En cours** — afficher barre et pourcentage. Le pourcentage dispose d'une zone fixe. Doit gérer proprement `5 %`, `58 %`, `100 %`.

**Terminé** — afficher simplement `100 %`. Aucun autre badge « terminé » n'est nécessaire.

## 18. Métadonnées de carte

Maximum **2 informations**.

Exemples : durée + chapitres ; durée + leçons ; chapitre courant + temps restant.

Le composant doit supporter `128 h 35`, `124 chapitres`, `258 vidéos` sans casser la carte.

## 19. Menu contextuel

Le bouton `⋮` est toujours visible.

Il doit rester secondaire ; être contenu dans une zone de contraste stable ; ne pas gêner le clic principal.

Le clic sur le menu ne doit pas déclencher l'ouverture de la fiche.

## 20. Fiche de contenu

Structure : breadcrumb ; hero ; métadonnées ; CTA ; onglets ; description ; tags ; programme / fichiers.

## 21. Hero de fiche

Disposition desktop : environ 30–35 % image ; 60–65 % informations.

Contenu : badge type ; titre ; auteur/formateur ; durée ; nombre de médias ; chapitres ; année ; actions.

## 22. Actions de fiche

Action principale : **Reprendre la formation** — plein orange.

Action secondaire : **Voir les ressources** — surface sombre.

Le bouton principal doit être nettement plus visible.

## 23. Titre de fiche

Maximum recommandé : 2 à 3 lignes.

Contrairement aux cartes, il peut occuper plus d'espace. Pas d'ellipse agressive sur une fiche détaillée.

## 24. Onglets

À propos / Programme / Ressources.

État actif : texte renforcé ; soulignement orange.

## 25. Description

Le texte doit rester lisible. Éviter les lignes trop longues.

Cible : environ 60 à 85 caractères par ligne.

## 26. Tags

Exemples : After Effects, Photoshop, Motion Design, Animation, 3D, Tracking, Typographie, Expressions.

Fond discret. Pas de bordure forte. Retour à la ligne automatique.

## 27. Programme de formation

Présentation tabulaire/accordéon.

Colonnes : état ; numéro ; titre ; nombre de vidéos ; durée ; chevron.

Le titre occupe la majorité de la largeur. Les colonnes numériques restent alignées.

## 28. Texte long dans le programme

Titre de chapitre : une ligne si possible ; ellipse si manque de place.

Les colonnes durée et quantité ne bougent jamais.

## 29. Lecteur vidéo

Disposition desktop : environ 65–70 % lecteur ; 30–35 % programme.

Programme à droite.

## 30. Programme du lecteur

Le panneau est repliable. Son état ouvert / fermé doit être conservé pendant la navigation entre vidéos.

Il contient : progression globale ; chapitres ; leçons ; états.

## 31. État d'une leçon

- **Active** — accent orange.
- **Terminée** — icône validée.
- **Non terminée** — icône neutre.

Titre long : une ligne ; ellipse. Durée : toujours visible.

## 32. Lecture et navigation

Sous la vidéo : titre ; chapitre ; précédent ; suivant.

CTA principal : **Suivant**. CTA secondaire : **Précédent**.

## 33. Notes

Onglets : Notes / Description / Ressources.

Par défaut sur le lecteur : **Notes**.

## 34. Note

Chaque note contient : timestamp ; texte ; éditer ; supprimer.

Exemple :

    14:32 — Revoir la différence entre animation 2D et 3D.

**Timestamp** — cliquable. Il repositionne immédiatement la vidéo au temps correspondant.

## 35. Notes longues

Les notes peuvent s'étendre sur plusieurs lignes. Pas de troncature obligatoire. La hauteur de la ligne s'adapte au contenu.

## 36. Insérer un repère

Le bouton **Insérer un repère** crée directement une note associée au temps courant. Elle peut ensuite être complétée ou éditée.

## 37. Lecteur audio / audiobook

Même langage visuel général.

Éléments principaux : couverture ; titre ; auteur ; progression ; position courante ; durée ; vitesse ; lecture/pause ; ±15 secondes ; chapitres ; notes.

Sur mobile, le lecteur peut devenir une vue plein écran ou une mini-barre persistante.

## 38. Livre / PDF

Fiche : couverture ; titre ; auteur ; éditeur ; année ; langue ; ISBN ; description ; action Lire.

Progression : page courante / page totale ; ou pourcentage.

## 39. État sans image

Chaque type dispose d'un placeholder spécifique.

- Formation : motif vidéo / play.
- Livre : forme de couverture stylisée.
- Audiobook : casque / onde audio.

Ils utilisent la palette Studia.

## 40. États interactifs

**Hover** — légère hausse de contraste ; surface légèrement plus claire ; accent renforcé.

**Focus clavier** — contour visible, plus fort que le hover.

**Actif** — accent orange.

**Sélectionné** — fond teinté orange sombre.

**Disabled** — opacité réduite et absence d'effet hover. Le disabled n'était pas visible sur les rendus, mais doit être prévu.

## 41. Accessibilité

Objectifs minimum :

- contraste texte/fond conforme WCAG AA ;
- navigation clavier ;
- focus visible ;
- boutons avec surface de clic confortable ;
- labels accessibles pour icônes ;
- tooltips pour texte tronqué ;
- aria-label pour boutons purement iconographiques ;
- état actif annoncé aux lecteurs d'écran.

## 42. Responsive détaillé

**Desktop large** — sidebar complète ; 4 cartes ; programme visible.

**Desktop intermédiaire** — sidebar réduite ; 3 cartes ; programme plus étroit.

**Tablette paysage** — sidebar compacte ; 2 cartes ; programme repliable.

**Tablette portrait** — menu compact ; 2 cartes ; hero empilé.

**Smartphone** — drawer ; 1 carte ; actions pleine largeur ; hero vertical ; programme lecteur en panneau repliable.

## 43. Gestion de la densité

Ne pas réduire sans limite : texte ; icônes ; boutons ; métadonnées.

Si le contenu devient trop dense : changer le layout, pas la lisibilité.

## 44. Règles de bordures

Les bordures doivent être limitées à : cartes ; contrôles ; séparation de sections importantes.

Éviter : bordure autour de chaque ligne ; bordure autour de chaque tag ; bordure autour de chaque sous-bloc.

L'espacement doit faire une partie du travail visuel.

## 45. Rayon des composants

Le design utilise des coins légèrement arrondis. Pas d'effet "bubble UI".

Les cartes, boutons et champs utilisent une famille de rayons cohérente, à définir dans les tokens du design system.

## 46. Ombres

Très légères voire absentes.

La profondeur vient principalement de : différence de fond ; contraste ; bordure discrète ; espacement.

## 47. Recherche

Si techniquement possible : recherche instantanée avec léger délai de debounce.

La recherche ne doit pas lancer une requête lourde à chaque frappe sans temporisation.

## 48. Persistance UI

Les éléments suivants doivent rester mémorisés après navigation :

- filtre actif ;
- tri ;
- vue grille/liste ;
- éventuellement position de scroll ;
- état du panneau Programme ;
- chapitres ouverts du lecteur.

## 49. États vides

À prévoir même s'ils ne figurent pas encore dans les rendus :

- aucune bibliothèque ;
- aucun résultat ;
- aucune note ;
- aucune progression ;
- aucune ressource ;
- média absent ;
- image absente.

Chaque état vide doit expliquer clairement ce qui manque.

## 50. Priorités de développement UI

Ordre conseillé : design tokens ; layout global ; sidebar ; Bibliothèque ; cartes ; responsive ; fiche ; lecteur vidéo ; notes ; audio ; PDF ; états vides et erreurs.

## 51. Design tokens recommandés

À centraliser : couleurs ; typographie ; espacements ; rayons ; transitions ; breakpoints ; hauteurs de contrôles ; états actifs ; focus.

Les composants ne doivent pas redéfinir ces valeurs individuellement.

## 52. Contraintes fonctionnelles décidées

- Les cartes ouvrent la fiche.
- Le bouton lecture de Continuer lance immédiatement le média.
- Le menu `⋮` est toujours visible.
- Un média sans image reçoit une image générique.
- Un contenu terminé affiche uniquement 100 %.
- Les badges changent de couleur selon le type.
- Aucun indicateur de progression n'est affiché avant la première lecture.
- Continuer contient 3 ou 4 éléments.
- Le panneau Programme est repliable.
- Son état reste conservé pendant la navigation.
- Une note longue peut prendre plusieurs lignes.
- Les timestamps sont cliquables.
- Insérer un repère crée directement une note.
- La recherche est instantanée si possible.
- La palette définie ci-dessus est officielle.
