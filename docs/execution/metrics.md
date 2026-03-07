# Execution Efficiency Metrics

> Append a row after each session's meta-reflection. Track trends to calibrate prompts.

## Session Metrics

| Date | MEU(s) | Tool Calls | Time to First Green | Tests Added | Codex Findings | Handoff Score | Rule Adherence | Prompt→Commit (min) | Notes |
|------|--------|------------|---------------------|-------------|---------------|---------------|----------------|---------------------|-------|
| 2026-03-06 | MEU-1 | ~50 | ~8 min | 9 | 0 (approved) | 7/7 | 100% | ~15 min | Pilot — bootstrap + TDD validated |
| 2026-03-07 | MEU-2 | ~40 | ~3 min | 17 | pending | 7/7 | 100% | ~10 min | Pure enums — fastest MEU type |

## Measurement Definitions

### Handoff Score (X/7)
Count how many of these 7 required sections are substantively filled (not blank/placeholder):
1. Scope
2. Feature Intent Contract (with ACs)
3. Design Decisions (with at least one decision + reasoning)
4. Changed Files (with descriptions)
5. Commands Executed (with results)
6. FAIL_TO_PASS Evidence
7. Test Mapping (AC → test function)

### Rule Adherence (%)
At session end, score: (rules followed / rules applicable) × 100.
Sample the top 10 most-relevant rules from AGENTS.md + GEMINI.md for the session's task type. Document which rules were checked in the reflection file.

### Trend Alerts
- Handoff Score below 5/7 for 2+ consecutive sessions → review template compliance
- Rule Adherence below 70% for any rule across 3+ sessions → candidate for removal or rewording

## Trend Notes

_Updated after second session when comparisons become possible._
