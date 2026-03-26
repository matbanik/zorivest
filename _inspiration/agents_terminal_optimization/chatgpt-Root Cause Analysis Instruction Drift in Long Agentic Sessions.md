# Root Cause Analysis: Instruction Drift in Long Agentic Sessions

LLM-based agents often **“lose” hard constraints over time** due to the causal Transformer’s attention dynamics.  In practice, even if an agent immediately repeats a rule when prompted, that rule can slip from focus after a few more tool uses or messages.  Recent studies confirm this: as the token count grows, models under-attend to earlier instructions and over-weight the most recent content【5†L229-L235】.  In effect, the very context (tool outputs, chat history, etc.) that the agent generates can **dilute and displace** system instructions.  This “attention dilution” is structural – softmax attention is a zero-sum game, so more context tokens means less attention per token【24†L110-L116】.  Empirically, agents exhibit strong **primacy and recency biases**: instructions at the very beginning of the prompt (or very end via prompt-repetition) are obeyed far more reliably than those in the middle【22†L162-L170】【24†L110-L116】.  In practice, a rule buried mid-file or not re-stated often enough simply “falls into the blind spot” of the agent【20†L46-L50】【22†L162-L170】.

Another mechanism is **unbounded memory growth**. If the agent naively appends each turn to its “internal state” (transcript replay) or retrieves loosely related past messages, it gets no clear signal about what to keep or discard【5†L228-L235】【3†L290-L299】.  Over long sessions the relevant constraints become a smaller fraction of the prompt, and the model’s output “drifts” (or “erodes”) from the original instructions.  Indeed, recent work frames *instruction drift* as a stochastic decay that reaches an equilibrium unless corrected【10†L101-L106】【11†L18-L21】.  Without explicit corrective signals, even a fine-tuned model will tend to **forget earlier constraints** over many turns.

In short, the culprit is architectural: a left-to-right model without bidirectional context sees earlier tokens as “distant” and is easily distracted by intervening content【24†L130-L138】【24†L110-L116】.  When many instructions or irrelevant logs accumulate, the original rules lose influence (attention dilution, “lost in the middle” and “dumb zone” effects【20†L64-L73】【24†L110-L116】).  The repeated violations despite human corrections suggest the agent is not “integrating” the rule into a persistent state; instead it momentarily parrots it and then reverts as if the correction were ephemeral.

**Mitigations:** Current best practice is to *actively manage* the agent’s prompt context.  Practitioners find that **explicit reminders** and prompt structuring help preserve constraints【10†L101-L106】【11†L18-L21】【24†L147-L152】. For example, injecting the rule *before and after* a long-running action (the “sandwich” or prompt-repetition trick) can simulate bidirectional attention【24†L130-L138】.  Agents like Claude Code even insert `<system-reminder>` tokens or long-conversation reminders into tool outputs to reinforce rules【24†L147-L152】.  More generally, *periodic goal- or rule-reminders* substantially reduce drift in multi-turn tests【10†L101-L106】【11†L18-L21】.

Other scaffolding approaches include keeping the **working context small and focused**.  Research suggests reserving a “Tier-0” working memory containing only the most critical content (the current objective, stable policies, recent steps, etc.)【18†L274-L283】.  In practice, this means **front-loading the most important rules** at the very top of the AGENTS.md and avoiding long digressions mid-file【22†L162-L170】【24†L110-L116】.  We also avoid negative commands (“never do X”) where possible, since prohibitions are empirically more fragile than affirmative guidance【22†L174-L180】. Finally, **modularizing and pruning** the instruction set (dividing rules into domain-specific files loaded only when needed【22†L168-L176】【30†L172-L180】) prevents irrelevant rules from choking the prompt. In summary, the agent’s “forgetfulness” is due to context dilution and memory drift【5†L228-L235】【20†L46-L50】; combating it requires repeated in-context reminders and lean, prioritized instructions【22†L162-L170】【11†L18-L21】.

# AGENTS.md Priority Hierarchy

| **Section**                | **Priority** | **Format**                 | **Notes / Placement**                                                                   |
|----------------------------|:------------:|----------------------------|-----------------------------------------------------------------------------------------|
| **Quality-First Policy**   | High         | Prose (brief manifesto)    | *Top of file.* States the overriding goal (code quality > speed), to frame all actions.|
| **Tool Commands (Key)**    | High         | Bulleted list              | *Early section.* List the concrete commands the agent is allowed/expected to use (pytest, pyright, etc.), with flags. Critical to see up front【27†L521-L524】. |
| **Windows Shell Rules**    | High         | **Mandatory pre-flight checklist (see below)** | Must come *before any command execution.* Enforced before running shell commands.   |
| **Testing Protocol (TDD)** | Medium-High  | Decision-tree / step list  | Stepwise: “Run tests, then static checks, then lint.” Present as an ordered workflow (numbered), with conditional branches (e.g. on test failures). |
| **Git Workflow Safety**    | Medium       | Decision-tree / bullet list| Outline rules for commits/pushes: one operation at a time, no interactive commit. Checks (e.g. verifying via `git log`) should be inline in test steps. |
| **Anti-Premature-Stop**    | Medium       | Inline reminder bullet     | Brief rule (“never stop until all steps completed”) reiterated at each workflow checkpoint.  |
| **Anti-Slop Checklist**    | Low-Med      | Bullet list                | Code style and formatting reminders. Could be modularized (or linked to a separate style guide file) to avoid bloating AGENTS.md. |
| **Examples / SOPs**       | Low          | Reference (link to docs)   | If needed, link to fuller docs or examples (e.g. sample test output) rather than embed. |

**Formatting notes:** We front-load the absolute essentials (mission statement and allowed commands) so the agent’s *attention sink* is on them【22†L162-L170】.  The Windows Shell rules must act as a *pre-flight gate* (see next section) so they are *unavoidable*.  The testing and git procedures are best shown as stepwise flows or decision trees (to avoid ambiguity).  We embed short rule-reminders (like “never stop early” or “always check exit codes”) at key junctures, ensuring the agent re-reads them in context. If the instruction file grows, we use progressive disclosure: heavy language-specific or Windows-specific rules can be moved to separate files (with pointers in AGENTS.md)【30†L172-L180】. A dedicated `RULES.md` with enumerated rules (**RULE-1**, **RULE-2**, etc.) could further clarify priorities, but might duplicate content. Given the need for sequential decision logic, our preference is embedded sections with clear headings and checklists, rather than a flat rule list.

# Mandatory Pre-Flight: Windows PowerShell Safety Checks

Before running *any* test or build command in PowerShell, enforce this checklist:

- **Redirect output to file:** For any long-running command (e.g. `uv run pytest`, `npm test`), use `> C:\Temp\out.txt 2>&1` instead of piping.  
- **No inline filters:** Do **not** pipe `pytest`, `vitest`, `npm run`, etc. into `| Select-String`, `| findstr` or `| Where-Object` – this causes hangs. Always write output to a file first.  
- **Use Get-Content to view:** After the command finishes, use `Get-Content C:\Temp\out.txt | Select-Object -Last N` to inspect results. This avoids hanging pipes.  
- **Error redirection:** Include `2>&1` in redirects so errors are captured.  
- **Check exit codes:** If the command exits nonzero, treat it as test failure (don’t ignore silent errors).  

> **Checklist Pass:** *Do not proceed unless each pre-flight item is satisfied.* Think of this as a mandatory gate: if any item is unchecked, abort the command and fix the invocation. Treat this checklist like a latch – it must always be closed before proceeding.

# Testing Workflow Skill (`SKILL.md`)

```markdown
---
name: zorivest-testing-workflow
description: Executes Zorivest test and analysis pipeline asynchronously (fire‐and‐read pattern), storing outputs in C:\Temp\zorivest\.
---
# Zorivest Testing Workflow

1. **Run Python tests (MEU gate):**  
   Execute:  
   ```
   uv run pytest tests/ > C:\Temp\zorivest\pytest-output.txt 2>&1
   ```  
   – Use `Start-Process` or equivalent to fire this non-blocking.  
   – *Wait:* Pause for 10000 ms.  
   – *Read output:* `Get-Content C:\Temp\zorivest\pytest-output.txt | Select-Object -Last 30`.  
   – *On failure:* If exit code ≠ 0 or “FAILED” found, record “pytest FAILED” and abort further steps.

2. **Run codebase validation:**  
   Execute:  
   ```
   uv run python validate_codebase.py > C:\Temp\zorivest\validate-output.txt 2>&1
   ```  
   – Wait 10000 ms, then read last lines similarly.  
   – Check for “Validation passed” or errors. Abort on failure.

3. **Run Pyright (TypeScript typecheck for Python stubs):**  
   Execute:  
   ```
   uv run pyright . > C:\Temp\zorivest\pyright-output.txt 2>&1
   ```  
   – Wait 10000 ms, then `Get-Content` last lines.  
   – If any errors or exit code ≠ 0, mark “pyright FAILED”.

4. **Run Ruff (Python linter):**  
   Execute:  
   ```
   uv run ruff check . > C:\Temp\zorivest\ruff-output.txt 2>&1
   ```  
   – Wait 10000 ms, read last lines.  
   – On any lint errors or exit ≠ 0, mark “ruff FAILED”.

5. **Run TypeScript tests (vitest):**  
   Execute:  
   ```
   uv run vitest --run > C:\Temp\zorivest\vitest-output.txt 2>&1
   ```  
   – Wait 10000 ms, then `Get-Content` last lines.  
   – If tests fail or exit ≠ 0, record “vitest FAILED”.

6. **Aggregate results:**  
   Combine outputs or summaries from each step. If any step failed, report overall failure. Otherwise report “All tests passed.”

```

*(Note: Each command uses output redirection and a fixed wait (10s) before reading, with **no polling** of the process status.)*

# Git Workflow Safety Decision Tree

1. **On `git commit`:**  
   - If the commit was (mistakenly) backgrounded (e.g. using `&`): **Abort.** Immediately terminate the commit process (e.g. `Stop-Process -Name git`) and delete any `.git/index.lock` file【39†L215-L217】【42†L68-L76】. Do a soft reset (`git reset --soft HEAD~1`) and log an error: *“Commit must not run in background. Retry as foreground step.”*  
   - Otherwise (commit is foreground): proceed.

2. **Wait for completion (≤5 min):** The agent should not continually poll a tool-API but may sleep or defer. After the commit command was issued with a `-m` message, **verify via Git** rather than API status: run `git log -1 --pretty=format:%s` to fetch the latest commit message.  
   - If the message matches the expected commit summary and exit code was 0: **Success** – continue.  
   - If not (no new commit or an editor prompt hung): see next.

3. **Timeout and stuck handling:** If **5 minutes elapse** with no sign of completion:  
   - Use system tools to **kill any lingering Git process** (`taskkill /IM git.exe /F` or similar)【42†L82-L90】.  
   - Remove any `.git/index.lock` (the lock prevents others from running)【42†L68-L76】.  
   - Verify repository state (`git status`). Perform cleanup: `git reset --mixed HEAD~1` if a partial commit was recorded.  
   - *Failure path:* Report an error “Git commit timed out (>5min). Operation aborted. Please check repository state.”

4. **Continuing safely:** After cleanup, either retry the commit with a proper message or halt. Throughout, **never run multiple Git commands concurrently** on the same repo【42†L158-L163】. Always verify by inspecting `git log` or `git status` instead of tool-API polling.

This flow ensures the agent never corrupts the repo by overlapping operations. It uses Git’s own mechanisms (logs and lock files) to check success, and resorts to *kill + cleanup* if a commit hangs, following best practices【42†L68-L76】【42†L158-L163】.
