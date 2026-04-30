/**
 * Behavior tests for zorivest_template compound tool.
 *
 * Verifies all 6 actions route correctly through CompoundToolRouter.
 * Source: mcp-consolidation-proposal-v3.md §11 zorivest_template
 * Phase: P2.5f corrections (Finding 3)
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { registerTemplateTool } from "../../src/compound/template-tool.js";
import { createClient, mockFetch, getLastFetchUrl, getLastFetchMethod } from "./helpers.js";

describe("zorivest_template compound tool", () => {
    let fetchMock: ReturnType<typeof vi.fn>;

    beforeEach(() => { fetchMock = mockFetch(); });
    afterEach(() => vi.restoreAllMocks());

    it("registers exactly 1 tool named zorivest_template", async () => {
        const client = await createClient(registerTemplateTool);
        const { tools } = await client.listTools();
        expect(tools).toHaveLength(1);
        expect(tools[0].name).toBe("zorivest_template");
    });

    it("routes create to POST /scheduling/templates", async () => {
        const client = await createClient(registerTemplateTool);
        await client.callTool({
            name: "zorivest_template",
            arguments: { action: "create", name: "test-tmpl", body_html: "<h1>Test</h1>" },
        });
        expect(getLastFetchUrl(fetchMock)).toContain("/scheduling/templates");
        expect(getLastFetchMethod(fetchMock)).toBe("POST");
    });

    it("routes get to GET /scheduling/templates/:name", async () => {
        const client = await createClient(registerTemplateTool);
        await client.callTool({
            name: "zorivest_template",
            arguments: { action: "get", name: "test-tmpl" },
        });
        expect(getLastFetchUrl(fetchMock)).toContain("/scheduling/templates/test-tmpl");
    });

    it("routes list to GET /scheduling/templates", async () => {
        const client = await createClient(registerTemplateTool);
        await client.callTool({
            name: "zorivest_template",
            arguments: { action: "list" },
        });
        expect(getLastFetchUrl(fetchMock)).toContain("/scheduling/templates");
    });

    it("routes update to PATCH /scheduling/templates/:name", async () => {
        const client = await createClient(registerTemplateTool);
        await client.callTool({
            name: "zorivest_template",
            arguments: { action: "update", name: "test-tmpl", description: "Updated" },
        });
        expect(getLastFetchUrl(fetchMock)).toContain("/scheduling/templates/test-tmpl");
        expect(getLastFetchMethod(fetchMock)).toBe("PATCH");
    });

    it("routes delete to DELETE /scheduling/templates/:name (pass-through mode)", async () => {
        const client = await createClient(registerTemplateTool);
        await client.callTool({
            name: "zorivest_template",
            arguments: { action: "delete", name: "test-tmpl" },
        });
        expect(getLastFetchUrl(fetchMock)).toContain("/scheduling/templates/test-tmpl");
        expect(getLastFetchMethod(fetchMock)).toBe("DELETE");
    });

    it("routes preview to POST /scheduling/templates/:name/preview", async () => {
        const client = await createClient(registerTemplateTool);
        await client.callTool({
            name: "zorivest_template",
            arguments: { action: "preview", name: "test-tmpl" },
        });
        expect(getLastFetchUrl(fetchMock)).toContain("/scheduling/templates/test-tmpl/preview");
        expect(getLastFetchMethod(fetchMock)).toBe("POST");
    });

    it("rejects unknown action", async () => {
        const client = await createClient(registerTemplateTool);
        const result = await client.callTool({ name: "zorivest_template", arguments: { action: "nonexistent" } });
        expect(result.isError).toBe(true);
    });
});

// ── Static-mode confirmation gate tests (Finding 5) ─────────────────────

import {
    setConfirmationMode,
    createConfirmationToken,
} from "../../src/middleware/confirmation.js";

describe("zorivest_template delete confirmation gate", () => {
    let fetchMock: ReturnType<typeof vi.fn>;

    beforeEach(() => { fetchMock = mockFetch(); });
    afterEach(() => {
        setConfirmationMode("dynamic"); // restore default
        vi.restoreAllMocks();
    });

    it("blocks delete without token in static mode", async () => {
        setConfirmationMode("static");
        const client = await createClient(registerTemplateTool);
        const result = await client.callTool({
            name: "zorivest_template",
            arguments: { action: "delete", name: "victim-template" },
        });
        // Should return confirmation-required error, NOT execute the DELETE
        const text = JSON.parse((result.content as Array<{ text: string }>)[0].text);
        expect(text.error).toBe("Confirmation required");
        expect(text.tool).toBe("delete_email_template");
        // fetch should NOT have been called (no DELETE sent)
        expect(fetchMock).not.toHaveBeenCalled();
    });

    it("can mint a token for delete_email_template", () => {
        // createConfirmationToken should NOT throw for delete_email_template
        const { token, expires_in_seconds } = createConfirmationToken("delete_email_template");
        expect(token).toMatch(/^ctk_/);
        expect(expires_in_seconds).toBe(60);
    });

    it("allows delete with valid token in static mode", async () => {
        setConfirmationMode("static");
        const { token } = createConfirmationToken("delete_email_template");
        const client = await createClient(registerTemplateTool);
        const result = await client.callTool({
            name: "zorivest_template",
            arguments: { action: "delete", name: "test-tmpl", confirmation_token: token },
        });
        // Should have executed — fetch called with DELETE
        expect(fetchMock).toHaveBeenCalled();
        expect(getLastFetchUrl(fetchMock)).toContain("/scheduling/templates/test-tmpl");
        expect(getLastFetchMethod(fetchMock)).toBe("DELETE");
    });
});
