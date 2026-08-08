---
name: OpenToAll Design System
colors:
  surface: '#faf8ff'
  surface-dim: '#d2d9f4'
  surface-bright: '#faf8ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f3ff'
  surface-container: '#eaedff'
  surface-container-high: '#e2e7ff'
  surface-container-highest: '#dae2fd'
  on-surface: '#131b2e'
  on-surface-variant: '#464555'
  inverse-surface: '#283044'
  inverse-on-surface: '#eef0ff'
  outline: '#777587'
  outline-variant: '#c7c4d8'
  surface-tint: '#4d44e3'
  primary: '#3525cd'
  on-primary: '#ffffff'
  primary-container: '#4f46e5'
  on-primary-container: '#dad7ff'
  inverse-primary: '#c3c0ff'
  secondary: '#a73a00'
  on-secondary: '#ffffff'
  secondary-container: '#fd651e'
  on-secondary-container: '#571a00'
  tertiary: '#005338'
  on-tertiary: '#ffffff'
  tertiary-container: '#006e4b'
  on-tertiary-container: '#67f4b7'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#e2dfff'
  primary-fixed-dim: '#c3c0ff'
  on-primary-fixed: '#0f0069'
  on-primary-fixed-variant: '#3323cc'
  secondary-fixed: '#ffdbce'
  secondary-fixed-dim: '#ffb599'
  on-secondary-fixed: '#370e00'
  on-secondary-fixed-variant: '#7f2b00'
  tertiary-fixed: '#6ffbbe'
  tertiary-fixed-dim: '#4edea3'
  on-tertiary-fixed: '#002113'
  on-tertiary-fixed-variant: '#005236'
  background: '#faf8ff'
  on-background: '#131b2e'
  surface-variant: '#dae2fd'
typography:
  display-lg:
    fontFamily: Lexend
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Lexend
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
  headline-lg-mobile:
    fontFamily: Lexend
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
  headline-md:
    fontFamily: Lexend
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0.05em
  code:
    fontFamily: jetbrainsMono
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 4px
  xs: 0.25rem
  sm: 0.5rem
  md: 1rem
  lg: 1.5rem
  xl: 2rem
  2xl: 3rem
  gutter: 1.5rem
  margin-mobile: 1rem
  max-width: 1280px
---

## Brand & Style
The design system is built to empower African open-source contributors through a "Vibrant Professionalism" aesthetic. It balances the precision of global technology with the warmth of community.

The style is **Modern SaaS with Cultural Soul**. It utilizes heavy whitespace and clean layouts but punctuates them with subtle, geometric background patterns inspired by traditional African motifs (kente-grid logic, repetitive triangles). These patterns should be used at very low opacities (2-5%) to add texture without distracting from technical content. The emotional response should be one of confidence, inclusivity, and technical excellence.

## Colors
The palette is centered on the **Electric Indigo** primary, signifying the digital frontier and technical reliability. The **Terracotta Orange** serves as a high-energy accent for community features, call-to-actions, and contribution streaks, grounding the tech-heavy UI in a sense of warmth and earthiness.

**Success Green** is reserved for positive states: merged Pull Requests, verified contributors, and "Good First Issue" indicators. For Dark Mode, use the Deep Navy neutral as the base surface, ensuring that the Terracotta maintains enough contrast for accessibility.

## Typography
This design system employs a dual-font strategy. **Lexend** is used for headlines to provide a modern, friendly, and highly legible character that feels optimistic. **Inter** is used for all body copy and UI elements to maintain high performance and readability in data-dense code environments.

Headlines should be bold and confident. Use tight letter-spacing for large display text to create a more "editorial" tech look. For labels and metadata (like "Repository Weight"), use uppercase Inter with slight tracking to differentiate from standard body text.

## Layout & Spacing
The layout follows a **Fluid-to-Fixed 12-column grid**. On mobile, margins shrink to 16px to maximize screen real estate for code snippets. On desktop, the content is centered with a max-width of 1280px.

Spacing follows an 8pt rhythm for structural elements and a 4pt rhythm for internal component padding. Use "Loose" vertical spacing between sections (xl or 2xl) to create a premium, uncluttered feel that reduces the perceived complexity of open-source data.

## Elevation & Depth
Depth is created using **Tonal Layering** rather than heavy shadows. Surfaces sit on a light gray background (`#F8FAFC`). 

- **Level 0 (Background):** Solid background color with subtle pattern overlay.
- **Level 1 (Cards):** White background with a 1px border (`#E2E8F0`) and a very soft, diffused shadow (0 4px 6px -1px rgb(0 0 0 / 0.1)).
- **Level 2 (Hover/Active):** Primary color 1px border or a slightly deeper shadow to indicate interactivity.
- **Overlays:** Large blur radius (12px+) on backdrop filters for modals to maintain the "Glassmorphism" hint.

## Shapes
The design system uses a **Hyper-Rounded** approach to feel approachable and "community-first." 

Standard components (inputs, small buttons) use the `rounded-lg` (1rem) setting. Content containers and cards use `rounded-xl` (1.5rem). Large feature cards or hero sections can push this to `2rem` (32px) to emphasize the soft, welcoming nature of the platform.

## Components
- **Buttons:** Primary buttons use a solid Indigo fill with white text. Secondary buttons use a Terracotta outline for community-focused actions like "Join Discussion."
- **Issue Cards:** Feature a left-border accent color based on status (e.g., Green for beginner-friendly, Indigo for high-priority).
- **Beginner Indicators:** Small, pill-shaped chips with a "Sprout" icon and Success Green background/text.
- **Repository Weight:** Represented by a 3-bar vertical visualizer (similar to signal bars), where more bars indicate higher complexity.
- **Inputs:** High-contrast borders in the neutral shade, becoming Primary Indigo on focus.
- **Avatars:** Rounded-xl (not circles) to maintain consistency with the blocky yet soft shape language.
- **Line Icons:** Use Lucide/Feather style icons with a 1.5px stroke weight for a clean, technical look.