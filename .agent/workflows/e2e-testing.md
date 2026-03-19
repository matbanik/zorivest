---
description: Run Playwright Electron E2E tests with wave-based activation
---

# E2E Testing Workflow

## Prerequisites

1. Build the Electron bundle: `cd ui && npm run build`
2. Python backend starts automatically via `global-setup.ts`
3. Verify `data-testid` attributes exist for the wave you're testing

> [!IMPORTANT]
> **Always rebuild before E2E.** Playwright launches the compiled `out/main/index.js`, not the source files.
> Source changes are invisible to E2E tests until you run `npm run build` (alias for `electron-vite build`).

## Steps

### 1. Check which wave is active

Review the wave activation schedule:

```powershell
# See which data-testid attributes exist in the codebase
rg 'data-testid' ui/src/ --count
```

| Wave | Gate MEU | Tests |
|:----:|----------|-------|
| 0 | MEU-46 | launch (3) + mcp-tool (2) |
| 1 | MEU-47 | trade-entry (5) + mode-gating (2) |
| 2 | MEU-71 | persistence (2) |
| 3 | MEU-74 | backup-restore (2) |
| 4 | MEU-48 | position-size (2) |
| 5 | MEU-96/99 | import (2) |

### 2. Build + run all E2E tests

```powershell
cd ui
npm run build
npx playwright test
```

### 3. Build + run a specific test file

```powershell
cd ui
npm run build
npx playwright test tests/e2e/launch.test.ts
```

### 4. Run with debug mode

```powershell
cd ui
npm run build
PWDEBUG=1 npx playwright test tests/e2e/launch.test.ts
```

### 5. Update visual regression baselines

```powershell
cd ui
npm run build
npx playwright test --update-snapshots
```

### 6. View test report

```powershell
cd ui
npx playwright show-report
```

## Mock-Contract Validation

> [!CAUTION]
> **Never hand-write mock response shapes from memory.**
> Always verify TS interface fields match the Python API model. The `locked` vs `is_locked` bug (Pass 2-3 of GUI review) was caused by mocks passing `{ locked: true }` while the API returned `{ is_locked: true }`.

When writing unit tests that mock API responses:

1. Check the OpenAPI spec: `openapi.committed.json` (search for the endpoint path)
2. Or read the Python route/model directly (e.g., `packages/api/src/zorivest_api/routes/`)
3. Mirror the exact field names in your TS `interface` and test mock

```typescript
// ❌ BAD: guessed field name
mockApiFetch.mockResolvedValue({ locked: true })

// ✅ GOOD: matches Python McpGuardStatus model (is_locked)
mockApiFetch.mockResolvedValue({ is_locked: true })
```

## Troubleshooting

- **App fails to launch**: Ensure `npm run build` completed successfully and `out/main/index.js` exists.
- **Backend health check timeout**: Check Python environment with `uv run uvicorn zorivest_api.main:app --port 8765`.
- **`data-testid` not found**: Add missing attributes to React components using constants from `ui/tests/e2e/test-ids.ts`.
- **Visual regression diff**: Run `--update-snapshots` if the change is intentional.
- **Stale bundle**: If source changes aren't reflected in E2E, you forgot to rebuild. Run `cd ui && npm run build`.
