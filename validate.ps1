# validate.ps1 — Zorivest Validation Pipeline
# Run this before every commit. All blocking checks must pass.

$ErrorActionPreference = "Stop"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Zorivest Validation Pipeline" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# --- BLOCKING CHECKS (must pass) ---

Write-Host "=== [1/6] Python Type Check ===" -ForegroundColor Yellow
pyright packages/
if ($LASTEXITCODE -ne 0) { Write-Host "❌ Python type check failed" -ForegroundColor Red; exit 1 }
Write-Host "✅ Python types OK" -ForegroundColor Green
Write-Host ""

Write-Host "=== [2/6] Python Lint ===" -ForegroundColor Yellow
ruff check packages/
if ($LASTEXITCODE -ne 0) { Write-Host "❌ Python lint failed" -ForegroundColor Red; exit 1 }
Write-Host "✅ Python lint OK" -ForegroundColor Green
Write-Host ""

Write-Host "=== [3/6] Python Unit Tests ===" -ForegroundColor Yellow
pytest tests/unit/ -q
if ($LASTEXITCODE -ne 0) { Write-Host "❌ Python unit tests failed" -ForegroundColor Red; exit 1 }
Write-Host "✅ Python tests OK" -ForegroundColor Green
Write-Host ""

Write-Host "=== [4/6] TypeScript Type Check ===" -ForegroundColor Yellow
npx tsc --noEmit
if ($LASTEXITCODE -ne 0) { Write-Host "❌ TypeScript type check failed" -ForegroundColor Red; exit 1 }
Write-Host "✅ TypeScript types OK" -ForegroundColor Green
Write-Host ""

Write-Host "=== [5/6] TypeScript Lint ===" -ForegroundColor Yellow
npx eslint src/ --max-warnings 0
if ($LASTEXITCODE -ne 0) { Write-Host "❌ TypeScript lint failed" -ForegroundColor Red; exit 1 }
Write-Host "✅ TypeScript lint OK" -ForegroundColor Green
Write-Host ""

Write-Host "=== [6/6] TypeScript Unit Tests ===" -ForegroundColor Yellow
npx vitest run
if ($LASTEXITCODE -ne 0) { Write-Host "❌ TypeScript unit tests failed" -ForegroundColor Red; exit 1 }
Write-Host "✅ TypeScript tests OK" -ForegroundColor Green
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

# --- DONE ---

Write-Host "============================================" -ForegroundColor Green
Write-Host "  ✅ All blocking checks passed!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
