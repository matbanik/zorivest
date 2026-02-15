---
description: Canonical multi-role workflow for scoped implementation tasks.
---

# Orchestrated Delivery Workflow

Use this workflow for implementation tasks where code is changed.

## Default Role Sequence

1. `orchestrator` (required)
2. `researcher` (optional, only when requirements/patterns are unclear)
3. `coder` (required)
4. `tester` (required)
5. `reviewer` (required)
6. `guardrail` (optional, required for high-risk changes)
7. Human approval gate (required before merge/release/deploy)

## High-Risk Triggers (Require Guardrail)

- Encryption or key-management changes
- Authentication/authorization changes
- Migration scripts or schema changes
- File deletion, destructive rewrite, or irreversible operations
- Changes to backup/restore or data export/import integrity

## Task Lifecycle

1. Intake and scope (orchestrator): keep one-task-per-session.
2. Research if needed (researcher): run `.agent/workflows/pre-build-research.md`.
3. Implement (coder): minimal changes to satisfy requested behavior.
4. Validate (tester): execute blocking checks for touched areas.
5. Adversarial review (reviewer): findings-first report with severity.
6. Safety gate (guardrail when triggered): block or clear with notes.
7. Human approval gate: explicit approval required for merge/release/deploy.

## Handoff Artifact

Create one handoff file per task:

`.agent/context/handoffs/{YYYY-MM-DD}-{task-slug}.md`

Use `.agent/context/handoffs/TEMPLATE.md`.

## Completion Criteria

1. Required roles are executed in sequence.
2. Blocking checks are green.
3. Review verdict is `approved` with no unresolved blockers.
4. Human approval gate is satisfied for merge/release/deploy.
