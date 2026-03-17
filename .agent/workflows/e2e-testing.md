---
description: Run Playwright Electron E2E tests with wave-based activation
---

# E2E Testing Workflow

## Prerequisites

1. Ensure the Electron app builds: `cd ui && npm run build`
2. Python backend starts automatically via `global-setup.ts`
3. Verify `data-testid` attributes exist for the wave you're testing

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

### 2. Run all E2E tests

```powershell
cd ui
npx playwright test
```

### 3. Run a specific test file

```powershell
cd ui
npx playwright test tests/e2e/launch.test.ts
```

### 4. Run with debug mode

```powershell
cd ui
PWDEBUG=1 npx playwright test tests/e2e/launch.test.ts
```

### 5. Update visual regression baselines

```powershell
cd ui
npx playwright test --update-snapshots
```

### 6. View test report

```powershell
cd ui
npx playwright show-report
```

## Troubleshooting

- **App fails to launch**: Ensure `npm run build` completed successfully and `build/main/index.js` exists.
- **Backend health check timeout**: Check Python environment with `uv run uvicorn zorivest_api.main:create_app --factory --port 8765`.
- **`data-testid` not found**: Add missing attributes to React components using constants from `ui/tests/e2e/test-ids.ts`.
- **Visual regression diff**: Run `--update-snapshots` if the change is intentional.
