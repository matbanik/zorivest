# validate.ps1 — Zorivest Validation Pipeline
# Run this before every commit. All blocking checks must pass.

$ErrorActionPreference = "Stop"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Zorivest Validation Pipeline" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# --- BLOCKING CHECKS (must pass) ---

Write-Host "=== [1/8] Python Type Check ===" -ForegroundColor Yellow
pyright packages/
if ($LASTEXITCODE -ne 0) { Write-Host "❌ Python type check failed" -ForegroundColor Red; exit 1 }
Write-Host "✅ Python types OK" -ForegroundColor Green
Write-Host ""

Write-Host "=== [2/8] Python Lint ===" -ForegroundColor Yellow
ruff check packages/
if ($LASTEXITCODE -ne 0) { Write-Host "❌ Python lint failed" -ForegroundColor Red; exit 1 }
Write-Host "✅ Python lint OK" -ForegroundColor Green
Write-Host ""

Write-Host "=== [3/8] Python Unit Tests ===" -ForegroundColor Yellow
pytest packages/core/tests -q
if ($LASTEXITCODE -ne 0) { Write-Host "❌ Python unit tests failed" -ForegroundColor Red; exit 1 }
Write-Host "✅ Python tests OK" -ForegroundColor Green
Write-Host ""

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

Write-Host "=== [7/8] Anti-Placeholder Scan ===" -ForegroundColor Yellow
$placeholderDirs = @()
if (Test-Path "packages/") { $placeholderDirs += "packages/" }
if (Test-Path "src/") { $placeholderDirs += "src/" }
if ($placeholderDirs.Count -gt 0) {
    $matches = rg -c "TODO|FIXME|NotImplementedError" @placeholderDirs 2>$null
    if ($LASTEXITCODE -eq 0 -and $matches) {
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

Write-Host "=== Coverage Report ===" -ForegroundColor Yellow
pytest --cov=packages/core --cov-report=term -q 2>$null
Write-Host ""

Write-Host "=== Security Scan ===" -ForegroundColor Yellow
bandit -r packages/ -q 2>$null
Write-Host ""

Write-Host "=== Evidence Bundle Check ===" -ForegroundColor Yellow
$latestHandoff = Get-ChildItem -Path ".agent/context/handoffs/" -Filter "2*.md" -ErrorAction SilentlyContinue |
    Sort-Object Name -Descending | Select-Object -First 1
if ($latestHandoff) {
    $content = Get-Content $latestHandoff.FullName -Raw
    $missingFields = @()
    if ($content -notmatch "Evidence bundle location:\s*\S") { $missingFields += "Evidence bundle location" }
    if ($content -notmatch "Pass/fail matrix:\s*\S") { $missingFields += "Pass/fail matrix" }
    if ($content -notmatch "Commands run:\s*\S") { $missingFields += "Commands run" }
    if ($missingFields.Count -gt 0) {
        Write-Host "⚠️  Latest handoff ($($latestHandoff.Name)) missing evidence fields:" -ForegroundColor Yellow
        $missingFields | ForEach-Object { Write-Host "   - $_" -ForegroundColor Yellow }
    } else {
        Write-Host "✅ Evidence fields present in $($latestHandoff.Name)" -ForegroundColor Green
    }
} else {
    Write-Host "ℹ️  No handoff files found (expected during early development)" -ForegroundColor Gray
}
Write-Host ""

# --- DONE ---

Write-Host "============================================" -ForegroundColor Green
Write-Host "  ✅ All blocking checks passed!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
