# [WF-SEGREGATE] Task List

| # | task | owner_role | deliverable | validation | status |
|---|------|------------|-------------|------------|--------|
| 1 | Create `plan-critical-review.md` — plan-review-only workflow extracted from `critical-review-feedback.md` | `coder` | `.agent/workflows/plan-critical-review.md` | §HARD STOP Compliance (below) for `plan-critical-review.md`; `rg "PR-1\|PR-2\|PR-3\|PR-4\|PR-5\|PR-6" .agent/workflows/plan-critical-review.md` → ≥6 matches; `rg "DR-" .agent/workflows/plan-critical-review.md` → ≥1 match; `rg "^### IR-" .agent/workflows/plan-critical-review.md` → 0 matches | `done` |
| 2 | Create `execution-critical-review.md` — impl-review-only workflow extracted from `critical-review-feedback.md` | `coder` | `.agent/workflows/execution-critical-review.md` | §HARD STOP Compliance (below) for `execution-critical-review.md`; `rg "IR-1\|IR-2\|IR-3\|IR-4\|IR-5\|IR-6" .agent/workflows/execution-critical-review.md` → ≥6 matches; `rg "DR-" .agent/workflows/execution-critical-review.md` → ≥1 match; `rg "^### PR-" .agent/workflows/execution-critical-review.md` → 0 matches | `done` |
| 3 | Create `plan-corrections.md` — plan-document corrections workflow extracted from `planning-corrections.md` | `coder` | `.agent/workflows/plan-corrections.md` | §HARD STOP Compliance (below) for `plan-corrections.md`; `rg "packages/\|ui/\|mcp-server/" .agent/workflows/plan-corrections.md` confirms forbidden scope is documented; write scope forbids production code | `done` |
| 4 | Create `execution-corrections.md` — production-code corrections workflow extracted from `planning-corrections.md` | `coder` | `.agent/workflows/execution-corrections.md` | §HARD STOP Compliance (below) for `execution-corrections.md`; write scope forbids plan/build-plan docs; `rg "TDD\|tests.*first\|test.*first" .agent/workflows/execution-corrections.md` → ≥1 match (TDD discipline stated) | `done` |
| 5 | Delete old `planning-corrections.md` | `coder` | File removed from `.agent/workflows/` | `Test-Path .agent/workflows/planning-corrections.md` → False | `done` |
| 6 | Delete old `critical-review-feedback.md` | `coder` | File removed from `.agent/workflows/` | `Test-Path .agent/workflows/critical-review-feedback.md` → False | `done` |
| 7 | Update `AGENTS.md` §Workflow Invocation — replace 2 old entries with 4 new entries | `coder` | Lines 173-174 replaced with 4 new slash commands | `rg "planning-corrections\|critical-review-feedback" AGENTS.md` → 0 matches | `done` |
| 8 | Update `session-meta-review.md` — 3 references | `coder` | Lines 39, 198, 225 updated to new workflow names | `rg "planning-corrections\|critical-review-feedback" .agent/workflows/session-meta-review.md` → 0 matches | `done` |
| 9 | Update `meu-handoff.md` — 1 reference | `coder` | Line 13: `/critical-review-feedback` → `/execution-critical-review` | `rg "critical-review-feedback" .agent/workflows/meu-handoff.md` → 0 matches | `done` |
| 10 | Update `execution-session.md` — 1 reference | `coder` | Line 76: `/critical-review-feedback` → `/execution-critical-review` | `rg "critical-review-feedback" .agent/workflows/execution-session.md` → 0 matches | `done` |
| 11 | Update `emerging-standards.md` — 3 references | `coder` | Lines 3, 11, 12 updated to new workflow names | `rg "planning-corrections\|critical-review-feedback" .agent/docs/emerging-standards.md` → 0 matches | `done` |
| 12 | Update `pre-handoff-review/SKILL.md` — 1 reference | `coder` | Line 14: `/planning-corrections` → `/plan-corrections` or `/execution-corrections` | `rg "planning-corrections" .agent/skills/pre-handoff-review/SKILL.md` → 0 matches | `done` |
| 13 | Update `docs/execution/README.md` — 1 reference | `coder` | Line 26: `.agent/workflows/critical-review-feedback.md` → new workflow names | `rg "critical-review-feedback" docs/execution/README.md` → 0 matches | `done` |
| 14 | Move [WF-SEGREGATE] from `known-issues.md` to `known-issues-archive.md` | `coder` | Entry archived with 1-line summary row | `rg "WF-SEGREGATE" .agent/context/known-issues.md` → only in Archived table | `done` |
| 15 | Final verification sweep — confirm 0 stale references in all active files | `tester` | All greps return 0 matches | `rg "critical-review-feedback\|planning-corrections" AGENTS.md .agent/workflows/ .agent/docs/ .agent/skills/ .agent/roles/ docs/execution/README.md` → 0 matches | `done` |

## HARD STOP Compliance Commands

Run these PowerShell commands for each new workflow file. All 3 checks must return `True` for the task to pass.

```powershell
# Set $f to each new workflow file in turn:
# .agent/workflows/plan-critical-review.md
# .agent/workflows/execution-critical-review.md
# .agent/workflows/plan-corrections.md
# .agent/workflows/execution-corrections.md

# Check 1: ## HARD STOP is the last H2 heading (no H2 after it)
(Select-String -Pattern '^## ' -Path $f | Select-Object -Last 1).Line.Trim() -eq '## HARD STOP'
# → True

# Check 2: CAUTION block exists in the HARD STOP section
$raw = Get-Content $f -Raw; $tail = $raw.Substring($raw.IndexOf('## HARD STOP')); $tail -match '\[!CAUTION\]'
# → True

# Check 3: Anti-chaining + stop-after-handoff language in the HARD STOP section
$tail -match 'Do NOT|MUST NOT|forbidden' -and $tail -match 'handoff'
# → True
```

**Loop form** (runs all 4 files, expects 4× PASS):

```powershell
foreach ($f in @('.agent/workflows/plan-critical-review.md','.agent/workflows/execution-critical-review.md','.agent/workflows/plan-corrections.md','.agent/workflows/execution-corrections.md')) { $h2s = Select-String '^## ' $f; $lastH2 = $h2s[-1].Line.Trim(); $raw = Get-Content $f -Raw; $tail = $raw.Substring($raw.IndexOf('## HARD STOP')); $pass = ($lastH2 -eq '## HARD STOP') -and ($tail -match '\[!CAUTION\]') -and ($tail -match 'Do NOT|MUST NOT|forbidden') -and ($tail -match 'handoff'); "$f : $(if($pass){'PASS'}else{'FAIL'})" }
```

Expected output: 4 lines, all `PASS`.
