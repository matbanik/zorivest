# Architecture Decision Records

Decisions are numbered sequentially (ADR-0001, ADR-0002, etc.).
File naming: `ADR-{NNNN}-{kebab-case-title}.md`

## Index

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| ADR-0001 | Architecture — Clean Architecture with Layered Monorepo | accepted | 2026-02-28 |
| ADR-0002 | MCP Guard Fail-Closed Default on Network Error | accepted | 2026-03-09 |
| ADR-0003 | Batch Import Error Isolation — Graceful Degradation over Fail-Fast | proposed | 2026-03-13 |

## When to Create an ADR

Create an ADR when a decision:
- Affects cross-package boundaries (core ↔ infra ↔ api ↔ mcp ↔ ui)
- Rejects a plausible alternative (document why)
- Is likely to be questioned by the other agent or by a future session
- Involves a trade-off with non-obvious consequences

## Integration with Handoffs

When a decision is made during MEU implementation, the handoff's "Design Decisions & Known Risks" section should **reference** the ADR by number (e.g., "See ADR-0003") rather than inlining the full rationale.
