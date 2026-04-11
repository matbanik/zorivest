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

Start from: [`.agent/context/handoffs/TEMPLATE.md`](TEMPLATE.md) (v2.1)

## Critical Review Files

Review artifacts use a separate template and naming convention:

```
{plan-folder-name}-plan-critical-review.md
{plan-folder-name}-implementation-critical-review.md
```

Start from: [`.agent/context/handoffs/REVIEW-TEMPLATE.md`](REVIEW-TEMPLATE.md) (v2.1)

One rolling review file per plan folder. Append dated sections for rechecks instead of creating new files.

## YAML Frontmatter Fields

### Handoff Template Fields (v2.1)

| Field | Type | Required | Values |
|-------|------|----------|--------|
| `seq` | string | ✅ | 3-digit global sequence |
| `date` | string | ✅ | YYYY-MM-DD |
| `project` | string | ✅ | project slug |
| `meu` | string | ✅ | MEU identifier |
| `status` | enum | ✅ | `draft` \| `in_progress` \| `complete` \| `blocked` |
| `action_required` | enum | ✅ | `VALIDATE_AND_APPROVE` \| `REVIEW_CORRECTIONS` \| `EXECUTE` |
| `template_version` | string | ✅ | `"2.1"` |
| `verbosity` | enum | ✅ | `summary` \| `standard` \| `detailed` (default: `standard`) |
| `plan_source` | string | ✅ | path to implementation-plan.md |
| `build_plan_section` | string | ✅ | bp{NN}s{X.Y} |
| `agent` | string | ✅ | implementing agent name |
| `reviewer` | string | ✅ | reviewing agent name |
| `predecessor` | string | ✅ | previous handoff filename or `none` |

### Review Template Fields (v2.1)

| Field | Type | Required | Values |
|-------|------|----------|--------|
| `date` | string | ✅ | YYYY-MM-DD |
| `review_mode` | enum | ✅ | `plan` \| `handoff` \| `multi-handoff` |
| `target_plan` | string | ✅ | path to implementation-plan.md |
| `verdict` | enum | ✅ | `approved` \| `changes_required` \| `pending` |
| `findings_count` | integer | ✅ | number of findings |
| `template_version` | string | ✅ | `"2.1"` |
| `requested_verbosity` | enum | ✅ | `summary` \| `standard` \| `detailed` (default: `standard`) |
| `agent` | string | ✅ | reviewing agent name |

### Verbosity Tiers

Both templates support verbosity control. See [`.agent/docs/context-compression.md`](file:///p:/zorivest/.agent/docs/context-compression.md) for full tier definitions.

| Tier | Token Budget | Use Case |
|------|-------------|----------|
| `summary` | ~500 | Quick status checks, low-risk MEUs, follow-up passes |
| `standard` | ~2,000 | Default for all handoffs and reviews |
| `detailed` | ~5,000+ | Complex MEUs, first-pass reviews, debugging sessions |

### v2.0 → v2.1 Migration Notes

v2.1 is backward-compatible with v2.0. Changes are additive:

- **Added** `verbosity` field to handoff template YAML (defaults to `standard`)
- **Added** `requested_verbosity` field to review template YAML (defaults to `standard`)
- **Added** `<!-- CACHE BOUNDARY -->` marker between AC table and Evidence section
- **Added** test output compression guidance in Evidence section
- **Added** delta-only code guidance in Changed Files section
- **Preserved** all existing sections and fields from v2.0

Existing handoffs (001–104) remain valid under v2.0. No retrofitting required.
