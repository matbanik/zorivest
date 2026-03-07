# Handoffs

This folder stores handoff files — one per MEU within a project session.

## Naming Convention

```
{SEQ}-{YYYY-MM-DD}-{slug}-bp{NN}s{X.Y}.md
```

| Part | Meaning | Example |
|------|---------|---------|
| `{SEQ}` | 3-digit global sequence | `001` |
| `{YYYY-MM-DD}` | Date completed | `2026-03-06` |
| `{slug}` | Descriptive slug | `calculator` |
| `bp{NN}s{X.Y}` | Build-plan file + section | `bp01s1.3` |

Examples:
- `001-2026-03-06-calculator-bp01s1.3.md`
- `002-2026-03-07-enums-bp01s1.2.md`
- `003-2026-03-08-entities-bp01s1.4+1.5.md` (single MEU covering sections 1.4 and 1.5)

For multi-section MEUs, join section numbers with `+` (e.g., `bp01s1.4+1.5`).

**Sequence bootstrap:** If no sequenced handoffs exist yet (legacy files use `YYYY-MM-DD-` prefix), start at `001`.

**One handoff per MEU.** Each MEU gets its own sequenced file. A multi-MEU project produces multiple handoffs.

Determine the next sequence number from the highest `{SEQ}` found in this folder.

## Template

Start from: `.agent/context/handoffs/TEMPLATE.md`
