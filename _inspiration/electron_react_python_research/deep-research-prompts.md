# Deep Research Prompts — Phase 6 GUI Shell Foundation

> Three tailored prompts for Gemini 3.1 Pro, GPT-5.4, and Claude Opus 4.6.
> Each leverages the model's strengths against different research dimensions.
> After all three return, synthesize into `docs/research/gui-shell-foundation/decision.md`.

---

## Prompt 1: Gemini 3.1 Pro — Architecture Pattern Extraction

> **Why Gemini**: Large context window + strong code analysis. Ideal for scanning GitHub repos, extracting file structures, and identifying architecture patterns from real-world Electron + React + Python applications.

```
# RESEARCH TASK: Electron + React + Python Desktop App Architecture Patterns

## Context
I'm building a trading portfolio management desktop application called Zorivest. The architecture is:

- **Backend**: Python (FastAPI on localhost:8765) — already complete with 60+ modules covering domain entities, SQLCipher encrypted DB, REST API (30+ endpoints), and MCP tools
- **Frontend**: Electron + React desktop app (not yet started — this is the research)
- **IPC**: The Electron main process spawns Python backend as child_process, React renderer communicates via REST on localhost
- **Key libraries already committed to**: TanStack Query (server state), TanStack Table (data grids), Lightweight Charts (financial charts), fuse.js (fuzzy search), sonner (toasts), electron-store (window persistence)

## What I Need From You

### 1. Electron + Vite Integration Analysis
Analyze these three approaches for Electron + Vite + React integration. For each, I need:
- Current maintenance status (last commit, open issues, community activity)
- Project directory structure it produces
- How it handles: main process, preload scripts, renderer process, HMR in dev, production builds
- How it handles TypeScript configuration
- How easy it is to add Electron Builder for distribution

**Approaches to compare:**
a) `electron-vite` by alex8088 (https://github.com/alex8088/electron-vite)
b) `electron-forge` with Vite plugin (https://github.com/electron/forge)  
c) `vite-plugin-electron` (https://github.com/electron-vite/vite-plugin-electron)

### 2. Reference Architecture Extraction
Scan these repos and extract their Electron + React project structure, IPC patterns, and Python/backend spawning approach:

a) **electron-react-boilerplate** (https://github.com/electron-react-boilerplate/electron-react-boilerplate) — Extract: directory layout, main/renderer separation, build pipeline
b) **Signal Desktop** (https://github.com/signalapp/Signal-Desktop) — Extract: security patterns (contextIsolation, nodeIntegration settings), preload script patterns, electron-store usage
c) Any Electron + Python apps you can find — Extract: child_process spawn patterns, health check, port discovery, graceful shutdown

### 3. Component Library Compatibility Matrix
For each component library below, verify compatibility with:
- React 18 AND React 19
- TanStack Table v8+  
- TanStack Query v5+
- Electron renderer context (no SSR/Server Components)
- TypeScript strict mode

**Libraries to check:**
a) shadcn/ui + Tailwind CSS
b) Radix UI primitives + custom CSS
c) Mantine v7+
d) MUI v6+

### 4. Python Backend Spawning Patterns
Research how Electron apps spawn and manage Python backends. I need:
- Process spawn code (child_process.spawn vs fork vs exec)
- Health check patterns (polling REST endpoint vs IPC)
- Port discovery (fixed port vs dynamic allocation)
- Dev mode vs production mode path resolution
- Graceful shutdown on app quit
- What happens when Python crashes (restart? user notification?)

## Output Format
For each section, provide:
1. **Recommendation** with rationale
2. **Code snippets** from reference repos demonstrating the pattern
3. **Risk assessment** for each option
4. **Version-locked dependency list** for the recommended choice
```

---

## Prompt 2: GPT-5.4 — Ecosystem Evaluation & Compatibility Research

> **Why GPT-5.4**: Strong reasoning + web search capabilities. Ideal for evaluating current ecosystem state, checking version compatibility, assessing community health, and identifying potential breaking changes.

```
# RESEARCH TASK: Technology Stack Validation for Electron + React Trading Desktop App

## Context
I'm building Zorivest, a trading portfolio management desktop app. The backend (Python/FastAPI) is complete. I'm now starting the Electron + React frontend (Phase 6), which will spawn the Python backend and communicate via REST.

This frontend is critical — 22+ downstream GUI modules depend on the foundation choices made now. Wrong choices cascade.

## Technology Decisions I Need You To Validate

### Decision 1: React 18 vs React 19 for Electron Desktop
Research and recommend:
- Is React 19 stable enough for production desktop apps as of March 2026?
- What React 19 features are relevant for Electron (NOT Server Components — those don't apply)?
- Are these libraries compatible with React 19?
  - `@tanstack/react-query` v5
  - `@tanstack/react-table` v8
  - `sonner` (toast library)
  - `fuse.js` (not React-specific, but check)
  - `@testing-library/react`
  - `react-router-dom` v6
  - `react-hook-form` (if I use it)
- What breaking changes in React 19 would affect an Electron app?
- If React 18, what's the recommended version and are security patches still active?

### Decision 2: Electron Version Selection
- What is the current Electron stable release as of March 2026?
- What are the Node.js and Chromium versions bundled?
- Are there ESM-related breaking changes I should know about?
- What's the recommended minimum Electron version for `electron-store`, `contextBridge`, and `contextIsolation`?
- Any known issues with Electron + Vite in the latest version?

### Decision 3: CSS Framework / Approach
For a trading platform UI with:
- Dense data tables (TanStack Table)
- Financial charts (Lightweight Charts)
- Forms (trade entry, settings, account management)
- Dark mode + theme switching
- Navigation rail + content panels layout

Compare these CSS approaches:
a) **Tailwind CSS v4** — utility-first, pairs with shadcn/ui
b) **CSS Modules** — scoped styles, no runtime overhead
c) **Vanilla Extract** — type-safe CSS-in-TS, zero runtime
d) **Plain CSS with custom properties** — maximum control

For each, assess: bundle size impact, developer experience, theme switching support, compatibility with TanStack Table custom renderers.

### Decision 4: Form Library
For trade entry forms, settings pages, account creation, plan management:
- **React Hook Form** vs **native controlled components** vs **Formik**
- Which works best with the chosen component library?
- Zod integration for validation (already using Zod in MCP server)?

### Decision 5: Testing Stack for Electron + React
- **Vitest** + **@testing-library/react** for component tests — any caveats with Electron renderer?
- **Playwright** for E2E — does it support Electron app testing natively? What's the setup?
- How to test Electron IPC (main process ↔ renderer process)?
- How to test Python backend health check during E2E?

### Decision 6: Router for Electron
- **React Router v6** (stable) vs **React Router v7** (Remix merger)
- For a desktop Electron app with no SSR, which is simpler?
- Hash router vs browser router in Electron context?
- TanStack Router as alternative?

## Output Format
For each decision, provide:
1. **Recommendation** with version number
2. **Rationale** (3-5 sentences)
3. **Compatibility evidence** (links to docs, changelog entries, GitHub issues)
4. **Risk if wrong choice is made**
5. **Migration difficulty** if we need to change later (Low/Medium/High)
```

---

## Prompt 3: Claude Opus 4.6 — Architectural Synthesis & Decision Framework

> **Why Claude Opus**: Nuanced architectural reasoning, structured analysis, strong at synthesizing trade-offs and making opinionated recommendations. Ideal for the "decision.md" output.

```
# RESEARCH TASK: Architecture Decision Synthesis for Electron + React Trading App

## Context
I'm building Zorivest — a trading portfolio management desktop application. Here's the full architecture context:

### What's Already Built (Python Backend — 60 MEUs complete)
- **Domain Layer**: 14 enums, 6 entities (Trade, Account, BalanceSnapshot, TradePlan, Watchlist, TradeReport), value objects (Money, PositionSize, Ticker), pure analytics (expectancy, SQN), position size calculator
- **Infrastructure**: SQLCipher encrypted DB, SQLAlchemy ORM (21 models), repositories, Unit of Work, backup/restore, settings resolver
- **Services**: Trade, Account, Image processing (WebP), Market Data (12 providers), IBKR FlexQuery adapter, CSV import framework
- **REST API**: FastAPI with 30+ endpoints on localhost:8765 (trades, accounts, settings, analytics, tax, system, market data)
- **MCP Server**: TypeScript MCP tools (27 tools across 6 toolsets), Vitest tests
- **Scheduling Domain**: Pipeline enums, policy models, step registry, policy validator

### What We're Building Now (Phase 6 GUI — 3 MEUs as single project)
- **MEU-43 (gui-shell)**: Electron main process, React AppShell (nav rail + header + route outlet), Python backend lifecycle, startup performance logging
- **MEU-44 (gui-command-registry)**: Static TypeScript registry of all navigable items, CommandRegistryEntry type
- **MEU-45 (gui-window-state)**: Window bounds persistence via electron-store, usePersistedState React hook

### Key Constraints
1. The Electron app spawns Python backend via child_process — NO embedded Python, just subprocess management
2. React renderer communicates with Python via REST (localhost:8765) — no direct IPC for data
3. IPC (Electron) is only for window management (bounds, theme, startup metrics)
4. Libraries already committed: TanStack Query v5 (server state), TanStack Table v8 (data grids), Lightweight Charts (financial charts), fuse.js (fuzzy search), sonner (toasts), electron-store
5. 22+ downstream GUI MEUs will build on this foundation — choices must scale
6. The MCP server (`mcp-server/`) already has TypeScript + Vitest + Zod — share ecosystem where possible

### What I Already Have From Other Research
(I'll paste findings from Gemini and GPT-5.4 here after they complete — for now, work from your own knowledge)

## What I Need From You

### 1. Architecture Decision Records (ADRs)
For each of these 7 decisions, produce a structured ADR:

**ADR format:**
```
## ADR-{N}: {Title}
**Status**: Proposed
**Context**: Why this decision matters
**Options Considered**: {list with pros/cons}
**Decision**: {recommended choice}
**Consequences**: {what this enables/constrains}
**Reversibility**: Low/Medium/High
```

Decisions:
1. Electron + Vite integration tool
2. React version (18 vs 19)
3. Component library / design system
4. CSS strategy
5. State management for local UI state
6. Router library and mode
7. Form handling approach

### 2. Dependency Lock Manifest
Produce the exact `package.json` dependencies section with locked major.minor versions for the recommended stack. Group by:
- Core (React, Electron)
- Data (TanStack, Lightweight Charts)
- UI (component library, CSS framework)
- Utility (fuse.js, sonner, electron-store)
- Dev (Vite, TypeScript, testing)

### 3. Project Directory Structure
Propose the `ui/` directory layout that supports:
- Electron main process + preload
- React renderer with route-level code splitting
- Shared types with mcp-server/ (if beneficial)
- Test file co-location vs separate test directory
- Component organization (feature-based vs type-based)

### 4. Risk Matrix
Identify the top 5 architectural risks in the proposed stack and for each:
- Likelihood (Low/Medium/High)
- Impact (Low/Medium/High)  
- Mitigation strategy
- Early warning signs

### 5. Integration Points
Map how the GUI shell integrates with existing backend:
- REST API consumption pattern (TanStack Query config, base URL, error handling)
- Python backend health check flow
- Settings persistence (electron-store for window bounds, REST for UI state)
- Startup sequence (Electron → Python → React → data)

### 6. Anti-Patterns to Avoid
Based on your knowledge of Electron + React applications, list the top 10 anti-patterns we should explicitly avoid, with explanation of why each is harmful in a trading app context.
```

---

## Synthesis Plan

After all three models return results:

1. **Cross-reference** recommendations — where do all 3 agree? (high confidence)
2. **Identify disagreements** — where models diverge (needs human decision)
3. **Extract unique insights** — what did each model surface that others missed?
4. **Produce** `docs/research/gui-shell-foundation/decision.md` with version-locked choices
5. **Save to pomera** for persistent memory

> [!TIP]
> The same cross-model synthesis pattern was used successfully for the health research project (conversation `e55838a6`). Apply the same methodology here.
