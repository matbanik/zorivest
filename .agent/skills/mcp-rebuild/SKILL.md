---
name: MCP Server Rebuild
description: Canonical commands for rebuilding the Zorivest MCP server and notifying
  the user to restart Antigravity IDE for live testing.
---

# MCP Server Rebuild Skill

## When to Use

- After modifying MCP server source code (`mcp-server/`)
- After adding/changing compound tool definitions
- Before running live API validation (Phase 3a audit)
- When `zorivest_system(action:"diagnose")` reports stale tool count

## Build Commands

```powershell
# Build the MCP server (redirect-to-file pattern per AGENTS.md §P0)
cd mcp-server; npm run build *> C:\Temp\zorivest\mcp-build.txt; Get-Content C:\Temp\zorivest\mcp-build.txt | Select-Object -Last 20
```

### Build Failure Troubleshooting

| Symptom | Fix |
|---------|-----|
| `Cannot find module` | Run `npm install` first |
| TypeScript type errors | Run `npx tsc --noEmit` to get full error list |
| Missing tool registration | Check `src/tools/index.ts` exports |

## Restart Notification Protocol

After a successful build, emit this message to the user:

> **⚠️ MCP server rebuilt.** Please restart Antigravity to pick up changes, then confirm when ready.

**Do NOT proceed with any MCP tool calls until the user confirms restart.**

## Post-Restart Verification

After the user confirms restart:

```
# 1. Verify MCP server connectivity
zorivest_system(action: "diagnose")
→ Check: mcp_server.connected = true

# 2. Verify tool count
zorivest_system(action: "toolsets_list")
→ Check: total tool count matches expected

# 3. Quick smoke test
zorivest_market(action: "providers")
→ Check: returns configured provider list
```

## Live API Testing Checklist

For each configured provider, run the following sequence:

```
# Step 1: Health check
zorivest_market(action: "test_provider", provider_name: "{name}")
→ Record: pass/fail, response_time, error

# Step 2: Data type validation (per ProviderCapabilities)
zorivest_market(action: "quote", ticker: "AAPL")          # if quote supported
zorivest_market(action: "ohlcv", ticker: "AAPL")           # if ohlcv supported
zorivest_market(action: "news", ticker: "AAPL")             # if news supported
# ... etc. for each supported data type

# Step 3: Validate response shape
→ Check: response contains expected DTO fields
→ Check: no 4xx/5xx errors
→ Record: provider, data_type, status, response_time
```

## Quick Reference

| Step | Command/Action | Wait For |
|------|---------------|----------|
| 1. Build | `cd mcp-server; npm run build` | Build output |
| 2. Notify | "Please restart Antigravity" | User confirmation |
| 3. Diagnose | `zorivest_system(action:"diagnose")` | Connected = true |
| 4. Verify tools | `zorivest_system(action:"toolsets_list")` | Tool count correct |
| 5. Smoke test | `zorivest_market(action:"providers")` | Provider list |
| 6. Live test | Per-provider health + data checks | All configured pass |

## Integration with MCP Audit

This skill is a prerequisite for **Phase 3a: Provider API Validation** in the
[mcp-audit workflow](../../workflows/mcp-audit.md). Run the full rebuild cycle
before starting audit Phase 3a.
