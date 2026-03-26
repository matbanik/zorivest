---
name: Terminal Pre-Flight
description: Mandatory pre-flight checklist for terminal commands. Enforces the redirect-to-file pattern to prevent PowerShell buffer saturation and session hangs.
---

# Terminal Command Pre-Flight

**Trigger:** MUST be invoked before any `run_command` / terminal execution tool in an execution phase.

**Objective:** Prevent PowerShell buffer saturation and session hang by ensuring every command uses the redirect-to-file pattern.

## Pre-Flight Checklist

Satisfy ALL before every `run_command`:

- [ ] **Redirect check**: command ends with `*> <filepath>` (all-stream redirect)
- [ ] **Receipts dir**: output routed to `C:\Temp\zorivest\` (created automatically)
- [ ] **No-pipe check**: no `|` piping stdout of long-running process to a filter
- [ ] **Background flag**: if command may run >5s, use appropriate `WaitMsBeforeAsync`

> These items are the single source of truth — they match `AGENTS.md §PRIORITY 0` exactly.

## SOP: Standard Operating Procedure

Follow this 4-step sequence for every terminal command:

### Step 1 — Declare

State the intent: "I need to run `<tool>` to verify `<what>`."

### Step 2 — Formulate

Build the command using the redirect pattern:
```
<command> *> C:\Temp\zorivest\<name>.txt; Get-Content C:\Temp\zorivest\<name>.txt | Select-Object -Last <N>
```

### Step 3 — Execute + Detach

Run the command with `run_command`. Set `WaitMsBeforeAsync` appropriately:
- Quick commands (rg, Get-Content): 3000–5000ms
- Test suites (pytest, vitest): 5000–10000ms

### Step 4 — Consume Artifact

Read the output file. Do NOT poll the terminal interactively. If the command was sent to background, use `command_status` to check completion, then read the file.

## Per-Tool Command Table

> See `AGENTS.md §PRIORITY 0` for the authoritative redirect table. The table below is a cross-reference — do not maintain a separate copy.

| Tool | Redirect Command |
|------|------------------|
| `pytest` | `uv run pytest tests/ -x --tb=short -v *> C:\Temp\zorivest\pytest.txt; Get-Content C:\Temp\zorivest\pytest.txt \| Select-Object -Last 40` |
| `vitest` | `npx vitest run *> C:\Temp\zorivest\vitest.txt; Get-Content C:\Temp\zorivest\vitest.txt \| Select-Object -Last 40` |
| `pyright` | `uv run pyright packages/ *> C:\Temp\zorivest\pyright.txt; Get-Content C:\Temp\zorivest\pyright.txt \| Select-Object -Last 30` |
| `ruff` | `uv run ruff check packages/ *> C:\Temp\zorivest\ruff.txt; Get-Content C:\Temp\zorivest\ruff.txt \| Select-Object -Last 20` |
| `validate_codebase.py` | `uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate.txt; Get-Content C:\Temp\zorivest\validate.txt \| Select-Object -Last 50` |
| `git` | `git status *> C:\Temp\zorivest\git-status.txt; Get-Content C:\Temp\zorivest\git-status.txt` |

## Example Thought Process

```
Agent thinking:
"I need to run pytest to verify the Green phase.

Step 1 — Declare: I need to run pytest on tests/unit/test_calculator.py.
Step 2 — Formulate:
  uv run pytest tests/unit/test_calculator.py -x --tb=short -v *> C:\Temp\zorivest\pytest.txt; Get-Content C:\Temp\zorivest\pytest.txt | Select-Object -Last 40
Step 3 — Execute: [run_command with WaitMsBeforeAsync=8000]
Step 4 — Consume: Read the output. 12 passed, 0 failed. Green phase confirmed."
```

## Anti-Patterns (Never Do These)

```powershell
# ❌ Direct execution without redirect
uv run pytest tests/ -x --tb=short -v

# ❌ Piping to a filter
npx vitest run | Select-String "FAIL"

# ❌ Using 2>&1 instead of *>
uv run pyright packages/ 2>&1 | findstr "Error"
```

## When to Skip

This skill may be skipped ONLY for:
- `rg` searches (lightweight, no buffer risk)
- `Get-Content` / `Test-Path` (read-only, instant)
- `(Get-Content <file>).Count` (single-value output)

All other commands — especially pytest, vitest, pyright, ruff, npm, git — MUST use the redirect pattern.
