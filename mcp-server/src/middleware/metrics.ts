/**
 * Per-tool performance metrics middleware for MCP server.
 *
 * In-memory metrics collector tracking per-tool latency, call counts,
 * error rates, and payload sizes. Ring buffer (last 1000 per tool)
 * for bounded memory. Auto-warnings for high error rates and slow tools.
 *
 * Source: 05-mcp-server.md §5.9
 * MEU: 39 (mcp-perf-metrics)
 */

// ── Types ──────────────────────────────────────────────────────────────

interface ToolMetrics {
    callCount: number;
    errorCount: number;
    latencies: number[]; // ms, ring buffer (last 1000)
    payloadSizes: number[]; // bytes, ring buffer (last 1000)
}

interface PerToolSummary {
    call_count: number;
    error_count: number;
    error_rate: number;
    latency: {
        avg: number;
        min: number;
        max: number;
        p50: number;
        p95: number;
        p99: number;
    };
    avg_payload_bytes: number;
}

export interface MetricsSummary {
    session_uptime_minutes: number;
    total_tool_calls: number;
    overall_error_rate: number;
    calls_per_minute: number;
    slowest_tool: string | null;
    most_errored_tool: string | null;
    per_tool?: Record<string, PerToolSummary>;
    warnings: string[];
}

import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";

// ── Constants ──────────────────────────────────────────────────────────

const RING_BUFFER_SIZE = 1000;

/** Network-bound tools excluded from slow-latency warnings. */
const NETWORK_TOOLS = new Set([
    "get_stock_quote",
    "get_market_news",
    "get_sec_filings",
    "search_ticker",
]);

// ── MetricsCollector ───────────────────────────────────────────────────

export class MetricsCollector {
    private tools = new Map<string, ToolMetrics>();
    private startTime = Date.now();

    /**
     * Record a tool invocation's metrics.
     */
    record(
        toolName: string,
        latencyMs: number,
        payloadBytes: number,
        isError: boolean,
    ): void {
        let metrics = this.tools.get(toolName);
        if (!metrics) {
            metrics = {
                callCount: 0,
                errorCount: 0,
                latencies: [],
                payloadSizes: [],
            };
            this.tools.set(toolName, metrics);
        }
        metrics.callCount++;
        if (isError) metrics.errorCount++;

        // Ring buffer: keep last N entries
        if (metrics.latencies.length >= RING_BUFFER_SIZE)
            metrics.latencies.shift();
        metrics.latencies.push(latencyMs);
        if (metrics.payloadSizes.length >= RING_BUFFER_SIZE)
            metrics.payloadSizes.shift();
        metrics.payloadSizes.push(payloadBytes);
    }

    /**
     * Session uptime in minutes (rounded down).
     */
    getUptimeMinutes(): number {
        return Math.floor((Date.now() - this.startTime) / 60_000);
    }

    /**
     * Compute metrics summary. When verbose=true, includes per-tool breakdown.
     */
    getSummary(verbose: boolean): MetricsSummary {
        const warnings: string[] = [];
        let totalCalls = 0;
        let totalErrors = 0;
        let slowestTool: string | null = null;
        let slowestAvg = 0;
        let mostErroredTool: string | null = null;
        let mostErrors = 0;
        const perTool: Record<string, PerToolSummary> = {};

        for (const [name, m] of this.tools.entries()) {
            totalCalls += m.callCount;
            totalErrors += m.errorCount;

            const sorted = [...m.latencies].sort((a, b) => a - b);
            const avg = sorted.length
                ? sorted.reduce((s, v) => s + v, 0) / sorted.length
                : 0;
            const percentile = (p: number): number => {
                if (!sorted.length) return 0;
                const idx = Math.ceil(p * sorted.length) - 1;
                return Math.round(sorted[Math.max(0, idx)]);
            };
            const errorRate = m.callCount
                ? m.errorCount / m.callCount
                : 0;

            if (avg > slowestAvg) {
                slowestAvg = avg;
                slowestTool = name;
            }
            if (m.errorCount > mostErrors) {
                mostErrors = m.errorCount;
                mostErroredTool = name;
            }

            // Auto-warnings
            if (errorRate > 0.1) {
                warnings.push(
                    `Tool '${name}' has ${Math.round(errorRate * 100)}% error rate (${m.errorCount}/${m.callCount} calls)`,
                );
            }
            if (percentile(0.95) > 2000 && !NETWORK_TOOLS.has(name)) {
                warnings.push(
                    `Tool '${name}' p95 latency is ${percentile(0.95)}ms`,
                );
            }

            if (verbose) {
                const avgPayload = m.payloadSizes.length
                    ? Math.round(
                        m.payloadSizes.reduce((s, v) => s + v, 0) /
                        m.payloadSizes.length,
                    )
                    : 0;
                perTool[name] = {
                    call_count: m.callCount,
                    error_count: m.errorCount,
                    error_rate:
                        Math.round(errorRate * 10000) / 10000,
                    latency: {
                        avg: Math.round(avg),
                        min: sorted.length ? Math.round(sorted[0]) : 0,
                        max: sorted.length
                            ? Math.round(sorted[sorted.length - 1])
                            : 0,
                        p50: percentile(0.5),
                        p95: percentile(0.95),
                        p99: percentile(0.99),
                    },
                    avg_payload_bytes: avgPayload,
                };
            }
        }

        const uptimeMin = this.getUptimeMinutes();
        const base = {
            session_uptime_minutes: uptimeMin,
            total_tool_calls: totalCalls,
            overall_error_rate: totalCalls
                ? Math.round((totalErrors / totalCalls) * 10000) / 10000
                : 0,
            calls_per_minute:
                uptimeMin > 0
                    ? Math.round((totalCalls / uptimeMin) * 100) / 100
                    : 0,
            slowest_tool: slowestTool,
            most_errored_tool: mostErroredTool,
            warnings,
        };
        if (verbose) {
            return { ...base, per_tool: perTool };
        }
        return base;
    }
}

// ── Singleton ──────────────────────────────────────────────────────────

export const metricsCollector = new MetricsCollector();

// ── withMetrics HOF ────────────────────────────────────────────────────

/**
 * Wraps an MCP tool handler with performance metrics recording.
 * Composable with withGuard: withMetrics('name', withGuard(handler))
 *
 * @param toolName - Canonical tool name for metrics key
 * @param handler - MCP tool handler function
 * @param collector - MetricsCollector instance (defaults to singleton)
 */
export function withMetrics<T>(
    toolName: string,
    handler: (args: T, extra: unknown) => Promise<CallToolResult>,
    collector: MetricsCollector = metricsCollector,
): (args: T, extra: unknown) => Promise<CallToolResult> {
    return async (args: T, extra: unknown) => {
        const start = performance.now();
        try {
            const result = await handler(args, extra);
            const elapsed = performance.now() - start;
            const payloadSize = JSON.stringify(result).length;
            collector.record(
                toolName,
                elapsed,
                payloadSize,
                !!result.isError,
            );
            return result;
        } catch (err) {
            collector.record(
                toolName,
                performance.now() - start,
                0,
                true,
            );
            throw err;
        }
    };
}
