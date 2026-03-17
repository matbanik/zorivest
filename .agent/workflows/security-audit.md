---
description: Run security scanning tools and review findings
---

# Security Audit Workflow

## Steps

### 1. Python security scan (Bandit)

```powershell
# turbo
uv run bandit -r packages/ -c pyproject.toml -q
```

Review any findings. Common false positives:
- `B101` (assert usage) — acceptable in tests
- `B603` (subprocess) — acceptable in controlled scripts

### 2. Python dependency audit

```powershell
# turbo
uv run pip-audit
```

If vulnerabilities found:
1. Check if a patched version exists: `uv lock --upgrade-package <package>`
2. If no patch available, document in `.agent/context/known-issues.md`

### 3. TypeScript dependency audit

```powershell
# turbo
cd mcp-server && npm audit --omit=dev
```

```powershell
# turbo
cd ui && npm audit --omit=dev
```

### 4. Log redaction audit

```powershell
# turbo
uv run pytest tests/security/test_log_redaction_audit.py -v
```

This test scans all logging calls across `packages/` for unredacted secrets (API keys, tokens, passwords).

### 5. Encryption integrity verification

```powershell
# turbo
uv run pytest tests/security/test_encryption_integrity.py -v
```

### 6. SAST scan (Semgrep)

```powershell
semgrep scan --config auto packages/ mcp-server/src/ ui/src/
```

> [!NOTE]
> Semgrep requires installation: `pip install semgrep` or use the GitHub Action in CI.

## Triage Guidelines

| Severity | Action | Timeline |
|----------|--------|----------|
| **Critical** (RCE, SQL injection, auth bypass) | Fix immediately, block release | Same session |
| **High** (XSS, SSRF, secret leak) | Create MEU, fix before next release | Next sprint |
| **Medium** (weak crypto, missing headers) | Document in known-issues | Scheduled |
| **Low** (informational, style) | Note in handoff, no action required | — |

## CI Integration

Security scans run automatically in CI (`.github/workflows/ci.yml`) with `continue-on-error: true` — they report findings without blocking the build. Critical findings should be escalated.
