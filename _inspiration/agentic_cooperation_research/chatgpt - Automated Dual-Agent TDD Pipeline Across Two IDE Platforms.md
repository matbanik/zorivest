# Automated Dual-Agent TDD Pipeline Across Two IDE Platforms

## Top 10 Findings

- **Dual-Agent Loops Improve Quality:** Real-world cases show that pairing two AI coding agents (with complementary strengths) significantly boosts code quality.  For example, one practitioner used **Claude Code** (as the “implementer”) and **Codex** (as the “reviewer”) in a loop: the implementer wrote code and ran tests until they passed, then the reviewer agent inspected the changes.  This loop converged reliably in just a few iterations, catching subtle bugs and yielding production-quality PRs【15†L138-L142】【12†L37-L40】.  Humans mainly orchestrated and broke ties.  The synergy came from separate context windows (each agent started with fresh state), specialized roles, and automated handoff of diffs and test results.  Reported failure modes were mostly “stuck” loops that required human reset, not fundamental logic errors【15†L138-L142】.

- **File-Based Handoff Protocols:** Successful multi-agent workflows almost always use files (or structured docs) to pass state.  A popular pattern is for Agent A to write a YAML/Markdown file that Agent B reads/validates.  For example, one expert recommends each Claude Code sub-agent output to `.claude/workflow/<agent>/output.yaml`, with a JSON/YAML schema for validation【55†L68-L72】.  The **Session-Handoff** skill (Softaworks’ agent-toolkit) similarly scaffolds a Markdown handoff file and uses Python scripts to populate metadata (git status, modified files, etc.)【61†L327-L334】. This creates an unambiguous “agent inbox/outbox” on disk.  Structured verdict files (approve/reject notes, test outcomes) are also common – agents append clear status fields (e.g. `test_status: pass`) for downstream reading. These file protocols dramatically reduce ambiguity compared to free-text copying, and tools can auto-validate or refuse malformed handoffs.

- **TDD & Spec-Driven by Design:** The most robust AI-driven workflows are test- or spec-first.  In practice, one agent session writes the failing test(s) or “Feature Intent Contract,” and another session generates code to turn them green.  For instance, in a reported PR loop, the Claude implementer ran a unit test suite after each fix (going “red→green”) before sending the diff to the Codex reviewer【15†L138-L142】.  Even when the same model was used for both roles, practitioners enforce a strict write-tests-then-code discipline.  Contracts (preconditions/postconditions) have also been encoded in “spec files” so agents know exact success criteria.  Capturing “red→green” evidence between sessions (e.g. test logs or CI badges) was noted as important documentation to feed back into the next agent’s prompt.

- **Specialized vs. Single-Agent Roles:** Successful projects use both approaches.  Frameworks like **Squad** explicitly split roles – e.g. separate *Reviewer*, *Fixer*, *Orchestrator* agents with fixed personas and state machines【81†L259-L266】【81†L290-L304】.  This ensured each agent had a narrow context (one PR, one subtask).  The orchestrator agent “conductor” managed multiple PRs in parallel, spinning up reviewer/fixer loops for each【81†L290-L304】.  By contrast, some best-practice guides (e.g. Microsoft) caution that not every role deserves its own agent; a single agent can often *simulate* multiple roles by switching persona or toolaccess within one conversation【78†L174-L182】.  In other words, start with one agent (using a powerful model with rules/prompts) and only split into multiple agents when the complexity (team boundaries, security, scale) demands it【78†L174-L182】.  In practice, hybrid patterns (one “manager” agent plus helper agents) also appear: the Squad Conductor is single-agent, but delegates subtasks to specialized bots.

- **Model and IDE Interoperability:** Examples show teams mixing models and platforms without a special API bridge.  One user manually ran two separate Codex chat sessions (in VS Code) on front-end and back-end repos, exchanging text prompts as the “communication layer”【71†L223-L232】.  Others scripted local tools: e.g. **claude-code-tools** includes a `tmux-cli` utility to spawn and direct multiple Claude sessions in parallel.  More formally, projects use the **Model Context Protocol (MCP)** or simple file sharing to unify context.  For instance, the open-source *OpenMemory* server lets different agents (VS Code Copilot, Google Antigravity, etc.) connect via MCP and share a SQLite memory【36†L63-L72】.  Likewise, git itself was suggested as a “message bus”: agents commit to a private branch and the other pulls updates.

- **Shared Persistent Memory:** To keep both agents aware of project state, teams use centralized memory stores.  OpenAI’s VS Code “Copilot Memory” and Autogen/MCP memory are examples.  One public solution is **OpenMemory** (Cavira): an SQLite-based store with MCP integration, letting multiple agent sessions read/write the same knowledge (for example, design notes or pomera-style bulletins)【36†L63-L72】.  Claude Code also has a local `cli memory` that persists across sessions (e.g. `claude memory read/write`).  By configuring both IDEs/agents to use a common memory endpoint or file path, agents can share learned facts or TODO lists across boundaries.

- **Automation and Tooling:** A number of practical tools speed up coordination.  The “File Watcher” skill (for Claude Code, Cursor, etc.) auto-detects changes to specified paths and triggers follow-up actions (e.g. post-processing by another agent)【38†L19-L27】.  Extensions and scripts handle approval prompts: VS Code Copilot Agent mode now supports a “YOLO” auto-approve setting (`chat.tools.global.autoApprove`: true) to skip manual confirms【46†L239-L247】【47†L1-L4】.  In Google Antigravity, users created an “Auto Accept Agent” extension that automatically clicks through the “run this command?” prompts【51†L1-L4】.  CLI tools (e.g. Python/Bash scripts) can launch new IDE agent sessions with specific prompts, transfer files between their “brain” folders, and poll for output – though no standard existed yet.  MCP Servers also help bridging: by running a shared MCP host (e.g. SonarQube or local LLM) that both IDE agents connect to, teams achieve indirect IPC.

- **Agent Configuration Patterns:** Structuring rules, roles, and skills is critical.  Many agents use YAML/JSON schemas for config.  For instance, the **yaml-agent-format** skill provides a full YAML schema (with linting) to define agent persona, tools, prompts and memory consistently【85†L94-L101】.  Others stick to Markdown frontmatter or JSON task graphs.  Github issue templates or Mermaid diagrams sometimes outline the workflow.  Empirically, **explicit rule files** appended to system prompts have high leverage.  In one study, carefully tuning a `.clinerules` file improved a coding agent’s accuracy by ~10–15%【74†L196-L204】【75†L1-L4】.  Good rule formats are concise YAML or bullet lists inserted at the top of a prompt.  Agents were also taught “slash commands” (e.g. `/resume-workflow`) that trigger reading an instruction file, and “skill discovery” by naming conventions (auto-loading `skill-*.md` from a known folder).

- **Iterative Improvement Loops:** Productionized workflows measure progress across runs.  Teams use version control diff sizes, test pass-rates, and error counts as proxies.  For example, the **SWE-Bench** metric (standardized GitHub issue→patch benchmark) was used to track improvement when refining agent prompts【76†L259-L268】.  Agents themselves have begun performing self-audit at the end of a session: e.g. an “Introspect” Claude skill that asks the agent to write a reflection on its own errors and suggest improvements【84†L63-L71】.  Storing each session’s prompts and outcomes allows automated A/B comparison of prompt versions.  We did not find a ready-made “prompt versioning system,” but teams log ChatGPT system prompts changes in a git repo and track metrics like build time, iterations needed, etc.

- **Human-in-the-Loop Optimization:** The effective workflows minimize needless human intervention.  Humans typically define the overall goal, fix tricky bugs, and approve final merges.  They **do not** hand-code or heavily rewrite the agent’s output in these examples.  Instead, humans intervene when agents diverge (e.g. infinite loop, hallucination) or when a judgment call is needed.  To maximize signal, engineers ask agents to annotate or “explain” their changes (as in TestCopilot experiments) so they only need to review summaries.  One key practice: feed agents all evidence (tests, lint results, static analysis) so humans only see final diffs flagged by tools.  No sources gave a single metric for efficiency, but users mentioned tracking number of prompt iterations, context window usage, or time per commit as ways to judge progress.

## Implementation Comparison Table

| Project / Example                         | Models (Roles)                   | Communication                 | Human Role              | TDD/Test-First? | What Worked                                                          | What Failed                                                       | Link                                        |
|-------------------------------------------|----------------------------------|-------------------------------|-------------------------|-----------------|----------------------------------------------------------------------|-------------------------------------------------------------------|---------------------------------------------|
| **Yar’s Dual-Agent Loop** (Hwee-Boon Yar)【12†L37-L40】 | Claude (“writer”, on Sonnet-4.5) & Codex (reviewer) | CLI skill (`codex exec` reads git diff) | Developer triggers review loops | Yes (Swift TDD) | Continuous refine-pass cycles; tests caught errors early【12†L37-L40】 | Occasional loops hung (needed manual restart)【12†L37-L40】 | [Blog (Feb 2026)【12†L37-L40】](https://hboon.com/2026/02/dual-agent/) |
| **Dev.to Dual-Agent PR Fix** (User yw1975)【15†L138-L142】 | Claude Code (implementer) & Codex (reviewer) | Manual copy-paste of git diffs | Tech lead orchestrator | Yes (ran full test suite) | Completed a real PR: 133/133 tests passing, all review comments addressed【15†L138-L142】 | Agents sometimes generated duplicated work; needed custom “review helper” scripts; stuck loops needed human reset【15†L138-L142】 | [Dev.to Case Study【15†L138-L142】](https://dev.to/yw1975/ai-dual-agent-workflow) |
| **Claude Code YAML Handoff** (Dan Dunford)【55†L68-L72】 | Claude Code (Inspector, Planner, Executor roles in series) | File: agent outputs structured YAML for next | N/A (scripted handoff)  | N/A (focus is spec flow) | Reliable data transfer: YAML with JSON schema meant no miscommunication【55†L68-L72】 | Requires defining schemas upfront; agents need robust schema validation (could crash if format wrong) | [Medium (Oct 2025)【55†L68-L72】](https://dan-dunford.medium.com/claude-yaml-handoff) |
| **Squad: AI Review Loops** (abbudjoe)【81†L259-L266】【81†L290-L304】 | (Orchestrator / Reviewer / Fixer are all AI agents, typically same model) | Persistent subprocesses and GitHub PRs | Developer initializes conductor agent | Yes (review-fix cycles until pass) | Scaling: parallel PRs managed by a “conductor” agent, automated diff review cycles【81†L259-L266】 | Complex setup; still experimental (0 stars); needs careful tuning of prompts & watchdog timers【81†L259-L266】 | [GitHub (Autonomous loop)【81†L259-L266】](https://github.com/abbudjoe/squad) |
| **Session-Handoff Skill** (Softaworks)【61†L327-L334】 | Any (user chooses agent, e.g. Claude Code) | File: generates structured Markdown (.claude/handoffs/*.md) | User fills in context and next steps | No (meta-level handoff) | Preserves context with metadata (git state, TODOs, decisions); built-in validation catches secrets【61†L327-L334】 | Manual effort: user must complete and review the template; depends on agent to recognize “create handoff” trigger【61†L327-L334】 | [GitHub Skill README【61†L327-L334】](https://github.com/softaworks/agent-toolkit/blob/main/skills/session-handoff/README.md) |
| **Multi-Model Code Review** (LevNikolai skills)【19†L1-L5】 | Claude Code (default) + Codex + Gemini (parallel reviewers) | Parallel API calls (MCP) and file skill hooks | User triggers `review-code` skill via CLI | No (code review focus) | 3× coverage of reviews: if one model misses an issue, another catches it【19†L1-L5】 | Overkill for small tasks; conflicting advice among agents; fallback logic needed | [GitHub (claude-code-skills)【19†L1-L5】](https://github.com/levnikolai/claude-code-skills) |
| **OpenAI Agents SDK Demo** (OpenAI example)【71†L223-L232】 | Codex (two sessions, FE and BE) | Manual prompt exchange between chat windows | Developer copy/pastes and synchronizes agents | No (concept)     | Demonstrated feasibility: one agent asked the other for context then continued work【71†L223-L232】 | Entirely manual: low-level and prone to human error | [GitHub Issue #3280【71†L223-L232】](https://github.com/openai/codex/issues/3280) |

## Automation Toolkit

- **File Watcher Skills:** For example, the Claude Code “File Watcher” skill (from Skills Playground) can monitor specified paths and trigger agent actions on file changes【38†L19-L27】.  Installing via `npx tessl i github:aidotnet/moyucode --skill file-watcher` lets you e.g. run an agent whenever `handoff.yaml` is updated.  This effectively automates agent B picking up agent A’s output without manual checks.  

- **Session Handoff Scripts:** The Softaworks Session-Handoff skill includes Python scripts (`create_handoff.py`, `validate_handoff.py`) to scaffold a Markdown handoff and verify it【61†L327-L334】.  We can reuse or adapt these scripts.  For instance:
  ```bash
  # Create a new handoff before pausing
  python3 sessions/create_handoff.py "implement-new-feature"
  # Validate it then resume later
  python3 sessions/validate_handoff.py .claude/handoffs/2026-03-05-new-feature.md
  ```
  The validation step checks for missing fields or secrets, easing oversight.

- **Global Auto-Approve (VS Code):** In VS Code’s Copilot Agent mode, enable “YOLO” mode to skip manual approvals.  In `settings.json`, set:
  ```json
  "chat.tools.global.autoApprove": true,
  "chat.tools.terminal.enableAutoApprove": true
  ```
  as per StackOverflow guidance【47†L1-L4】.  This lets the agent automatically run suggested shell commands and continue iterations without user clicks (use with caution).  

- **Auto-Accept Extension (Antigravity):** For Google Antigravity IDE, install the community extension “Auto Accept Agent” (MunKhin/auto-accept-agent) which clicks the “approve” dialogs in the background【51†L1-L4】.  This circumvents the bug where Antigravity repeatedly asks permission despite “always proceed” being set.

- **MCP Memory Server:** Deploy a shared memory server like **OpenMemory**.  For example, run `openmemory-server` on localhost and configure both agents to use it.  From Claude’s CLI:
  ```bash
  claude mcp add --transport http openmemory http://localhost:8080/mcp
  ```
  Now both IDEs’ agents can `memory read/write openmemory somekey` to share notes, docs, or task state (e.g. pomera_notes) across sessions【36†L63-L72】.  

- **File-Based IPC Scripts:** Use shell inotify or PowerShell watchers to bridge IDEs.  E.g. on Linux:
  ```bash
  while inotifywait -e close_write /path/to/agentA/output.yaml; do
    cp /path/to/agentA/output.yaml /path/to/agentB/input.yaml
  done
  ```
  This would detect when Agent A (in one IDE) writes a handoff file, and automatically feed it to Agent B’s workspace.  (No off-the-shelf tool found, but simple to script.)

- **Test Execution Automation:** Integrate your CI/test runner as a tool.  For instance, expose `npm test` or `pytest` so the agent can run tests.  Use Copilot’s “Run Tests” tool or Antigravity’s equivalent so that after implementation, the agent itself triggers tests and captures the results (red/green) as output context.

## Agent Configuration Patterns

| Pattern                    | Examples/Projects                            | Format/Tools Used                                 |
|----------------------------|----------------------------------------------|---------------------------------------------------|
| **Agent Rules Files**      | Cline (`.clinerules`), Cursor (`ru.json`)    | YAML/JSON appended to system prompt【74†L196-L204】; define style, security, architecture constraints. |
| **Role Personas**          | Squad, Dual-agent loops                      | Multiple skill folders or prompts: e.g. `architect.md`, `developer.md`, each with persona instructions.  |
| **Sequential Workflows**   | Dan Dunford, Softaworks Handoff              | File-based steps (YAML/MD). Agents follow a fixed handoff sequence (Investigation → Planning → Execution)【55†L68-L72】. |
| **Checkbox/Natural Steps**| Blog walkthroughs, LobeHub skills            | Markdown tasks list (e.g. `- [ ] Write tests`, `- [ ] Implement function`). Agents check off steps as done. |
| **YAML Frontmatter**       | YAML Agent Format skill                      | Agent config in `.yaml`: name, prompt, tools, memory, with schema validation【85†L94-L101】. Easier CI checking than free-text. |
| **JSON Task Graphs**       | LangGraph/Mastra (not found in sources)      | (Not yet common in coding demos; conceptually a DAG of tasks for orchestration). |
| **Mermaid Flowcharts**     | Rare in code (more in docs)                  | Some teams draft mermaid diagrams of the workflow as human docs. Not used at runtime. |
| **Slash Commands/Workflows** | Custom CLI triggers (e.g. `/start-review` in chat) | Agents read commands and lookup a file/skill by name (like LobeHub triggers a skill by slash command). |
| **Skill Composition**      | Many Claude Code projects                    | Agents auto-load multiple “skill” files: e.g. code linter, test-runner, changelog generator. Files named `skill-*.js` auto-imported. |

Notably, structured formats (YAML with schema) outperformed free-form.  When agents had to parse each other’s output, clearly labeled sections (JSON or YAML) made automation far more reliable【55†L68-L72】【85†L94-L101】.  Multimodal workflows tend to stick to one format for clarity – e.g. “all handoffs are `.yaml`” or “agents only output markdown tables”.

## Proposed Improved Workflow

1. **Spec/Test Agent (Agent A):** In IDE-1, start an agent session that reads the feature request or ticket. It writes a test stub or contract first (e.g. in a file `feature.spec.js` or YAML schema). Save this “intent” file (triggers can auto-create it from a prompt).
2. **File Handoff:** Agent A commits or writes the spec file into a shared location (could be a git branch, or simply `/workspace/handsoff.yaml`). A file-watcher or git-hook then notifies IDE-2 (Agent B) that new work is ready.
3. **Implement Agent (Agent B):** In IDE-2 with the other model, open a session. It reads the spec/test file. It implements the code to satisfy the test. After coding, it auto-runs the test suite (e.g. invoking npm/jest or pytest as a tool). If tests fail, it updates its code and repeats. Once tests pass (“red→green”), it generates a patch/diff.
4. **Patch Handoff:** Agent B writes its patch or commit to a shared location (push to a git branch, or write `fix.patch`). This triggers Agent A to resume.
5. **Review Agent (Agent A resuming):** Back in IDE-1, Agent A (or possibly the same session as Step 1, now in “review” mode) loads the patch. It runs static analysis and test suite to double-check. It adds comments or a brief report (approve/fix suggestions) and marks the PR ready.
6. **Final Integration:** Human reviews any flagged issues (straightforward, since tests already passed and both agents “signed off”). Human merges or tweaks only if essential.

Key improvements over current loop:
- **Automated Triggers:** Use OS file watchers or MCP to auto-switch contexts between IDEs (minimize copy/paste). Both IDEs run scripts listening for a “new_file” event.
- **Shared Memory:** Store project context (e.g. architectural notes, pomera bulletins) in a central database so both agents remember goals and prior decisions.
- **Prompt Evolution:** Each iteration’s input/output is logged. Periodically, run a “Self-Refine” step: have an agent (or GPT-5) review past PRs and propose prompt tweaks or identify recurring mistakes, then update system prompts or rules accordingly.
- **Introspection:** After each full cycle, an agent or automated script runs an introspection prompt (as in the AI Soul Introspection skill【84†L63-L71】) to record what went well and what to watch out for next time (e.g. “The agents keep tripping on async boundaries; add a rule about using async/await consistently.”).
- **Metric Logging:** Record metrics per session: number of user prompts, number of edit iterations to green, total wall-clock time, and diff size. Over time, show trends (e.g. “last week’s loop took 1.2× fewer steps”).

This improved loop explicitly separates **roles** (spec vs implement vs review), uses **file-based pipelines** (to bridge IDEs), and builds in **continuous improvement** by automated self-checks. The human’s job becomes managing the workflow trigger (“start feature loop”), verifying final results, and occasionally refining the prompts/rules – not writing code directly.

## Quick Wins (implement <1h)

- **Enable Auto-Approve Mode:** Add `"chat.tools.global.autoApprove": true` to VS Code settings (Copilot Agents)【47†L1-L4】. This immediately removes manual "Proceed?" prompts. Also set `"chat.tools.terminal.enableAutoApprove": true` to skip command approvals.  (For Antigravity, install the **Auto Accept Agent** extension as a one-click solution.)
- **Install File Watcher Skill:** Run
  ```
  npx tessl i github:aidotnet/moyucode --skill file-watcher
  ```
  and configure it to watch your `handoff` folder. This requires minimal setup and lets Agent B auto-start when Agent A writes a file.
- **Use Session-Handoff Templates:** Clone the softaworks handoff skill or just copy its template Markdown (the `[TODO]` fields). Whenever pausing, run the provided `create_handoff.py` (or just copy the template) so you never forget critical context.  This takes minutes and improves clarity greatly.
- **Shared MCP Server:** Deploy a quick SQLite-backed memory (e.g. run `openmemory serve` in a terminal). Configure both agents to connect to it (or just share a network drive if ideal). You now have one source of truth for notes and facts.  (OpenMemory also provides example config for VMware or Docker.)
- **Prompt Checklist:** Update your agent system prompts to include a brief rule checklist at the top. For example:
  ```
  #Rules:
  - Focus only on tasks in current PR.
  - Validate with tests after every change.
  ```
  This costs nothing and often prevents off-track responses (as noted in Arize’s experience【74†L196-L204】).

## Strategic Improvements

- **Robust Orchestrator Agent:** Build or adopt a light “conductor” agent (like Squad’s Conductor) in one environment to manage parallel tasks and merges. This handles scheduling, CI integration, and ensures no race conditions. It would watch branches, trigger feature loops, and coordinate agents on both IDEs. (Extending tools like OpenAI’s Agent SDK or CrewAI could accelerate this.)
- **Schema and Contract Templates:** Formalize file protocols with JSON Schema (or YAML schema). For each handoff file (e.g. `{intent:…, tests:…, code_changes:[…]}`), define a schema and use the agent or a validator to enforce it. This eliminates parsing errors. The YAML-agent-format skill shows how to do this cleanly【85†L94-L101】.
- **Monitor & Metrics Dashboard:** Build a dashboard (could be as simple as a script appending CSV logs) tracking dual-agent metrics: average cycles per feature, test coverage gains, code churn, etc. Tie these to prompt revisions. For example, if average iterations climb, introspect prompts for fix.
- **Expert Prompt Tuning:** Periodically apply prompt optimization techniques (e.g. Arize’s prompt learning) to evolve system prompts and rules【76†L259-L268】. As the domain grows, ensure prompts capture new patterns. Store all prompt versions in git for audit.
- **Cross-IDE Integration:** Investigate using MCP more fully. For instance, host a local MCP that both VS Code and Antigravity agents connect to (via WebSocket). This could allow, e.g., Antigravity’s search plugin to serve documents to Copilot by updating memory in real-time. Also consider leveraging Discord or Slack APIs as a novel channel for agent-to-agent messaging if both IDEs can hit the API.
- **Agent Governance:** Define clear “light” rules for error conditions (e.g. if tests still fail after N attempts, escalate to human). Automate these checks so that agents refuse to push code if certain policies aren’t met (security lint, compliance). Using a policy-as-code tool (like OPA) with the AI loop could catch issues early.
- **Skill Library and Orchestration:** Invest time in building or curating a modular skill library (linting, searching docs, refactoring). Agents can then “call” these skills as needed (Claude Code supports this via `"tools"`). A standardized toolkit reduces primitive prompts and repetition.

By gradually automating the approvals, handoffs, and memos – and by systematically refining prompts – this dual-agent TDD workflow can become mostly self-driving, with humans intervening only for oversight or strategy shifts.

**Sources:** Implementation details were drawn from practitioner blogs and code repositories【12†L37-L40】【15†L138-L142】【55†L68-L72】【61†L327-L334】【71†L223-L232】【74†L196-L204】【84†L63-L71】, as cited above. Each recommendation is supported by these up-to-date community examples or documentation.
