---
name: Git Workflow
description: Agent-safe git operations with SSH commit signing. Handles commit, push, and signing configuration to avoid interactive prompt hangs.
---

# Git Workflow Skill

## The One Rule

> **Run the script. Don't improvise git commands.**
>
> ```powershell
> # // turbo
> pwsh -File .agent/skills/git-workflow/scripts/agent-commit.ps1 -Message "feat: description"
> ```
>
> The script validates signing config, stages, commits, pushes, and verifies — all in one command.
> If you skip the script, you WILL cause a hang.

**Agent invocation rules:**
- Set `WaitMsBeforeAsync` to **30000** (push can take 10-20s on large changesets)
- If the command goes to background anyway, do NOT poll `command_status` — run `git log --oneline -1` directly to verify
- Never issue more than one `command_status` check; if it shows no output, the command finished and output was lost — verify the result instead

## Script Usage

```powershell
# Basic commit + push to main
# // turbo
pwsh -File .agent/skills/git-workflow/scripts/agent-commit.ps1 -Message "feat: add new feature"

# With body text
# // turbo
pwsh -File .agent/skills/git-workflow/scripts/agent-commit.ps1 -Message "feat: add feature" -Body "Detailed description here"

# Push to a different branch
# // turbo
pwsh -File .agent/skills/git-workflow/scripts/agent-commit.ps1 -Message "fix: correct bug" -Branch "dev"

# Commit without pushing
# // turbo
pwsh -File .agent/skills/git-workflow/scripts/agent-commit.ps1 -Message "wip: save progress" -Push $false
```

### What the Script Does (Do NOT Do These Manually)

1. ✅ Validates SSH signing config (fails fast if GPG would hang)
2. ✅ Checks remote URL format (warns on HTTPS)
3. ✅ Stages all changes (`git add -A`)
4. ✅ Commits with `-m` flag (never opens editor)
5. ✅ Pushes to origin (unless `-Push $false`)
6. ✅ Verifies with `git log --oneline -1`

## Agent Workflow Checklist

If you cannot use the script for any reason, copy this checklist and check off each step:

```
Git Commit Progress:
- [ ] Step 1: Check signing — `git config --global gpg.format` must be "ssh" (if gpgsign=true)
- [ ] Step 2: Check remote — `git remote get-url origin` (must be SSH, not HTTPS)
- [ ] Step 3: Status — `git status --short`
- [ ] Step 4: Stage — `git add -A`
- [ ] Step 5: Commit — `git commit -m "type: description"` (ALWAYS -m flag)
- [ ] Step 6: Push — `git push origin main`
- [ ] Step 7: Verify — `git log --oneline -1`
```

> [!CAUTION]
> **NEVER skip Step 1.** If `commit.gpgsign=true` and `gpg.format` is not `ssh`, the commit WILL hang waiting for GPG pinentry. Either fix the config or use `--no-gpg-sign`.

## Commit Message Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

| Prefix | Use |
|--------|-----|
| `feat:` | New feature |
| `fix:` | Bug fix |
| `docs:` | Documentation only |
| `test:` | Adding/updating tests |
| `refactor:` | Code restructuring |
| `chore:` | Maintenance tasks |

## Commands That WILL Hang (Never Use)

```powershell
git commit              # Opens editor
git commit --amend      # Opens editor
git rebase -i HEAD~3    # Interactive — opens editor
git merge --no-ff branch # Opens editor for merge message
```

## Troubleshooting

### Commit hangs

```powershell
# Quick fix — bypass signing for one commit:
git commit --no-gpg-sign -m "feat: description"
```

### Push hangs

```powershell
# Check remote format:
git remote get-url origin
# Must be: git@github.com:user/repo.git (SSH)
# Fix:     git remote set-url origin git@github.com:USER/REPO.git
```

## One-Time Setup: SSH Signing

Only needed if SSH signing is not already configured. Check first:

```powershell
git config --global gpg.format
# If output is "ssh" → already configured, skip this section
```

### Setup Steps

```powershell
# 1. Generate dedicated signing key
# // turbo
ssh-keygen -t ed25519 -C "banikm@gmail.com" -f "$HOME/.ssh/id_ed25519_signing" -N ""

# 2. Configure git
git config --global gpg.format ssh
git config --global user.signingkey "$HOME/.ssh/id_ed25519_signing.pub"
git config --global commit.gpgsign true
git config --global tag.gpgsign true

# 3. Remove old GPG config
git config --global --unset gpg.program 2>$null

# 4. Display key for GitHub registration
Get-Content "$HOME/.ssh/id_ed25519_signing.pub"
```

Then add to GitHub → Settings → SSH and GPG keys → **New SSH key** → Key type: **Signing Key**.
