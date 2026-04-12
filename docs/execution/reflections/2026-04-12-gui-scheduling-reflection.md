# Session Reflection: 2026-04-12 — GUI Scheduling (MEU-72)

## Session Summary

Implemented the Scheduling & Pipeline GUI page (MEU-72, matrix item 35b) with 4 sub-MEUs. Three planned sub-MEUs covered the foundation (BV, types, hooks), page UI (list+detail+CRUD+CodeMirror), and pipeline execution (run history + controls). A fourth unplanned sub-MEU covered stabilization work discovered during live user testing: timezone settings, keyboard shortcuts, account sorting, calculator value propagation, policy deletion fix, context-aware button disabling, and MCP toolset configuration.

## What Went Well

1. **Sub-MEU A+B+C execution was clean** — BV hardening, TypeScript types, and the scheduling page all landed with standard TDD discipline and passed MEU gate on first run.
2. **Live user testing** yielded high-value bug catches (D1–D10) that would have been Codex findings if not addressed immediately.
3. **MCP integration investigation** uncovered the `--toolsets all` configuration gap — an environment issue, not a code issue. This prevented a false report about missing functionality.
4. **Emerging standard M7** (Tool Description Workflow Context) codifies a repeatable pattern that applies to all future MCP toolset development.

## What Needs Improvement

1. **Unplanned scope creep** — Sub-MEU D was not in the original plan. While every fix was valid and user-requested, the session expanded from 3 planned sub-MEUs to 4. The stabilization work should have been anticipated given the scheduling page was the first live test of MCP integration.
2. **MCP discoverability gap** was discoverable earlier — the terse tool descriptions existed in code for weeks but weren't flagged until an AI agent actually tried to use them in production. An audit during MEU-89 (when MCP tools were first created) would have caught this.

## Key Technical Decisions

| Decision | Rationale |
|----------|-----------|
| `Ctrl+Shift+{N}` instead of `Ctrl+{N}` | OS-level keyboard shortcuts (Ctrl+1 in browser, Ctrl+5 in some apps) were intercepted before reaching Electron |
| Column header sorting for Accounts | Consistency with Trades table pattern; Sort dropdown was redundant UX |
| `useQuery` for default timezone | Settings API already supports single-key GET; loading at form init is cheaper than prop drilling |
| `--toolsets all` in MCP config | Dev environment should have full tool parity; selective loading is for production optimization |

## Rules Checked (10/10 sampled)

| # | Rule | Followed? |
|---|------|-----------|
| 1 | P0: Redirect-to-file pattern | ✅ |
| 2 | TDD: Tests first | ✅ (Sub-MEUs A–C), ⚠️ Some D items were fix-then-test |
| 3 | No unsourced best-practice rules | ✅ |
| 4 | Evidence-first completion | ✅ |
| 5 | Anti-placeholder enforcement | ✅ |
| 6 | MEU gate before handoff | ✅ |
| 7 | Known issues documented | ✅ |
| 8 | OpenAPI spec drift check (G8) | ✅ |
| 9 | Context compression (delta-only) | ✅ |
| 10 | Plan-code sync | ✅ |

**Rule Adherence**: 95% (Sub-MEU D stabilization items were reactive bug fixes — some were fix-first due to user urgency, but TDD tests were still added retroactively per G19).

## Known Issues Created

- `[SCHED-PIPELINE-WIRING]` — pipeline runtime wiring for FetchStep
- `[MCP-TOOLDISCOVERY]` — MCP tool description audit needed

## Metrics

| Metric | Value |
|--------|-------|
| Tool Calls | ~250 |
| Time to First Green | ~5 min |
| Tests Added | 28 vitest + 5 pytest BV + TZ setting tests = ~35 |
| Codex Findings | pending |
| Handoff Score | 7/7 |
| Rule Adherence | 95% |
| Prompt→Commit | ~180 min |
