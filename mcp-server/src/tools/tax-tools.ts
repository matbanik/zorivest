/**
 * Tax MCP tool stubs — 501 Not Implemented.
 *
 * Source: BUILD_PLAN.md §P2.5e MEU-TA3
 *
 * These tools are registered so they appear in toolset discovery
 * and return structured 501 errors instead of cryptic 404s.
 * Backend tax endpoints are not yet implemented.
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { withMetrics } from "../middleware/metrics.js";
import { withGuard } from "../middleware/mcp-guard.js";
import type { RegisteredToolHandle } from "../toolsets/registry.js";

// ── 501 stub response ──────────────────────────────────────────────────

const NOT_IMPLEMENTED_RESPONSE = {
    content: [
        {
            type: "text" as const,
            text: JSON.stringify({
                success: false,
                error: "501: Not Implemented — This tool is planned but not yet implemented.",
            }),
        },
    ],
};

/**
 * Register 501 stub handlers for all 4 tax tools.
 */
export function registerTaxTools(server: McpServer): RegisteredToolHandle[] {
    const handles: RegisteredToolHandle[] = [];

    // ── estimate_tax ─────────────────────────────────────────────────
    handles.push(server.registerTool(
        "estimate_tax",
        {
            description: "Estimate tax liability. (Not yet implemented)",
            inputSchema: {
                account_id: z.string().optional().describe("Filter by account"),
                period: z.string().default("ytd").describe("Time period"),
            },
            annotations: {
                readOnlyHint: true,
                destructiveHint: false,
                idempotentHint: true,
                openWorldHint: false,
            },
            _meta: {
                toolset: "tax",
                alwaysLoaded: false,
            },
        },
        withMetrics(
            "estimate_tax",
            withGuard(async (_params: unknown, _extra: unknown) => NOT_IMPLEMENTED_RESPONSE),
        ),
    ));

    // ── find_wash_sales ──────────────────────────────────────────────
    handles.push(server.registerTool(
        "find_wash_sales",
        {
            description: "Find wash sale violations. (Not yet implemented)",
            inputSchema: {
                account_id: z.string().optional().describe("Filter by account"),
            },
            annotations: {
                readOnlyHint: true,
                destructiveHint: false,
                idempotentHint: true,
                openWorldHint: false,
            },
            _meta: {
                toolset: "tax",
                alwaysLoaded: false,
            },
        },
        withMetrics(
            "find_wash_sales",
            withGuard(async (_params: unknown, _extra: unknown) => NOT_IMPLEMENTED_RESPONSE),
        ),
    ));

    // ── manage_lots ──────────────────────────────────────────────────
    handles.push(server.registerTool(
        "manage_lots",
        {
            description: "Manage tax lot assignments. (Not yet implemented)",
            inputSchema: {
                account_id: z.string().optional().describe("Filter by account"),
            },
            annotations: {
                readOnlyHint: false,
                destructiveHint: false,
                idempotentHint: false,
                openWorldHint: false,
            },
            _meta: {
                toolset: "tax",
                alwaysLoaded: false,
            },
        },
        withMetrics(
            "manage_lots",
            withGuard(async (_params: unknown, _extra: unknown) => NOT_IMPLEMENTED_RESPONSE),
        ),
    ));

    // ── harvest_losses ───────────────────────────────────────────────
    handles.push(server.registerTool(
        "harvest_losses",
        {
            description: "Identify tax-loss harvesting opportunities. (Not yet implemented)",
            inputSchema: {
                account_id: z.string().optional().describe("Filter by account"),
            },
            annotations: {
                readOnlyHint: true,
                destructiveHint: false,
                idempotentHint: true,
                openWorldHint: false,
            },
            _meta: {
                toolset: "tax",
                alwaysLoaded: false,
            },
        },
        withMetrics(
            "harvest_losses",
            withGuard(async (_params: unknown, _extra: unknown) => NOT_IMPLEMENTED_RESPONSE),
        ),
    ));

    return handles;
}
