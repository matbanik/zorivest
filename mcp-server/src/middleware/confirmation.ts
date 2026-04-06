/**
 * Confirmation middleware for destructive operations.
 *
 * Implements a self-contained MCP-layer 2-step confirmation gate:
 * 1. `createConfirmationToken(action)` generates a crypto-random token (60s TTL)
 * 2. `withConfirmation()` validates token against the store (existence + TTL + action)
 *
 * On dynamic/anthropic clients, confirmation is handled by the IDE and this
 * middleware passes through.
 *
 * Source: 05-mcp-server.md §5.13 L877-889, §5.14 L964
 * MEU: 42 (toolset-registry)
 */

import { randomBytes } from "node:crypto";
import type { ClientMode } from "../client-detection.js";

// ── Module state ───────────────────────────────────────────────────────

let confirmationRequired = false; // Default to pass-through; set to true by setConfirmationMode("static")

/** Destructive tools that require confirmation on static clients */
const DESTRUCTIVE_TOOLS = new Set([
    "zorivest_emergency_stop",
    "create_trade",
    "delete_trade",
    "delete_account",
    "reassign_trades",
    "sync_broker",
    "disconnect_market_provider",
    "zorivest_service_restart",
]);

// ── Token store ────────────────────────────────────────────────────────

interface StoredToken {
    action: string;
    expiresAt: number;
}

const TOKEN_TTL_MS = 60_000; // 60 seconds
const tokenStore = new Map<string, StoredToken>();

/**
 * Check whether a tool name is in the MCP destructive-tools list.
 */
export function isDestructiveTool(name: string): boolean {
    return DESTRUCTIVE_TOOLS.has(name);
}

/**
 * Generate a time-limited confirmation token for a destructive action.
 * Token is stored in-memory with 60s TTL. Returns the token string.
 *
 * Throws if the action is not a recognized destructive tool.
 */
export function createConfirmationToken(action: string): {
    token: string;
    expires_in_seconds: number;
} {
    if (!DESTRUCTIVE_TOOLS.has(action)) {
        throw new Error(`Unknown destructive action: ${action}`);
    }

    // Purge expired tokens opportunistically
    const now = Date.now();
    for (const [tok, entry] of tokenStore) {
        if (entry.expiresAt <= now) {
            tokenStore.delete(tok);
        }
    }

    const token = `ctk_${randomBytes(16).toString("hex")}`;
    tokenStore.set(token, {
        action,
        expiresAt: now + TOKEN_TTL_MS,
    });

    return { token, expires_in_seconds: 60 };
}

/**
 * Validate a confirmation token. Consumes the token on success (single-use).
 * Returns true if valid, false otherwise.
 */
function validateToken(token: string, expectedAction: string): boolean {
    const entry = tokenStore.get(token);
    if (!entry) return false;
    if (entry.expiresAt <= Date.now()) {
        tokenStore.delete(token);
        return false;
    }
    if (entry.action !== expectedAction) return false;

    // Single-use: consume the token
    tokenStore.delete(token);
    return true;
}

// ── Configuration ──────────────────────────────────────────────────────

/**
 * Set confirmation mode based on detected client mode.
 * Static → confirmation required; dynamic/anthropic → pass-through.
 */
export function setConfirmationMode(mode: ClientMode): void {
    confirmationRequired = mode === "static";
}

// ── Middleware ──────────────────────────────────────────────────────────

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type ToolHandler = (params: any, extra: any) => Promise<{ content: any[];[key: string]: unknown }>;

/**
 * Wrap a tool handler with confirmation logic.
 *
 * On static clients, destructive tools require a valid `confirmation_token`
 * that was issued by `createConfirmationToken()`. The token must match the
 * tool name and not be expired. On dynamic/anthropic clients, the handler
 * is called directly.
 */
export function withConfirmation(
    toolName: string,
    handler: ToolHandler,
): ToolHandler {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    return async (params: any, extra: any) => {
        // Non-destructive tools always pass through
        if (!DESTRUCTIVE_TOOLS.has(toolName)) {
            return handler(params, extra);
        }

        // On dynamic/anthropic clients, pass through (IDE handles confirmation)
        if (!confirmationRequired) {
            return handler(params, extra);
        }

        // Static clients: require valid confirmation_token
        if (!params.confirmation_token) {
            return {
                content: [
                    {
                        type: "text" as const,
                        text: JSON.stringify({
                            error: "Confirmation required",
                            message: `The tool '${toolName}' is destructive and requires confirmation. Use 'get_confirmation_token' to obtain a token, then pass it as 'confirmation_token' parameter.`,
                            tool: toolName,
                        }),
                    },
                ],
            };
        }

        // Validate the token against the store
        if (!validateToken(params.confirmation_token, toolName)) {
            return {
                content: [
                    {
                        type: "text" as const,
                        text: JSON.stringify({
                            error: "Invalid or expired confirmation token",
                            message: `The provided confirmation_token is invalid, expired, or was issued for a different action. Use 'get_confirmation_token' to obtain a fresh token for '${toolName}'.`,
                            tool: toolName,
                        }),
                    },
                ],
            };
        }

        // Valid token — execute handler
        return handler(params, extra);
    };
}
