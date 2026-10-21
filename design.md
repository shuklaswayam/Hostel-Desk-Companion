# Design — Hostel Parcel Desk

A locked design system for the Hostel Parcel Desk application. Every route, view, panel, and component reads from this specification. Do not invent un-tokenized styles on individual views.

## System
- Genre · modern-minimal
- Macrostructure · Workbench (app)
- Theme · Cobalt Precision (Deep Obsidian/Slate Base, Crisp Contrast, Electric Cobalt Accent)
- Axes · Dark/Light Slate Paper / Roman Display / Electric Signal Accent (Cobalt & Emerald)

## Design Tokens

```css
:root {
  /* Surface & Base - Dark Mode (Default) */
  --color-paper:        oklch(0.13 0.012 250);     /* #0c0f17 Deep obsidian base */
  --color-paper-2:      oklch(0.17 0.015 250);     /* #131824 Elevated card surface */
  --color-paper-3:      oklch(0.21 0.018 250);     /* #1a2233 Interactive surface / input */
  --color-paper-hover:  oklch(0.25 0.022 250);     /* #222c42 Hover surface */
  
  /* Borders & Rules */
  --color-rule:         oklch(0.26 0.015 250);     /* Hairline structural border */
  --color-rule-subtle:  oklch(0.20 0.012 250);     /* Faint inner divider */
  --color-rule-strong:  oklch(0.38 0.030 250);     /* Emphasized active border */
  
  /* Ink & Typography */
  --color-ink:          oklch(0.96 0.005 250);     /* Crisp primary text */
  --color-ink-2:        oklch(0.74 0.015 250);     /* Secondary descriptive text */
  --color-ink-muted:    oklch(0.52 0.015 250);     /* Tertiary metadata & labels */
  --color-ink-faint:    oklch(0.36 0.012 250);     /* Placeholders & disabled text */

  /* Semantic Signal Accents */
  --color-accent:       oklch(0.62 0.220 260);     /* Electric Cobalt / Indigo signal */
  --color-accent-hover: oklch(0.56 0.230 260);     /* Darker cobalt for hover */
  --color-accent-ink:   oklch(0.98 0.005 260);     /* High-contrast ink on accent */
  --color-accent-subtle:oklch(0.62 0.220 260 / 0.12);/* Tinted background wash */
  --color-focus:        oklch(0.68 0.200 260);     /* Focus outline ring */

  --color-success:      oklch(0.72 0.170 155);     /* Emerald for verified pickup */
  --color-success-bg:   oklch(0.72 0.170 155 / 0.12);
  --color-success-rule: oklch(0.72 0.170 155 / 0.35);

  --color-warning:      oklch(0.78 0.160 75);      /* Amber for pending & holding */
  --color-warning-bg:   oklch(0.78 0.160 75 / 0.12);
  --color-warning-rule: oklch(0.78 0.160 75 / 0.35);

  --color-danger:       oklch(0.65 0.220 25);      /* Crimson for overdue alerts */
  --color-danger-bg:    oklch(0.65 0.220 25 / 0.12);
  --color-danger-rule:  oklch(0.65 0.220 25 / 0.35);

  /* Typography Stack */
  --font-display:       'Space Grotesk', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-body:          'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-mono:          'JetBrains Mono', ui-monospace, SFMono-Regular, monospace;

  /* Type Scale (1.25 Major Third Anchor) */
  --text-2xs:           0.6875rem; /* 11px */
  --text-xs:            0.75rem;   /* 12px */
  --text-sm:            0.875rem;  /* 14px */
  --text-base:          0.9375rem; /* 15px */
  --text-md:            1.125rem;  /* 18px */
  --text-lg:            1.375rem;  /* 22px */
  --text-xl:            1.75rem;   /* 28px */
  --text-display:       clamp(1.75rem, 3vw + 0.5rem, 2.375rem);

  /* Spacing Scale (4-point System) */
  --space-3xs:          0.25rem;   /* 4px */
  --space-2xs:          0.5rem;    /* 8px */
  --space-xs:           0.75rem;   /* 12px */
  --space-sm:           1rem;      /* 16px */
  --space-md:           1.5rem;    /* 24px */
  --space-lg:           2rem;      /* 32px */
  --space-xl:           2.5rem;    /* 40px */
  --space-2xl:          3.5rem;    /* 56px */

  /* Radii */
  --radius-xs:          4px;
  --radius-sm:          6px;
  --radius-md:          10px;
  --radius-lg:          14px;
  --radius-xl:          20px;
  --radius-pill:        9999px;

  /* Shadows - Minimalist and crisp elevation, strictly no colored halo slop */
  --shadow-sm:          0 1px 2px rgba(0, 0, 0, 0.3);
  --shadow-md:          0 4px 12px rgba(0, 0, 0, 0.4);
  --shadow-lg:          0 12px 32px -4px rgba(0, 0, 0, 0.5);

  /* Motion - Natural exponential ease-out */
  --ease-out:           cubic-bezier(0.16, 1, 0.3, 1);
  --dur-fast:           150ms;
  --dur-base:           220ms;
  --dur-slow:           350ms;
}

/* Light Theme Variables */
[data-theme="light"] {
  --color-paper:        oklch(0.985 0.005 250);    /* Pure porcelain canvas */
  --color-paper-2:      oklch(1.000 0.000 0);      /* Clean crisp card surface */
  --color-paper-3:      oklch(0.955 0.008 250);    /* Input / light surface */
  --color-paper-hover:  oklch(0.930 0.012 250);
  
  --color-rule:         oklch(0.890 0.012 250);    /* Clean silver hairline */
  --color-rule-subtle:  oklch(0.930 0.008 250);
  --color-rule-strong:  oklch(0.780 0.025 250);

  --color-ink:          oklch(0.15 0.020 250);     /* Deep charcoal ink */
  --color-ink-2:        oklch(0.40 0.020 250);     /* Slate body */
  --color-ink-muted:    oklch(0.58 0.015 250);     /* Medium muted */
  --color-ink-faint:    oklch(0.75 0.010 250);

  --color-accent:       oklch(0.52 0.220 260);     /* Deep cobalt */
  --color-accent-hover: oklch(0.46 0.230 260);
  --color-accent-ink:   oklch(0.99 0.000 0);
  --color-accent-subtle:oklch(0.52 0.220 260 / 0.08);
  --color-focus:        oklch(0.52 0.220 260);

  --color-success:      oklch(0.55 0.170 155);
  --color-success-bg:   oklch(0.55 0.170 155 / 0.10);
  --color-success-rule: oklch(0.55 0.170 155 / 0.25);

  --color-warning:      oklch(0.65 0.160 75);
  --color-warning-bg:   oklch(0.65 0.160 75 / 0.10);
  --color-warning-rule: oklch(0.65 0.160 75 / 0.25);

  --color-danger:       oklch(0.55 0.220 25);
  --color-danger-bg:    oklch(0.55 0.220 25 / 0.10);
  --color-danger-rule:  oklch(0.55 0.220 25 / 0.25);

  --shadow-sm:          0 1px 2px rgba(0, 0, 0, 0.06);
  --shadow-md:          0 4px 14px rgba(0, 0, 0, 0.08);
  --shadow-lg:          0 12px 28px rgba(0, 0, 0, 0.10);
}
```

## Typography Rules
- Headings are Roman (`font-style: normal`). No italic emphasis inside headings.
- Display tracking is tight (`-0.025em` to `-0.035em`) for punch and confidence.
- Monospace font (`JetBrains Mono`) applied strictly to:
  - Carrier tracking numbers (`TRK-AMZ-8841`)
  - 6-digit verification PINs (`849201`)
  - Locker shelf racks (`Shelf A-02`)
  - Student registration IDs (`23BCE1048`)
  - Timestamps, waiting hours, and log records.

## CTA & Interactive Voice
- **Primary CTA:** High-contrast solid fill (`var(--color-accent)`), crisp text (`var(--color-accent-ink)`), `var(--radius-sm)` (6px), 8-state interactive transitions.
- **Secondary CTA:** Ghost / hairline bordered button (`var(--color-paper-2)` surface with `var(--color-rule)` border), crisp hover state.
- **Microinteraction Stance:**
  - Fast feedback: hover response within 150ms.
  - Active tap depression: `transform: translateY(1px)`.
  - Focus rings: 2px solid `var(--color-focus)` with 2px offset.
  - Zero bounce, zero rubber-banding, zero gratuitous glowing halos.
- **All 8 Interactive States Implemented:**
  1. Default
  2. Hover
  3. Focus-Visible
  4. Active
  5. Disabled
  6. Loading
  7. Error
  8. Success

## Mobile Responsiveness Guardrails
- Root `overflow-x: clip;` on both `html` and `body` (never `overflow-x: hidden`).
- Strict verification at 320px, 375px, 414px, 768px, 1024px, 1440px.
- Image and card grid tracks use `minmax(0, 1fr)`.
- Buttons and CTAs use `white-space: nowrap` and flexible wrapping without awkward split lines.
- Display headers wrap smoothly via `overflow-wrap: anywhere; min-width: 0`.

## Architecture Alignment
- Macrostructure: Workbench
- Stations:
  1. Active Inventory Workbench (search, filter, density-optimized table)
  2. Pickup Verification Station (split terminal with live preview certificate)
  3. Overdue Retention Watchdog (aging alerts & bulk dispatch triggers)
  4. Activity & Notification Transmission Log (dual live streams)
- Modals:
  - Parcel Intake Modal (structured, keyboard-accessible)
  - Handover PIN Voucher Dialog (clean mono display with copy button)
