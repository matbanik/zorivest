# GUI Shell Foundation — Reflection

> MEU-43 (Electron + React Infrastructure), MEU-44 (Command Registry + Palette), MEU-45 (Window State Persistence)
> Date: 2026-03-14

## What Went Well

- **Electron-vite scaffolding worked cleanly.** Zero blocked dependencies; React + TanStack Router + TanStack Query + Fuse.js all integrated on first attempt.
- **Dracula theme approach.** CSS custom properties as a design system (rather than inline colors) made every component consistent from the start.
- **Window state persistence via electron-store.** Lazy initialization pattern handled ESM-only issues gracefully in both production and test environments.

## What Went Wrong

1. **IPC bridge gap.** Preload script exposed 6 channels, but `main/index.ts` only registered 3 handlers initially. The disconnect wasn't caught until critical review.
2. **No-op command actions.** All 13 static entries had `action: () => { }` — the handoff claimed "users can execute actions" when nothing actually happened. Spec alignment should have been verified before handoff.
3. **Non-existent test files cited in evidence.** Handoff 063 referenced `NavRail.test.tsx`, `StatusFooter.test.tsx`, and `theme.test.ts` — none existed on disk. Evidence bundle must be validated against actual files.
4. **Dev-mode handoff claims overstated.** `npm run dev` was cited as proof of AC-1/AC-2 (Python startup), but dev mode explicitly skips Python.
5. **TanStack Router tests hang in jsdom.** `RouterProvider` + `createRouter` render asynchronously and require either `router.load()` or `waitFor` — direct synchronous `getByRole` queries fail silently or hang.

## Lessons Learned

| Lesson | Action |
|--------|--------|
| Always verify preload↔main IPC parity before handoff | Add to MEU checklist: "All preload channels have main handlers" |
| Don't claim functionality that's stubbed | Use `console.info()` stubs with clear messages, not empty bodies |
| Evidence must reference real files | Run `rg --files` to confirm every test path cited in FAIL_TO_PASS |
| Dev-mode skip ≠ AC proof | Narrow terminology: "validated by unit tests" when runtime skips behavior |
| TanStack Router + jsdom = async | Mock `useNavigate` for component tests; full router tests need router.load() |

## Category Pattern: "Claimed vs Actual" Drift

Three of the five findings (Findings 2, 3, 4) followed the same meta-pattern: the handoff documentation claimed behavior that didn't match the actual file state. This is a recurring category across multiple projects. Mitigation: before writing any handoff claim, verify it against `rg` or file-read output — never copy-paste from implementation notes without verification.

## Codex Review Summary

| Round | Findings | Resolved |
|-------|----------|----------|
| Round 1 | 3 High + 2 Medium | 3 High + 1 Medium |
| Round 2 | 1 High + 3 Medium + 1 Low | All |
| Round 3 | 1 Medium | All |
| Round 4 | 0 | — (**approved**) |
