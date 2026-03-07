# validate.ps1 — Zorivest Validation Pipeline
# Run this as a PHASE GATE when all MEUs in a phase are complete.
# For individual MEU work, use targeted checks (pytest/pyright/ruff scoped to touched packages).

$ErrorActionPreference = "Stop"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Zorivest Validation Pipeline" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# --- DETECT ACTIVE PHASE ---
# Gracefully skip checks for phases that don't exist yet

$hasPythonPkg = Test-Path "packages/"
$hasTypeScript = (Test-Path "mcp-server/") -or (Test-Path "ui/")

# --- BLOCKING CHECKS (must pass for active phases) ---

if ($hasPythonPkg) {
    Write-Host "=== [1/8] Python Type Check ===" -ForegroundColor Yellow
    uv run pyright packages/
    if ($LASTEXITCODE -ne 0) { Write-Host "❌ Python type check failed" -ForegroundColor Red; exit 1 }
    Write-Host "✅ Python types OK" -ForegroundColor Green
    Write-Host ""

    Write-Host "=== [2/8] Python Lint ===" -ForegroundColor Yellow
    uv run ruff check packages/
    if ($LASTEXITCODE -ne 0) { Write-Host "❌ Python lint failed" -ForegroundColor Red; exit 1 }
    Write-Host "✅ Python lint OK" -ForegroundColor Green
    Write-Host ""

    Write-Host "=== [3/8] Python Unit Tests ===" -ForegroundColor Yellow
    uv run pytest -x --tb=short -m "unit" -q
    if ($LASTEXITCODE -ne 0) { Write-Host "❌ Python unit tests failed" -ForegroundColor Red; exit 1 }
    Write-Host "✅ Python tests OK" -ForegroundColor Green
    Write-Host ""
}
else {
    Write-Host "⏭️  [1-3/8] Python checks skipped (no packages/ directory)" -ForegroundColor Gray
    Write-Host ""
}

if ($hasTypeScript) {
    Write-Host "=== [4/8] TypeScript Type Check ===" -ForegroundColor Yellow
    npx tsc --noEmit
    if ($LASTEXITCODE -ne 0) { Write-Host "❌ TypeScript type check failed" -ForegroundColor Red; exit 1 }
    Write-Host "✅ TypeScript types OK" -ForegroundColor Green
    Write-Host ""

    Write-Host "=== [5/8] TypeScript Lint ===" -ForegroundColor Yellow
    npx eslint src/ --max-warnings 0
    if ($LASTEXITCODE -ne 0) { Write-Host "❌ TypeScript lint failed" -ForegroundColor Red; exit 1 }
    Write-Host "✅ TypeScript lint OK" -ForegroundColor Green
    Write-Host ""

    Write-Host "=== [6/8] TypeScript Unit Tests ===" -ForegroundColor Yellow
    npx vitest run
    if ($LASTEXITCODE -ne 0) { Write-Host "❌ TypeScript unit tests failed" -ForegroundColor Red; exit 1 }
    Write-Host "✅ TypeScript tests OK" -ForegroundColor Green
    Write-Host ""
}
else {
    Write-Host "⏭️  [4-6/8] TypeScript checks skipped (no mcp-server/ or ui/ directory)" -ForegroundColor Gray
    Write-Host ""
}

Write-Host "=== [7/8] Anti-Placeholder Scan ===" -ForegroundColor Yellow
$placeholderDirs = @()
if (Test-Path "packages/") { $placeholderDirs += "packages/" }
if (Test-Path "src/") { $placeholderDirs += "src/" }
if (Test-Path "tests/") { $placeholderDirs += "tests/" }
if ($placeholderDirs.Count -gt 0) {
    $placeholderMatches = rg -c "TODO|FIXME|NotImplementedError" @placeholderDirs 2>$null
    if ($LASTEXITCODE -eq 0 -and $placeholderMatches) {
        Write-Host "❌ Unresolved placeholders found:" -ForegroundColor Red
        rg -n "TODO|FIXME|NotImplementedError" @placeholderDirs
        exit 1
    }
}
Write-Host "✅ No unresolved placeholders" -ForegroundColor Green
Write-Host ""

Write-Host "=== [8/8] Anti-Deferral Pattern Scan ===" -ForegroundColor Yellow
$deferralDirs = @()
if (Test-Path "packages/") { $deferralDirs += "packages/" }
if (Test-Path "src/") { $deferralDirs += "src/" }
if (Test-Path "tests/") { $deferralDirs += "tests/" }
if ($deferralDirs.Count -gt 0) {
    $deferralMatches = rg -c "pass\s+#\s*placeholder|\.\.\.?\s+#\s*placeholder|raise\s+NotImplementedError" @deferralDirs 2>$null
    if ($LASTEXITCODE -eq 0 -and $deferralMatches) {
        Write-Host "❌ Deferral patterns found:" -ForegroundColor Red
        rg -n "pass\s+#\s*placeholder|\.\.\.?\s+#\s*placeholder|raise\s+NotImplementedError" @deferralDirs
        exit 1
    }
}
Write-Host "✅ No deferral patterns" -ForegroundColor Green
Write-Host ""

# --- ADVISORY CHECKS (report only) ---

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Advisory Checks (non-blocking)" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

if ($hasPythonPkg) {
    Write-Host "=== Coverage Report ===" -ForegroundColor Yellow
    uv run pytest --cov=packages/core --cov-report=term -q 2>$null
    Write-Host ""

    Write-Host "=== Security Scan ===" -ForegroundColor Yellow
    uv run bandit -r packages/ -q 2>$null
    Write-Host ""
}
else {
    Write-Host "⏭️  Coverage and security scans skipped (no packages/)" -ForegroundColor Gray
    Write-Host ""
}

Write-Host "=== Evidence Bundle Check ===" -ForegroundColor Yellow
$latestHandoff = Get-ChildItem -Path ".agent/context/handoffs/" -Filter "*.md" -ErrorAction SilentlyContinue |
Where-Object { $_.Name -ne "README.md" -and $_.Name -ne "TEMPLATE.md" } |
Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($latestHandoff) {
    $content = Get-Content $latestHandoff.FullName -Raw
    $missingFields = @()
    # Support both legacy format (Evidence bundle location, Pass/fail matrix, Commands run)
    # and MEU handoff format (FAIL_TO_PASS Evidence, Commands Executed, Codex Validation Report)
    if ($content -notmatch "(Evidence bundle location|FAIL_TO_PASS Evidence)") { $missingFields += "Evidence/FAIL_TO_PASS" }
    if ($content -notmatch "(Pass/fail matrix|Commands Executed)") { $missingFields += "Pass-fail/Commands" }
    if ($content -notmatch "(Commands run|Codex Validation Report)") { $missingFields += "Commands/Codex Report" }
    if ($missingFields.Count -gt 0) {
        Write-Host "⚠️  Latest handoff ($($latestHandoff.Name)) missing evidence fields:" -ForegroundColor Yellow
        $missingFields | ForEach-Object { Write-Host "   - $_" -ForegroundColor Yellow }
    }
    else {
        Write-Host "✅ Evidence fields present in $($latestHandoff.Name)" -ForegroundColor Green
    }
}
else {
    Write-Host "ℹ️  No handoff files found (expected during early development)" -ForegroundColor Gray
}
Write-Host ""

# --- DONE ---

Write-Host "============================================" -ForegroundColor Green
Write-Host "  ✅ All blocking checks passed!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
