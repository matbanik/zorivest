#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Agent-safe git commit and push. Validates signing config, stages, commits, pushes.
.DESCRIPTION
    This script wraps the git commit workflow to prevent agent hangs from GPG/editor prompts.
    It validates SSH signing config before committing and provides clear error messages.
.PARAMETER Message
    The commit message (required). Use conventional commits format.
.PARAMETER Body
    Optional commit body for multi-line messages.
.PARAMETER Push
    If set, push to origin after commit. Default: true.
.PARAMETER Branch
    Branch to push to. Default: main.
.EXAMPLE
    .\agent-commit.ps1 -Message "feat: add new feature"
    .\agent-commit.ps1 -Message "feat: add feature" -Body "Detailed description" -Branch "dev"
    .\agent-commit.ps1 -Message "fix: correct bug" -Push:$false
#>
param(
    [Parameter(Mandatory=$true)]
    [string]$Message,

    [string]$Body = "",

    [bool]$Push = $true,

    [string]$Branch = "main"
)

$ErrorActionPreference = "Stop"

Write-Host "`n=== Agent-Safe Git Commit ===" -ForegroundColor Cyan

# ── Step 1: Validate signing config ──────────────────────────────────────
Write-Host "`n[1/6] Checking signing config..." -ForegroundColor Yellow

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
} else {
    Write-Host "  Signing: disabled (commits will be unsigned)" -ForegroundColor DarkYellow
}

# ── Step 2: Check remote URL ────────────────────────────────────────────
Write-Host "[2/6] Checking remote URL..." -ForegroundColor Yellow

$remoteUrl = git remote get-url origin 2>$null
if ($remoteUrl -match "^https://") {
    Write-Host "  WARNING: Remote uses HTTPS ($remoteUrl) — push may prompt for credentials." -ForegroundColor DarkYellow
} else {
    Write-Host "  Remote: OK ($remoteUrl)" -ForegroundColor Green
}

# ── Step 3: Show status ─────────────────────────────────────────────────
Write-Host "[3/6] Staging changes..." -ForegroundColor Yellow

git add -A
$status = git status --short
if (-not $status) {
    Write-Host "  Nothing to commit — working tree clean." -ForegroundColor DarkYellow
    exit 0
}
$fileCount = ($status -split "`n").Count
Write-Host "  Staged $fileCount file(s)" -ForegroundColor Green

# ── Step 4: Commit ──────────────────────────────────────────────────────
Write-Host "[4/6] Committing..." -ForegroundColor Yellow

if ($Body) {
    git commit -m $Message -m $Body
} else {
    git commit -m $Message
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: git commit failed with exit code $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}
Write-Host "  Committed successfully" -ForegroundColor Green

# ── Step 5: Push ────────────────────────────────────────────────────────
if ($Push) {
    Write-Host "[5/6] Pushing to origin/$Branch..." -ForegroundColor Yellow
    git push origin $Branch
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: git push failed with exit code $LASTEXITCODE" -ForegroundColor Red
        exit $LASTEXITCODE
    }
    Write-Host "  Pushed successfully" -ForegroundColor Green
} else {
    Write-Host "[5/6] Push skipped (--Push:false)" -ForegroundColor DarkYellow
}

# ── Step 6: Verify ──────────────────────────────────────────────────────
Write-Host "[6/6] Verifying..." -ForegroundColor Yellow

$lastCommit = git log --oneline -1
Write-Host "  Latest: $lastCommit" -ForegroundColor Green

Write-Host "`n=== Done ===" -ForegroundColor Cyan
