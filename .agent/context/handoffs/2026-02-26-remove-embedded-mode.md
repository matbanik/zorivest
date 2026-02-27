# Remove Embedded Mode from Build Plan

## Task

- **Date:** 2026-02-26
- **Task slug:** remove-embedded-mode
- **Owner role:** coder
- **Scope:** Remove MCP "embedded mode" (MCP server inside Electron) from build plan docs
- **Status:** ✅ Complete

---

## Plan

### Goal

Remove the MCP "embedded mode" from the build plan. The MCP server will be standalone-only — a separate process that communicates with the Python API via HTTP. This eliminates 5 security risks identified in the [security assessment](2026-02-26-embedded-mode-security-risks.md).

> [!IMPORTANT]
> The GUI and MCP server can still run simultaneously. Both connect independently to the same Python REST API. Removing embedded mode only removes the *in-process* deployment — not the ability to use both at once.

### Proposed Changes

#### [MODIFY] [05-mcp-server.md](file:///p:/zorivest/docs/build-plan/05-mcp-server.md)

1. **Rename §5.7 heading** — `MCP Auth Bootstrap (Standalone Mode)` → `MCP Auth Bootstrap`
2. **Remove the Embedded Mode subsection** (lines 284-286)
3. **Add a design decision note** linking to the security assessment

#### [MODIFY] [input-index.md](file:///p:/zorivest/docs/build-plan/input-index.md)

1. Line 336: `MCP standalone mode` → `MCP auth`

#### [MODIFY] [04-rest-api.md](file:///p:/zorivest/docs/build-plan/04-rest-api.md)

1. Line 366: `MCP standalone mode` → `the MCP server`

---

## Walkthrough (Evidence)

### Files Modified

| File | Change |
|---|---|
| [05-mcp-server.md](file:///p:/zorivest/docs/build-plan/05-mcp-server.md) | Renamed §5.7 heading. Removed 3-line Embedded Mode subsection. Added design decision NOTE block linking to security assessment. |
| [input-index.md](file:///p:/zorivest/docs/build-plan/input-index.md) | Line 336: `MCP standalone mode` → `MCP auth` |
| [04-rest-api.md](file:///p:/zorivest/docs/build-plan/04-rest-api.md) | Line 366: `MCP standalone mode` → `the MCP server` |

### Diffs

**`05-mcp-server.md`:**
- §5.7 heading: `MCP Auth Bootstrap (Standalone Mode)` → `MCP Auth Bootstrap`
- §5.7 opening: `In standalone mode the MCP server must…` → `The MCP server must…`
- `### IDE Configuration (Standalone)` → `### IDE Configuration`
- `### Embedded Mode` (3 lines) → replaced with self-contained `> [!NOTE]` design decision block

**`input-index.md`:**
- Line 336: `Envelope encryption unlock — MCP standalone mode` → `Envelope encryption unlock — MCP auth`

**`04-rest-api.md`:**
- Line 366: `Database unlock endpoint for MCP standalone mode.` → `Database unlock endpoint for the MCP server.`

### Verification

- `rg -n "embedded.mode|standalone.mode|standalone-mode|mcp-auth-bootstrap-standalone" docs/build-plan/` → **0 results** ✅
- `rg -n "\.agent/context/handoffs" docs/build-plan/` → **0 results** ✅

### Motivation

See [embedded mode security risk assessment](2026-02-26-embedded-mode-security-risks.md) for the 5 risks that motivated this decision.
