---
name: Git Workflow
description: Agent-safe git operations with SSH commit signing. Handles commit, push, and signing configuration to avoid interactive prompt hangs.
---

# Git Workflow Skill

## Problem

AI coding agents hang when running `git commit` because:
1. **GPG signing** launches `pinentry` which can't find a terminal in the agent's shell
2. **No `core.editor`** set — git opens vim/nano and waits for interactive input
3. **Credential prompts** — HTTPS auth can trigger interactive login

This skill provides agent-safe git commands and a one-time SSH signing setup.

## Prerequisites

- Git 2.34+ (SSH signing support) — verify: `git --version`
- OpenSSH installed — verify: `ssh -V`
- SSH key registered with GitHub/remote — verify: `ssh -T git@github.com`

## One-Time Setup: GPG → SSH Signing Migration

Run these commands **once** to switch from GPG to SSH signing. The agent should guide the user through these steps if SSH signing is not configured.

### Step 1: Check Current State

```powershell
# Check if SSH key exists
if (Test-Path ~/.ssh/id_ed25519.pub) { Write-Host "SSH key exists" } else { Write-Host "No SSH key — generate one" }

# Check current signing config
git config --global commit.gpgsign
git config --global gpg.format
git config --global user.signingkey
```

### Step 2: Generate SSH Key (if needed)

```powershell
# Generate ed25519 key (no passphrase for agent-safe automation)
// turbo
ssh-keygen -t ed25519 -C "banikm@gmail.com" -f "$HOME/.ssh/id_ed25519_signing" -N ""
```

> [!IMPORTANT]
> Use a **dedicated signing key** separate from your SSH authentication key (principle of least privilege). Name it `id_ed25519_signing` to distinguish it.

### Step 3: Configure Git for SSH Signing

```powershell
# Switch from GPG to SSH signing format
git config --global gpg.format ssh

# Point to the signing key
git config --global user.signingkey "$HOME/.ssh/id_ed25519_signing.pub"

# Enable automatic signing for all commits
git config --global commit.gpgsign true

# Also sign tags
git config --global tag.gpgsign true
```

### Step 4: Disable GPG (if previously configured)

```powershell
# Remove any GPG-specific config that might conflict
git config --global --unset gpg.program 2>$null
```

### Step 5: Register Key with GitHub

```powershell
# Display the public key for GitHub registration
Get-Content "$HOME/.ssh/id_ed25519_signing.pub"
```

Then add it to GitHub → Settings → SSH and GPG keys → **New SSH key** → Key type: **Signing Key**.

### Step 6: Verify

```powershell
# Test a signed commit
git commit --allow-empty -m "test: verify SSH signing" -S
git log --show-signature -1
```

## Agent-Safe Git Commands

### MUST ALWAYS use these patterns:

```powershell
# ✅ CORRECT: Always use -m flag (never open editor)
git commit -m "feat: description"

# ✅ CORRECT: Multi-line commit message
git commit -m "feat: short summary" -m "Detailed body paragraph."

# ✅ CORRECT: Stage and commit
git add -A && git commit -m "feat: description"

# ✅ CORRECT: Amend without editor
git commit --amend --no-edit

# ✅ CORRECT: Push (non-interactive with SSH remote)
git push origin main
```

### MUST NEVER use these patterns:

```powershell
# ❌ WRONG: Opens editor — WILL HANG
git commit

# ❌ WRONG: Opens editor for amend message
git commit --amend

# ❌ WRONG: Interactive rebase — WILL HANG
git rebase -i HEAD~3

# ❌ WRONG: Merge with editor — WILL HANG
git merge --no-ff branch-name
```

### Conditional Patterns:

```powershell
# ⚠️ Only if SSH signing is configured (otherwise hangs on GPG)
git commit -S -m "feat: signed commit"

# ⚠️ Only use git push if remote uses SSH (not HTTPS with credential prompt)
# Check: git remote get-url origin
# SSH format: git@github.com:user/repo.git ✅
# HTTPS format: https://github.com/user/repo.git ⚠️ may prompt
```

## Troubleshooting

### Commit hangs

1. **Check if GPG is the cause:**
   ```powershell
   git config --global commit.gpgsign
   # If "true" and gpg.format is not "ssh", GPG pinentry is the issue
   ```

2. **Quick fix — bypass signing for one commit:**
   ```powershell
   git commit --no-gpg-sign -m "feat: description"
   ```

3. **Check if editor is the cause:**
   ```powershell
   git config --global core.editor
   # If empty, git opens system default editor
   # Fix: git config --global core.editor "code --wait"
   ```

### Push hangs

1. **Check remote URL format:**
   ```powershell
   git remote get-url origin
   # Must be SSH format: git@github.com:user/repo.git
   # HTTPS may prompt for credentials
   ```

2. **Switch to SSH remote:**
   ```powershell
   git remote set-url origin git@github.com:USER/REPO.git
   ```

### Verification

```powershell
# Verify SSH signing is working
git log --show-signature -1

# Verify GitHub shows "Verified" badge
# Check: https://github.com/USER/REPO/commits
```

## Agent Workflow Integration

When the agent needs to commit, follow this sequence:

1. **Pre-commit:** `git status --short` — verify what will be committed
2. **Stage:** `git add -A` (or specific files)
3. **Commit:** `git commit -m "type: description"` — ALWAYS with `-m`
4. **Push:** `git push origin BRANCH`
5. **Verify:** `git log --oneline -1` — confirm commit landed

### Commit Message Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: new feature
fix: bug fix
docs: documentation only
test: adding/updating tests
refactor: code restructuring
chore: maintenance tasks
```

### When SSH Signing Is Not Yet Configured

If the agent detects that SSH signing is not configured (no `user.signingkey` or `gpg.format` ≠ `ssh`), it should:

1. **Inform the user** that SSH signing is recommended
2. **Offer to run the one-time setup** (Steps 1–6 above)
3. **Fall back to `--no-gpg-sign`** for the current commit if the user declines setup
