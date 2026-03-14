# Zorivest Design Style Guide

> Adapted from [matbanik.info style-guide.md](file:///p:/zorivest/_inspiration/style-guide.md) for a desktop trading application. This is the canonical visual identity reference for all GUI MEUs.

---

## §0 — Guiding Principle: Optimal Cognitive Load

> **Every screen must demand the optimal amount of cognitive effort — not too much, not too little.**

Financial trading UIs face a unique design tension: the data is inherently complex (market data, positions, P&L, risk), but every pixel of confusion costs real money. The design system optimizes for **germane cognitive load** (productive analysis) while minimizing **extraneous cognitive load** (wasted effort deciphering the UI).

### The Cognitive Load Balance Equation

```
Optimal UX = Minimize(Extraneous Load) + Maximize(Germane Load) + Accept(Intrinsic Load)
```

| Load Type | Definition | Trading Example | Design Response |
|-----------|------------|-----------------|-----------------|
| **Intrinsic** | Inherent complexity of the data | Markets ARE complex — P&L depends on position size, entry price, current price, fees | Accept it. Don't hide risk-relevant data behind abstractions |
| **Extraneous** | Cognitive waste from poor UI | Misaligned columns, inconsistent colors, decorative shadows, unclear icons | Eliminate it. Every visual element must convey data or enable navigation |
| **Germane** | Productive thinking | Pattern recognition, risk assessment, decision-making | Maximize it. Clear data-ink ratio, consistent visual language, logical grouping |

### Per-Screen Design Protocol

For EVERY screen in Zorivest, apply this 5-point checklist:

1. **One-thing test**: What is the ONE question this screen answers? *(Dashboard: "Am I profitable today?" — Trade Entry: "Will this order execute correctly?" — Analytics: "Where am I losing money?")*
2. **5-second test**: Can the user answer that question within 5 seconds of seeing the screen?
3. **Progressive disclosure audit**: What detail is hidden behind a click/expand? What is shown immediately? *(Summary → click for detail reduces cognitive load by ~55% per NNG research)*
4. **Data-ink audit**: Remove every visual element one at a time — does removing it lose data understanding? If no, it's decoration → remove it.
5. **Color signal check**: Does every color on this screen have a semantic meaning? Non-semantic color = background layer.

> [!IMPORTANT]
> This protocol is enforced per-tool/per-screen during content MEUs. The shell (MEU-43) establishes the token system; content MEUs apply the protocol to their specific screens.

---

## §1 — Color System

### Dark Theme Foundation (Dracula)

Inherited from matbanik.info. All tokens defined as CSS custom properties via Tailwind CSS v4 `@theme`:

| Token | Hex | Role | WCAG vs `--color-bg` |
|-------|-----|------|----------------------|
| `--color-bg` | `#282a36` | Primary background | — |
| `--color-bg-elevated` | `#44475a` | Cards, panels, table headers | — |
| `--color-bg-subtle` | `#6272a4` | Borders, muted backgrounds | ~3.2:1 (decorative only) |
| `--color-fg` | `#f8f8f2` | Primary text | ~11.5:1 ✅ AAA |
| `--color-fg-muted` | `#bae6fd` | Secondary text, metadata | ~11.1:1 ✅ AAA |

### Trading Semantic Colors

Extended beyond the blog palette for financial data:

| Token | Hex (Dark) | Role | Redundancy Cue |
|-------|-----------|------|----------------|
| `--color-pnl-profit` | `#50fa7b` | Gains, positive P&L | `↑` arrow + `+` prefix |
| `--color-pnl-loss` | `#ff5555` | Losses, negative P&L | `↓` arrow + `−` prefix |
| `--color-pnl-neutral` | `#6272a4` | Unchanged, zero P&L | `—` dash |
| `--color-status-pending` | `#ffb86c` | Order pending | ◉ dot icon |
| `--color-status-filled` | `#50fa7b` | Order filled | ✓ check |
| `--color-status-canceled` | `#6272a4` | Order canceled | ✗ cross |
| `--color-status-rejected` | `#ff5555` | Order rejected | ⚠ warning |

### Accent Colors

| Token | Hex | Role |
|-------|-----|------|
| `--color-accent-cyan` | `#8be9fd` | Interactive elements, links, focus rings |
| `--color-accent-green` | `#50fa7b` | CTA buttons, success states |
| `--color-accent-purple` | `#bd93f9` | Text selection, blockquote accents |
| `--color-accent-red` | `#ff5555` | Error states, destructive actions |
| `--color-accent-yellow` | `#f1fa8c` | Search highlights, warnings |

### Design Rules

- **Dark-first, light-capable**: Ship with dark theme. Light theme deferred to a polish MEU — but tokens are named semantically (`--color-bg`, not `--color-dark-bg`) so theming is a token swap, not a rewrite.
- **Non-color redundancy**: P&L MUST use arrows, prefixes, or icons alongside color (WCAG 1.4.1 — colorblind safety). Never rely on green/red alone.
- **Color as signal**: If a color doesn't convey meaning (profit, loss, interactive, error, warning), it's a background layer color.

---

## §2 — Typography

### Font Stacks (GitHub Primer — System Fonts)

Zero web font loading. Renders OS-native fonts for consistent desktop experience:

| Token | Stack | Usage |
|-------|-------|-------|
| `--font-sans` | `-apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji"` | Body text, headings, UI labels |
| `--font-mono` | `ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace` | Financial numbers, prices, quantities, code, timestamps |

### Type Scale (Dense Trading UI)

| Element | Size | Weight | Notes |
|---------|------|--------|-------|
| Base body | `14px` (0.875rem) | 400 | Tighter than 16px blog — suits data-dense views |
| Data grid cells | `13px` (0.8125rem) | 400 | Monospace, tabular-nums |
| Column headers | `12px` (0.75rem) | 600 | Uppercase, letter-spacing 0.05em |
| Panel titles | `16px` (1rem) | 600 | — |
| Page headings | `20px` (1.25rem) | 600 | — |
| Section headings | `14px` (0.875rem) | 600 | Uppercase, letter-spacing 0.05em |
| Small metadata | `11px` (0.6875rem) | 400 | Timestamps, secondary labels |

### Financial Number Rules

```css
.tabular-nums {
  font-variant-numeric: tabular-nums;
  font-family: var(--font-mono);
}
```

- ALL prices, quantities, and P&L values use `tabular-nums` + monospace — column alignment without jitter
- Decimal places: consistent per column (2 for USD, 8 for crypto, 4 for forex)
- Negative values: `−` (minus sign U+2212), never hyphen

---

## §3 — Spacing System

### Token Scale

| Token | Value | Usage |
|-------|-------|-------|
| `--space-2xs` | `2px` | Micro-gap (data cell padding, icon-to-text) |
| `--space-xs` | `4px` | Inline gaps, tight inner spacing |
| `--space-sm` | `8px` | Data grid row padding, list items, button padding |
| `--space-md` | `16px` | Panel padding, section margins |
| `--space-lg` | `24px` | Container padding, major separators |
| `--space-xl` | `48px` | Page-level spacing (rare in desktop) |

### Density Alignment

The shadcn/ui Mira preset uses compact spacing. Zorivest aligns with Mira:
- Table rows: `8px` vertical padding (not 16px)
- Card internal padding: `12-16px` (not 24px like blog cards)
- Form field gaps: `8px`
- Panel gaps: `8px`

---

## §4 — Border Radius

| Token | Value | Elements |
|-------|-------|----------|
| `--radius-none` | `0px` | Data table cells, inline elements |
| `--radius-sm` | `4px` | Code blocks, focus outlines, badges |
| `--radius-md` | `6px` | Form inputs, buttons |
| `--radius-lg` | `8px` | Cards, panels, dropdowns |
| `--radius-xl` | `12px` | Modals, command palette |
| `--radius-full` | `9999px` | Tags (pill), icon buttons |

---

## §5 — Visual Effects

### Principle: Depth via Borders, Not Shadows

Trading app users spend 8-16 hours on these screens. Heavy visual effects cause eye fatigue. Depth is communicated through background color layers and borders — NOT shadows or blur.

| Technique | Usage | Properties |
|-----------|-------|------------|
| Background layers | Base → Elevated → Subtle | `bg`, `bg-elevated`, `bg-subtle` (darkest → lightest) |
| Borders | Section dividers, input outlines | `1px solid var(--color-bg-elevated)` |
| Interactive highlight | Hover/focus states | Border color → `var(--color-accent-cyan)` |
| Blur (limited) | Command palette backdrop ONLY | `backdrop-filter: blur(8px)` |

### What We DON'T Use

- ❌ Decorative shadows on cards, panels, or data rows
- ❌ 3D transforms or perspective effects
- ❌ Background gradients
- ❌ Glassmorphism on data surfaces (reserved for overlays only)
- ❌ Animated backgrounds or particle effects

---

## §6 — Motion & Transitions

### Core Rule: Signal, Don't Decorate

Motion signals state change. It never decorates.

| Animation | Duration | Easing | Usage |
|-----------|----------|--------|-------|
| Color/background transitions | `150ms` | `ease-out` | Hover, focus, active states |
| Modal/overlay open | `200ms` | `cubic-bezier(0.16, 1, 0.3, 1)` | Command palette, dialogs |
| Modal/overlay close | `150ms` | `ease-in` | Fast dismissal |
| Error shake | `300ms` | spring | Form validation error |
| Toast slide-in | `200ms` | `ease-out` | Notification appearance |

### What We DON'T Animate

- ❌ Table row hover lifts (`translateY`) — causes visual jitter in dense grids
- ❌ Card entrance animations — data should appear instantly
- ❌ Continuous loading spinners on data cells — use skeleton/shimmer
- ❌ Decorative particle or background animations

### Reduced Motion Support (WCAG 2.3.3)

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

Tailwind: `motion-safe:transition-all motion-reduce:transition-none`

---

## §7 — Component Principles (Deferred to Content MEUs)

> [!NOTE]
> Component PATTERNS (cards, forms, tables, charts) are NOT specified here. They are built per-screen during content MEUs (MEU-46+). This section provides the guiding PRINCIPLES each component must follow.

### Per-Component Cognitive Load Checklist

When building any new component or screen, apply:

- [ ] **5-second test** passed — primary metric visible immediately
- [ ] **Data-ink audit** passed — no decorative pixels
- [ ] **Progressive disclosure** — detail behind click/expand, not upfront
- [ ] **Logical grouping** — related metrics in same card/section
- [ ] **Color signals only** — every color conveys meaning
- [ ] **Consistent vocabulary** — same term, same icon, same color as all other screens
- [ ] **Non-color redundancy** — P&L has arrows/prefixes alongside color
- [ ] **Keyboard accessible** — all interactions reachable via keyboard
- [ ] **Focus visible** — clear focus indicator on every interactive element

### Deferred Component Mapping

| Component Type | Target MEU | Style Guide Section Applied |
|---------------|------------|---------------------------|
| Data grid (positions, orders) | MEU-46 (Trades View) | §2 tabular-nums, §3 dense spacing, §5 borders |
| Trade entry form | MEU-47+ | §1 error colors, §6 error shake, this checklist |
| Chart overlays | MEU-65 (Market Data GUI) | §5 limited blur, §6 toast animations |
| Settings panels | MEU-44 (Settings) | §3 form spacing, §1 status colors |
| Command palette | MEU-44 | §5 blur backdrop, §6 modal transitions |
| Navigation rail | MEU-43 | §1 accent-cyan active, §3 compact spacing |
| Dashboard cards | MEU-46+ | §4 radius-lg, §3 card padding, this checklist |

---

## §8 — Desktop Layout

### Window Constraints

| Constraint | Value | Rationale |
|-----------|-------|-----------|
| Minimum size | `1024 × 600` | Smallest usable trading setup |
| Default size | `1280 × 800` | Common laptop resolution |
| Recommended size | `1920 × 1080` | Standard desktop monitor |
| Nav rail width (expanded) | `200px` | Icon + label navigation |
| Nav rail width (collapsed) | `48px` | Icon-only, hover to expand |
| Content header height | `48px` | Page title + breadcrumb + actions |

### No Responsive Breakpoints

Zorivest is desktop-only (Electron). Replace mobile breakpoints with:
- **Panel resizing**: Nav rail collapse/expand, split panes with drag handles
- **Window state persistence**: Restore size, position, maximized state via `electron-store`
- **Minimum size enforcement**: `BrowserWindow.setMinimumSize(1024, 600)`

---

## §9 — Accessibility

### MEU-43 Infrastructure (Build Now)

These accessibility features are part of the shell foundation — they must exist before any content is rendered:

| Feature | WCAG | Implementation |
|---------|------|----------------|
| **Keyboard navigation** | 2.1.1 | All functionality reachable via keyboard. Tab order follows visual order. |
| **Focus-visible ring** | 2.4.7 | `2px solid var(--color-accent-cyan)`, `2px` offset. Never `outline: none`. |
| **ARIA landmarks** | 1.3.1 | `<nav>` (rail), `<main>` (content area), `<aside>` (panels), `<header>` |
| **Skip-to-content link** | 2.4.1 | Hidden until focused, jumps to `<main id="main-content">` |
| **Heading hierarchy** | 1.3.1 | Single `<h1>` per page, sequential `h2` → `h3` |
| **`lang` attribute** | 3.1.1 | `<html lang="en">` on root |
| **Reduced motion** | 2.3.3 | `prefers-reduced-motion: reduce` media query (see §6) |
| **Color contrast** | 1.4.3 | All text ≥ 4.5:1 against background. See §1 WCAG ratios. |
| **Semantic HTML** | 1.3.1 | `<button>`, `<a>`, `<input>`, never `<div onClick>` |

### Content MEU Accessibility (Build Per-Screen)

| Feature | WCAG | Target MEU |
|---------|------|------------|
| **Focus trapping in modals** | 2.4.3 | Command palette (MEU-44), trade confirmations |
| **Form error identification** | 3.3.1 | Trade entry, settings forms |
| **Error suggestion** | 3.3.3 | Trade entry validation |
| **Non-color P&L indicators** | 1.4.1 | Trades view (MEU-46) — arrows + prefixes |
| **Target size 24×24px** | 2.5.8 | All buttons, clickable controls |
| **Screen reader live regions** | 4.1.3 | Real-time data updates (`aria-live="polite"`) |
| **High contrast mode** | — | `forced-colors: active` overrides |
| **Text zoom 200%** | 1.4.4 | Layout must not break at 200% zoom |

---

## §10 — Tailwind CSS v4.2 `@theme` Block

The starting template for `ui/src/renderer/styles/globals.css`:

```css
@import "tailwindcss";

@theme {
  /* ── Colors: Dracula Foundation ── */
  --color-bg: #282a36;
  --color-bg-elevated: #44475a;
  --color-bg-subtle: #6272a4;
  --color-fg: #f8f8f2;
  --color-fg-muted: #bae6fd;

  /* ── Colors: Accents ── */
  --color-accent-cyan: #8be9fd;
  --color-accent-green: #50fa7b;
  --color-accent-purple: #bd93f9;
  --color-accent-pink: #ff79c6;
  --color-accent-orange: #ffb86c;
  --color-accent-red: #ff5555;
  --color-accent-yellow: #f1fa8c;

  /* ── Colors: Trading Semantic ── */
  --color-pnl-profit: #50fa7b;
  --color-pnl-loss: #ff5555;
  --color-pnl-neutral: #6272a4;
  --color-status-pending: #ffb86c;
  --color-status-filled: #50fa7b;
  --color-status-canceled: #6272a4;
  --color-status-rejected: #ff5555;

  /* ── Fonts: GitHub Primer System Stacks ── */
  --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans",
    Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji";
  --font-mono: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas,
    "Liberation Mono", monospace;

  /* ── Spacing: Compact Trading Scale ── */
  --spacing-2xs: 2px;
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
  --spacing-xl: 48px;

  /* ── Border Radius ── */
  --radius-none: 0px;
  --radius-sm: 4px;
  --radius-md: 6px;
  --radius-lg: 8px;
  --radius-xl: 12px;
  --radius-full: 9999px;
}

/* ── Reduced Motion ── */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}

/* ── Tabular Numbers for Financial Data ── */
.tabular-nums {
  font-variant-numeric: tabular-nums;
  font-family: var(--font-mono);
}

/* ── Selection ── */
::selection {
  background: var(--color-accent-purple);
  color: var(--color-fg);
}

/* ── Focus Ring ── */
:focus-visible {
  outline: 2px solid var(--color-accent-cyan);
  outline-offset: 2px;
}

/* ── Skip Link ── */
.skip-link {
  position: absolute;
  top: -100%;
  left: 16px;
  z-index: 9999;
  padding: 8px 16px;
  background: var(--color-bg-elevated);
  color: var(--color-fg);
  border-radius: var(--radius-sm);
}
.skip-link:focus {
  top: 8px;
}
```

---

## Sources

| Source | Contribution |
|-------|-------------|
| [matbanik.info style-guide.md](file:///p:/zorivest/_inspiration/style-guide.md) | Color system, font stacks, spacing scale, border radius, accessibility baseline |
| [Dracula Theme](https://draculatheme.com/) | Color palette origin |
| [GitHub Primer](https://primer.style/) | System font stacks |
| [shadcn/ui Mira preset](https://ui.shadcn.com/) | Dense spacing, compact component patterns |
| WCAG 2.1 Level AA | Accessibility requirements |
| NNG Progressive Disclosure Research | 55% cognitive load reduction |
| Edward Tufte "Data-Ink Ratio" | Data visualization principle |
| [ChartsWatcher Trading Dashboard Best Practices](https://chartswatcher.com/pages/blog/top-dashboard-design-best-practices-for-traders-in-2025) | Trading-specific design patterns |
| [Fireart Dashboard Design Principles](https://fireart.studio/blog/dashboard-design-best-practices/) | 5-second rule, cognitive load management |
