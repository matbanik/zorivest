# Execution Tracking

> Prompts, plans, reflections, and metrics for each dual-agent build session.

## Structure

```
execution/
├── README.md
├── prompts/           ← Agent A (GPT-5.4) creates; human may tune
│   └── {YYYY-MM-DD}-meu-{N}-{slug}.md
├── plans/             ← Archived from Antigravity brain folder after approval
│   ├── {YYYY-MM-DD}-implementation-plan.md
│   └── {YYYY-MM-DD}-task.md
├── reflections/       ← Post-execution meta-reflection
│   └── {YYYY-MM-DD}-reflection.md
└── metrics.md         ← Session-over-session tracking (Handoff Score, Rule Adherence, etc.)
```

## 7-Step Dual-Agent Lifecycle

Each MEU build session follows this cycle. Steps 3–5 may loop (max 2 revision cycles).

| Step | Agent | Action | Governing Files | Artifacts Produced |
|------|-------|--------|----------------|--------------------|
| **1. Create execution prompt** | Agent A (GPT-5.4) | Drafts MEU prompt following roles and SOUL.md identity | `.agent/roles/orchestrator.md`, `AGENTS.md`, `SOUL.md` | `docs/execution/prompts/{date}-meu-{N}-{slug}.md` |
| **2. Plan** | Agent B (Opus 4.6) | Reads prompt, enters PLANNING mode, generates plan | `GEMINI.md` §Mode Transitions, `.agent/workflows/execution-session.md` §3 | `implementation_plan.md` + `task.md` (in brain folder → archived to `docs/execution/plans/`) |
| **3. Validate plan** | Agent A (GPT-5.4) | Reviews plan, approves or sends correction findings | `.agent/workflows/validation-review.md`, `.agent/workflows/critical-review-feedback.md` | Verdict in `.agent/context/handoffs/{date}-{slug}.md` |
| **4. Implement via TDD** | Agent B (Opus 4.6) | FIC → Red → Green → quality checks → handoff | `GEMINI.md` §TDD-First Protocol, `.agent/workflows/tdd-implementation.md`, `.agent/workflows/meu-handoff.md` | Handoff at `.agent/context/handoffs/{date}-meu-{N}-{slug}.md` + `pomera_notes` backup + ADRs in `docs/decisions/` |
| **5. Validate implementation** | Agent A (GPT-5.4) | Adversarial checks, banned patterns, FIC audit | `.agent/workflows/validation-review.md`, `.agent/roles/reviewer.md`, `.agent/roles/guardrail.md` | Codex Validation Report (appended to handoff), status transition |
| **6. Next MEU prompt** | Agent A (GPT-5.4) | Uses reflection outline to draft next session's prompt | Previous reflection §5d "Next Session Outline", `docs/execution/prompts/TEMPLATE.md` | Next prompt file |
| **7. Meta-reflection** | Agent B (Opus 4.6) | Friction/quality/workflow logs → pattern extraction → design rules | `.agent/workflows/execution-session.md` §5a–5e | `docs/execution/reflections/{date}-reflection.md`, `metrics.md` row, `pomera_notes` save |

### How Steps Chain Together

```
Step 1 (prompt) → Step 2 (plan) → Step 3 (validate plan)
                                       ↓
                              ┌── approved ──→ Step 4 (implement)
                              └── changes ──→ Agent B fixes → back to Step 3 (max 2 cycles)
                                                    ↓
                              Step 5 (validate implementation)
                                       ↓
                              ┌── approved ──→ Step 6 + 7 (next prompt + reflection)
                              └── changes ──→ Agent B fixes → back to Step 5 (max 2 cycles)
                                                    ↓
                              Step 7 outputs feed Step 1 of the next session
```

### Key Safeguards

- **Max 2 revision cycles** per validation step — escalate to human after (`.agent/workflows/meu-handoff.md` §Max Revision Cycles)
- **Test immutability** — never modify test assertions to make implementation pass (`GEMINI.md` §TDD-First Protocol)
- **Anti-placeholder enforcement** — `rg "TODO|FIXME|NotImplementedError"` before declaring complete (`GEMINI.md` §Execution Contract)
- **Evidence-first completion** — handoff must contain commands + results + artifact references (`GEMINI.md` §Execution Contract)
- **Human approval gate** — mandatory before merge/release/deploy (`AGENTS.md` §Session Discipline)
- **ADR-based decision tracking** — cross-boundary decisions recorded in `docs/decisions/` and referenced from handoffs
- **Progressive skill loading** — `.agent/skills/` loaded on-demand per task scope to prevent context bloat

## Naming Convention

All files use **`{YYYY-MM-DD}-{slug}`** format, consistent with `.agent/context/handoffs/`.

- **Prompts**: `{YYYY-MM-DD}-meu-{N}-{slug}.md`
- **Plans**: `{YYYY-MM-DD}-implementation-plan.md` / `{YYYY-MM-DD}-task.md`
- **Reflections**: `{YYYY-MM-DD}-reflection.md`

## Invocation

Invoke `/execution-session` in any AI session to run the full lifecycle.
