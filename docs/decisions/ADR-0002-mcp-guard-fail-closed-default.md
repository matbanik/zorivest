# ADR-0002: MCP Guard Fail-Closed Default on Network Error

> Status: accepted
> Date: 2026-03-09
> Deciders: Antigravity (agent) + Mat (human)

## Context

The MCP guard middleware (`withGuard`) checks `POST /api/v1/mcp-guard/check` before each guarded tool call. When that endpoint is unreachable (network error, backend down), two behaviors are plausible:

- **Fail-closed**: Block the tool call. Conservative — prevents runaway tool calls when the API is down, but locks users out of all guarded tools.
- **Fail-open**: Allow the tool call. Permissive — avoids locking users out, but risks uncontrolled tool execution without guard oversight.

No canonical build-plan document specifies which behavior to use. The planning workflow (`create-plan.md`) requires explicit human approval for behaviors not sourced from spec or local canon.

## Decision

**Default to fail-closed.** When `guardCheck()` encounters a network error, `withGuard()` blocks the tool call with an error message explaining the situation and suggesting remediation.

**Additionally**, create a GUI setting (deferred to Phase 6) that allows the user to toggle to fail-open mode. That setting must display a prominent warning about the risk of runaway tool calls without guard oversight.

## Consequences

### Positive
- Prevents uncontrolled tool execution when the backend is unavailable
- Conservative default aligns with circuit breaker patterns
- User retains the option to override via GUI when they understand the tradeoff

### Negative
- Users cannot use guarded MCP tools when the backend is temporarily unreachable
- Requires Phase 6 GUI work to implement the toggle

### Risks
- If the backend has intermittent connectivity issues, users may experience frequent tool blocks — mitigated by the GUI toggle option

## References

- Build plan section: [05-mcp-server.md §5.6](../build-plan/05-mcp-server.md)
- REST endpoint: [04g-api-system.md](../build-plan/04g-api-system.md) — `POST /api/v1/mcp-guard/check`
- Related ADRs: none
- Handoff: [critical-review](../../.agent/context/handoffs/2026-03-09-mcp-guard-metrics-discovery-plan-critical-review.md) — user approval recorded 2026-03-09
- Conversation: 53d0d1d4-af80-494f-b459-b2a61f5be866 (user message approving fail-closed + GUI toggle)
