#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Agent-safe git commit and push. Validates signing config, runs tests, stages, commits, pushes.
.DESCRIPTION
    This script wraps the git commit workflow to prevent agent hangs from GPG/editor prompts.
    It validates SSH signing config before committing, runs lint + tests, and provides clear error messages.
.PARAMETER Message
    The commit message (required). Use conventional commits format.
.PARAMETER Body
    Optional commit body for multi-line messages.
.PARAMETER NoPush
    Skip pushing to origin after commit. Default: push enabled.
.PARAMETER Branch
    Branch to push to. Default: main.
.PARAMETER SkipTests
    Skip the lint + test gate (for WIP commits). Default: false.
.EXAMPLE
    .\agent-commit.ps1 -Message "feat: add new feature"
    .\agent-commit.ps1 -Message "feat: add feature" -Body "Detailed description" -Branch "dev"
    .\agent-commit.ps1 -Message "fix: correct bug" -NoPush
    .\agent-commit.ps1 -Message "wip: save progress" -SkipTests -NoPush
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$Message,

    [string]$Body = "",

    [switch]$NoPush,

    [string]$Branch = "main",

    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"

Write-Host "`n=== Agent-Safe Git Commit ===" -ForegroundColor Cyan

# ── Step 1: Validate signing config ──────────────────────────────────────
Write-Host "`n[1/7] Checking signing config..." -ForegroundColor Yellow

$gpgSign = git config --global commit.gpgsign 2>$null
$gpgFormat = git config --global gpg.format 2>$null
$signingKey = git config --global user.signingkey 2>$null

if ($gpgSign -eq "true" -and $gpgFormat -ne "ssh") {
    Write-Host "ERROR: GPG signing is enabled but format is '$gpgFormat' (not 'ssh')." -ForegroundColor Red
    Write-Host "This WILL cause a hang. Fix with:" -ForegroundColor Red
    Write-Host "  git config --global gpg.format ssh" -ForegroundColor White
    Write-Host "  git config --global user.signingkey `"C:/Users/$env:USERNAME/.ssh/id_ed25519_signing.pub`"" -ForegroundColor White
    exit 1
}

if ($gpgSign -eq "true" -and $gpgFormat -eq "ssh") {
    if (-not $signingKey -or -not (Test-Path ($signingKey -replace '^~', $env:USERPROFILE))) {
        Write-Host "ERROR: SSH signing key not found at '$signingKey'." -ForegroundColor Red
        exit 1
    }
    Write-Host "  SSH signing: OK (key: $signingKey)" -ForegroundColor Green
}
else {
    Write-Host "  Signing: disabled (commits will be unsigned)" -ForegroundColor DarkYellow
}

# ── Step 2: Check remote URL ────────────────────────────────────────────
Write-Host "[2/7] Checking remote URL..." -ForegroundColor Yellow

$remoteUrl = git remote get-url origin 2>$null
if ($remoteUrl -match "^https://") {
    Write-Host "  WARNING: Remote uses HTTPS ($remoteUrl) — push may prompt for credentials." -ForegroundColor DarkYellow
}
else {
    Write-Host "  Remote: OK ($remoteUrl)" -ForegroundColor Green
}

# ── Step 3: Staging changes ─────────────────────────────────────────────
Write-Host "[3/7] Staging changes..." -ForegroundColor Yellow

git add -A
$status = git status --short
if (-not $status) {
    Write-Host "  Nothing to commit — working tree clean." -ForegroundColor DarkYellow
    exit 0
}
$fileCount = ($status -split "`n").Count
Write-Host "  Staged $fileCount file(s)" -ForegroundColor Green

# ── Step 4: Run lint + tests ────────────────────────────────────────────
if ($SkipTests) {
    Write-Host "[4/7] Lint + tests skipped (-SkipTests)" -ForegroundColor DarkYellow
}
else {
    Write-Host "[4/7] Running lint + tests..." -ForegroundColor Yellow

    # 4a: Ruff lint
    Write-Host "  [4a] Ruff lint..." -ForegroundColor Yellow
    $ruffOutput = uv run ruff check packages/ tests/ 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  FAILED: Ruff lint errors found:" -ForegroundColor Red
        Write-Host $ruffOutput -ForegroundColor Red
        Write-Host "`n  Fix with: uv run ruff check packages/ tests/ --fix" -ForegroundColor White
        exit 1
    }
    Write-Host "  Ruff: passed" -ForegroundColor Green

    # 4b: Unit tests
    Write-Host "  [4b] Unit tests..." -ForegroundColor Yellow
    $pytestOutput = uv run pytest tests/unit/ -x --tb=line -q 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  FAILED: Unit tests:" -ForegroundColor Red
        Write-Host $pytestOutput -ForegroundColor Red
        exit 1
    }
    Write-Host "  Unit tests: passed" -ForegroundColor Green
}

# ── Step 5: Commit ──────────────────────────────────────────────────────
Write-Host "[5/7] Committing..." -ForegroundColor Yellow

if ($Body) {
    git commit -m $Message -m $Body
}
else {
    git commit -m $Message
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: git commit failed with exit code $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}
Write-Host "  Committed successfully" -ForegroundColor Green

# ── Step 6: Push ────────────────────────────────────────────────────────
if (-not $NoPush) {
    Write-Host "[6/7] Pushing to origin/$Branch..." -ForegroundColor Yellow
    git push origin $Branch
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: git push failed with exit code $LASTEXITCODE" -ForegroundColor Red
        exit $LASTEXITCODE
    }
    Write-Host "  Pushed successfully" -ForegroundColor Green
}
else {
    Write-Host "[6/7] Push skipped (-NoPush)" -ForegroundColor DarkYellow
}

# ── Step 7: Verify ──────────────────────────────────────────────────────
Write-Host "[7/7] Verifying..." -ForegroundColor Yellow

$lastCommit = git log --oneline -1
Write-Host "  Latest: $lastCommit" -ForegroundColor Green

Write-Host "`n=== Done ===" -ForegroundColor Cyan
