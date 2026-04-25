# Execution Tracking

> Prompts, plans, reflections, and metrics for each dual-agent build session.

## Structure

```
execution/
├── README.md
├── plans/             ← Canonical project plans (written directly here during planning)
│   └── {YYYY-MM-DD}-{project-slug}/
│       ├── implementation-plan.md
│       └── task.md
├── reflections/       ← Post-execution meta-reflection
│   └── {YYYY-MM-DD}-{project-slug}-reflection.md
└── metrics.md         ← Session-over-session tracking (Handoff Score, Rule Adherence, etc.)
```

## 5-Step Dual-Agent Lifecycle

Each build session follows this cycle for its project scope. Steps 3–5 may loop per MEU (max 2 revision cycles).

| Step | Agent | Action | Governing Files | Artifacts Produced |
|------|-------|--------|----------------|--------------------|
| **1. Create project plan** | Agent B (Opus 4.7) | Runs `/create-plan`: reads handoffs, registry, build-plan; runs spec-sufficiency gate; scopes project | `.agent/workflows/create-plan.md`, `AGENTS.md` §Operating Model | `implementation_plan.md` + `task.md` in `docs/execution/plans/{date}-{project-slug}/` |
| **2. Validate plan** | Agent A (GPT-5.5) | Reviews plan, approves or sends correction findings | `.agent/workflows/validation-review.md`, `.agent/workflows/plan-critical-review.md` | Findings returned inline (plan artifacts live in `docs/execution/plans/`) |
| **3. Implement via TDD** | Agent B (Opus 4.7) | FIC → Red → Green → quality checks → handoff (per MEU) | `AGENTS.md` §Testing & TDD Protocol, `.agent/workflows/tdd-implementation.md`, `.agent/workflows/meu-handoff.md` | Creates `.agent/context/handoffs/{SEQ}-{date}-{slug}-bp{NN}s{X.Y}.md` per MEU + `pomera_notes` backup + ADRs in `docs/decisions/` |
| **4. Validate implementation** | Agent A (GPT-5.5) | Adversarial checks, banned patterns, FIC audit (per MEU) | `.agent/workflows/validation-review.md`, `.agent/roles/reviewer.md`, `.agent/roles/guardrail.md` | Codex Validation Report (appended to handoff), status transition |
| **5. Meta-reflection** | Agent B (Opus 4.7) | Friction/quality/workflow logs → pattern extraction → design rules | `.agent/workflows/execution-session.md` §5a–5e | `docs/execution/reflections/{date}-{project-slug}-reflection.md`, `metrics.md` row, `pomera_notes` save |

### How Steps Chain Together

```
Step 1 (/create-plan) → Step 2 (validate plan)
                               ↓
                      ┌── approved ──→ Step 3 (implement per MEU)
                      └── changes ──→ Agent B fixes → back to Step 2 (max 2 cycles)
                                            ↓
                      Step 4 (validate implementation per MEU)
                               ↓
                      ┌── approved ──→ Step 5 (meta-reflection)
                      └── changes ──→ Agent B fixes → back to Step 4 (max 2 cycles)
                                            ↓
                      Step 5 outputs feed Step 1 of the next session
```

### Key Safeguards

- **Max 2 revision cycles** per validation step — escalate to human after (`.agent/workflows/meu-handoff.md` §Max Revision Cycles)
- **Test immutability** — never modify test assertions to make implementation pass (`AGENTS.md` §Testing & TDD Protocol)
- **Anti-placeholder enforcement** — `rg "TODO|FIXME|NotImplementedError"` before declaring complete (`AGENTS.md` §Execution Contract)
- **Evidence-first completion** — handoff must contain commands + results + artifact references (`AGENTS.md` §Execution Contract)
- **Spec sufficiency gate** — under-specified behavior must be resolved via local canon, targeted web research, or explicit human decision before coding
- **Human approval gate** — mandatory before merge/release/deploy (`AGENTS.md` §Session Discipline)
- **ADR-based decision tracking** — cross-boundary decisions recorded in `docs/decisions/` and referenced from handoffs
- **Progressive skill loading** — `.agent/skills/` loaded on-demand per task scope to prevent context bloat

## Naming Convention

Plan archives use project-scoped folders. Handoffs use sequenced names with build-plan references.

- **Plans**: `{YYYY-MM-DD}-{project-slug}/implementation-plan.md`
- **Plans**: `{YYYY-MM-DD}-{project-slug}/task.md`
- **Replans on the same day**: append `-v2`, `-v3`, etc. to the folder name
- **Handoffs**: `{SEQ}-{YYYY-MM-DD}-{slug}-bp{NN}s{X.Y}.md` (in `.agent/context/handoffs/`)
- **Reflections**: `{YYYY-MM-DD}-{project-slug}-reflection.md`

## Invocation

Invoke `/execution-session` in any AI session to run the full lifecycle.
