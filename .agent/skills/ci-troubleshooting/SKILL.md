---
name: CI Troubleshooting
description: Diagnose GitHub Actions CI failures using the gh CLI. Handles PowerShell output truncation, log filtering, and common failure patterns for the Zorivest monorepo.
---

# CI Troubleshooting Skill

## Overview

Diagnose failing GitHub Actions runs using the `gh` CLI from a local PowerShell terminal. This skill addresses the specific pitfalls AI agents encounter when parsing CI logs — particularly **output truncation** in PowerShell and knowing which `gh` sub-commands to use in which order.

## Prerequisites

- `gh` CLI installed and authenticated (`gh auth status`)
- PowerShell terminal (Windows)
- Working directory: repository root (`p:\zorivest`)

## Diagnosis Workflow

Follow these steps **in order**. Each step narrows the problem before pulling large log volumes.

### Step 1: List Recent Runs

Get a quick overview of recent runs to find the failing one.

```powershell
gh run list --limit 5 --json databaseId,displayTitle,status,conclusion,headBranch
```

> **Output**: JSON array. Look for `"conclusion": "failure"` entries. Note the `databaseId`.

### Step 2: Get Run Summary

View the run overview to see which jobs passed/failed and their step-level status.

```powershell
gh run view <run-id>
```

> **Output**: Text summary with ✓/X per job and step names. Note the job IDs for failed jobs.

To view a specific failed job's steps:

```powershell
gh run view <run-id> --job <job-id>
```

### Step 3: Get Failed-Only Logs (Preferred First Attempt)

Use `--log-failed` for a focused view of just the failing steps:

```powershell
gh run view <run-id> --log-failed 2>&1 | Out-File -FilePath "$env:TEMP\ci_failed_log.txt" -Encoding utf8
```

Then read the file:

```
view_file $env:TEMP\ci_failed_log.txt
```

> [!IMPORTANT]
> **Always pipe to a temp file first.** Direct terminal capture of `gh run view --log` output gets **truncated** by the agent's terminal tool. The `run_command` tool captures limited output bytes, and `gh` logs can be thousands of lines. Piping to a file and then using `view_file` gives the complete, untruncated content.

### Step 4: Get Full Job Logs (If Needed)

If `--log-failed` doesn't provide enough context (e.g., you need to see what happened *before* the failure):

```powershell
gh run view <run-id> --job <job-id> --log 2>&1 | Out-File -FilePath "$env:TEMP\ci_full_log.txt" -Encoding utf8
```

### Step 5: Keyword-Filtered Quick Scan

For a rapid first-pass without downloading the full log:

```powershell
gh run view <run-id> --job <job-id> --log 2>&1 | Select-String -Pattern "FAIL|ERROR|error|DRIFT|exit code" | Select-Object -First 30
```

> **Caveat**: This is useful for a quick signal but may miss important context lines. Always follow up with the full log if the pattern matches aren't self-explanatory.

## Common Failure Patterns

### OpenAPI Spec Drift

**Symptom**: Quality Gate fails at "Check OpenAPI spec drift" with `OpenAPI spec DRIFT detected!`

**Cause**: API routes or Pydantic models in `packages/api/` were modified without regenerating the committed spec snapshot.

**Fix**:
```bash
uv run python tools/export_openapi.py -o openapi.committed.json
```
Then commit and push the updated file.

**When to run**: Any time files in `packages/api/` are created or modified (new endpoints, changed request/response models, renamed paths, updated status codes/tags).

### Python Type Errors (Pyright)

**Symptom**: Quality Gate fails at type check step with `pyright` errors.

**Diagnosis**: Look for lines containing `error:` in the pyright output section of the log. Note the file path and line number.

**Fix**: Address the type error in the indicated file. Run locally:
```bash
uv run pyright packages/
```

### Test Failures (Pytest)

**Symptom**: Quality Gate, MCP Server Tests, or UI Tests job fails with `FAILED` test names.

**Diagnosis**: Search the log for `FAILED` to get the test names, then `short test summary` for the concise error messages.

**Fix**: Run the failing test locally:
```bash
uv run pytest tests/path/to/test_file.py::test_name -v
```

### Lint Failures (Ruff)

**Symptom**: Quality Gate fails at lint step.

**Diagnosis**: Ruff errors include file:line:col and rule codes.

**Fix**:
```bash
uv run ruff check packages/ --fix   # auto-fix safe issues
uv run ruff check packages/         # verify remaining issues
```

### Semgrep Security Scan

**Symptom**: Quality Gate fails at Semgrep step with security findings.

**Diagnosis**: Look for `severity:` and `rule:` lines in the Semgrep output.

**Fix**: Address the specific security pattern flagged. If it's a false positive, add a `# nosemgrep: <rule-id>` comment.

## PowerShell Pitfalls for Agents

### Problem: Truncated Output

The `run_command` tool has a limited output buffer. GitHub Actions logs are routinely 200-500+ lines. When the agent reads `gh` output directly from the terminal, it gets truncated mid-line.

**Solution**: Always use the **file-pipe pattern**:
```powershell
<gh command> 2>&1 | Out-File -FilePath "$env:TEMP\<descriptive_name>.txt" -Encoding utf8
```
Then read with `view_file`. This guarantees the complete log.

### Problem: --jq Flag Quoting

PowerShell handles quotes differently from Bash. Complex `--jq` expressions with nested quotes fail silently or error out.

**Solution**: Skip `--jq` on PowerShell. Instead:
1. Use `--json <fields>` to get JSON output
2. Pipe to a temp file
3. Read and parse the JSON manually

```powershell
# Instead of: gh run view <id> --json jobs --jq ".jobs[] | ..."
# Do this:
gh run view <id> --json jobs | Out-File -FilePath "$env:TEMP\jobs.json" -Encoding utf8
```

### Problem: Both Run ID and Job ID Specified

When using `--job <id>`, `gh` ignores the run ID and emits a warning: `both run and job IDs specified; ignoring run ID`.

**Solution**: Use either form:
```powershell
gh run view <run-id>                    # run-level overview
gh run view <run-id> --job <job-id>     # job-level detail (run ID ignored but harmless)
```

## Structured Diagnosis Template

When asked to diagnose a CI failure, follow this reporting structure:

```markdown
## CI Diagnosis — Run [<run-id>](https://github.com/<owner>/<repo>/actions/runs/<run-id>)

| Job | Result |
|-----|--------|
| **Job Name** | ✅ Passed / ❌ Failed (duration) |

### Root Cause: <Category>

<Description of what failed and why>

### Fix

<Exact commands to run locally to fix the issue>
```

## GitHub Actions Jobs in This Repository

Reference for interpreting CI results:

| Job | What It Checks |
|-----|----------------|
| **Quality Gate** | Pyright types, Ruff lint, pytest, anti-placeholder scan, OpenAPI drift, Semgrep |
| **MCP Server Tests** | MCP server integration tests |
| **UI Tests** | Electron/GUI tests via Playwright |
