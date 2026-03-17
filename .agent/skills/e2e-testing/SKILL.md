---
name: E2E Testing
description: Playwright Electron E2E test infrastructure with wave-based activation. Run E2E tests, manage visual regression baselines, and add data-testid attributes to GUI components.
---

# E2E Testing Skill

## Overview

The E2E test suite uses Playwright's Electron support (`_electron.launch()`) to test the full application stack: Electron shell → React UI → REST API → Python backend → SQLCipher database.

Tests activate incrementally as GUI pages are built (see Wave Activation below).

## Commands

```bash
# Run all E2E tests
cd ui && npx playwright test

# Run specific test file
cd ui && npx playwright test tests/e2e/launch.test.ts

# Debug mode (opens inspector)
cd ui && PWDEBUG=1 npx playwright test tests/e2e/launch.test.ts

# Update visual regression baselines
cd ui && npx playwright test --update-snapshots

# View HTML report
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
