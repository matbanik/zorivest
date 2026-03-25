# Technology Stack Validation for an Electron + React Trading Desktop App

This report validates foundation choices for an Electron renderer built with React, where Electron spawns a local Python backend and the UI communicates over HTTP (REST). The emphasis is on “wrong choice cascades” risks: ecosystem compatibility, long-lived maintenance, and late-stage migration cost.

## React version strategy for Electron renderer

**Recommendation (version):** Use **React 19.2.4** for new work (renderer + shared UI packages). Keep **React 18.3.1** as your fallback “stability baseline” if you hit a third‑party dependency wall. citeturn7search20turn8view0turn9search2turn19search24

**Rationale (3–5 sentences):** React 19 has been stable since December 2024 and has had multiple minor/patch rounds since, which is long enough that mainstream libraries have updated peer dependency ranges for React 19. citeturn10search13turn8view0turn22view0turn13search1 In a desktop Electron renderer, React 19’s most relevant benefits are *not* Server Components, but (a) improved form and async state ergonomics via Actions and related hooks, (b) better control over “busy/idle” UI and state preservation patterns that matter in multi-panel trading workflows, and (c) incremental improvements in the core runtime and tooling compatibility as the ecosystem standardized on React 19. citeturn10search13turn26search3 If you ever have to pause on React 19, React 18.3.x exists specifically to surface deprecation warnings and migration issues before jumping to 19. citeturn19search24turn9search2

**React 19 features that matter for Electron (excluding Server Components):**
- **Actions + improved form submission patterns**: useful for trade tickets and settings forms where you need clean pending/error/optimistic UX without bespoke boilerplate. citeturn10search13turn26search3  
- **Activity-oriented UI control (React 19.2)**: relevant for “module switching” (portfolio → orders → analytics) where you want to preserve state while marking sections inactive, and keep the UI responsive during heavy updates. citeturn26search3turn26search25  
- **New/refined deprecations and runtime semantics**: mostly important because they affect library compatibility and testing utilities (e.g., deprecated/removed legacy test utils). citeturn19search24turn16search17  

**Compatibility evidence (libraries listed):**
- **TanStack Query v5**: explicitly peers React `^18 || ^19` in package metadata (example v5.87.1). citeturn13search1  
- **TanStack Table v8**: docs explicitly state the adapter works with React 16.8–19. citeturn13search10  
- **Sonner**: package peer dependencies include React 18 and 19. citeturn12search7  
- **React Testing Library**: current package peer dependencies include React `^18 || ^19` (and also peers `@testing-library/dom`). citeturn22view0  
- **React Router (v6 / v7)**: the project positions v6→v7 as **non‑breaking** and explicitly “bridge to React 19” (important if you want React 19 without routing friction). citeturn23search28turn23search6  
- **React Hook Form**: package peer dependencies include React up through `^19` (example package.json snapshot). citeturn13search3  
- **Fuse.js**: framework-agnostic fuzzy search usage is not inherently coupled to React; React 18 vs 19 doesn’t typically change how you call a standalone JS search index (the main practical concern is bundler/ESM compatibility, not React itself).

**Breaking changes in React 19 that can affect an Electron app:**
- **New JSX Transform required** (if you have older toolchains or unusual TS/JS builds). citeturn19search24  
- **Testing surface changes**: removal/migration away from certain legacy testing utilities (notably `react-dom/test-utils` guidance) can force test refactors. citeturn19search24turn9search5  
- **Deprecations around `ref` access (`element.ref`)** and other subtle runtime behaviors can break older libraries or internal abstractions. citeturn16search17  

**If you choose React 18: recommended version & security patch status**
- **Recommended React 18 baseline:** **18.3.1** (designed to be “18.2 + warnings” so you can cleanly migrate). citeturn19search24turn9search2  
- **Security patch posture:** React’s versioning policy states security vulnerabilities are backported for **all affected major versions**, even if new features are not. citeturn9search0  

**Risk if wrong choice is made:**  
Choosing React 19 *before* all dependencies accept React 19 peer ranges can block installs (or push you into `--force` / overrides), and those “install anyway” paths can hide real incompatibilities until runtime or CI. citeturn11search21turn22view0 On the other hand, staying on React 18 too long increases the probability that newer versions of key dependencies increasingly assume React 19+ semantics and testing patterns, pushing upgrade cost downstream into the exact “22+ module” phase you’re trying to protect. citeturn9search1turn23search28

**Migration difficulty if you change later:** **Medium**  
React 18→19 is typically manageable but touches compiler/tooling (JSX transform), tests, and any deprecated APIs across a large UI surface area. citeturn19search24turn16search17 React 19→18 is harder if you adopt 19‑only hooks/patterns widely (you’d end up refactoring “backward”).  

## Electron runtime version selection

**Recommendation (version):** Target **Electron 41.0.2** (stable as of March 13, 2026). citeturn1search0

**Rationale (3–5 sentences):** Electron’s security and stability posture is heavily coupled to its bundled Chromium and Node versions, so the latest stable is the safest default for a trading app that will ship to end users. citeturn1search0turn1search17 Electron 41.0.2 bundles **Chromium 146.0.7680.72** and **Node 24.14.0**, which materially affects native APIs, TLS/cert behavior, and dependency compatibility in the main process. citeturn1search0 Aligning to current stable also reduces the chance you’ll be forced into a rushed major upgrade later due to Chromium security windows. citeturn1search17

**Bundled versions (as requested):**
- **Electron stable:** 41.0.2 citeturn1search0  
- **Chromium:** 146.0.7680.72 citeturn1search0  
- **Node.js:** 24.14.0 citeturn1search0  

**ESM-related breaking changes / considerations:**
- Electron supports **ES Modules in the main process**, but ESM migration interacts with preload scripts, sandboxing, and tooling. citeturn2search4turn2search9  
- Some ecosystem packages are now **ESM-only** (notably `electron-store`), which forces your main/preload build to be compatible with ESM. citeturn2search0turn2search1  

**Recommended minimum Electron versions for key security primitives & libraries:**
- `electron-store`: **requires Electron 30+** and is **ESM-only** in current releases. citeturn2search0turn2search1  
- `contextBridge`: introduced as a first-class module in **Electron 7.1.0**, and is the standard way to expose a safe API into the renderer. citeturn3search0turn3search1  
- `contextIsolation`: Electron docs note it has been **enabled by default since Electron 12**, which is consistent with modern security guidance. citeturn2search6turn3search3  

**Known issues with Electron + Vite (latest):**
- **Preload + ESM + sandbox/context isolation** remains a common sharp edge; Electron issue threads show real-world failures and race-condition-like behavior when using ESM preloads. citeturn2search9turn2search11  
- The Electron-Vite ecosystem explicitly documents production routing constraints (hash routing) and the “dev works, prod breaks” category that often comes from history handling and packaging differences. citeturn23search36  

**Risk if wrong choice is made:**  
Selecting an Electron major that’s too old can force you into insecure Chromium/Node combinations and can hard-block libraries that have already moved their minimum Electron/Node requirements (e.g., `electron-store` requiring Electron 30+). citeturn2search0turn1search17 Selecting a very new Electron major without validating your Vite + preload + ESM strategy can lead to “production-only” failures that are expensive to debug once 20+ UI modules exist. citeturn2search9turn23search36

**Migration difficulty if you change later:** **Medium**  
Electron major upgrades commonly require coordinated updates to build tooling, preload security patterns, native modules, and OS-specific packaging. Electron’s published support timelines are explicitly designed around frequent major movement. citeturn1search17  

## CSS framework and styling approach for a dense trading UI

**Recommendation (version):** Use **Tailwind CSS 4.2.1** as the baseline styling system, paired with CSS custom properties for tokens and theme-switching (and optionally a component layer like shadcn/ui if you want a ready-made, accessible baseline). citeturn26search32turn24search0turn24search1

**Rationale (3–5 sentences):** Tailwind v4 is explicitly built around a modern build-time engine and modern CSS primitives, enabling fast iteration and consistent styling across a large, modular UI surface. citeturn24search0 Its dark mode approach is well-defined and works naturally with local persistence (e.g., storing theme choice), which is important for trading apps where users often demand persistent dark mode preferences. citeturn24search1 For data-heavy tables and charts, Tailwind’s utility approach reduces “mystery CSS” debugging and makes layout constraints (grid/flex, sticky headers, overflow behaviors) more explicit at the component boundary. citeturn24search0turn24search3

**Assessment by option (bundle size, DX, themes, TanStack Table renderers):**

**Tailwind CSS v4 (utility-first)**
- **Bundle size impact:** Tailwind is a build-time CSS generator; it’s designed for a specific workflow and produces static CSS output, so runtime overhead is effectively nil. citeturn24search0turn26search28  
- **Developer experience:** v4 highlights simplified setup and a new engine optimized for build performance. citeturn24search0  
- **Theme switching:** Tailwind’s dark mode supports class-based toggling and persistence patterns (e.g., applying `class="dark"` and saving preference). citeturn24search1  
- **TanStack Table compatibility:** TanStack Table is presented as “headless UI,” meaning you own rendering and styling; Tailwind works well for this because you style cells/rows directly in render functions. citeturn13search6turn13search10  

**CSS Modules (scoped styles)**
- **Bundle size impact:** Compiled CSS with no runtime library; Vite extracts CSS per chunk automatically, which can help keep initial renderer load lean. citeturn24search3turn24search9  
- **Developer experience:** Excellent for component-scoped styles without global collisions; naming conventions and local scope are core to the model. citeturn24search9  
- **Theme switching:** Straightforward with CSS variables in `:root` / `[data-theme]` plus toggling attributes from Electron (or persisted store).  
- **TanStack Table compatibility:** Works well; you apply module class names in cell renderers, but you may spend more time building a reusable “table styling kit” instead of composing utilities inline.

**Vanilla Extract (type-safe CSS-in-TS, zero runtime)**
- **Bundle size impact:** Generates static CSS at build time (“zero runtime”), so it stays performant in Electron. citeturn24search2turn24search8  
- **Developer experience:** Strong if your team wants type-safe tokens and theme contracts (useful in trading UIs where colors and spacing often become a “design system”). citeturn24search2turn24search8  
- **Theme switching:** First-class theming primitives (e.g., generated variables/themes) designed into the library. citeturn24search2turn24search8  
- **TanStack Table compatibility:** Works well; you’ll likely create style objects/classes for table primitives and apply them in renderers.

**Plain CSS with custom properties**
- **Bundle size impact:** Minimal and fully under your control.  
- **Developer experience:** Lowest abstraction, but can become “global CSS entropy” unless you enforce conventions.  
- **Theme switching:** Excellent (CSS variables are the native mechanism), but you must design the token system yourself.  
- **TanStack Table compatibility:** Fine, but you may end up re-creating utility patterns and layout primitives in bespoke CSS as the UI grows.

**Risk if wrong choice is made:**  
Picking a styling system that doesn’t scale with your component count can create a compounding refactor tax—especially for trading UIs where table density, sticky regions, and theming can become pervasive cross-cutting concerns. Tailwind v4 also has explicit browser-baseline expectations; if you needed to support older browsers, you’d be forced to remain on v3.x—but this is rarely a constraint for Electron because Chromium is bundled. citeturn26search5turn1search0

**Migration difficulty if you change later:** **High**  
A styling approach is “everywhere” (tables, charts, and forms), so switching later often means rewriting markup, class composition, and token definitions across most modules.  

## Form library choice for trade entry and settings flows

**Recommendation (version):** Use **React Hook Form 7.71.2** + **Zod** validation via **@hookform/resolvers** (and align components to the same patterns used by shadcn/ui forms if you adopt that component ecosystem). citeturn12search17turn25search3turn25search30

**Rationale (3–5 sentences):** React Hook Form has current package support for React 19 in its peer dependency range, so adopting React 19 does not force a form rewrite. citeturn13search3turn10search13 Zod integration is explicitly supported through the resolvers package and is widely used in modern React stacks because it centralizes schema validation and keeps validation logic consistent across client and server boundaries. citeturn25search3turn25search30 For trading ticket UX, the practical advantages are predictable validation, low-latency keystroke handling, and clean integration with a component library layer (inputs/selects) without turning every keystroke into a global re-render. citeturn25search30turn25search14

**Comparison: React Hook Form vs native controlled components vs Formik**
- **React Hook Form:** Best fit when you have many forms and want schema-driven validation. The resolvers package exists explicitly to integrate external validators like Zod. citeturn25search3turn25search30  
- **Native controlled components:** React documents the controlled component pattern (single source of truth in state), but implementing this across many complex forms can expand boilerplate quickly. citeturn25search14  
- **Formik:** Formik is explicitly designed to help build forms in React and provides structured validation guidance (including schema-style validation). citeturn25search11turn25search35 It is viable, but tends to be more “framework-like,” and many modern stacks choose Hook Form for leaner integration with schema validators and component libraries.

**Zod integration evidence (explicit):**
- Resolvers project states it enables integration with external validation libraries including Zod. citeturn25search3  
- shadcn/ui’s forms docs show `zodResolver` usage with React Hook Form. citeturn25search30  

**Risk if wrong choice is made:**  
If you standardize on controlled components everywhere, you risk an accumulation of one-off form abstractions (especially across settings/account/plan management) that become difficult to maintain consistently—validation drift becomes a real risk in a trading product. citeturn25search14turn25search35 If you choose a heavier form framework and later decide you need more performance or tighter component-library integration, the refactor tends to cut across every screen that has input state.

**Migration difficulty if you change later:** **Medium**  
Switching between form libraries is usually localized to form-heavy modules, but in your case (multiple “entry points” + shared validation schemas), it will still touch many modules and shared components.  

## Testing stack for Electron plus a spawned local backend

**Recommendation (version):**  
- **Vitest 4.1.x** for unit/component tests. citeturn26search22turn26search7  
- **React Testing Library 16.3.2** for renderer component tests. citeturn22view0turn17search3  
- **Playwright 1.58** (Playwright Test) for E2E, using its Electron automation APIs. citeturn26search1turn25search15turn25search1  

**Rationale (3–5 sentences):** Vitest is designed to reuse Vite’s pipeline and is configured through Vite config, which aligns with modern Electron+Vite setups and keeps renderer testing fast. citeturn26search0turn25search6 React Testing Library requires minimal setup and is designed to work with any test runner, so it pairs cleanly with Vitest for component testing. citeturn25search0turn22view0 For E2E, both Electron’s own documentation and Playwright’s API docs show Electron automation via `_electron.launch`, and Playwright’s ElectronApplication API supports controlling both windows and the main process. citeturn25search15turn27view0

**Compatibility evidence (what confirms feasibility):**
- Electron docs: Playwright launches Electron apps through `_electron.launch` and shows a minimal test pattern. citeturn25search15  
- Playwright Electron API: Playwright documents Electron support as experimental, and provides `electron.launch`, `ElectronApplication.evaluate()` (main process), and `firstWindow()` (renderer window). citeturn25search1turn27view0  
- Vitest configuration: Vitest is configured via `test` property in Vite config (or via `vitest/config`), aligning with a Vite-first stack. citeturn25search6  
- React Testing Library peer deps accept React 18/19 and is compatible with current React majors. citeturn22view0  

**Vitest + React Testing Library caveats in Electron renderer:**
- Treat renderer tests as “web-like”: run in `jsdom` for component tests, and mock Electron-only modules (IPC, native dialogs, file access) behind your preload boundary. Vitest supports configuration centrally in Vite/Vitest config. citeturn25search6turn25search0  
- Keep most business logic in pure TS modules so you can test without an Electron runtime.

**How to test Electron IPC (main ↔ renderer):**
- **Main-process integration tests:** Use Playwright’s `electronApp.evaluate()` to run assertions in the main process context (e.g., validate that certain IPC handlers were registered, or call internal functions that your IPC handlers delegate to). citeturn27view0  
- **Renderer integration tests:** Use `firstWindow()` to drive the UI and assert the renderer behavior; if your renderer calls `window.api.someMethod()` (exposed through `contextBridge`), you can validate end-to-end behavior by observing UI updates or by instrumenting events/logging. citeturn27view0turn3search0  

**How to test Python backend health check during E2E:**
- Playwright provides **APIRequestContext** specifically for API/REST testing and for verifying server-side postconditions during E2E. citeturn28search2turn28search5  
- Pattern: in Playwright E2E, after launching Electron (which spawns the backend), call your backend health endpoint via APIRequestContext (or via `page.request`) and assert success before continuing UI flows. citeturn28search2turn28search5  
- FastAPI’s own docs show a standard testing model via `TestClient`, which you can leverage separately for backend-only tests; for E2E, you’ll still prefer a real process + real HTTP call. citeturn28search15  

**Risk if wrong choice is made:**  
Using a test stack that cannot reliably automate Electron + main process behavior often results in either (a) an untested main process or (b) reintroducing brittle, UI-only tests that miss IPC/backend integration bugs. The Electron and Playwright docs indicate the “correct path” for modern Electron automation is Playwright-based, so deviating usually means adopting community-only tooling with uncertain maintenance. citeturn25search15turn27view0

**Migration difficulty if you change later:** **Medium**  
Unit tests are relatively portable, but E2E harness changes (how you launch Electron, capture logs/screenshots, control the main process, and validate backend readiness) can be time-consuming once CI pipelines and fixtures are established. citeturn27view0turn28search5  

## Router strategy in Electron

**Recommendation (version):** Use **React Router v7.13.1** (current) with **Hash-based routing** for production Electron builds. citeturn23search14turn23search36

**Rationale (3–5 sentences):** React Router explicitly frames v6→v7 as **non‑breaking**, and positions v7 as a bridge to React 19, which reduces risk if you are adopting React 19 now. citeturn23search28turn0search17 In Electron production, you typically load the renderer from a packaged file path rather than a web server with rewrite rules; hash routing avoids the “refresh / deep link” failures that occur when the environment can’t serve `/route` as `index.html`. Electron-Vite’s troubleshooting guide explicitly calls out that only hash-based routing works properly in production and even shows how to load a hash route via `BrowserWindow.loadFile(..., { hash })`. citeturn23search36

**Compatibility evidence (links to project guidance and docs):**
- React Router: “Upgrading from v6 to v7 is non-breaking” and “Bridge to React 19.” citeturn23search28  
- React Router v6.30.3 changelog exists and is actively maintained as a v6 line (useful if you lock to v6 temporarily). citeturn23search6  
- Electron-Vite: recommends `HashRouter` for `react-router-dom` in production and shows hash loading. citeturn23search36  
- TanStack Router alternative: documents hash routing and other history types (browser/hash/memory), which is relevant if you consider switching for type-safe routing. citeturn23search3turn23search19  

**Hash router vs browser router in Electron context:**
- **Hash routing:** safest default for packaged desktop apps because it doesn’t rely on server-side rewrites. citeturn23search36  
- **Browser/history routing:** can work in development (because dev servers handle rewrites) but is a common source of production-only breakage after packaging. citeturn23search36  

**TanStack Router as an alternative (when it’s worth it):**  
TanStack Router offers fully type-safe routing and first-class search param typing, which can be compelling in a trading app where route state can encode filters, account context, and “view modes.” citeturn23search19turn23search11 That said, it is a different router paradigm; if React Router already solves your needs, TanStack Router should be treated as a deliberate “type-safety push,” not a casual substitution.

**Risk if wrong choice is made:**  
Choosing BrowserRouter/history routing without controlling URL rewriting at runtime can yield a renderer that navigates fine in dev but breaks in production packages, and fixing it later can require touching navigation across many modules. citeturn23search36 Choosing a router that doesn’t align with your React major (or your build tooling) can also create peer dependency churn and pressure you into overrides that mask real incompatibilities. citeturn23search28turn22view0  

**Migration difficulty if you change later:**  
- **React Router v6 → v7:** **Low** (explicitly non-breaking). citeturn23search28turn0search17  
- **BrowserRouter → HashRouter:** **Medium** (URL scheme changes; deep links/route parsing updates). citeturn23search36  
- **React Router → TanStack Router:** **High** (routing primitives, loaders, link generation, and type systems differ). citeturn23search19turn23search3
