---
name: E2E Testing
description: Playwright Electron E2E test infrastructure with wave-based activation. Run E2E tests, manage visual regression baselines, and add data-testid attributes to GUI components.
---

# E2E Testing Skill

## Overview

The E2E test suite uses Playwright's Electron support (`_electron.launch()`) to test the full application stack: Electron shell → React UI → REST API → Python backend → SQLCipher database.

Tests activate incrementally as GUI pages are built (see Wave Activation below).

## Prerequisites

> [!IMPORTANT]
> **Build before every E2E run.** Playwright launches the compiled `out/main/index.js`, not source files.
> Source changes are invisible to E2E tests until you rebuild.

Before running any E2E test:

1. **Build the Electron bundle**: `cd ui && npm run build`
2. **Python backend**: Handled automatically by `global-setup.ts`
3. **data-testid attributes**: Must exist in components for the target wave

## Commands

```bash
# Build + run all E2E tests
cd ui && npm run build && npx playwright test

# Build + run specific test file
cd ui && npm run build && npx playwright test tests/e2e/launch.test.ts

# Debug mode (opens inspector)
cd ui && npm run build && PWDEBUG=1 npx playwright test tests/e2e/launch.test.ts

# Update visual regression baselines
cd ui && npm run build && npx playwright test --update-snapshots

# View HTML report (no build needed)
cd ui && npx playwright show-report
```

## File Structure

```
ui/
├── playwright.config.ts          # Electron config (single worker)
└── tests/e2e/
    ├── global-setup.ts           # Spawns Python backend
    ├── global-teardown.ts        # Kills backend (cross-platform)
    ├── test-ids.ts               # Shared data-testid constants
    ├── pages/
    │   └── AppPage.ts            # Base Page Object Model
    ├── fixtures/
    │   └── sample-trades.csv     # Import test fixture
    ├── launch.test.ts            # Wave 0
    ├── mcp-tool.test.ts          # Wave 0
    ├── trade-entry.test.ts       # Wave 1
    ├── mode-gating.test.ts       # Wave 1
    ├── persistence.test.ts       # Wave 2
    ├── backup-restore.test.ts    # Wave 3
    ├── position-size.test.ts     # Wave 4
    └── import.test.ts            # Wave 5
```

## Wave Activation

Each wave activates after its gate MEU is implemented:

| Wave | Gate MEU | Tests | Cumulative |
|:----:|----------|:-----:|:----------:|
| 0 | MEU-46 `gui-mcp-status` | 5 | 5 |
| 1 | MEU-47 `gui-trades` | 7 | 12 |
| 2 | MEU-71 `gui-accounts` | 2 | 14 |
| 3 | MEU-74 `gui-backup-restore` | 2 | 16 |
| 4 | MEU-48 `gui-plans` | 2 | 18 |
| 5 | MEU-96/99 import GUI | 2 | 20 |

## Adding data-testid to Components

When implementing a GUI page, import test IDs from `ui/tests/e2e/test-ids.ts`:

```tsx
// Import the constants
// ui/tests/e2e/test-ids.ts is the source of truth
// Use the string values directly in components:

<div data-testid="trades-page">
  <button data-testid="add-trade-btn">Add Trade</button>
</div>
```

Constants use `SCREAMING_SNAKE_CASE`, values use `kebab-case`.

## Mock-Contract Validation

> [!CAUTION]
> **Unit test mocks must match the real API response shape.**
> Hand-writing mocks from memory causes contract drift. The `locked` vs `is_locked` bug passed all 122 unit tests but broke the app at runtime.

When mocking API responses in unit tests:

1. **Check the source of truth**: Read the Python route or Pydantic model (e.g., `packages/api/src/zorivest_api/routes/mcp_guard.py`)
2. **Or check the OpenAPI spec**: Search `openapi.committed.json` for the endpoint path
3. **Never guess field names**: Copy exact field names into your TS `interface` and mock

```typescript
// ❌ BAD: assumed field name from TS convention
interface GuardStatusResponse { locked: boolean }
mockApiFetch.mockResolvedValue({ locked: true })

// ✅ GOOD: matches Python McpGuardStatus.is_locked
interface GuardStatusResponse { is_locked: boolean }
mockApiFetch.mockResolvedValue({ is_locked: true })
```

## Page Object Model

All tests use `AppPage` (from `pages/AppPage.ts`):

```typescript
const appPage = new AppPage()
await appPage.launch()           // Start Electron + wait for ready
await appPage.navigateTo('trades') // Click sidebar nav
await appPage.testId('add-trade-btn').click() // data-testid locator
await appPage.apiGet('/trades')  // Direct API call
await appPage.close()            // Clean shutdown
```

## Accessibility Testing

Four test files include AxeBuilder (WCAG 2.1 AA) assertions:
- `launch.test.ts` — main page scan
- `trade-entry.test.ts` — trades page scan
- `position-size.test.ts` — calculator scan
- `import.test.ts` — import flow scan

Example:
```typescript
const results = await new AxeBuilder({ page: appPage.page }).analyze()
expect(results.violations).toEqual([])
```

## Visual Regression

`trade-entry.test.ts` includes `toHaveScreenshot()` with financial data masking:

```typescript
await expect(appPage.page).toHaveScreenshot('trades-page.png', {
    mask: [appPage.testId('balance-amount'), appPage.testId('pnl-value')],
})
```

Baselines are auto-generated on first run and stored in `tests/e2e/__screenshots__/`.

## Table Visual Consistency

> [!IMPORTANT]
> **Tables must be screenshotted at BOTH widths** — with detail panel open (~60%) and closed (100%).
> Header/cell alignment drift only shows at full width because right-aligned values separate from left-aligned headers in wide cells.

```typescript
// Screenshot with detail panel open (narrow table)
await appPage.testId('add-trade-btn').click() // opens panel
await expect(appPage.testId('trade-list')).toHaveScreenshot('trades-table-narrow.png')

// Screenshot with detail panel closed (full width)
await appPage.testId('panel-close-btn').click()
await expect(appPage.testId('trade-list')).toHaveScreenshot('trades-table-wide.png')
```

**Pattern rule:** All table components must use a shared `getAlignClass()` helper for both `<th>` and `<td>` — see `TradesTable.tsx` for the reference implementation.

## Headless / CI / Sandbox Environments

> [!WARNING]
> **Electron requires a display server.** Running `npx playwright test` in environments without X11/Wayland (Docker containers, CI runners, Codex sandboxes) will fail with `Process failed to launch!` before any test code executes. See `[E2E-ELECTRONLAUNCH]` in `known-issues.md`.

### Option 1: `xvfb-run` (Recommended)

```bash
# Install virtual framebuffer (Debian/Ubuntu)
apt-get update && apt-get install -y xvfb

# Run with virtual display
cd ui
xvfb-run --auto-servernum --server-args="-screen 0 1920x1080x24" \
  npx playwright test tests/e2e/account-crud.test.ts --reporter=line
```

### Option 2: `--no-sandbox`

Chromium's kernel sandbox requires `CLONE_NEWUSER`/`CLONE_NEWPID` namespaces, which are often disabled in containers.

```bash
cd ui
ELECTRON_DISABLE_SANDBOX=1 npx playwright test --reporter=line
```

If the env var is not honored, modify `AppPage.ts:35-37`:

```typescript
this.app = await electron.launch({
    executablePath,
    args: ['--no-sandbox', MAIN_ENTRY],
    // ...
})
```

### Option 3: Combined

```bash
cd ui
xvfb-run --auto-servernum -- env ELECTRON_DISABLE_SANDBOX=1 \
  npx playwright test --reporter=line
```

### Diagnostics

```bash
# Verify Electron binary resolves
node -e "console.log(require('electron'))"

# Check Xvfb availability
which Xvfb || which xvfb-run

# Check kernel namespace support
cat /proc/sys/user/max_user_namespaces
```

### Accepted Exception Path

If none of the above work (e.g., locked-down sandbox without root access), the E2E verification gap should be accepted:

1. Verify unit tests pass: `npx vitest run --reporter=verbose`
2. Verify type safety: `npx tsc --noEmit`
3. Verify build succeeds: `npm run build`
4. Review the E2E test source code for completeness
5. Note: "E2E verification deferred — environment lacks display server (see `[E2E-ELECTRONLAUNCH]`)"
