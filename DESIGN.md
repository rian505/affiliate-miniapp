---
name: Premium Editorial UI
colors:
  surface: '#f9f9fc'
  surface-dim: '#dadadc'
  surface-bright: '#f9f9fc'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f3f3f6'
  surface-container: '#eeeef0'
  surface-container-high: '#e8e8ea'
  surface-container-highest: '#e2e2e5'
  on-surface: '#1a1c1e'
  on-surface-variant: '#3d494d'
  inverse-surface: '#2f3133'
  inverse-on-surface: '#f0f0f3'
  outline: '#6d797e'
  outline-variant: '#bcc8cd'
  surface-tint: '#00677d'
  primary: '#00677d'
  on-primary: '#ffffff'
  primary-container: '#00a3c4'
  on-primary-container: '#00333f'
  inverse-primary: '#5cd5f8'
  secondary: '#3c6470'
  on-secondary: '#ffffff'
  secondary-container: '#bce6f5'
  on-secondary-container: '#406874'
  tertiary: '#4d6265'
  on-tertiary: '#ffffff'
  tertiary-container: '#83999c'
  on-tertiary-container: '#1d3134'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#b3ebff'
  primary-fixed-dim: '#5cd5f8'
  on-primary-fixed: '#001f27'
  on-primary-fixed-variant: '#004e5f'
  secondary-fixed: '#bfe9f7'
  secondary-fixed-dim: '#a4cddb'
  on-secondary-fixed: '#001f27'
  on-secondary-fixed-variant: '#234c58'
  tertiary-fixed: '#d0e7ea'
  tertiary-fixed-dim: '#b4cbce'
  on-tertiary-fixed: '#091f21'
  on-tertiary-fixed-variant: '#364a4d'
  background: '#f9f9fc'
  on-background: '#1a1c1e'
  surface-variant: '#e2e2e5'
typography:
  display-lg:
    fontFamily: Montserrat
    fontSize: 64px
    fontWeight: '700'
    lineHeight: '1.1'
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Montserrat
    fontSize: 48px
    fontWeight: '700'
    lineHeight: '1.2'
  headline-lg-mobile:
    fontFamily: Montserrat
    fontSize: 32px
    fontWeight: '700'
    lineHeight: '1.2'
  headline-md:
    fontFamily: Montserrat
    fontSize: 32px
    fontWeight: '600'
    lineHeight: '1.3'
  headline-sm:
    fontFamily: Montserrat
    fontSize: 24px
    fontWeight: '600'
    lineHeight: '1.4'
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: '1.6'
    letterSpacing: -0.01em
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.6'
  label-md:
    fontFamily: Montserrat
    fontSize: 14px
    fontWeight: '500'
    lineHeight: '1.2'
    letterSpacing: 0.04em
  label-sm:
    fontFamily: Montserrat
    fontSize: 12px
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: 0.02em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 4px
  gutter: 24px
  margin-desktop: 64px
  margin-mobile: 20px
  max-width: 1280px
---

## Brand & Style
Premium editorial design that bridges classical typography with modern digital surfaces. Targets a discerning audience that values clarity and aesthetic precision. The emotional response is "curated calm"—high-contrast Montserrat headings provide authority, while cyan accents inject energy.

Minimalism with subtle Glassmorphism. Generous whitespace and rigid grid allow typography to breathe. Translucent layers establish depth without clutter.

## Colors
- **Primary:** High-vibrancy Cyan (#00a3c4) for interaction and emphasis.
- **Secondary:** Near-black Teal (#00323d) for high-contrast text and navigation.
- **Tertiary:** Soft Cyan wash (#e0f7fa) for background surfaces.
- **Neutral:** Cool grays (#1a1c1e) for legible body copy.

## Typography
Montserrat for headings (geometric, confident, tight letter-spacing). Inter for body text (systematic, neutral, increased line-height). Labels use Montserrat medium-to-bold with increased letter-spacing.

## Layout & Spacing
Fixed Grid model. 1280px max-width on desktop, centered. 4px baseline spacing with increments of 8px, 16px, 24px, 48px. Breakpoints at 768px (tablet) and 1024px (desktop). Asymmetrical layouts preferred.

## Elevation & Depth
Tonal Layers and Backdrop Blurs. Ambient cyan-tinted shadows (0px 8px 32px rgba(0, 163, 196, 0.08)). No heavy shadows.

- **Level 0 (Base):** White or Tertiary Cyan (#e0f7fa).
- **Level 1 (Cards):** White with 1px border or soft cyan shadow.
- **Level 2 (Overlays):** Glassmorphic with 20px backdrop blur, 80% opacity.

## Shapes
Rounded shape language. 0.5rem (8px) base radius. Large containers (cards) use 1rem (16px).

## Components
- **Buttons:** Solid Cyan with white Montserrat (Medium). No gradients. Secondary = transparent + 1px Cyan border.
- **Cards:** White backgrounds with subtle Cyan shadows. Montserrat headline-sm inside.
- **Inputs:** Bottom-border-only or enclosed with 1px neutral border → Cyan on focus.
- **Chips:** Rounded pills, label-sm, light Cyan background (#e0f7fa), deep Cyan text (#00323d).
- **Lists:** Border-less rows, 16px vertical padding, subtle neutral divider.
