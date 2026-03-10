/**
 * Unit tests for per-tool performance metrics middleware.
 *
 * Tests verify MetricsCollector: ring buffer, percentile computation,
 * error tracking, auto-warnings, network tool exclusion, and
 * withMetrics HOF wrapper.
 *
 * Source: 05-mcp-server.md §5.9, FIC AC-1 through AC-8
 * MEU: 39 (mcp-perf-metrics)
 */

import { describe, it, expect, vi } from "vitest";

import {
    MetricsCollector,
    withMetrics,
    metricsCollector,
} from "../src/middleware/metrics.js";
import { withGuard } from "../src/middleware/mcp-guard.js";

// ── MetricsCollector unit tests ────────────────────────────────────────

describe("MetricsCollector", () => {
    // AC-1: record() stores per-tool data
    // AC-3: getSummary(true) includes per-tool percentiles
    it("records latency and computes percentiles", () => {
        const mc = new MetricsCollector();
        for (let i = 1; i <= 100; i++) mc.record("test_tool", i, 500, false);
        const summary = mc.getSummary(true);
        expect(summary.per_tool?.test_tool.latency.p50).toBeCloseTo(50, 0);
        expect(summary.per_tool?.test_tool.latency.p95).toBeCloseTo(95, 0);
        expect(summary.per_tool?.test_tool.latency.p99).toBeCloseTo(99, 0);
        expect(summary.per_tool?.test_tool.latency.avg).toBeCloseTo(51, 0);
        expect(summary.per_tool?.test_tool.latency.min).toBe(1);
        expect(summary.per_tool?.test_tool.latency.max).toBe(100);
    });

    // AC-1: error tracking
    it("tracks error count and rate", () => {
        const mc = new MetricsCollector();
        for (let i = 0; i < 10; i++) mc.record("test_tool", 10, 100, i < 2);
        const summary = mc.getSummary(true);
        expect(summary.per_tool?.test_tool.error_count).toBe(2);
        expect(summary.per_tool?.test_tool.error_rate).toBeCloseTo(0.2);
    });

    // AC-5: auto-warning when error rate >10%
    it("warns when error rate exceeds 10%", () => {
        const mc = new MetricsCollector();
        for (let i = 0; i < 10; i++) mc.record("bad_tool", 10, 100, i < 3);
        const summary = mc.getSummary(true);
        expect(summary.warnings).toContainEqual(
            expect.stringContaining("error rate"),
        );
    });

    // AC-6: auto-warning when p95 >2000ms for non-network tools
    it("warns when p95 exceeds 2000ms for non-network tool", () => {
        const mc = new MetricsCollector();
        // All latencies are 3000ms — p95 will be 3000
        for (let i = 0; i < 20; i++) mc.record("slow_tool", 3000, 100, false);
        const summary = mc.getSummary(true);
        expect(summary.warnings).toContainEqual(
            expect.stringContaining("slow_tool"),
        );
    });

    // AC-7: network tools excluded from slow warnings
    it("excludes network tools from slow warnings", () => {
        const mc = new MetricsCollector();
        mc.record("get_stock_quote", 5000, 100, false);
        mc.record("get_market_news", 5000, 100, false);
        mc.record("get_sec_filings", 5000, 100, false);
        mc.record("search_ticker", 5000, 100, false);
        const summary = mc.getSummary(true);
        expect(summary.warnings).not.toContainEqual(
            expect.stringContaining("get_stock_quote"),
        );
        expect(summary.warnings).not.toContainEqual(
            expect.stringContaining("get_market_news"),
        );
        expect(summary.warnings).not.toContainEqual(
            expect.stringContaining("get_sec_filings"),
        );
        expect(summary.warnings).not.toContainEqual(
            expect.stringContaining("search_ticker"),
        );
    });

    // AC-2: ring buffer caps at 1000
    it("uses ring buffer to bound memory", () => {
        const mc = new MetricsCollector();
        for (let i = 0; i < 2000; i++) mc.record("test_tool", i, 100, false);
        const summary = mc.getSummary(true);
        // latency min should reflect ring buffer truncation, not i=0
        expect(summary.per_tool?.test_tool.latency.min).toBeGreaterThanOrEqual(
            1000,
        );
    });

    // AC-4: getSummary(false) omits per_tool
    it("omits per_tool when verbose=false", () => {
        const mc = new MetricsCollector();
        mc.record("test_tool", 50, 100, false);
        const summary = mc.getSummary(false);
        expect(summary.session_uptime_minutes).toBeDefined();
        expect(summary.total_tool_calls).toBe(1);
        expect(summary).not.toHaveProperty("per_tool");
    });

    // AC-1: session-level aggregates
    it("computes session-level totals and rates", () => {
        const mc = new MetricsCollector();
        mc.record("tool_a", 10, 100, false);
        mc.record("tool_a", 20, 200, true);
        mc.record("tool_b", 30, 300, false);
        const summary = mc.getSummary(false);
        expect(summary.total_tool_calls).toBe(3);
        expect(summary.overall_error_rate).toBeCloseTo(1 / 3, 2);
    });

    // AC-1: slowest and most-errored tool identification
    it("identifies slowest and most-errored tools", () => {
        const mc = new MetricsCollector();
        mc.record("fast_tool", 10, 100, false);
        mc.record("slow_tool", 5000, 100, false);
        mc.record("error_tool", 10, 100, true);
        mc.record("error_tool", 10, 100, true);
        const summary = mc.getSummary(false);
        expect(summary.slowest_tool).toBe("slow_tool");
        expect(summary.most_errored_tool).toBe("error_tool");
    });

    // AC-1: payload size tracking
    it("tracks average payload size", () => {
        const mc = new MetricsCollector();
        mc.record("test_tool", 10, 100, false);
        mc.record("test_tool", 10, 300, false);
        const summary = mc.getSummary(true);
        expect(summary.per_tool?.test_tool.avg_payload_bytes).toBe(200);
    });
});

// ── withMetrics wrapper tests ──────────────────────────────────────────

describe("withMetrics wrapper", () => {
    // AC-8: records successful call
    it("records successful call metrics", async () => {
        const mc = new MetricsCollector();
        const handler = withMetrics(
            "test_tool",
            async () => ({
                content: [{ type: "text" as const, text: "ok" }],
            }),
            mc,
        );
        await handler({});
        const summary = mc.getSummary(true);
        expect(summary.total_tool_calls).toBe(1);
        expect(summary.per_tool?.test_tool.call_count).toBe(1);
        expect(summary.per_tool?.test_tool.error_count).toBe(0);
    });

    // AC-8: records failed call
    it("records failed call metrics and re-throws", async () => {
        const mc = new MetricsCollector();
        const handler = withMetrics(
            "test_tool",
            async () => {
                throw new Error("fail");
            },
            mc,
        );
        await expect(handler({})).rejects.toThrow("fail");
        const summary = mc.getSummary(true);
        expect(summary.total_tool_calls).toBe(1);
        expect(summary.per_tool?.test_tool.error_count).toBe(1);
    });

    // AC-8: records isError results as errors
    it("records isError results as errors", async () => {
        const mc = new MetricsCollector();
        const handler = withMetrics(
            "test_tool",
            async () => ({
                content: [{ type: "text" as const, text: "blocked" }],
                isError: true,
            }),
            mc,
        );
        await handler({});
        const summary = mc.getSummary(true);
        expect(summary.per_tool?.test_tool.error_count).toBe(1);
    });
});

// ── Singleton export test ──────────────────────────────────────────────

describe("metricsCollector singleton", () => {
    it("exports a singleton MetricsCollector instance", () => {
        expect(metricsCollector).toBeInstanceOf(MetricsCollector);
    });
});

// ── MEU-38+39 AC-10: Composition proof ─────────────────────────────────

describe("withMetrics(withGuard(handler)) composition", () => {
    // AC-10: both middleware layers execute on a registered tool
    it("executes both metrics and guard layers in composition", async () => {
        // Mock guard as allowed
        vi.stubGlobal(
            "fetch",
            vi.fn().mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({ allowed: true }),
            }),
        );

        const mc = new MetricsCollector();
        const innerHandler = vi.fn().mockResolvedValue({
            content: [{ type: "text" as const, text: "composed result" }],
        });

        const composed = withMetrics(
            "composed_tool",
            withGuard(innerHandler),
            mc,
        );
        const result = await composed({});

        // Guard allowed → inner handler was called
        expect(innerHandler).toHaveBeenCalledOnce();
        expect(result.content[0].text).toBe("composed result");

        // Metrics recorded the call
        const summary = mc.getSummary(true);
        expect(summary.total_tool_calls).toBe(1);
        expect(summary.per_tool?.composed_tool.call_count).toBe(1);
        expect(summary.per_tool?.composed_tool.error_count).toBe(0);
    });

    it("records guard-blocked call as error in metrics", async () => {
        // Mock guard as blocked
        vi.stubGlobal(
            "fetch",
            vi.fn().mockResolvedValue({
                ok: true,
                json: () =>
                    Promise.resolve({ allowed: false, reason: "manual" }),
            }),
        );

        const mc = new MetricsCollector();
        const innerHandler = vi.fn().mockResolvedValue({
            content: [{ type: "text" as const, text: "should not reach" }],
        });

        const composed = withMetrics(
            "blocked_tool",
            withGuard(innerHandler),
            mc,
        );
        const result = await composed({});

        // Guard blocked → inner handler NOT called
        expect(innerHandler).not.toHaveBeenCalled();
        expect(result.isError).toBe(true);

        // Metrics recorded the call as error
        const summary = mc.getSummary(true);
        expect(summary.total_tool_calls).toBe(1);
        expect(summary.per_tool?.blocked_tool.error_count).toBe(1);
    });
});
