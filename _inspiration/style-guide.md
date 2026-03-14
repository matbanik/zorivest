# Style Guide — matbanik.info

Design system reference documenting all look-and-feel decisions, token values, component patterns, and accessibility features. Written for AI agents, developers, and anyone recreating or extending the visual identity.

---

## Design Philosophy

The site presents a **dark-first, developer-centric aesthetic** inspired by code editors and terminal interfaces. Key principles:

- **Terminal elegance** — Monospace accents, code-style headings, subtle hover states
- **Minimal but polished** — No visual clutter; content-forward design with restrained decoration
- **Performance-first typography** — System font stacks (zero font-loading latency)
- **Accessibility by default** — ARIA landmarks, keyboard navigation, skip links, semantic HTML

The visual identity aligns with the author's brand as a Solutions Architect — technical, systems-oriented, clean.

---

## 1. Color System — Dracula Theme

The entire palette is based on the [Dracula Theme](https://draculatheme.com/), a popular dark color scheme originally designed for code editors. All colors are defined as CSS custom properties in [Layout.astro](file:///p:/matbanik.info/src/layouts/Layout.astro#L128-L164).

### Core Tokens

| Token | Hex | Role | WCAG Ratio vs `--color-bg` |
|-------|-----|------|----------------------------|
| `--color-bg` | `#282a36` | Primary background | — |
| `--color-bg-elevated` | `#44475a` | Cards, elevated surfaces, table headers | — |
| `--color-bg-subtle` | `#6272a4` | Borders, muted backgrounds, dividers | ~3.2:1 (large text only) |
| `--color-fg` | `#f8f8f2` | Primary text | ~11.5:1 ✅ AAA |
| `--color-fg-muted` | `#bae6fd` | Secondary text, placeholders, metadata | ~11.1:1 ✅ AAA |

### Accent Colors

| Token | Hex | Role | WCAG Ratio vs `--color-bg` |
|-------|-----|------|----------------------------|
| `--color-accent-cyan` | `#8be9fd` | Links, active states, focus rings, primary accent | ~9.4:1 ✅ AAA |
| `--color-accent-green` | `#50fa7b` | Success states, CTA buttons (Subscribe, Send) | ~10.1:1 ✅ AAA |
| `--color-accent-purple` | `#bd93f9` | Text selection background, blockquote borders | ~5.8:1 ✅ AA |
| `--color-accent-pink` | `#ff79c6` | Available but rarely used | ~5.7:1 ✅ AA |
| `--color-accent-orange` | `#ffb86c` | Available but rarely used | ~8.3:1 ✅ AAA |
| `--color-accent-red` | `#ff5555` | Error states, destructive actions | ~4.9:1 ✅ AA |
| `--color-accent-yellow` | `#f1fa8c` | Search highlight marks | ~13.3:1 ✅ AAA |

### Design Decisions

> [!NOTE]
> **Deviation from standard Dracula:** The `--color-fg-muted` value is `#bae6fd` (light blue) rather than the standard Dracula comment color `#6272a4`. This was done intentionally to achieve excellent contrast (~11.1:1) for secondary text elements like metadata, dates, and placeholders. Standard Dracula's comment color would fall below AA threshold for normal text.

> [!IMPORTANT]
> The site is **dark-mode only** — there is no light theme toggle and no `prefers-color-scheme` detection. This is a deliberate branding choice, not an omission.

### Semantic Color Usage

```
Background layers:    bg → bg-elevated → bg-subtle  (darkest → lightest)
Text layers:          fg → fg-muted                  (white → light blue)
Interactive:          accent-cyan (links, focus)
Success/CTA:          accent-green (buttons)
Error:                accent-red (form errors)
Selection:            accent-purple (::selection)
Highlight:            accent-yellow (search marks)
```

---

## 2. Typography — GitHub Primer System Fonts

No custom web fonts are loaded. Both stacks come from GitHub's [Primer Design System](https://primer.style/), defined in [Layout.astro](file:///p:/matbanik.info/src/layouts/Layout.astro#L145-L151).

### Font Stacks

| Token | Stack | Usage |
|-------|-------|-------|
| `--font-sans` | `-apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji"` | Body text, headings, UI elements |
| `--font-mono` | `ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace` | Logo, dates, tags, code, metadata, copyright, character counts, audio time |

### Type Scale

| Element | Size | Weight | Line Height | Notes |
|---------|------|--------|-------------|-------|
| Base body | `16px` (1rem) | 400 | 1.5 | CSS `html { font-size: 16px }` |
| Blog prose | `17px` (1.0625rem) | 400 | 1.5 | Slightly larger for readability |
| Paragraphs | — | — | 1.6 | `max-width: 65ch` for optimal line length |
| `h1` | `2.5rem` (40px) | 600 | 1.3 | — |
| `h2` | `2rem` (32px) | 600 | 1.3 | Blog h2: `1.5rem`, color: cyan |
| `h3` | `1.5rem` (24px) | 600 | 1.3 | Blog h3: `1.25rem` |
| `h4` | `1.25rem` (20px) | 600 | 1.3 | — |
| Nav links | `0.9375rem` | 400 | — | — |
| Small text | `0.875rem` | — | — | Dates, tags, metadata |
| Tiny text | `0.75rem` | — | — | Monospace UI labels |

### Design Decisions

- **System fonts = zero FOUT/FOIT** — No flash of unstyled or invisible text
- **Monospace accents** create the "developer terminal" aesthetic — used on the logo, dates, tags, bottom copyright, and time displays
- **65ch paragraph max-width** follows the typographic best practice of 45–75 characters per line for comfortable reading
- **-webkit-font-smoothing: antialiased** for crisper rendering on macOS

---

## 3. Spacing System

A 6-step scale defined as CSS custom properties in [Layout.astro](file:///p:/matbanik.info/src/layouts/Layout.astro#L153-L159):

| Token | Value | Usage Examples |
|-------|-------|----------------|
| `--space-xs` | `4px` | Inline gaps, icon padding, tight inner spacing |
| `--space-sm` | `8px` | Form field gaps, list item margins, button padding |
| `--space-md` | `16px` | General content padding, modal padding, list indentation |
| `--space-lg` | `24px` | Container padding, section margins, card padding, header height buffer |
| `--space-xl` | `48px` | Page-level padding, article top/bottom spacing |
| `--space-2xl` | `96px` | Major section separators (e.g., share section top margin) |

### Scale Logic

The scale doubles from xs→sm→md (4→8→16), then shifts to 1.5× increments (16→24) and 2× increments (24→48→96). This balances mathematical precision with practical spacing needs.

### Layout Constraints

| Variable | Value | Purpose |
|----------|-------|---------|
| `--max-width` | `1200px` | Global container max-width |
| `--header-height` | `64px` | Sticky header height |
| Blog post width | `800px` | `.post { max-width: 800px }` |
| Search dialog | `600px` | Modal max-width |
| Contact form | `500px` | Form max-width |
| Email subscription | `400px` | Footer/CTA form max-width |

---

## 4. Border Radius System

Not formally tokenized, but used consistently across components:

| Radius | Elements |
|--------|----------|
| `4px` | Inline code blocks, skip-link, focus outlines |
| `6px` | Form inputs, buttons, email inputs |
| `8px` | Social link icons, search trigger, language trigger, card actions |
| `12px` | Blog post cards, CTA containers, terminal blocks, language dropdown, post card |
| `16px` | Search modal dialog |
| `24px` | Audio player controls (pill shape) |
| `9999px` | Tags (full pill), audio trigger button |
| `50%` | Circular play/pause buttons, seek thumb |

---

## 5. Visual Effects

### Glassmorphism / Frosted Glass

Used on floating overlays to maintain depth hierarchy:

| Component | Background | Blur Amount |
|-----------|------------|-------------|
| AudioPlayer controls | `rgba(68, 71, 90, 0.8)` | `blur(8px)` |
| ShareCTA panel | `rgba(40, 42, 54, 0.5)` | `blur(20px)` |
| Search backdrop | `rgba(0, 0, 0, 0.8)` | `blur(4px)` |
| ShareCTA email input | `rgba(40, 42, 54, 0.8)` | none |

### Shadows

- Language dropdown: `0 8px 32px rgba(0, 0, 0, 0.3)`
- ShareCTA content: `0 8px 32px rgba(0, 0, 0, 0.2)`
- Most elements use **no shadow** — depth is communicated via background color layers and borders

### Borders

Consistent `1px solid` using background-layer tokens:
- Primary dividers: `var(--color-bg-elevated)` (header bottom, footer top, section dividers)
- Secondary/subtle: `var(--color-bg-subtle)` (form inputs, table cells, terminal)
- Interactive highlight: `var(--color-accent-cyan)` on hover/focus
- ShareCTA: `rgba(139, 233, 253, 0.3)` (semi-transparent cyan)

---

## 6. Interaction & Motion Patterns

### Transition Standards

| Property | Duration | Easing | Usage |
|----------|----------|--------|-------|
| Color, background, border | `0.2s` | `ease` | All links, buttons, inputs (default) |
| Transform | `0.2s` | `ease` | Card hover lift, button hover lift |
| Opacity + transform | `0.4s` | `cubic-bezier(0.16, 1, 0.3, 1)` | ShareCTA slide-in animation |
| Lang dropdown | `0.2s` | `ease` | Opacity + visibility + translateY |
| Progress bar | `0.1s` | `linear` | Audio player progress width |

### Hover Effects

| Element | Effect |
|---------|--------|
| Blog post cards | `translateY(-2px)` + cyan border |
| CTA/subscribe buttons | `translateY(-1px)` + bg color change |
| Social share buttons | `translateY(-2px)` + darken |
| Nav links | Color change to `--color-fg` + cyan underline |
| Logo | Color → accent-cyan |

### Selection Style

```css
::selection {
  background: var(--color-accent-purple);  /* #bd93f9 */
  color: var(--color-fg);                  /* #f8f8f2 */
}
```

---

## 7. Component Style Patterns

### Cards

Used in [BlogPostCard.astro](file:///p:/matbanik.info/src/components/BlogPostCard.astro):
- Background: `--color-bg-elevated`
- Border: `1px solid transparent` → `cyan` on hover
- Border-radius: `12px`
- Padding: `--space-lg` (24px)
- Hover: `translateY(-2px)` lift

### Forms

Used in [ContactForm.astro](file:///p:/matbanik.info/src/components/ContactForm.astro) and [Footer.astro](file:///p:/matbanik.info/src/components/Footer.astro):
- Input background: `--color-bg-elevated`
- Input border: `1px solid --color-bg-subtle` → `cyan` on focus
- Border-radius: `6px`
- Label: `<label class="visually-hidden">` (always present for accessibility)
- Submit button: `--color-accent-green` background, `--color-bg` text

### Terminal Block

Styled via global `.terminal-prompt` class in [Layout.astro](file:///p:/matbanik.info/src/layouts/Layout.astro#L312-L347):
- Background: `--color-bg-elevated`
- Border: `1px solid --color-bg-subtle`, radius `12px`
- Title bar pseudo-element (macOS-style) with `--color-bg-subtle` background
- Monospace font, `0.875rem`, line-height `1.35`
- `white-space: pre-wrap; word-wrap: break-word` for responsiveness

### Tags

- Font: `--font-mono`, `0.75rem`
- Background: `--color-bg-elevated`
- Color: `--color-accent-cyan`
- Border-radius: `9999px` (pill)
- Padding: `0.25em 0.75em`
- Text: uppercase, letter-spacing `0.05em`

---

## 8. Responsive Breakpoints

Only one breakpoint is used consistently:

| Breakpoint | Purpose |
|------------|---------|
| `768px` | Mobile ↔ Desktop switch for nav, footer layout, ShareCTA visibility |
| `640px` | Search label visibility toggle |
| `480px` | Contact form stacking, audio player compact mode |

> [!NOTE]
> The site does **not** use a comprehensive responsive breakpoint system. `768px` is the primary divider between mobile and desktop layouts. Components adapt with flexbox direction changes rather than complex grid reconfiguration.

---

## 9. Accessibility Features

### Implemented ✅

| Feature | WCAG | Implementation |
|---------|------|----------------|
| **Skip navigation link** | 2.4.1 | [Header.astro](file:///p:/matbanik.info/src/components/Header.astro#L29) — `<a href="#main-content" class="skip-link">`, translated text |
| **Keyboard focus visibility** | 2.4.7 | Global `:focus-visible` with `2px solid cyan` outline, `2px` offset |
| **ARIA landmarks** | 1.3.1 | `<nav aria-label>`, `<main id="main-content">`, `<article>`, `<footer>`, `<aside>` |
| **ARIA labels** | 4.1.2 | Translated labels on all buttons, links, and interactive elements |
| **aria-current="page"** | — | Active nav link identification |
| **aria-expanded** | — | Mobile menu, language switcher dropdown |
| **aria-haspopup="listbox"** | — | Language switcher trigger |
| **role="dialog" aria-modal** | — | Search modal |
| **role="listbox"** | — | Language dropdown |
| **aria-live="polite"** | 4.1.3 | Audio player time display |
| **aria-hidden="true"** | — | Decorative SVGs, honeypot fields |
| **Visually hidden labels** | 1.3.1, 3.3.2 | `.visually-hidden` class on all form labels |
| **Semantic HTML** | 1.3.1 | `<article>`, `<header>`, `<footer>`, `<main>`, `<aside>`, `<nav>`, `<time>` |
| **Heading hierarchy** | 1.3.1 | Proper h1 → h2 → h3 structure |
| **Keyboard shortcuts** | 2.1.1 | Audio: Space/Enter/Arrows. Search: Cmd+K, Escape. Dropdowns: Escape |
| **Color contrast** | 1.4.3 | All primary text exceeds AA; most exceed AAA (see color table above) |
| **lang attribute** | 3.1.1 | `<html lang={lang}>` with correct ISO code per page |
| **hreflang tags** | — | All 8 languages + x-default for multilingual SEO |
| **TTS audio narration** | — | Full-page narration in 8 languages for text-to-speech accessibility |
| **Autocomplete attributes** | 1.3.5 | `autocomplete="email"`, `autocomplete="name"` on forms |
| **External link security** | — | `rel="noopener noreferrer"` on all `target="_blank"` links |

### Hearing Impairment Accessibility

The site addresses hearing accessibility through content design rather than media accommodations:

- **No video with audio content** — Video embeds exist but are supplementary, not critical
- **TTS is additive, not required** — Audio narration duplicates existing text content; no unique audio-only content exists
- **All information is text-first** — The site's architecture ensures no information is conveyed exclusively through sound

### Color Blindness Considerations

The Dracula palette presents moderate color blindness challenges:

| Vision Type | Concern | Mitigations in Place |
|-------------|---------|---------------------|
| Protanopia (no red) | Red and green CTA buttons may appear similar | Buttons are context-separated (error vs. success) |
| Deuteranopia (no green) | Green CTA buttons may appear brownish | Text labels ("Subscribe", "Send") provide redundancy |
| Tritanopia (no blue) | Cyan links may lose vibrancy | Underline decoration on prose links provides secondary cue |

> [!WARNING]
> **Gap:** The site does not use patterns, textures, or icons as secondary indicators alongside color for error/success states. Currently relying on text content (e.g., "✓" / "✗") provides partial redundancy.

### Not Implemented (Gaps)

| Feature | WCAG | Status |
|---------|------|--------|
| `prefers-reduced-motion` | 2.3.3 | ❌ No motion suppression — all animations play unconditionally |
| `prefers-color-scheme` | — | ❌ Dark-mode only, no OS preference detection |
| `prefers-contrast` | 1.4.6 | ❌ No high-contrast mode support |
| `forced-colors` (Windows High Contrast) | — | ❌ No `forced-color-adjust` overrides |
| Focus trap in modals | 2.4.3 | ⚠️ Search modal opens but does not trap focus |

---

## 10. Tailwind CSS v4.2.x Translation

This section documents how the matbanik.info design system maps to Tailwind CSS v4.2.x, specifically for use in **desktop applications** (Tauri or Electron).

### v4 Architecture Overview

Tailwind CSS v4 uses a **CSS-first configuration** model. Instead of `tailwind.config.js`, customizations are defined in the CSS file via `@theme`:

```css
@import "tailwindcss";

@theme {
  /* Colors — Dracula */
  --color-bg: #282a36;
  --color-bg-elevated: #44475a;
  --color-bg-subtle: #6272a4;
  --color-fg: #f8f8f2;
  --color-fg-muted: #bae6fd;
  --color-accent-cyan: #8be9fd;
  --color-accent-green: #50fa7b;
  --color-accent-purple: #bd93f9;
  --color-accent-pink: #ff79c6;
  --color-accent-orange: #ffb86c;
  --color-accent-red: #ff5555;
  --color-accent-yellow: #f1fa8c;

  /* Fonts — GitHub Primer stacks */
  --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans",
    Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji";
  --font-mono: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas,
    "Liberation Mono", monospace;

  /* Spacing */
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
  --spacing-xl: 48px;
  --spacing-2xl: 96px;

  /* Border Radius */
  --radius-sm: 4px;
  --radius-md: 6px;
  --radius-lg: 8px;
  --radius-xl: 12px;
  --radius-2xl: 16px;
  --radius-full: 9999px;
}
```

### Utility Class Mapping

| Current CSS | Tailwind v4.2 Equivalent |
|-------------|--------------------------|
| `background: var(--color-bg)` | `bg-bg` |
| `background: var(--color-bg-elevated)` | `bg-bg-elevated` |
| `color: var(--color-fg)` | `text-fg` |
| `color: var(--color-accent-cyan)` | `text-accent-cyan` |
| `font-family: var(--font-mono)` | `font-mono` |
| `padding: var(--space-lg)` | `p-lg` |
| `border-radius: 12px` | `rounded-xl` |
| `max-width: 65ch` | `max-w-prose` (or `max-w-[65ch]`) |
| `.visually-hidden` | `sr-only` |
| `transition: all 0.2s ease` | `transition-all duration-200 ease-in-out` |
| `transform: translateY(-2px)` | `hover:-translate-y-0.5` |

### Tailwind v4.2 Accessibility Variants

These built-in variants address the accessibility gaps identified in section 9:

| Variant | CSS Media Query | Usage |
|---------|-----------------|-------|
| `motion-safe:` | `prefers-reduced-motion: no-preference` | Apply animations only when user allows |
| `motion-reduce:` | `prefers-reduced-motion: reduce` | Disable animations for sensitive users |
| `contrast-more:` | `prefers-contrast: more` | Enhance contrast for low-vision users |
| `contrast-less:` | `prefers-contrast: less` | Reduce contrast if preferred |
| `dark:` | `prefers-color-scheme: dark` | OS-level dark mode detection |
| `forced-colors:` | `forced-colors: active` | Windows High Contrast Mode |
| `forced-color-adjust-auto` | Utility class | Allow OS to override colors |
| `forced-color-adjust-none` | Utility class | Opt out of forced color adjustments |
| `sr-only` | — | Visually hidden, screen-reader accessible (replaces `.visually-hidden`) |

#### Example: Converting Hover Animations with Motion Safety

```html
<!-- Current: always animates -->
<div class="post-card">...</div>

<!-- Tailwind v4.2: respects user preference -->
<div class="motion-safe:hover:-translate-y-0.5 motion-safe:transition-transform
            motion-reduce:transition-none">
  ...
</div>
```

#### Example: High Contrast Support

```html
<!-- Enhance borders for high-contrast users -->
<input class="border border-bg-subtle
              contrast-more:border-fg-muted
              focus:border-accent-cyan" />
```

### Desktop Application Integration

Tailwind CSS v4.2 integrates seamlessly with both major desktop frameworks:

#### Tauri (Recommended)

| Aspect | Details |
|--------|---------|
| Webview | Uses OS native webview (WebView2 on Windows, WebKit on macOS/Linux) |
| Build tool | Vite (native Tailwind v4 integration via `@tailwindcss/vite`) |
| Bundle size | Minimal — no bundled browser engine |
| System fonts | The GitHub Primer font stack renders **OS-native fonts** — ideal for desktop apps |
| OS detection | `window.__TAURI__` for Tauri-specific features |

```bash
# Setup
npm create tauri-app@latest ./ -- --template vanilla-ts
npm install tailwindcss @tailwindcss/vite
```

#### Electron

| Aspect | Details |
|--------|---------|
| Webview | Bundles Chromium (~150MB) |
| Build tool | Vite or Webpack |
| Bundle size | Larger but consistent cross-platform rendering |
| System fonts | Same font stacks work — Chromium renders them correctly |

```bash
# Setup with Vite
npx -y create-electron-vite@latest ./
npm install tailwindcss @tailwindcss/vite
```

### Desktop-Specific Considerations

| Consideration | Recommendation |
|---------------|----------------|
| **Window chrome** | Use `--header-height: 64px` for custom title bar area |
| **OS theme detection** | Use `dark:` variant with `prefers-color-scheme` from OS |
| **Reduced motion** | Use `motion-safe:` / `motion-reduce:` — desktop users set this in OS accessibility settings |
| **High contrast** | Use `contrast-more:` — critical for enterprise desktop apps |
| **Forced colors** | Use `forced-color-adjust-none` on branded elements to preserve identity |
| **System font rendering** | The GitHub Primer stack is already optimal — each OS renders its native font |

### Additional Plugins

| Plugin | Purpose | Install |
|--------|---------|---------|
| `@tailwindcss/forms` | Accessible, consistent form element styling | `npm install @tailwindcss/forms` |
| `@tailwindcss/typography` | Prose styling (similar to `.prose` class in blog template) | `npm install @tailwindcss/typography` |
| `tailwindcss-accessibility` | Additional a11y utilities | `npm install tailwindcss-accessibility` |

---

## Sources

| Component | File | Key Styles |
|-----------|------|------------|
| Global CSS & tokens | [Layout.astro](file:///p:/matbanik.info/src/layouts/Layout.astro) | Colors, fonts, spacing, reset, tables, terminal blocks |
| Header & navigation | [Header.astro](file:///p:/matbanik.info/src/components/Header.astro) | Sticky header, skip-link, mobile menu, nav active states |
| Footer & subscription | [Footer.astro](file:///p:/matbanik.info/src/components/Footer.astro) | Social icons, email form, responsive layout |
| Blog post template | [[...slug].astro](file:///p:/matbanik.info/src/pages/hobbies/%5Bhobby%5D/posts/%5B...slug%5D.astro) | Prose styling, heading hierarchy, tag pills, share section |
| Audio player | [AudioPlayer.astro](file:///p:/matbanik.info/src/components/AudioPlayer.astro) | Glassmorphism, seekbar, keyboard shortcuts, ARIA |
| Blog post card | [BlogPostCard.astro](file:///p:/matbanik.info/src/components/BlogPostCard.astro) | Card pattern, hover lift, date formatting |
| Contact form | [ContactForm.astro](file:///p:/matbanik.info/src/components/ContactForm.astro) | Form inputs, validation states, honeypot |
| Search modal | [Search.astro](file:///p:/matbanik.info/src/components/Search.astro) | Modal dialog, backdrop blur, result highlighting |
| Language switcher | [LanguageSwitcher.astro](file:///p:/matbanik.info/src/components/LanguageSwitcher.astro) | Dropdown pattern, ARIA listbox, keyboard nav |
| Share CTA | [ShareCTA.astro](file:///p:/matbanik.info/src/components/ShareCTA.astro) | Scroll-triggered, glassmorphism, social buttons |
