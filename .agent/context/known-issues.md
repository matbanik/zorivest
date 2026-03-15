# Known Issues — Zorivest

> Track bugs, limitations, and workarounds here.

## Active Issues

### [MCP-TOOLCAP] — IDE tool limits render 68-tool flat registration non-viable
- **Severity:** Critical
- **Component:** mcp-server
- **Discovered:** 2026-03-04 (pre-mortem research)
- **Status:** Mitigated by Design
- **Details:** Cursor enforces 40-tool hard cap (silently drops 28 tools). ChatGPT has 5,000-token definition cap (~10 tools). LLM accuracy degrades above ~20 tools. See `friction-inventory.md` FR-3.x, FR-10.x.
- **Workaround:** Three-tier strategy: static ≤40 for Cursor, dynamic toolsets for VS Code, full for CLI/API. Client detection via `clientInfo.name` (§5.11).

### [MCP-ZODSTRIP] — `server.tool()` silently strips arguments with z.object()
- **Severity:** Critical
- **Component:** mcp-server
- **Discovered:** 2026-03-04 (pre-mortem research)
- **Status:** Open — upstream SDK bug
- **Details:** Passing `z.object({...})` instead of raw Zod shape causes tool to register with empty parameters. No error, no warning. TS-SDK #1291, #1380, PR #1603. See `friction-inventory.md` FR-1.1.
- **Workaround:** Enforce raw shape convention. Add startup assertion that every tool has non-empty `inputSchema.properties`.

### [MCP-AUTHRACE] — Token refresh race condition under concurrent tool execution
- **Severity:** Critical
- **Component:** mcp-server
- **Discovered:** 2026-03-04 (pre-mortem research)
- **Status:** Open — needs architectural mitigation
- **Details:** Concurrent 401s trigger overlapping refresh requests. No MCP client reliably handles token lifecycle. See `friction-inventory.md` FR-4.1, FR-4.7.
- **Workaround:** In-memory mutex for refresh; proactive JWT expiry check before each REST call.

### [MCP-WINDETACH] — Node.js `detached: true` broken on Windows since 2016
- **Severity:** Critical
- **Component:** infrastructure
- **Discovered:** 2026-03-04 (pre-mortem research)
- **Status:** Open — upstream Node.js bug
- **Details:** `child_process.fork()` with `detached: true` does not work on Windows. Node #5146, #36808. Orphaned processes leave SQLCipher locks. See `friction-inventory.md` FR-9.1.
- **Workaround:** Windows Job Objects for process group management. Platform-specific spawn logic.

### [MCP-HTTPBROKEN] — Streamable HTTP transport has 5 failure modes
- **Severity:** High
- **Component:** mcp-server
- **Discovered:** 2026-03-04 (pre-mortem research)
- **Status:** Mitigated by Design (stdio primary)
- **Details:** Stateless mode broken (#340), async timeouts (#1106), cross-client data leak (GHSA-345p), SSE disconnects (#1211), EPIPE crash (#1564). See `friction-inventory.md` FR-6.x.
- **Workaround:** Use stdio as primary transport. Pin SDK version. Never use stateless mode.

### [UI-ESMSTORE] — electron-store v9+ (ESM-only) crashes electron-vite main process
- **Severity:** Medium
- **Component:** ui
- **Discovered:** 2026-03-14
- **Status:** Workaround Applied (pinned to v8)
- **Details:** `electron-store` v9+ is `"type": "module"` (ESM-only). electron-vite compiles the main process as CJS, so `import Store from 'electron-store'` resolves to `{ default: [class] }` instead of the class — `new Store()` throws `"Store is not a constructor"`. The app crashes before the window opens.
- **Workaround:** Pinned to `electron-store@8` (last CJS version). Same API (`new Store()`, `.get()`, `.set()`), zero code changes. Upgrade back to v10 when electron-vite adds native ESM output for the main process.

## Template

When adding issues, use this format:

```markdown
### [SHORT-TITLE] — Brief description
- **Severity:** Critical / High / Medium / Low
- **Component:** core / infrastructure / api / ui / mcp-server
- **Discovered:** YYYY-MM-DD
- **Status:** Open / In Progress / Workaround Applied
- **Details:** What happens, how to reproduce
- **Workaround:** (if any)
```
