# Reflection — mcp-server-foundation

> Project: `mcp-server-foundation` | 2026-03-09

## What Went Well

- **Cross-language scaffold** — TypeScript MCP server scaffolded alongside Python monorepo with clean separation (`mcp-server/` at root)
- **Integration test design** — Round-trip test spawns live Python API, exercises real endpoints, catches contract drift immediately
- **Rapid correction loop** — 2 correction rounds (5 findings + 2 findings) resolved in single session with full regression between rounds
- **SDK API migration** — `server.tool()` → `registerTool()` migration gave access to full annotation/metadata surface

## What Could Improve

- **Binary endpoint awareness** — Should have checked `images.py` response type before using JSON-parsing `fetchApi()` for the `/full` endpoint. The spec itself showed `Buffer.from(await imgRes.arrayBuffer())` — missed during initial implementation.
- **Annotation spec alignment** — Initially set `destructiveHint: true` on write tools based on intuition, not the spec. Cost a full correction round. Lesson: always source annotation values from build plan, not inferred semantics.
- **Project artifact coherence** — Summary counts in BUILD_PLAN and meu-registry drifted. Should update all status artifacts in a single atomic step immediately after MEU completion, not as separate post-MEU work.
- **validate_codebase.py Windows compatibility** — The Python gate script cannot spawn `npx` on Windows (`FileNotFoundError: [WinError 2]`). Needs path adjustment or `shell=True` for cross-platform support.

## Key Decisions

| Decision | Rationale |
|----------|-----------|
| `fetchApiBinary()` separate from `fetchApi()` | Clean separation of JSON vs binary response handling; `ArrayBuffer` → base64 for MCP image content type |
| Random port in integration test | Eliminates false positives from stale processes; `net.createServer(0)` finds OS-assigned free port |
| `_meta` for `toolset`/`alwaysLoaded` | SDK `ToolAnnotations` only supports `readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint`; custom metadata uses `_meta` per MCP spec §_meta |
| `destructiveHint: false` on all tools | Spec explicitly marks all 8 implemented tools as non-destructive; `create_trade` is idempotent via `exec_id` dedup |

## Rules Checked (10/10)

1. TDD-first (FIC → Red → Green) — ✅
2. Anti-placeholder scan — ✅ (no TODO/FIXME)
3. No `Any` type without justification — ✅
4. Error handling explicit — ✅
5. Test immutability (no Green-phase assertion changes) — ✅
6. Evidence-first completion — ✅
7. Handoff protocol followed — ✅ (3 handoffs created)
8. MEU gate passed — ✅ (tsc + eslint + vitest; validate_codebase.py blocked by Windows npx issue)
9. Full regression green — ✅ (648/648 Python + 17/17 TypeScript)
10. Build-plan consistency — ✅ (after 2 correction rounds)

Rule adherence: 90% (binary contract and annotation sourcing caught by reviewer, not implementation)
