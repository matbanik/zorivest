import { S as Subscribable, s as shallowEqualObjects, h as hashKey, g as getDefaultState, n as notifyManager, u as useQueryClient, r as reactExports, e as noop, f as shouldThrowError, a as useStatusBar, b as useQuery, j as jsxRuntimeExports, c as compilerRuntimeExports, d as apiFetch } from "./index-BZpIS9tl.js";
var MutationObserver = class extends Subscribable {
  #client;
  #currentResult = void 0;
  #currentMutation;
  #mutateOptions;
  constructor(client, options) {
    super();
    this.#client = client;
    this.setOptions(options);
    this.bindMethods();
    this.#updateResult();
  }
  bindMethods() {
    this.mutate = this.mutate.bind(this);
    this.reset = this.reset.bind(this);
  }
  setOptions(options) {
    const prevOptions = this.options;
    this.options = this.#client.defaultMutationOptions(options);
    if (!shallowEqualObjects(this.options, prevOptions)) {
      this.#client.getMutationCache().notify({
        type: "observerOptionsUpdated",
        mutation: this.#currentMutation,
        observer: this
      });
    }
    if (prevOptions?.mutationKey && this.options.mutationKey && hashKey(prevOptions.mutationKey) !== hashKey(this.options.mutationKey)) {
      this.reset();
    } else if (this.#currentMutation?.state.status === "pending") {
      this.#currentMutation.setOptions(this.options);
    }
  }
  onUnsubscribe() {
    if (!this.hasListeners()) {
      this.#currentMutation?.removeObserver(this);
    }
  }
  onMutationUpdate(action) {
    this.#updateResult();
    this.#notify(action);
  }
  getCurrentResult() {
    return this.#currentResult;
  }
  reset() {
    this.#currentMutation?.removeObserver(this);
    this.#currentMutation = void 0;
    this.#updateResult();
    this.#notify();
  }
  mutate(variables, options) {
    this.#mutateOptions = options;
    this.#currentMutation?.removeObserver(this);
    this.#currentMutation = this.#client.getMutationCache().build(this.#client, this.options);
    this.#currentMutation.addObserver(this);
    return this.#currentMutation.execute(variables);
  }
  #updateResult() {
    const state = this.#currentMutation?.state ?? getDefaultState();
    this.#currentResult = {
      ...state,
      isPending: state.status === "pending",
      isSuccess: state.status === "success",
      isError: state.status === "error",
      isIdle: state.status === "idle",
      mutate: this.mutate,
      reset: this.reset
    };
  }
  #notify(action) {
    notifyManager.batch(() => {
      if (this.#mutateOptions && this.hasListeners()) {
        const variables = this.#currentResult.variables;
        const onMutateResult = this.#currentResult.context;
        const context = {
          client: this.#client,
          meta: this.options.meta,
          mutationKey: this.options.mutationKey
        };
        if (action?.type === "success") {
          try {
            this.#mutateOptions.onSuccess?.(
              action.data,
              variables,
              onMutateResult,
              context
            );
          } catch (e) {
            void Promise.reject(e);
          }
          try {
            this.#mutateOptions.onSettled?.(
              action.data,
              null,
              variables,
              onMutateResult,
              context
            );
          } catch (e) {
            void Promise.reject(e);
          }
        } else if (action?.type === "error") {
          try {
            this.#mutateOptions.onError?.(
              action.error,
              variables,
              onMutateResult,
              context
            );
          } catch (e) {
            void Promise.reject(e);
          }
          try {
            this.#mutateOptions.onSettled?.(
              void 0,
              action.error,
              variables,
              onMutateResult,
              context
            );
          } catch (e) {
            void Promise.reject(e);
          }
        }
      }
      this.listeners.forEach((listener) => {
        listener(this.#currentResult);
      });
    });
  }
};
function useMutation(options, queryClient) {
  const client = useQueryClient();
  const [observer] = reactExports.useState(
    () => new MutationObserver(
      client,
      options
    )
  );
  reactExports.useEffect(() => {
    observer.setOptions(options);
  }, [observer, options]);
  const result = reactExports.useSyncExternalStore(
    reactExports.useCallback(
      (onStoreChange) => observer.subscribe(notifyManager.batchCalls(onStoreChange)),
      [observer]
    ),
    () => observer.getCurrentResult(),
    () => observer.getCurrentResult()
  );
  const mutate = reactExports.useCallback(
    (variables, mutateOptions) => {
      observer.mutate(variables, mutateOptions).catch(noop);
    },
    [observer]
  );
  if (result.error && shouldThrowError(observer.options.throwOnError, [result.error])) {
    throw result.error;
  }
  return { ...result, mutate, mutateAsync: result.mutate };
}
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
    queryFn: () => apiFetch("/health"),
    refetchOnWindowFocus: false
  });
  const {
    data: version
  } = useQuery({
    queryKey: ["mcp-version"],
    queryFn: () => apiFetch("/version"),
    refetchOnWindowFocus: false
  });
  const {
    data: guard
  } = useQuery({
    queryKey: ["mcp-guard-status"],
    queryFn: () => apiFetch("/api/v1/mcp-guard/status"),
    refetchOnWindowFocus: false
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
  const dbOk = health?.database === "connected";
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
          /* @__PURE__ */ jsxRuntimeExports.jsx(StatusDot, { ok: dbOk }),
          "Database"
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-fg-muted", children: dbOk ? "Connected" : "Disconnected" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(StatusDot, { ok: !guardLocked }),
          "Guard"
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-fg-muted", children: guardLocked ? "🔒 Locked" : `🟢 Active (${callsPerHour} calls/hr)` }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-fg-muted", children: "Registered tools" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-fg-muted", title: "Requires MCP proxy — see MEU-46a", children: "N/A" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-fg-muted", children: "Uptime" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-fg-muted", title: "Requires MCP proxy — see MEU-46a", children: "N/A" })
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
  const $ = compilerRuntimeExports.c(31);
  const queryClient = useQueryClient();
  const {
    setStatus
  } = useStatusBar();
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
    t7 = /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: "text-base font-semibold text-fg mb-3", children: "MCP Guard" });
    $[17] = t7;
  } else {
    t7 = $[17];
  }
  const t8 = `text-sm font-medium ${isLocked ? "text-red-400" : "text-green-400"}`;
  const t9 = isLocked ? "🔒 Locked" : "🟢 Unlocked";
  let t10;
  if ($[18] !== t8 || $[19] !== t9) {
    t10 = /* @__PURE__ */ jsxRuntimeExports.jsx("span", { "data-testid": "mcp-guard-status", className: t8, children: t9 });
    $[18] = t8;
    $[19] = t9;
    $[20] = t10;
  } else {
    t10 = $[20];
  }
  const t11 = lockMutation.isPending ? "⏳ Working..." : isLocked ? "🔓 Unlock" : "🔒 Lock";
  let t12;
  if ($[21] !== handleToggle || $[22] !== lockMutation.isPending || $[23] !== t11) {
    t12 = /* @__PURE__ */ jsxRuntimeExports.jsx("button", { "data-testid": "mcp-guard-lock-toggle", onClick: handleToggle, disabled: lockMutation.isPending, className: "px-4 py-1.5 text-sm font-medium rounded-md border border-bg-subtle bg-bg hover:bg-bg-elevated text-fg transition-colors disabled:opacity-50 cursor-pointer", children: t11 });
    $[21] = handleToggle;
    $[22] = lockMutation.isPending;
    $[23] = t11;
    $[24] = t12;
  } else {
    t12 = $[24];
  }
  let t13;
  if ($[25] !== t10 || $[26] !== t12) {
    t13 = /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "bg-bg-elevated rounded-lg border border-bg-subtle p-4", children: [
      t7,
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-4", children: [
        t10,
        t12
      ] })
    ] });
    $[25] = t10;
    $[26] = t12;
    $[27] = t13;
  } else {
    t13 = $[27];
  }
  let t14;
  if ($[28] === /* @__PURE__ */ Symbol.for("react.memo_cache_sentinel")) {
    t14 = /* @__PURE__ */ jsxRuntimeExports.jsx(McpServerStatusPanel, {});
    $[28] = t14;
  } else {
    t14 = $[28];
  }
  let t15;
  if ($[29] !== t13) {
    t15 = /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { "data-testid": "settings-page", className: "space-y-8 max-w-3xl", children: [
      t6,
      t13,
      t14
    ] });
    $[29] = t13;
    $[30] = t15;
  } else {
    t15 = $[30];
  }
  return t15;
}
function _temp() {
  return apiFetch("/api/v1/mcp-guard/status");
}
export {
  SettingsLayout as default
};
