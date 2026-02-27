# Embedded Mode Security Risk Assessment

## Task

- **Date:** 2026-02-26
- **Task slug:** embedded-mode-security-risks
- **Owner role:** guardrail
- **Scope:** Security risk analysis for MCP server embedded inside Electron GUI

---

## Context

Zorivest supports two MCP deployment modes:

| | Standalone Mode | Embedded Mode |
|---|---|---|
| **MCP runs in** | Separate Node.js process | Inside Electron GUI process |
| **Auth** | IDE sends API key → session token | GUI passphrase → inherited session |
| **Connects from** | External IDEs (Cursor, Antigravity) | Internal GUI + potentially external IDEs |

---

## 5 Identified Security Risks

### Risk 1: Shared Process Trust Boundary

- **Severity:** 🔴 High
- **Problem:** In embedded mode, MCP server and GUI share the same Electron process and memory space. A vulnerability in the MCP transport layer could access GUI state, including the decrypted session token and user data.
- **Standalone comparison:** Separate processes with separate memory — MCP exploit can't read GUI memory.
- **Mitigation:** Even in embedded mode, MCP server calls REST API via HTTP (not direct function calls). Data access goes through authenticated API, not raw memory. But the session token itself is in-process.
- **Residual risk:** Medium — the session token is the attack target, and it's in shared memory.

### Risk 2: IDE-Initiated Attacks on Embedded Server

- **Severity:** 🔴 High
- **Problem:** If the embedded MCP server also accepts connections from external IDEs, a malicious IDE extension or compromised MCP client could call destructive tools (`emergency_stop`, `create_trade`) using the GUI's pre-authenticated session. No API key exists to revoke — auth was via passphrase.
- **Standalone comparison:** External IDEs use scoped API keys; revoking the key disconnects the IDE without affecting the GUI.
- **Mitigation options:**
  - **Option A:** Don't expose embedded MCP to external clients. Embedded = GUI-only. External IDEs use standalone mode with own API key.
  - **Option B:** Require explicit user approval via GUI dialog ("Cursor wants to connect to Zorivest. Allow?")
- **Recommendation:** Option A — clean separation.

### Risk 3: MCP Guard Bypass in Embedded Mode

- **Severity:** 🟡 Medium
- **Problem:** The MCP Guard (rate limiting, emergency stop) protects against runaway agent behavior. In embedded mode, if GUI components bypass the guard (since they share the same process), a bug could make unguarded MCP calls.
- **Standalone comparison:** Guard always enforced — MCP server is the only caller.
- **Mitigation:** Enforce `withGuard()` middleware on all embedded MCP calls. Never expose unguarded tool handlers to the GUI even in shared process.

### Risk 4: Session Token Scope Inflation

- **Severity:** 🟡 Medium
- **Problem:** In standalone mode, the MCP session token may have limited scope (based on API key role). In embedded mode, the MCP inherits the GUI's full `owner` role — every MCP tool call has unrestricted privileges.
- **Standalone comparison:** API keys can be scoped to read-only or specific categories.
- **Mitigation:** Create a scoped MCP session token derived from the GUI session with restricted permissions. Aligns with the Safety Confirmation Adaptation pattern from the MCP architecture proposal.

### Risk 5: Electron Node.js Attack Surface

- **Severity:** 🟢 Low
- **Problem:** Embedding a Node.js MCP server inside Electron inherits all Electron Node.js security surface (prototype pollution, npm supply chain). MCP server dependencies become part of Electron's attack surface.
- **Standalone comparison:** Standalone MCP server's dependency vulnerabilities don't affect the GUI.
- **Mitigation:** Standard Electron hardening: `nodeIntegration: false`, `contextIsolation: true`, minimal npm dependencies. Regular dependency audits.

---

## Risk Summary Matrix

| Risk | Standalone | Embedded | Delta |
|---|---|---|---|
| Process isolation | ✅ Separate | ❌ Shared | Worse |
| Auth model | API key → scoped token | Passphrase → full owner | Wider scope |
| External IDE access | Built-in, scoped | ⚠️ Must be explicitly gated | Risk if ungated |
| MCP Guard enforcement | Always enforced | Must ensure never bypassed | Requires discipline |
| Dependency surface | Isolated | Merged with Electron | Slightly worse |

---

## Recommendation

**If embedded mode is retained:** Implement Option A (GUI-only, no external IDE connections). This eliminates Risk 2 entirely and reduces Risk 4 impact. Combined with `withGuard()` enforcement, residual risk is acceptable.

**Alternative:** Remove embedded mode entirely. See separate analysis on trade-offs of GUI-only architecture.
