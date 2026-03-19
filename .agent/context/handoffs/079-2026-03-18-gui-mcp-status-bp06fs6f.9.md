---
meu: 46
slug: gui-mcp-status
phase: 6
priority: P0
status: ready_for_review
agent: antigravity
iteration: 1
files_changed: 4
tests_added: 19
tests_passing: 19
---

# MEU-46: GUI MCP Status

## Scope

MCP Server Status panel, IDE configuration generator, sidebar `data-testid` attributes, and MCP Guard controls in the Settings page. Gates E2E Wave 0. Implements build plan [06f §6f.9 MCP Server Status Panel](../../../docs/build-plan/06f-gui-settings.md).

## Feature Intent Contract

### Intent Statement
The Settings page shows real-time MCP server health (via REST), generates IDE configuration JSON, and provides MCP Guard lock/unlock controls. Sidebar navigation has proper `data-testid` attributes for E2E selectors.

### Acceptance Criteria

- AC-1 (Source: Human-approved): `McpServerStatusPanel` renders: backend status, version, DB status, guard state. Tool count and uptime show "N/A" (MCP-only, deferred to MEU-46a).
- AC-2 (Source: Spec): "Refresh Status" button re-fetches all REST data sources on demand
- AC-3 (Source: Spec): IDE Configuration section generates correct JSON for Cursor, Claude Desktop, and Windsurf
- AC-4 (Source: Spec): "Copy to Clipboard" button copies generated JSON via `navigator.clipboard.writeText()`
- AC-5 (Source: Spec): `NavRail` has `data-testid` attributes: `nav-accounts`, `nav-trades`, `nav-planning`, `nav-scheduling`, `nav-settings`
- AC-6 (Source: Spec): `SettingsLayout` renders `data-testid="settings-page"`, MCP Guard lock toggle (`mcp-guard-lock-toggle`), and status indicator (`mcp-guard-status`) via `GET/POST /api/v1/mcp-guard/*`
- AC-7 (Source: Spec): E2E Wave 0 tests pass against running app (deferred — requires Electron build + backend)

### Negative Cases

- Must NOT: attempt to fetch MCP-only data (toolset count, uptime) via REST — show N/A instead
- Must NOT: allow guard toggle without calling the correct REST endpoint

### Test Mapping

| Criterion | Test File | Test Function |
|-----------|-----------|---------------|
| AC-1 | `settings/__tests__/McpServerStatusPanel.test.tsx` | `should show backend status`, `version`, `database status`, `guard state`, `N/A for tool count and uptime` |
| AC-2 | `settings/__tests__/McpServerStatusPanel.test.tsx` | `should render Refresh Status button` |
| AC-3 | `settings/__tests__/McpServerStatusPanel.test.tsx` | `should generate correct JSON for Cursor`, `should switch IDE config when clicking Claude Desktop tab` |
| AC-4 | `settings/__tests__/McpServerStatusPanel.test.tsx` | `should copy JSON to clipboard` |
| AC-5 | `NavRail.tsx` source (data-testid attrs visible in code) |
| AC-6 | `settings/__tests__/McpServerStatusPanel.test.tsx` | `should render with data-testid=settings-page`, `MCP Guard status`, `lock toggle`, `toggle guard when clicking` |

## Design Decisions & Known Risks

- **Decision**: REST-only data sources; N/A for MCP-only fields — **Reasoning**: No REST proxy exists for MCP tools. MEU-46a will add proxy endpoints. N/A display with tooltip communicates the reason.
- **Decision**: Used `useQuery` + `useMutation` for guard controls — **Reasoning**: TanStack Query handles cache invalidation after lock/unlock mutation, keeping guard status in sync.
- **Risk**: E2E Wave 0 cannot be verified without a running Electron + Python backend. Unit tests cover component behavior; E2E execution deferred.

## Changed Files

| File | Action | Description |
|------|--------|-------------|
| `ui/src/renderer/src/features/settings/McpServerStatusPanel.tsx` | Created | Status panel, IDE config gen, copy-to-clipboard |
| `ui/src/renderer/src/features/settings/SettingsLayout.tsx` | Modified (rewrite) | MCP Guard controls (lock toggle, status indicator) + McpServerStatusPanel |
| `ui/src/renderer/src/components/layout/NavRail.tsx` | Modified | Added `data-testid` to 5 nav items |
| `ui/src/renderer/src/features/settings/__tests__/McpServerStatusPanel.test.tsx` | Created | 19 unit tests |

## Commands Executed

| Command | Result | Notes |
|---------|--------|-------|
| `npx vitest run src/renderer/src/features/settings/__tests__/McpServerStatusPanel.test.tsx` | PASS (19 tests) | All green |
| `npx vitest run` | PASS (92 tests, 10 files) | No regressions |
| `npx tsc --noEmit` | PASS | No type errors |

## FAIL_TO_PASS Evidence

| Test | Before | After |
|------|--------|-------|
| `should render status panel` | N/A (file didn't exist) | PASS |
| `should show backend status from /health` | N/A | PASS |
| `should show N/A for tool count and uptime` | N/A | PASS |
| `should generate correct JSON for Cursor` | N/A | PASS |
| `should copy JSON to clipboard` | N/A | PASS |
| `should render MCP Guard lock toggle` | FAIL (stub SettingsLayout) | PASS |
| `should toggle guard when clicking lock toggle` | FAIL | PASS |

---
## Codex Validation Report
{Left blank — Codex fills this section during validation-review workflow}
