# OpenToAll — design system « Kernel »

Registre éditorial pour un annuaire d’issues open source : surfaces menthe,
titres serif, métadonnées en mono. La hiérarchie vient de la composition
(asymétrie, numéros, filets), pas de la décoration.

Référence visuelle : [kernel-copy.webflow.io](https://kernel-copy.webflow.io/).

## Anti-clichés (évités)

1. ~~Dégradés violet/bleu génériques~~
2. ~~Glassmorphism, blobs, cartes flottantes floues~~
3. ~~Héros centré avec deux boutons identiques~~

## Palette

| Nom | Hex | Usage |
|-----|-----|-------|
| **Menthe** | `#E4FAEE` | Fond de page (clair) |
| **Forêt** | `#015239` | Accent principal, liens, puces actives |
| **Forêt profond** | `#113A2D` | Panneaux sombres, cartes mises en avant |
| **Carte menthe** | `#D5F1E3` | Surface des cartes et encarts (jamais de blanc opaque) |
| **Aqua** | `#B8FFE1` | Texte fort sur forêt, puce sélectionnée |
| **Violet** | `#7D56FC` | Focus visible, accents rares ; `#5B32E0` pour le texte au survol sur menthe |
| **Encre** | `#08251C` | Texte principal |
| **Gris-vert** | `#41604F` | Texte secondaire |
| **Powder** | `#BDD7CA` | Texte secondaire sur forêt |
| **Crème** | `#FBFEFB` | Texte sur forêt uniquement |

Le thème sombre inverse le fond (`#08130F`) et éclaircit le texte ; les cartes
menthe restent claires et conservent leurs couleurs d’encre.

## Typographie

| Rôle | Police | Usage |
|------|--------|-------|
| Titres | **Fraunces** | h1/h2, chiffres clés, numéros de registre |
| Corps | **DM Sans** | lecture, UI, boutons |
| Méta | **JetBrains Mono** | `owner/repo`, eyebrows, horodatages |

Échelle : h1 `clamp(2.3rem, 4.4vw, 3.4rem)` · h2 ~1.25–1.5rem · corps 0.9375–1rem · méta 10–11 px.
Titres en 600, interlettrage négatif (`-0.03em`), interligne serré (0.98–1.05).

## Surfaces et composition

- **Panneau forêt** (`.panel-forest`) : bloc de tête, CTA, pied de page, 404, connexion.
  Texture pointillée en surimpression (`.hero-dots`), jamais de dégradé.
- **Cartes** (`.issue-tile`, `.card-mint`) : menthe, filet vertical de 4 px coloré par
  niveau ; une carte sur quatre et la deuxième de la liste passent en forêt pour créer
  un rythme. Chaque carte porte un numéro de registre.
- **Carte à la une** (`.issue-feature`) : deux colonnes, numéro fantôme, CTA aqua.
- **Filets plutôt que boîtes** : classement, activité du profil, statistiques utilisent
  des séparateurs (`border-b`), pas des cartes empilées.
- **Pas de blanc opaque** : champs et boutons secondaires en `#E4FAEE` / `#D5F1E3`.

## Signature

**`.weight-meter`** — 3 barres (léger / moyen / lourd) qui matérialisent le coût d’un
`git clone`. Présent sur les cartes, la fiche et la page d’accueil.

## Mouvement

- Révélation `fade-up` légère via `[data-reveal]` (IntersectionObserver), avec repli
  `<noscript>` qui force l’opacité à 1.
- `prefers-reduced-motion` coupe animations et transitions.
- Hover de carte : translation de 3 px, bordure et ombre discrètes.
- Focus visible : contour violet 2 px, jamais supprimé.

## Accessibilité

- Cible 4.5:1 pour le texte ; le violet texte sur menthe passe par `#5B32E0`.
- HTML sémantique (`article`, `dl`, `ol`, `time`), `aria-live` sur les mises à jour HTMX,
  `sr-only` pour les libellés de filtres, navigation clavier complète.
- Aucun débordement horizontal à 375 px.

## Copie

Verbes actifs, point de vue utilisateur : « Trouve ta prochaine PR », « Ouvre sur GitHub ».
États vides → action suivante, jamais un simple constat.
