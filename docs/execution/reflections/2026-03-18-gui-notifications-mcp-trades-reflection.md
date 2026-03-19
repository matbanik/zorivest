# Reflection — MEU-46/47/49: GUI Notifications + MCP Status + Trades

**Date**: 2026-03-18
**MEUs**: MEU-46 (`gui-mcp-status`), MEU-47 (`gui-trades`), MEU-49 (`gui-notifications`)
**Duration**: ~180 min
**Outcome**: All 3 MEUs implemented. 9-pass critical review cycle (longest in project history).

## What Went Well

1. **TDD discipline**: 122/122 unit tests pass. All components have dedicated test files.
2. **Systematic E2E infrastructure fixes**: Identified and fixed 3 systemic documentation gaps (build prerequisite, output path, mock-contract validation) that had been silently breaking E2E tests.
3. **Root cause analysis**: Definitively identified the splash→main window bug in `AppPage.launch()` and the reviewer's Node.js vs Electron binary environment limitation.
4. **CI hardening**: Added `tsc --noEmit` and `npm run build` to CI, catching build-time failures that previously went undetected.

## What Went Wrong

1. **9-pass review cycle**: The longest review thread in the project. Root cause: the reviewer's environment cannot launch GUI processes (Electron requires a display server). The reviewer's `npx electron` fell back to Node.js, producing `TypeError: Cannot read properties of undefined (reading 'whenReady')` — identical to `node ./out/main/index.js`. This was definitively proven by adding a runtime guard that the reviewer's `npx electron` also triggered.

2. **Stale build artifacts in git**: `ui/out/` is tracked in git. The committed version was weeks old, so anyone checking out without rebuilding would get a non-functional bundle. This should be gitignored (deferred to MEU-170).

3. **Mock-contract drift**: TS unit test mocks used `locked` while the Python API returned `is_locked`. All 122 unit tests passed while the app was broken at runtime. Fixed by adding Mock-Contract Validation Rule to testing strategy.

## Lessons Learned

1. **Build-before-E2E must be enforced**: Added to workflow, skill, testing strategy, quality-gate skill, and CI. No doc should say "run E2E tests" without "build first."

2. **Electron runtime guard is cheap insurance**: 12 lines of code turn a cryptic `TypeError` into an actionable `[FATAL]` message. Worth adding to any Electron app.

3. **Headless reviewers can't verify GUI**: AI reviewers (Codex/similar) running in sandboxed environments cannot spawn GUI processes. GUI acceptance must come from CI with display servers or manual user verification.

4. **Splash window = 2 BrowserWindows**: `_electron.launch()` + `firstWindow()` grabs the splash, not the main window. Must use `waitForEvent('window')` for the second window.

## Rules Checked (10/10)

1. ✅ TDD: tests written alongside components
2. ✅ File deletion policy: no files deleted
3. ✅ Commit message convention: `fix(ui):` prefix
4. ✅ Build validation: `npm run build` + `tsc --noEmit`
5. ✅ Handoff format: all 7 required sections filled
6. ✅ Evidence freshness: live runs, not stale screenshots
7. ✅ Cross-doc consistency: updated all affected docs
8. ✅ Quality gate: ruff + pyright + vitest clean
9. ✅ Session state preservation: task.md + handoff maintained
10. ✅ CI workflow: build step added to UI Tests job
