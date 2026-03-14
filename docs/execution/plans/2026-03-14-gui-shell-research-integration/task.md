# GUI Shell Research Integration — Task List

## Phase A: Pre-Build Research Deliverables

### Task 1 — Create feature scope for GUI shell MEU-43/44/45
- **owner_role:** orchestrator
- **Deliverable:** `docs/research/gui-shell-foundation/scope.md`
- **Status:** `done`
- **Validation:**
```powershell
Test-Path docs\research\gui-shell-foundation\scope.md
# Expected: True
```

### Task 2 — Consolidate architecture patterns from 3 model research outputs
- **owner_role:** researcher
- **Deliverable:** `docs/research/gui-shell-foundation/patterns.md`
- **Status:** `done`
- **Validation:**
```powershell
Test-Path docs\research\gui-shell-foundation\patterns.md
# Expected: True
rg "Research-backed|Local Canon|Spec|Human-approved" docs\research\gui-shell-foundation\patterns.md
# Expected: ≥1 match
```

### Task 3 — Create AI instruction set for GUI shell implementation
- **owner_role:** coder
- **Deliverable:** `docs/research/gui-shell-foundation/ai-instructions.md`
- **Status:** `done`
- **Validation:**
```powershell
Test-Path docs\research\gui-shell-foundation\ai-instructions.md
# Expected: True
rg "Research-backed|Local Canon|Spec|Human-approved" docs\research\gui-shell-foundation\ai-instructions.md
# Expected: ≥1 match
```

### Task 4 — Document technology decisions with rationale and version locks
- **owner_role:** orchestrator
- **Deliverable:** `docs/research/gui-shell-foundation/decision.md`
- **Status:** `done`
- **Validation:**
```powershell
Test-Path docs\research\gui-shell-foundation\decision.md
# Expected: True
```

### Task 5 — Validate and finalize Zorivest-adapted style guide
- **owner_role:** orchestrator
- **Deliverable:** `docs/research/gui-shell-foundation/style-guide-zorivest.md`
- **Status:** `done`
- **Validation:**
```powershell
Test-Path docs\research\gui-shell-foundation\style-guide-zorivest.md
# Expected: True (pre-created during research phase)
```

### Task 6 — Save research brief to pomera notes
- **owner_role:** orchestrator
- **Deliverable:** Pomera note ID logged
- **Status:** `done`
- **Validation:**
```powershell
# Run via MCP: pomera_notes search "gui-shell"
# Expected: ≥1 result
```

---

## Phase B: Build Plan Document Updates

### Task 7 — Update Phase 6 npm install commands with full stack
- **owner_role:** coder
- **Deliverable:** `docs/build-plan/dependency-manifest.md` modified
- **Status:** `done`
- **Validation:**
```powershell
rg "zustand|@tanstack/react-router|react-hook-form|electron-vite|tailwindcss|babel-plugin-react-compiler" docs\build-plan\dependency-manifest.md
# Expected: 6 matches
```

### Task 8 — Replace React Router example with TanStack Router + reconcile route map
- **owner_role:** coder
- **Deliverable:** `docs/build-plan/06-gui.md` modified
- **Status:** `done`
- **Validation:**
```powershell
rg "React\.lazy|<Routes|<Route " docs\build-plan\06-gui.md
# Expected: 0 matches
```

### Task 9 — Add 8 architectural subsections + reconcile command registry routes
- **owner_role:** coder
- **Deliverable:** `docs/build-plan/06a-gui-shell.md` modified
- **Status:** `done`
- **Validation:**
```powershell
rg -i "bearer|ephemeral|nonce" docs\build-plan\06a-gui-shell.md
# Expected: ≥1 match
rg "navigate\('/planning'|navigate\('/scheduling'|navigate\('/trades'|navigate\('/settings'" docs\build-plan\06a-gui-shell.md
# Expected: ≥4 matches
```

### Task 10 — Update security contract to reflect ephemeral Bearer token
- **owner_role:** coder
- **Deliverable:** `.agent/docs/architecture.md` modified
- **Status:** `done`
- **Validation:**
```powershell
rg -i "No authentication needed" .agent\docs\architecture.md
# Expected: 0 matches
rg -i "bearer|ephemeral" .agent\docs\architecture.md
# Expected: ≥1 match
```

---

## Phase C: Verification

### Task 11 — Run automated consistency checks
- **owner_role:** tester
- **Deliverable:** Console output showing 0 orphaned refs
- **Status:** `done`
- **Validation:**
```powershell
# Check 1: No orphaned react-router references
rg -i "react-router-dom|BrowserRouter|HashRouter" docs\build-plan\06-gui.md docs\build-plan\06a-gui-shell.md
# Expected: 0 matches

# Check 2: All 5 research deliverables exist
Get-ChildItem docs\research\gui-shell-foundation\
# Expected: 5 files

# Check 3: All required packages in dependency manifest
rg "zustand|@tanstack/react-router|react-hook-form|electron-vite|tailwindcss|babel-plugin-react-compiler" docs\build-plan\dependency-manifest.md
# Expected: 6 matches

# Check 4: No orphaned React Router JSX patterns
rg "React\.lazy|<Routes|<Route " docs\build-plan\06-gui.md
# Expected: 0 matches

# Check 5: Security section in both files
rg -i "bearer|ephemeral|nonce" docs\build-plan\06a-gui-shell.md .agent\docs\architecture.md
# Expected: ≥2 matches

# Check 6: Stale route paths absent from command registry
rg "navigate\('/plans'|navigate\('/schedules'|navigate\('/accounts'|navigate\('/reports'|navigate\('/watchlists'" docs\build-plan\06a-gui-shell.md
# Expected: 0 matches

# Check 7: No authentication contradiction
rg -i "No authentication needed" .agent\docs\architecture.md
# Expected: 0 matches
```

### Task 12 — Submit to Codex for adversarial re-review
- **owner_role:** reviewer
- **Deliverable:** Codex verdict = `approved` or `changes_required`
- **Status:** `done`
- **Validation:**
```powershell
Get-ChildItem .agent\context\handoffs\ -Filter "*gui-shell-research-integration*"
# Expected: ≥1 file
Select-String -Path .agent\context\handoffs\2026-03-14-gui-shell-research-integration-implementation-critical-review.md -Pattern "verdict"
# Expected: ≥1 match
```
