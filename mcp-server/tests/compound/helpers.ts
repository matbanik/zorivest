/**
 * Shared test helpers for compound tool behavior tests.
 *
 * Provides reusable mock setup, client creation, and assertion helpers
 * for all 13 compound tool test files.
 */

import { vi } from "vitest";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";
import type { RegisteredToolHandle } from "../../src/toolsets/registry.js";

/**
 * Create a test client with a single compound tool registration function.
 */
export async function createClient(
    registerFn: (server: McpServer) => RegisteredToolHandle[],
): Promise<Client> {
    const server = new McpServer({ name: "test", version: "0.1.0" });
    registerFn(server);
    const [ct, st] = InMemoryTransport.createLinkedPair();
    const client = new Client({ name: "test-client", version: "0.1.0" });
    await Promise.all([client.connect(ct), server.connect(st)]);
    return client;
}

/**
 * Mock the global fetch to return success for any URL.
 * Returns a reference to the mock for call inspection.
 */
export function mockFetch(): ReturnType<typeof vi.fn> {
    const mock = vi.fn().mockImplementation(() =>
        Promise.resolve({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ success: true }),
        }),
    );
    vi.stubGlobal("fetch", mock);
    return mock;
}

/**
 * Extract the text content from a tool call result.
 */
export function getResultText(result: unknown): string {
    const r = result as { content: Array<{ text: string }> };
    return r.content[0].text;
}

/**
 * Get the URL path from the last fetch call.
 * Strips the API base URL prefix.
 */
export function getLastFetchUrl(mock: ReturnType<typeof vi.fn>): string {
    const lastCall = mock.mock.calls[mock.mock.calls.length - 1];
    const url = lastCall[0] as string;
    // Strip API base prefix
    return url.replace(/^https?:\/\/[^/]+\/api\/v1/, "");
}

/**
 * Get the HTTP method from the last fetch call.
 */
export function getLastFetchMethod(mock: ReturnType<typeof vi.fn>): string {
    const lastCall = mock.mock.calls[mock.mock.calls.length - 1];
    const init = lastCall[1] as RequestInit | undefined;
    return init?.method ?? "GET";
}

/**
 * Get the URL path from a specific fetch call (0-indexed).
 */
export function getFetchUrl(mock: ReturnType<typeof vi.fn>, index: number): string {
    const call = mock.mock.calls[index];
    const url = call[0] as string;
    return url.replace(/^https?:\/\/[^/]+\/api\/v1/, "");
}
