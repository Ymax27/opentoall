# OpenToAll — design system « Signal »

Plateforme de découverte d’issues open source pour développeurs africains.
Raffinement produit (pas une refonte) : palette liée au sujet, typo distinctive,
une signature visuelle unique — le **compteur de poids de clone**.

## Anti-clichés IA (évités)

1. ~~Crème chaud + serif + terracotta~~
2. ~~Noir + accent acide~~
3. ~~Broadsheet filets / zéro radius~~

## Palette nommée

| Nom | Hex | Rôle |
|-----|-----|------|
| **Ink** | `#0E1525` | Texte, surfaces inversées — densité « terminal / nuit » sans mode dark forcé |
| **Stone** | `#F5F4F1` | Papier froid (gris-beige), pas le cream #F4F1EA |
| **Signal** | `#4B46F0` | Indigo du logo — CTA, focus, liens |
| **Ember** | `#E07A2F` | Accent rare (communauté / #2–#3), jamais dominante |
| **Merge** | `#0F7A4B` | Succès, débutant, PR mergée |
| **Mute** | `#667085` | Texte secondaire |

## Typographie

| Rôle | Police | Usage |
|------|--------|-------|
| Display / headings | **Sora** | Titres, brand, chiffres clés |
| Body | **Source Sans 3** | Lecture longue, UI |
| Code | **JetBrains Mono** | `owner/repo`, labels |

Échelle indicative : display 2.35–3.25rem · h2 1.5–1.875rem · body 1–1.125rem · meta 0.75–0.875rem.
Graisses : 600 pour les titres Sora (pas 800 partout), 400–600 pour le corps.

## Signature

**`.weight-meter`** — 3 barres (léger / moyen / lourd) qui matérialisent le coût d’un `git clone`
sur une connexion réelle. Aucun autre agrégateur d’issues ne le met en avant ainsi.

## Mouvement

- Une révélation `fade-up` légère sur le hero uniquement
- Hover de carte = ombre / bordure (pas de bounce)
- `prefers-reduced-motion` coupe animations / transitions

## Copie

Point de vue utilisateur, verbes actifs (« Trouve ta prochaine issue », « Ouvre sur GitHub »).
États vides → action suivante, pas constat passif.
