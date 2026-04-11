# Context Compression Rules

> **Source**: [ACON Compression Synthesis](file:///p:/zorivest/_inspiration/acon_research/acon-compression-synthesis.md) §Phase 1
> **Applies to**: All handoff artifacts, review artifacts, and agent-produced evidence bundles
> **Version**: 1.0 (introduced with TEMPLATE.md v2.1)

---

## Verbosity Tiers

Agents producing handoff artifacts and review artifacts must respect the `verbosity` field in YAML frontmatter. Reviewers requesting specific detail levels use `requested_verbosity` in the review template.

| Tier | Token Budget | When to Use | What's Included |
|------|-------------|-------------|-----------------|
| `summary` | ~500 tokens | Quick status checks, low-risk MEUs, follow-up passes where prior context is already loaded | AC table + verdict + 1-line per finding. No evidence section, no changed-files detail. |
| `standard` | ~2,000 tokens | Default for all handoffs and reviews | Full AC table, FAIL_TO_PASS summary, commands executed (key output only), changed files table with diff excerpts, quality gate summary. |
| `detailed` | ~5,000+ tokens | Complex MEUs, first-pass reviews with no prior context, debugging sessions | Everything in `standard` plus full stack traces for failures, extended diff blocks, architectural rationale, and cross-reference audit results. |

### Tier Selection Rules

1. **Default**: `standard` unless explicitly overridden in YAML frontmatter.
2. **Reviewer override**: A reviewer may set `requested_verbosity` in the review template to request a specific tier for the response.
3. **Escalation**: If a `summary` tier handoff receives a `changes_required` verdict, the correction pass automatically escalates to `standard`.
4. **No downgrade during active findings**: While findings are `open`, the tier cannot be reduced below `standard`.

---

## Test Output Compression

> **Rule**: Only output failing test names, assertion messages, and relevant stack frames. Never output passing test details.

### Required Format

```
pytest: {N} passed, {M} failed

FAILURES:
- test_name_1: {assertion message} ({file}:{line})
- test_name_2: {assertion message} ({file}:{line})
```

### Prohibited Patterns

- Full `pytest -v` output showing every passing test name
- Complete stack traces for passing tests
- Verbose fixture setup/teardown output for passing tests
- Raw `stdout`/`stderr` capture from passing tests

### What `detailed` Tier Affects

The `detailed` verbosity tier increases *explanation depth* (extended diff blocks, architectural rationale, cross-reference audit results) — it does **not** override test output compression. Passing tests are always summarized as `{N} passed` regardless of verbosity tier.

---

## Delta-Only Code Sections

> **Rule**: Use unified diff blocks (` ```diff `) instead of full file contents in handoff Changed Files sections.

### Required Format

Show only the changed lines with sufficient context (2–3 lines above/below):

````
```diff
 unchanged context line
-old_line_removed
+new_line_added
 unchanged context line
```
````

### Prohibited Patterns

- Inlining full source files in the Changed Files section
- Pasting entire file contents as "before" and "after" blocks
- Using non-standard formatting helpers or shorthand macros

### When to Show More

- **New files**: Show the key structural elements (imports, class definitions, public API), not every line
- **Deleted files**: A one-line summary is sufficient (e.g., "Deleted: file contained {N} lines of {description}")
- **Large refactors**: Show representative diff excerpts + a summary of total changes

---

## Cache Boundary

> **Rule**: Handoff templates use a `<!-- CACHE BOUNDARY -->` marker to separate stable prefix content from variable content.

### Stable Prefix (Above Cache Boundary)

Content that is identical across revision passes of the same handoff:

- YAML frontmatter (except `status` field transitions)
- Scope section (MEU ID, build plan section, predecessor)
- Acceptance Criteria table (fixed at FIC time)

### Variable Content (Below Cache Boundary)

Content that changes between passes:

- Evidence section (FAIL_TO_PASS, commands executed, quality gate)
- Changed Files section
- Codex Validation Report
- Corrections Applied
- Deferred Items
- History

### Why This Matters

LLM KV cache operates on prefix matching. When the beginning of a document is stable across calls, the cache can reuse computed attention for those tokens — reducing cost by up to 90% on cached portions and improving response latency.

### Constraint

No dynamic content (timestamps other than YAML `date`, command outputs, test results, quality gate numbers) may appear above the cache boundary. The YAML `date` field is permitted because it is deterministic per handoff instance.

---

## Timestamp Pinning

> **Rule**: All event timestamps go in the History section at the end of the artifact.

The History section must be the last `##`-level section in the handoff template. This ensures timestamp churn does not invalidate KV cache for the stable prefix.

Only the YAML frontmatter `date` field (which is set once at creation and never changes) is permitted above the cache boundary.

---

## Related Files

- [TEMPLATE.md](file:///p:/zorivest/.agent/context/handoffs/TEMPLATE.md) — Handoff template (v2.1)
- [REVIEW-TEMPLATE.md](file:///p:/zorivest/.agent/context/handoffs/REVIEW-TEMPLATE.md) — Review template (v2.1)
- [AGENTS.md §Context Compression Rules](file:///p:/zorivest/AGENTS.md) — Mandatory agent rules
- [ACON Synthesis](file:///p:/zorivest/_inspiration/acon_research/acon-compression-synthesis.md) — Research source
