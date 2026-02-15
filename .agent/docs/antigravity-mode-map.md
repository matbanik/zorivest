# Antigravity Mode Map — Zorivest

How Antigravity's `task_boundary` modes map to the six project roles.

## Mode-to-Role Mapping

| Mode | Roles | Activities |
|---|---|---|
| **PLANNING** | orchestrator, researcher | Scope task, read context files, research patterns, create `implementation_plan.md` |
| **EXECUTION** | coder | Implement changes, run targeted tests after each change |
| **VERIFICATION** | tester, reviewer, guardrail | Run full validation (`.\validate.ps1`), adversarial review, safety checks |

## Transition Rules

```
PLANNING ──(plan approved)──► EXECUTION ──(implementation complete)──► VERIFICATION
    ▲                                                                        │
    └──────────────────(design flaw found)────────────────────────────────────┘
                                         EXECUTION ◄──(minor bug)──┘
```

- **PLANNING → EXECUTION**: Only after user approves the `implementation_plan.md`.
- **EXECUTION → VERIFICATION**: After all implementation is complete.
- **VERIFICATION → PLANNING**: If fundamental design flaws are discovered (new TaskName).
- **VERIFICATION → EXECUTION**: If minor bugs found (same TaskName, fix and resume).

## Role Adoption

Adopt roles inline by following each role spec's **Must Do**, **Must Not Do**, and **Output Contract**:

| During | Read & Follow |
|---|---|
| PLANNING | `.agent/roles/orchestrator.md` — scope one task, plan role sequence |
| PLANNING (unclear requirements) | `.agent/roles/researcher.md` — research before coding |
| EXECUTION | `.agent/roles/coder.md` — read full files, no placeholders, handle errors |
| VERIFICATION (testing) | `.agent/roles/tester.md` — run checks, report evidence |
| VERIFICATION (review) | `.agent/roles/reviewer.md` — findings-first, severity-ordered |
| VERIFICATION (high-risk) | `.agent/roles/guardrail.md` — safety gate for risky changes |

## MCP Server Requirements

Verify at session start via `pomera_diagnose`:

| Server | Purpose | Verify With |
|---|---|---|
| `pomera` | Notes, text processing, web search, AI tools | `pomera_diagnose` |
| `text-editor` | Hash-based conflict-safe file editing | `get_text_file_contents` |
| `sequential-thinking` | Complex multi-step analysis | `sequentialthinking` |
