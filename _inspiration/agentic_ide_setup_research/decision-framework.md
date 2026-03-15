# Agentic IDE Setup — Decision Framework

> **Context**: 10 open questions to resolve before creating a plan to update the build plan documents for `zorivest_setup_workspace` (MEU-165 expansion).
>
> Each question includes the **evidence** (project patterns + web research), a **recommended choice** (⭐), and **alternatives**. Pick one option per question.

---

## Q1: MEU Structure — Expand In-Place or Split?

**Evidence**: MEU sizing pattern is tightly scoped — 1 entity/service/tool per MEU. Largest single MEU was MEU-42 (ToolsetRegistry + client detection, ~13K handoff). Multi-MEU projects group 2-6 related MEUs (Market Data: 6, GUI Shell: 3, Scheduling Foundation: 4).

| Option | Description | Precedent |
|--------|-------------|-----------|
| **A** | **Expand MEU-165** as a single large MEU covering tool + templates | MEU-42 covered registry + detection + CLI + mode filter in one |
| ⭐ **B** | **Split into 2 MEUs**: MEU-165a (tool infrastructure) + MEU-165b (template content) | Phase 2A split backup into 5 separate MEUs (17-21), each one thing |
| **C** | **Split into 3 MEUs**: tool core + template content + advanced features (merge/diff preview) | No precedent for shipping v2 features in the same project |

> ⭐ **Recommended: B** — Two MEUs keeps each focused. The tool infrastructure (safeWrite, path validation, scaffold-meta, registration) is distinct from the content authoring work (AGENTS.md, IDE shims, docs, workflows).

---

## Q2: Progressive Tiers — Separate Tools or One Tool with Parameters?

**Evidence**: `zorivest_diagnose` uses a `verbose` parameter for different detail levels (same operation, different scope). Discovery uses separate tools for separate actions (`list_available_toolsets`, `describe_toolset`, `enable_toolset`). The tiers are the same operation at different depths.

| Option | Description | Precedent |
|--------|-------------|-----------|
| ⭐ **A** | **Single tool with `scope` parameter**: `"minimal"` / `"standard"` / `"full"` | `zorivest_diagnose` `verbose` flag |
| **B** | **Three separate tools**: `setup_minimal`, `setup_standard`, `setup_full` | Discovery tool split (but those are genuinely different operations) |
| **C** | **Single tool, auto-detect scope**: always generate the right amount based on what's missing | `eslint --init` auto-detects framework |

> ⭐ **Recommended: A** — One tool, one name, one purpose. The `scope` parameter defaults to `"standard"` (AGENTS.md + IDE shims + basic `.agent/`). Users request `"full"` for the complete package.

---

## Q3: Priority Level — Tier 2 Research or Elevate?

**Evidence**: Research-Enhanced items sit after P0 core phases. MEU-165 depends only on MEU-42 (✅ already approved). No dependency on other research items (5.A–5.G). Current project has completed through Phase 6 GUI Shell Foundation.

| Option | Description | Precedent |
|--------|-------------|-----------|
| ⭐ **A** | **Keep at Tier 2** in Research-Enhanced section, mark as "dependency-met, buildable now" | Consistent with existing placement; no artificial elevation |
| **B** | **Elevate to P0** between Phase 5 and Phase 6 | Would require restructuring the matrix; the feature isn't blocking anything |
| **C** | **Create a new P1.25 tier** specifically for agentic infrastructure | No precedent for inserting new priority tiers |

> ⭐ **Recommended: A** — Keep placement, update status. The feature is buildable whenever you want to pick it up — no priority change needed.

---

## Q4: Build Timing — Now or Later?

**Evidence**: All 85 completed MEUs are ✅ approved. GUI Shell Foundation (MEU-43..45) was the latest project (2026-03-14). Pending work includes: more GUI pages (16, 16a-c), Phase 9 scheduling infra (40-49), and Research-Enhanced items (5.A–5.H).

| Option | Description | Trade-off |
|--------|-------------|-----------|
| **A** | **Build next** — make it the next project after GUI Shell | Immediate differentiator; agentic-first positioning (per Claude report) |
| **B** | **Build alongside GUI** — interleave with next GUI pages | Good variety; breaks up GUI monotony |
| ⭐ **C** | **Build when ready** — add to backlog, pick up when natural | Flexible; doesn't delay more critical trading features |
| **D** | **Build after Phase 9 scheduling** — complete scheduling first | Scheduling infrastructure is more complex and foundational |

> ⭐ **Recommended: C** — The build plan update documents the feature properly so it's ready to execute whenever you choose. No urgency to build before other features.

---

## Q5: Help Docs Audience — Developer-Facing or User-Facing?

**Evidence**: Web research confirms AGENTS.md is agent-facing (for AI coding agents), not user-facing. It should contain "non-inferable project-specific knowledge" (under 200 lines per community consensus). Zorivest's `docs/build-plan/` contains developer implementation specs (49 files). The generated docs need to be for end users of Zorivest's MCP tools.

| Option | Description | Precedent |
|--------|-------------|-----------|
| ⭐ **A** | **User-facing docs** — "Getting Started with Zorivest MCP", tool catalog, common workflows | AGENTS.md spec: domain vocabulary, build commands, tool references |
| **B** | **Agent-facing docs only** — instructions for AI explaining how to use each MCP tool | Claude pattern: CLAUDE.md is agent memory, not user guide |
| **C** | **Dual-audience docs** — structured for both humans and AI agents (MAGI approach per Claude report) | GitBook: AI readership of docs is 40%+ of traffic |

> ⭐ **Recommended: A** — The generated AGENTS.md IS the agent-facing document (it teaches the AI how to use Zorivest tools). The `.agent/docs/` folder should contain user-readable guides that also serve as agent context — a "getting started" guide, tool catalog, and common trading workflows.

---

## Q6: Workflows — Trading-Domain or Generic?

**Evidence**: Existing `.agent/workflows/` contains developer-focused workflows (create-plan, tdd-implementation, meu-handoff). These are for BUILDING Zorivest. The scaffolded workflows should be for USING Zorivest. Web search confirms AGENTS.md should include "executable commands" and "tech stack details" specific to the project.

| Option | Description | Content Examples |
|--------|-------------|------------------|
| ⭐ **A** | **Trading workflows** — how an AI agent helps a user with Zorivest | "Trade setup analysis", "Portfolio review", "Market research" |
| **B** | **Generic agentic workflows** — universally useful patterns | "Research before action", "Verify changes", "Report findings" |
| **C** | **Both** — trading + generic | Larger file count but more comprehensive |

> ⭐ **Recommended: A** — Ship 3-4 trading-domain workflows that demonstrate how AI agents should use Zorivest MCP tools. These teach the AI agent the domain-specific patterns (trade evaluation → position sizing → plan creation → execution tracking).

---

## Q7: Roles — Trading-Specific or Generic Agentic?

**Evidence**: The existing 6 roles (orchestrator, coder, tester, reviewer, guardrail, researcher) are generic software engineering roles for building code. Zorivest end users need AI assistance with trading decisions, not code reviews.

| Option | Description | Content |
|--------|-------------|---------|
| ⭐ **A** | **Trading-domain roles** adapted from generic template | Trade Analyst, Portfolio Reviewer, Risk Manager |
| **B** | **Generic agentic roles** — ship the same 6 from Zorivest's `.agent/` | Orchestrator, Coder, Tester, Reviewer, Guardrail, Researcher |
| **C** | **No roles** — roles add complexity with unclear value for end users | Skip roles directory entirely |
| **D** | **Both** — generic + trading roles | 8-9 role files, potential config fatigue |

> ⭐ **Recommended: A** — Ship 3 trading-domain roles. These give the AI agent distinct behavioral modes when helping with trading tasks (analytical vs. risk-focused vs. review-focused). Adapt the structure (Must Do, Must Not Do, Output Contract) from the existing role template.

---

## Q8: Build Plan File — New Section File or Fold In?

**Evidence**: Every MCP toolset gets its own subpage (`05a` through `05j`). `zorivest_diagnose` has `05b-mcp-zorivest-diagnostics.md`. `zorivest_launch_gui` is §5.10 in the main `05-mcp-server.md`. Complex features with multiple components warrant their own file.

| Option | Description | Precedent |
|--------|-------------|-----------|
| ⭐ **A** | **New file `05k-mcp-setup-workspace.md`** — dedicated spec | `05b-mcp-zorivest-diagnostics.md` for `zorivest_diagnose` |
| **B** | **Add section to `05-mcp-server.md`** — §5.15 or similar | `zorivest_launch_gui` is §5.10 in the main file |
| **C** | **New file + update main** — spec in `05k` + summary reference in `05-mcp-server.md` | All existing sub-files follow this pattern (e.g., `05c` is referenced from §5.7) |

> ⭐ **Recommended: A (with C's update pattern)** — Create `05k-mcp-setup-workspace.md` with the full spec AND add a summary reference in `05-mcp-server.md` (following established pattern of all `05x` files).

---

## Q9: Build Priority Matrix — Update in Place or Replace?

**Evidence**: When features split into multiple MEUs, each gets its own matrix row (items 10a–10e each have dedicated rows). Current 5.H is a single row. With 2 MEUs, we need 2 rows.

| Option | Description | Precedent |
|--------|-------------|-----------|
| ⭐ **A** | **Replace 5.H with 5.H1 + 5.H2** — two rows for two MEUs | Items 10a–10e: each separate MEU gets its own row |
| **B** | **Expand 5.H in-place** — one row noting "2 MEUs" in Notes | MEU-42: 15k row covered 4 build plan sub-sections |
| **C** | **Keep 5.H + add 5.I** — original row + new row for template content | Would displace the existing sequence (no 5.I currently exists) |

> ⭐ **Recommended: A** — Two rows: `5.H1` (Setup workspace tool core) and `5.H2` (Workspace template content). Both stay Tier 2, both say "After 15k". This is consistent with how Phase 2A items 10a–10e each got dedicated matrix rows.

---

## Q10: Windows Symlink Compatibility

**Evidence**: Windows NTFS symlinks require admin/developer mode. Zorivest is an Electron desktop app with Windows as primary target. All three research reports flagged symlink fragility. No symlinks are used anywhere in the existing codebase.

| Option | Description | Risk |
|--------|-------------|------|
| ⭐ **A** | **Thin shim copies** — each IDE file is real file, ~5 lines referencing AGENTS.md + IDE-specific content | Zero risk, works everywhere |
| **B** | **Symlinks with fallback** — try symlink, fall back to copy if it fails | Complexity for minimal benefit |
| **C** | **Full content copies** — each IDE file duplicates all of AGENTS.md + IDE sections | Content sync problem on updates |

> ⭐ **Recommended: A** — Thin shim copies. Each IDE file (GEMINI.md, CLAUDE.md, etc.) contains ~5-15 lines: a reference to AGENTS.md for full instructions, plus 5-10 lines of IDE-specific configuration hints. No symlink risk.

---

## Summary — Quick Pick Table

| # | Question | ⭐ Recommendation | Your Pick |
|---|----------|-------------------|-----------|
| 1 | MEU structure | **B**: Split into 2 MEUs (tool + content) | |
| 2 | Progressive tiers | **A**: Single tool, `scope` parameter | |
| 3 | Priority level | **A**: Keep Tier 2, mark buildable | |
| 4 | Build timing | **C**: Build when ready (backlog) | |
| 5 | Help docs audience | **A**: User-facing docs | |
| 6 | Workflows | **A**: Trading-domain workflows | |
| 7 | Roles | **A**: Trading-domain roles | |
| 8 | Build plan file | **A**: New `05k-mcp-setup-workspace.md` | |
| 9 | Matrix update | **A**: Replace with 5.H1 + 5.H2 rows | |
| 10 | Symlinks | **A**: Thin shim copies (no symlinks) | |
