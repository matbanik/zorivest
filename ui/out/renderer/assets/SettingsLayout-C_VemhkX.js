import { r as reactExports, u as useQueryClient, a as useStatusBar, b as useQuery, j as jsxRuntimeExports, c as compilerRuntimeExports, d as apiFetch, e as useTheme, f as useMutation, g as useNavigate } from "./index-BOpkIIp5.js";
function generateIdeConfig(target, baseUrl) {
  const serverConfig = {
    url: `${baseUrl}/mcp`,
    headers: {
      Authorization: "Bearer <your-api-token>"
    }
  };
  const configs = {
    cursor: {
      mcpServers: {
        zorivest: serverConfig
      }
    },
    "claude-desktop": {
      mcpServers: {
        zorivest: {
          ...serverConfig,
          transport: "sse"
        }
      }
    },
    windsurf: {
      mcpServers: {
        zorivest: serverConfig
      }
    }
  };
  return JSON.stringify(configs[target], null, 2);
}
function StatusDot(t0) {
  const $ = compilerRuntimeExports.c(3);
  const {
    ok
  } = t0;
  const t1 = `inline-block w-2 h-2 rounded-full mr-2 ${ok ? "bg-green-400" : "bg-red-400"}`;
  const t2 = ok ? "OK" : "Error";
  let t3;
  if ($[0] !== t1 || $[1] !== t2) {
    t3 = /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: t1, "aria-label": t2 });
    $[0] = t1;
    $[1] = t2;
    $[2] = t3;
  } else {
    t3 = $[2];
  }
  return t3;
}
function formatUptime(seconds) {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor(seconds % 3600 / 60);
  const s = Math.floor(seconds % 60);
  if (h > 0) return `${h}h ${m}m`;
  if (m > 0) return `${m}m ${s}s`;
  return `${s}s`;
}
function McpServerStatusPanel() {
  const [ideTarget, setIdeTarget] = reactExports.useState("cursor");
  const [copyFeedback, setCopyFeedback] = reactExports.useState(false);
  const [refreshing, setRefreshing] = reactExports.useState(false);
  const queryClient = useQueryClient();
  const {
    setStatus
  } = useStatusBar();
  const {
    data: health
  } = useQuery({
    queryKey: ["mcp-health"],
    queryFn: () => apiFetch("/api/v1/health"),
    refetchOnWindowFocus: false
  });
  const {
    data: version
  } = useQuery({
    queryKey: ["mcp-version"],
    queryFn: () => apiFetch("/api/v1/version/"),
    refetchOnWindowFocus: false
  });
  const {
    data: guard
  } = useQuery({
    queryKey: ["mcp-guard-status"],
    queryFn: () => apiFetch("/api/v1/mcp-guard/status"),
    refetchOnWindowFocus: false
  });
  const {
    data: toolsets
  } = useQuery({
    queryKey: ["mcp-toolsets"],
    queryFn: () => apiFetch("/api/v1/mcp/toolsets"),
    refetchOnWindowFocus: false,
    refetchInterval: 3e4
    // G5: auto-refresh for externally mutated data
  });
  const {
    data: diagnostics
  } = useQuery({
    queryKey: ["mcp-diagnostics"],
    queryFn: () => apiFetch("/api/v1/mcp/diagnostics"),
    refetchOnWindowFocus: false,
    refetchInterval: 3e4
    // G5: auto-refresh
  });
  const handleRefresh = reactExports.useCallback(async () => {
    setRefreshing(true);
    setStatus("Refreshing MCP status...");
    try {
      await Promise.all([queryClient.invalidateQueries({
        queryKey: ["mcp-health"]
      }), queryClient.invalidateQueries({
        queryKey: ["mcp-version"]
      }), queryClient.invalidateQueries({
        queryKey: ["mcp-guard-status"]
      }), queryClient.invalidateQueries({
        queryKey: ["mcp-toolsets"]
      }), queryClient.invalidateQueries({
        queryKey: ["mcp-diagnostics"]
      })]);
      setStatus("Status refreshed", 3e3);
    } catch {
      setStatus("Refresh failed — backend unreachable", 5e3);
    } finally {
      setRefreshing(false);
    }
  }, [queryClient, setStatus]);
  const handleCopy = reactExports.useCallback(async () => {
    const config = generateIdeConfig(ideTarget, window.api?.baseUrl ?? "http://localhost:8766");
    await navigator.clipboard.writeText(config);
    setCopyFeedback(true);
    setStatus("IDE config copied to clipboard", 2e3);
    setTimeout(() => setCopyFeedback(false), 2e3);
  }, [ideTarget, setStatus]);
  const backendOk = health?.status === "ok";
  const dbReachable = health != null;
  const dbUnlocked = health?.database?.unlocked === true;
  const guardLocked = guard?.is_locked ?? false;
  const callsPerHour = guard?.calls_per_hour ?? 0;
  const baseUrl = typeof window !== "undefined" && window.api?.baseUrl ? window.api.baseUrl : "http://localhost:8766";
  const ideJson = generateIdeConfig(ideTarget, baseUrl);
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "space-y-6", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "bg-bg-elevated rounded-lg border border-bg-subtle p-4", "data-testid": "mcp-status-panel", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: "text-base font-semibold text-fg mb-3", children: "MCP Server Status" }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "grid grid-cols-2 gap-y-2 text-sm", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(StatusDot, { ok: backendOk }),
          "Backend"
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-fg-muted", children: backendOk ? "OK" : "Unreachable" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(StatusDot, { ok: !!version }),
          "Version"
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-fg-muted", children: version?.version ?? "—" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(StatusDot, { ok: dbUnlocked }),
          "Database"
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-fg-muted", children: !dbReachable ? "Unreachable" : dbUnlocked ? "Unlocked" : "Locked" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(StatusDot, { ok: !guardLocked }),
          "Guard"
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-fg-muted", children: guardLocked ? "🔒 Locked" : `🟢 Active (${callsPerHour} calls/hr)` }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-fg-muted", children: "Registered tools" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-fg-muted", "data-testid": "mcp-tool-count", children: toolsets ? `${toolsets.total_tools} (${toolsets.toolset_count} toolsets)` : "—" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-fg-muted", children: "Uptime" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-fg-muted", "data-testid": "mcp-uptime", children: diagnostics?.api_uptime_seconds != null ? formatUptime(diagnostics.api_uptime_seconds) : health?.uptime_seconds != null ? formatUptime(health.uptime_seconds) : "N/A" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("button", { onClick: handleRefresh, disabled: refreshing, "data-testid": "mcp-refresh-btn", className: "mt-4 px-4 py-1.5 text-sm font-medium rounded-md border border-bg-subtle bg-bg hover:bg-bg-elevated text-fg transition-colors disabled:opacity-50 cursor-pointer", children: refreshing ? "⏳ Refreshing..." : "🔄 Refresh Status" })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "bg-bg-elevated rounded-lg border border-bg-subtle p-4", "data-testid": "mcp-ide-config", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: "text-base font-semibold text-fg mb-3", children: "IDE Configuration" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-sm text-fg-muted mb-3", children: "Generate configuration for your AI IDE:" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "flex gap-2 mb-3", children: ["cursor", "claude-desktop", "windsurf"].map((target) => /* @__PURE__ */ jsxRuntimeExports.jsx("button", { onClick: () => setIdeTarget(target), "data-testid": `ide-tab-${target}`, className: `px-3 py-1 text-sm font-medium rounded-md border transition-colors cursor-pointer ${ideTarget === target ? "border-accent bg-accent/10 text-fg" : "border-bg-subtle bg-bg text-fg-muted hover:bg-bg-elevated hover:text-fg"}`, children: target === "claude-desktop" ? "Claude Desktop" : target.charAt(0).toUpperCase() + target.slice(1) }, target)) }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("pre", { className: "bg-bg rounded-md p-3 text-xs text-fg-muted overflow-x-auto border border-bg-subtle", children: /* @__PURE__ */ jsxRuntimeExports.jsx("code", { children: ideJson }) }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("button", { onClick: handleCopy, "data-testid": "ide-copy-btn", className: "mt-3 px-4 py-1.5 text-sm font-medium rounded-md border border-bg-subtle bg-bg hover:bg-bg-elevated text-fg transition-colors cursor-pointer", children: copyFeedback ? "✓ Copied!" : "📋 Copy to Clipboard" })
    ] })
  ] });
}
function SettingsLayout() {
  const $ = compilerRuntimeExports.c(56);
  const queryClient = useQueryClient();
  const {
    setStatus
  } = useStatusBar();
  const [theme, setTheme] = useTheme();
  let t0;
  if ($[0] === /* @__PURE__ */ Symbol.for("react.memo_cache_sentinel")) {
    t0 = {
      queryKey: ["mcp-guard-status"],
      queryFn: _temp
    };
    $[0] = t0;
  } else {
    t0 = $[0];
  }
  const {
    data: guardStatus
  } = useQuery(t0);
  let t1;
  if ($[1] !== guardStatus?.is_locked || $[2] !== setStatus) {
    t1 = async () => {
      const action = guardStatus?.is_locked ? "unlock" : "lock";
      setStatus(`${action === "lock" ? "Locking" : "Unlocking"} MCP Guard...`);
      const endpoint = `/api/v1/mcp-guard/${action}`;
      await apiFetch(endpoint, {
        method: "POST"
      });
    };
    $[1] = guardStatus?.is_locked;
    $[2] = setStatus;
    $[3] = t1;
  } else {
    t1 = $[3];
  }
  let t2;
  if ($[4] !== guardStatus?.is_locked || $[5] !== queryClient || $[6] !== setStatus) {
    t2 = () => {
      const wasLocked = guardStatus?.is_locked;
      setStatus(`MCP Guard ${wasLocked ? "unlocked" : "locked"} successfully`, 3e3);
      queryClient.invalidateQueries({
        queryKey: ["mcp-guard-status"]
      });
    };
    $[4] = guardStatus?.is_locked;
    $[5] = queryClient;
    $[6] = setStatus;
    $[7] = t2;
  } else {
    t2 = $[7];
  }
  let t3;
  if ($[8] !== setStatus) {
    t3 = (err) => {
      setStatus(`Guard toggle failed: ${err.message}`, 5e3);
    };
    $[8] = setStatus;
    $[9] = t3;
  } else {
    t3 = $[9];
  }
  let t4;
  if ($[10] !== t1 || $[11] !== t2 || $[12] !== t3) {
    t4 = {
      mutationFn: t1,
      onSuccess: t2,
      onError: t3
    };
    $[10] = t1;
    $[11] = t2;
    $[12] = t3;
    $[13] = t4;
  } else {
    t4 = $[13];
  }
  const lockMutation = useMutation(t4);
  let t5;
  if ($[14] !== lockMutation) {
    t5 = () => {
      lockMutation.mutate();
    };
    $[14] = lockMutation;
    $[15] = t5;
  } else {
    t5 = $[15];
  }
  const handleToggle = t5;
  const navigate = useNavigate();
  const isLocked = guardStatus?.is_locked ?? false;
  let t6;
  if ($[16] === /* @__PURE__ */ Symbol.for("react.memo_cache_sentinel")) {
    t6 = /* @__PURE__ */ jsxRuntimeExports.jsx("div", { children: /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { className: "text-lg font-semibold text-fg mb-6", children: "Settings" }) });
    $[16] = t6;
  } else {
    t6 = $[16];
  }
  let t7;
  if ($[17] === /* @__PURE__ */ Symbol.for("react.memo_cache_sentinel")) {
    t7 = /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "px-4 py-3 border-b border-bg-subtle", children: /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: "text-sm font-semibold text-fg-muted uppercase tracking-wide", children: "Data Sources" }) });
    $[17] = t7;
  } else {
    t7 = $[17];
  }
  let t8;
  if ($[18] !== navigate) {
    t8 = () => navigate({
      to: "/settings/market"
    });
    $[18] = navigate;
    $[19] = t8;
  } else {
    t8 = $[19];
  }
  let t9;
  if ($[20] === /* @__PURE__ */ Symbol.for("react.memo_cache_sentinel")) {
    t9 = /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-lg", children: "🌐" });
    $[20] = t9;
  } else {
    t9 = $[20];
  }
  let t10;
  let t11;
  if ($[21] === /* @__PURE__ */ Symbol.for("react.memo_cache_sentinel")) {
    t10 = /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-3", children: [
      t9,
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-left", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-sm font-medium text-fg", children: "Market Data Providers" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-xs text-fg-muted", children: "Configure API keys for 12 market data sources" })
      ] })
    ] });
    t11 = /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-fg-muted group-hover:text-fg transition-colors", children: "›" });
    $[21] = t10;
    $[22] = t11;
  } else {
    t10 = $[21];
    t11 = $[22];
  }
  let t12;
  if ($[23] !== t8) {
    t12 = /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "bg-bg-elevated rounded-lg border border-bg-subtle overflow-hidden", children: [
      t7,
      /* @__PURE__ */ jsxRuntimeExports.jsxs("button", { "data-testid": "settings-market-data-link", onClick: t8, className: "w-full flex items-center justify-between px-4 py-3 hover:bg-bg-subtle transition-colors cursor-pointer group", children: [
        t10,
        t11
      ] })
    ] });
    $[23] = t8;
    $[24] = t12;
  } else {
    t12 = $[24];
  }
  let t13;
  if ($[25] === /* @__PURE__ */ Symbol.for("react.memo_cache_sentinel")) {
    t13 = /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: "text-base font-semibold text-fg mb-3", children: "Appearance" });
    $[25] = t13;
  } else {
    t13 = $[25];
  }
  let t14;
  if ($[26] === /* @__PURE__ */ Symbol.for("react.memo_cache_sentinel")) {
    t14 = /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-sm text-fg-muted", children: "Theme" });
    $[26] = t14;
  } else {
    t14 = $[26];
  }
  let t15;
  if ($[27] !== setTheme) {
    t15 = () => setTheme("dark");
    $[27] = setTheme;
    $[28] = t15;
  } else {
    t15 = $[28];
  }
  const t16 = `px-4 py-1.5 text-sm font-medium rounded-md border transition-colors cursor-pointer ${theme === "dark" ? "bg-accent-purple text-fg border-accent-purple" : "bg-bg border-bg-subtle text-fg-muted hover:bg-bg-elevated hover:text-fg"}`;
  let t17;
  if ($[29] !== t15 || $[30] !== t16) {
    t17 = /* @__PURE__ */ jsxRuntimeExports.jsx("button", { "data-testid": "theme-dark-btn", onClick: t15, className: t16, children: "🌙 Dark" });
    $[29] = t15;
    $[30] = t16;
    $[31] = t17;
  } else {
    t17 = $[31];
  }
  let t18;
  if ($[32] !== setTheme) {
    t18 = () => setTheme("light");
    $[32] = setTheme;
    $[33] = t18;
  } else {
    t18 = $[33];
  }
  const t19 = `px-4 py-1.5 text-sm font-medium rounded-md border transition-colors cursor-pointer ${theme === "light" ? "bg-accent-purple text-fg border-accent-purple" : "bg-bg border-bg-subtle text-fg-muted hover:bg-bg-elevated hover:text-fg"}`;
  let t20;
  if ($[34] !== t18 || $[35] !== t19) {
    t20 = /* @__PURE__ */ jsxRuntimeExports.jsx("button", { "data-testid": "theme-light-btn", onClick: t18, className: t19, children: "☀️ Light" });
    $[34] = t18;
    $[35] = t19;
    $[36] = t20;
  } else {
    t20 = $[36];
  }
  let t21;
  if ($[37] !== t17 || $[38] !== t20) {
    t21 = /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "bg-bg-elevated rounded-lg border border-bg-subtle p-4", children: [
      t13,
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-4", children: [
        t14,
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex gap-2", children: [
          t17,
          t20
        ] })
      ] })
    ] });
    $[37] = t17;
    $[38] = t20;
    $[39] = t21;
  } else {
    t21 = $[39];
  }
  let t22;
  if ($[40] === /* @__PURE__ */ Symbol.for("react.memo_cache_sentinel")) {
    t22 = /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: "text-base font-semibold text-fg mb-3", children: "MCP Guard" });
    $[40] = t22;
  } else {
    t22 = $[40];
  }
  const t23 = `text-sm font-medium ${isLocked ? "text-red-400" : "text-green-400"}`;
  const t24 = isLocked ? "🔒 Locked" : "🟢 Unlocked";
  let t25;
  if ($[41] !== t23 || $[42] !== t24) {
    t25 = /* @__PURE__ */ jsxRuntimeExports.jsx("span", { "data-testid": "mcp-guard-status", className: t23, children: t24 });
    $[41] = t23;
    $[42] = t24;
    $[43] = t25;
  } else {
    t25 = $[43];
  }
  const t26 = lockMutation.isPending ? "⏳ Working..." : isLocked ? "🔓 Unlock" : "🔒 Lock";
  let t27;
  if ($[44] !== handleToggle || $[45] !== lockMutation.isPending || $[46] !== t26) {
    t27 = /* @__PURE__ */ jsxRuntimeExports.jsx("button", { "data-testid": "mcp-guard-lock-toggle", onClick: handleToggle, disabled: lockMutation.isPending, className: "px-4 py-1.5 text-sm font-medium rounded-md border border-bg-subtle bg-bg hover:bg-bg-elevated text-fg transition-colors disabled:opacity-50 cursor-pointer", children: t26 });
    $[44] = handleToggle;
    $[45] = lockMutation.isPending;
    $[46] = t26;
    $[47] = t27;
  } else {
    t27 = $[47];
  }
  let t28;
  if ($[48] !== t25 || $[49] !== t27) {
    t28 = /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "bg-bg-elevated rounded-lg border border-bg-subtle p-4", children: [
      t22,
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-4", children: [
        t25,
        t27
      ] })
    ] });
    $[48] = t25;
    $[49] = t27;
    $[50] = t28;
  } else {
    t28 = $[50];
  }
  let t29;
  if ($[51] === /* @__PURE__ */ Symbol.for("react.memo_cache_sentinel")) {
    t29 = /* @__PURE__ */ jsxRuntimeExports.jsx(McpServerStatusPanel, {});
    $[51] = t29;
  } else {
    t29 = $[51];
  }
  let t30;
  if ($[52] !== t12 || $[53] !== t21 || $[54] !== t28) {
    t30 = /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { "data-testid": "settings-page", className: "space-y-8 max-w-3xl", children: [
      t6,
      t12,
      t21,
      t28,
      t29
    ] });
    $[52] = t12;
    $[53] = t21;
    $[54] = t28;
    $[55] = t30;
  } else {
    t30 = $[55];
  }
  return t30;
}
function _temp() {
  return apiFetch("/api/v1/mcp-guard/status");
}
export {
  SettingsLayout as default
};
