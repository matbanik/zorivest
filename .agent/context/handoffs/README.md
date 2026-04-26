# Handoffs

This folder stores handoff files — one per MEU or multi-MEU project.

## Naming Convention (Going Forward)

```
{YYYY-MM-DD}-{project-slug}-handoff.md
```

| Part | Meaning | Example |
|------|---------|---------|
| `{YYYY-MM-DD}` | Date completed | `2026-04-25` |
| `{project-slug}` | Descriptive project slug | `pipeline-capabilities` |
| `-handoff` | Artifact type suffix | `-handoff` |

Examples:
- `2026-04-25-pipeline-capabilities-ph4-ph7-handoff.md` (multi-MEU, same-day disambiguation via MEU range)
- `2026-04-25-pipeline-security-hardening-ph3-handoff.md`

**Same-day collision:** Append MEU range or letter suffix (`-a`, `-b`) when multiple handoffs share the same date and project slug.

**Multi-MEU projects** may use one combined handoff per project or one per MEU — decide based on scope.

### Legacy Convention (files 001–125)

Existing sequenced files use the original convention. **Do NOT rename them** — they are referenced from review artifacts, registries, and other docs.

```
{SEQ}-{YYYY-MM-DD}-{slug}-bp{NN}s{X.Y}.md
```

## Template

Start from: [`.agent/context/handoffs/TEMPLATE.md`](TEMPLATE.md) (v2.1)

## Critical Review Files

Review artifacts use a separate template and naming convention:

```
{YYYY-MM-DD}-{project-slug}-plan-critical-review.md
{YYYY-MM-DD}-{project-slug}-implementation-critical-review.md
```

Start from: [`.agent/context/handoffs/REVIEW-TEMPLATE.md`](REVIEW-TEMPLATE.md) (v2.1)

One rolling review file per plan folder. Append dated sections for rechecks instead of creating new files.

## YAML Frontmatter Fields

### Handoff Template Fields (v2.1)

| Field | Type | Required | Values |
|-------|------|----------|--------|
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
- **Removed** `seq` field from required YAML (legacy files retain it)

Existing handoffs (001–125) remain valid under v2.0. No retrofitting required.

### v2.1 → v2.2 Convention Change (2026-04-25)

- **Changed** file naming from `{SEQ}-{YYYY-MM-DD}-{slug}-bp{NN}s{X.Y}.md` to `{YYYY-MM-DD}-{project-slug}-handoff.md`
- **Rationale** (Research-backed): Date-based naming eliminates global sequence state dependency, prevents cross-agent naming collisions, and provides temporal context that reviewers prioritize over linear ordering
- **Legacy files untouched**: Files 001–125 retain original names — they are referenced from review artifacts and registries
