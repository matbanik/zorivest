# {YYYY-MM-DD} Execution Prompt — {MEU Scope}

> Purpose: paste this into a fresh Opus 4.6 / Antigravity session.
>
> Read-first workflow set:
> - `.agent/workflows/execution-session.md`
> - `.agent/workflows/tdd-implementation.md`
> - `.agent/workflows/meu-handoff.md`

---

## Session Contract

Read these files in order before planning or coding:

1. `SOUL.md`
2. `GEMINI.md`
3. `AGENTS.md`
4. `.agent/context/current-focus.md`
5. `.agent/context/known-issues.md`
6. `.agent/context/meu-registry.md`
7. `docs/build-plan/{NN}-{phase}.md` {relevant sections}
8. `docs/build-plan/testing-strategy.md`
9. `.agent/workflows/execution-session.md`
10. `.agent/workflows/tdd-implementation.md`
11. `.agent/workflows/meu-handoff.md`
12. `.agent/workflows/validation-review.md`

Task: complete {MEU-N} only.

In scope:
- {list of in-scope items}

Out of scope:
- all future-MEU modules and package scaffolds not required for this MEU
- placeholder stubs for future work
- auto-commits
- unrelated documentation rewrites

If any repo rule conflicts with this prompt, stop and ask the human before proceeding.

---

## Planning Phase

Start in PLANNING mode.

Before coding, generate both:
- `implementation_plan.md`
- `task.md`

The plan must include:
- a task table with: task, owner_role, deliverable, validation, status
- exact file paths to create or modify
- the MEU Feature Intent Contract
- exact validation commands for this session
- explicit stop conditions
- the handoff file path to write

Present the plan to the human for approval before switching to EXECUTION mode.

After approval, archive the approved planning artifacts into:
- `docs/execution/plans/{YYYY-MM-DD}-implementation-plan.md`
- `docs/execution/plans/{YYYY-MM-DD}-task.md`

Use the native shell for the host OS. On PowerShell, the archive step is:

```powershell
Copy-Item "$HOME\.gemini\antigravity\brain\{conversation-id}\implementation_plan.md" `
  "docs\execution\plans\{YYYY-MM-DD}-implementation-plan.md"

Copy-Item "$HOME\.gemini\antigravity\brain\{conversation-id}\task.md" `
  "docs\execution\plans\{YYYY-MM-DD}-task.md"
```

---

## Execution Phase

### A. Bootstrap (if needed)

{Describe any scaffold or infrastructure work needed for this MEU. If no bootstrap is needed, state: "No bootstrap needed — workspace already scaffolded."}

### B. Feature Intent Contract

{Write the FIC inline with acceptance criteria, negative cases, etc.}

### C. Red Phase

{Test file path, marker config, run command}

### D. Green Phase

{Implementation file path, run command}

### E. Verification Gate for This Session

```powershell
uv run pytest tests/unit/ -x --tb=short -v
uv run pyright packages/core/src
uv run ruff check packages/core/src tests
rg "TODO|FIXME|NotImplementedError|pass\s+#\s*placeholder" packages tests
```

Run `.\tools\validate.ps1` only as an informational probe after the MEU gate above.

If `.\tools\validate.ps1` fails because unrelated repo surfaces are intentionally out of scope, do not widen scope. Record the exact failure in the handoff under known risks and stop at `ready_for_review`.

### F. Handoff and State

Create the handoff file:
- `.agent/context/handoffs/{YYYY-MM-DD}-meu-{N}-{slug}.md`

Use `.agent/workflows/meu-handoff.md` and include:
- scope summary, FIC, test mapping, changed files
- commands executed with results
- FAIL_TO_PASS evidence
- design decisions, known risks

Update:
- `.agent/context/meu-registry.md` → set MEU-{N} to `ready_for_review`

Save session state to `pomera_notes` with:
- title: `Memory/Session/Zorivest-MEU-{N}-{YYYY-MM-DD}`

Do not create git commits. Instead, propose the exact conventional commit message(s) to the human in your final summary.

---

## Codex Validation Trigger

After implementation is complete, give the human this exact follow-up text for a separate Codex session:

```text
Follow .agent/workflows/validation-review.md exactly.

Read the handoff at .agent/context/handoffs/{YYYY-MM-DD}-meu-{N}-{slug}.md.
Read all changed files listed in the handoff.
Run the validation workflow and append the Codex Validation Report to the handoff.

Scope: packages/core/src/ and tests/unit/ only.
```

---

## Post-Execution Reflection

After the implementation and handoff are complete:

1. Create `docs/execution/reflections/{YYYY-MM-DD}-reflection.md` from `docs/execution/reflections/TEMPLATE.md`.
2. Update the metrics table in `docs/execution/metrics.md` using the existing row format.
3. In the reflection, state at least:
   - what slowed the session down
   - what instructions were ambiguous
   - what should change in the next prompt
   - whether `tools/validate.ps1` was usable as a MEU gate or only as a later checkpoint

---

## Completion Target

This session is successful when all of the following are true:

- MEU tests were written first and shown failing before implementation
- implementation is green on the MEU gate
- handoff file exists and is self-contained
- MEU registry is updated to `ready_for_review`
- `pomera_notes` entry exists
- reflection file exists
- metrics row is updated
- the human receives the Codex validation trigger text and proposed commit message(s)
