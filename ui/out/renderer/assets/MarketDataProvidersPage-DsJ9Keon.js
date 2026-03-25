import { r as reactExports, u as useQueryClient, a as useStatusBar, b as useQuery, d as apiFetch, j as jsxRuntimeExports } from "./index-BOpkIIp5.js";
const DUAL_AUTH_PROVIDERS = /* @__PURE__ */ new Set(["Alpaca"]);
const FREE_PROVIDERS = /* @__PURE__ */ new Set(["Yahoo Finance", "TradingView"]);
function statusIcon(status) {
  if (status === "success") return "✅";
  if (status === "failed") return "❌";
  return "⚪";
}
function buildForm(p) {
  return {
    api_key: "",
    api_secret: "",
    rate_limit: p.rate_limit,
    timeout: p.timeout,
    is_enabled: p.is_enabled
  };
}
function MarketDataProvidersPage() {
  const [selectedName, setSelectedName] = reactExports.useState(null);
  const [form, setForm] = reactExports.useState({
    api_key: "",
    api_secret: "",
    rate_limit: 5,
    timeout: 30,
    is_enabled: false
  });
  const [testResult, setTestResult] = reactExports.useState(null);
  const [testingAll, setTestingAll] = reactExports.useState(false);
  const queryClient = useQueryClient();
  const {
    setStatus
  } = useStatusBar();
  const {
    data: providers = []
  } = useQuery({
    queryKey: ["market-providers"],
    queryFn: async () => {
      try {
        return await apiFetch("/api/v1/market-data/providers");
      } catch {
        return [];
      }
    },
    refetchInterval: 5e3
  });
  const selectedProvider = providers.find((p) => p.provider_name === selectedName) ?? null;
  const handleSelect = reactExports.useCallback((provider) => {
    setSelectedName(provider.provider_name);
    setForm(buildForm(provider));
    setTestResult(null);
  }, []);
  const updateField = reactExports.useCallback((key, value) => {
    setForm((prev) => ({
      ...prev,
      [key]: value
    }));
  }, []);
  const handleSave = reactExports.useCallback(async () => {
    if (!selectedName) return;
    const payload = {
      rate_limit: form.rate_limit,
      timeout: form.timeout,
      is_enabled: form.is_enabled
    };
    if (form.api_key) payload.api_key = form.api_key;
    if (form.api_secret && DUAL_AUTH_PROVIDERS.has(selectedName)) {
      payload.api_secret = form.api_secret;
    }
    try {
      setStatus("Saving...");
      await apiFetch(`/api/v1/market-data/providers/${selectedName}`, {
        method: "PUT",
        body: JSON.stringify(payload)
      });
      await queryClient.invalidateQueries({
        queryKey: ["market-providers"]
      });
      setStatus("Saved");
    } catch (err) {
      setStatus(`Error: ${err instanceof Error ? err.message : "Failed to save"}`);
    }
  }, [selectedName, form, queryClient, setStatus]);
  const handleTest = reactExports.useCallback(async () => {
    if (!selectedName) return;
    try {
      setStatus("Testing connection...");
      setTestResult(null);
      const result = await apiFetch(`/api/v1/market-data/providers/${selectedName}/test`, {
        method: "POST"
      });
      await queryClient.invalidateQueries({
        queryKey: ["market-providers"]
      });
      setTestResult(result.message);
      setStatus(result.success ? "Connection successful" : `Test failed: ${result.message}`);
    } catch (err_0) {
      const msg = err_0 instanceof Error ? err_0.message : "Test failed";
      setTestResult(msg);
      setStatus(`Error: ${msg}`);
    }
  }, [selectedName, queryClient, setStatus]);
  const handleTestAll = reactExports.useCallback(async () => {
    const targets = providers.filter((p_0) => p_0.has_api_key);
    if (targets.length === 0) {
      setStatus("No providers with API keys to test");
      return;
    }
    setTestingAll(true);
    setStatus(`Testing ${targets.length} providers...`);
    let passed = 0;
    for (const p_1 of targets) {
      try {
        const result_0 = await apiFetch(`/api/v1/market-data/providers/${p_1.provider_name}/test`, {
          method: "POST"
        });
        if (result_0.success) passed++;
      } catch {
      }
    }
    await queryClient.invalidateQueries({
      queryKey: ["market-providers"]
    });
    setTestingAll(false);
    setStatus(`Test all complete: ${passed}/${targets.length} passed`);
  }, [providers, queryClient, setStatus]);
  const handleRemoveKey = reactExports.useCallback(async () => {
    if (!selectedName || !selectedProvider?.has_api_key) return;
    try {
      setStatus("Removing API key...");
      await apiFetch(`/api/v1/market-data/providers/${selectedName}/key`, {
        method: "DELETE"
      });
      await queryClient.invalidateQueries({
        queryKey: ["market-providers"]
      });
      setForm((prev_0) => ({
        ...prev_0,
        api_key: "",
        api_secret: ""
      }));
      setStatus("API key removed");
    } catch (err_1) {
      setStatus(`Error: ${err_1 instanceof Error ? err_1.message : "Failed to remove key"}`);
    }
  }, [selectedName, selectedProvider, queryClient, setStatus]);
  const isDualAuth = selectedName !== null && DUAL_AUTH_PROVIDERS.has(selectedName);
  const isFree = selectedName !== null && FREE_PROVIDERS.has(selectedName);
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { "data-testid": "market-data-providers", className: "flex h-full", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "w-64 shrink-0 border-r border-bg-subtle overflow-y-auto", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "p-3 border-b border-bg-subtle", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center justify-between", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { className: "text-sm font-semibold text-fg", children: "Market Data Providers" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("button", { "data-testid": "provider-test-all-btn", onClick: handleTestAll, disabled: testingAll, className: "px-2 py-1 text-xs rounded-md border border-bg-subtle bg-bg hover:bg-bg-elevated text-fg transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed", children: testingAll ? "Testing…" : "Test All" })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "mt-1 text-xs text-fg-muted", "aria-label": "Legend: connected, failed, not tested", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { "aria-hidden": "true", children: "✅" }),
          " connected",
          " ",
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { "aria-hidden": "true", children: "❌" }),
          " failed",
          " ",
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { "aria-hidden": "true", children: "⚪" }),
          " not tested"
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("ul", { "data-testid": "provider-list", className: "py-1", children: providers.map((provider_0) => /* @__PURE__ */ jsxRuntimeExports.jsx("li", { children: /* @__PURE__ */ jsxRuntimeExports.jsxs("button", { "data-testid": "provider-item", "aria-label": `${provider_0.provider_name} — ${provider_0.last_test_status ?? "not tested"}${!provider_0.is_enabled ? ", disabled" : ""}`, onClick: () => handleSelect(provider_0), className: `w-full text-left px-3 py-2 text-sm transition-colors cursor-pointer flex items-center gap-2 ${selectedName === provider_0.provider_name ? "bg-accent/10 text-accent" : "text-fg hover:bg-bg-elevated"}`, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { "aria-hidden": "true", children: statusIcon(provider_0.last_test_status) }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "flex-1 truncate", children: provider_0.provider_name }),
        !provider_0.is_enabled && /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-xs text-fg-muted", "aria-hidden": "true", children: "off" })
      ] }) }, provider_0.provider_name)) })
    ] }),
    selectedProvider ? /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { "data-testid": "provider-detail", className: "flex-1 overflow-y-auto p-4 space-y-4", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center justify-between", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { className: "text-base font-semibold text-fg", children: selectedProvider.provider_name }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-sm", "aria-hidden": "true", children: statusIcon(selectedProvider.last_test_status) })
      ] }),
      isFree ? /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2 p-3 rounded-md border border-green-500/30 bg-green-500/10", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-green-400 text-sm", "aria-hidden": "true", children: "✅" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-sm font-medium text-green-400", children: "Free — no API key required" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-xs text-fg-muted", children: "This provider works without authentication" })
        ] })
      ] }) : /* @__PURE__ */ jsxRuntimeExports.jsxs("section", { className: "space-y-3 p-3 rounded-md border border-bg-subtle bg-bg-elevated", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("h3", { className: "text-xs font-semibold text-fg-muted uppercase tracking-wide", children: [
          "API Configuration ",
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { "aria-hidden": "true", children: "🔒" })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "provider-api-key", className: "block text-xs text-fg-muted mb-1", children: "API Key" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("input", { id: "provider-api-key", "data-testid": "provider-api-key-input", type: "password", value: form.api_key, onChange: (e) => updateField("api_key", e.target.value), placeholder: selectedProvider.has_api_key ? "••••••••" : "Enter API key", className: "w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg" })
        ] }),
        isDualAuth && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "provider-api-secret", className: "block text-xs text-fg-muted mb-1", children: "API Secret" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("input", { id: "provider-api-secret", "data-testid": "provider-api-secret-input", type: "password", value: form.api_secret, onChange: (e_0) => updateField("api_secret", e_0.target.value), placeholder: selectedProvider.has_api_key ? "••••••••" : "Enter API secret", className: "w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg" })
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("section", { className: "space-y-3 p-3 rounded-md border border-bg-subtle bg-bg-elevated", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: "text-xs font-semibold text-fg-muted uppercase tracking-wide", children: "Rate Limiting" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "grid grid-cols-2 gap-3", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "provider-rate-limit", className: "block text-xs text-fg-muted mb-1", children: "Requests / min" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("input", { id: "provider-rate-limit", "data-testid": "provider-rate-limit-input", type: "number", min: 1, value: form.rate_limit, onChange: (e_1) => updateField("rate_limit", parseInt(e_1.target.value, 10) || 1), className: "w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg" })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "provider-timeout", className: "block text-xs text-fg-muted mb-1", children: "Timeout (s)" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("input", { id: "provider-timeout", "data-testid": "provider-timeout-input", type: "number", min: 1, value: form.timeout, onChange: (e_2) => updateField("timeout", parseInt(e_2.target.value, 10) || 1), className: "w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg" })
          ] })
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("section", { className: "space-y-3 p-3 rounded-md border border-bg-subtle bg-bg-elevated", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: "text-xs font-semibold text-fg-muted uppercase tracking-wide", children: "Connection Status" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("input", { "data-testid": "provider-enable-toggle", type: "checkbox", id: "provider-enable", checked: form.is_enabled, onChange: (e_3) => updateField("is_enabled", e_3.target.checked), className: "w-4 h-4 accent-accent cursor-pointer" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "provider-enable", className: "text-sm text-fg cursor-pointer", children: "Enabled" })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-sm text-fg", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { "aria-hidden": "true", children: statusIcon(selectedProvider.last_test_status) }),
          " ",
          testResult ?? (selectedProvider.last_test_status === "success" ? "Connection successful" : selectedProvider.last_test_status === "failed" ? "Last test failed" : "Not yet tested")
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("button", { "data-testid": "provider-test-btn", onClick: handleTest, className: "px-3 py-1.5 text-sm rounded-md border border-bg-subtle bg-bg hover:bg-bg-elevated text-fg transition-colors cursor-pointer", children: "Test Connection" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("section", { className: "space-y-2 p-3 rounded-md border border-bg-subtle bg-bg-elevated", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: "text-xs font-semibold text-fg-muted uppercase tracking-wide", children: "Provider Info" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-xs text-fg-muted space-y-1", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
            "Default rate limit: ",
            selectedProvider.rate_limit,
            " req/min"
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
            "Default timeout: ",
            selectedProvider.timeout,
            "s"
          ] })
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex gap-2 pt-2 border-t border-bg-subtle", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("button", { "data-testid": "provider-save-btn", onClick: handleSave, className: "px-4 py-1.5 text-sm rounded-md bg-accent text-accent-fg hover:bg-accent/90 border border-accent cursor-pointer", children: "Save Changes" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("button", { "data-testid": "provider-remove-key-btn", onClick: handleRemoveKey, disabled: !selectedProvider.has_api_key, className: "px-4 py-1.5 text-sm rounded-md bg-red-500/10 text-red-400 border border-red-500/20 hover:bg-red-500/20 cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed", children: "Remove Key" })
      ] }),
      selectedProvider.signup_url && /* @__PURE__ */ jsxRuntimeExports.jsx("button", { "data-testid": "provider-get-api-key-btn", onClick: () => window.electron.openExternal(selectedProvider.signup_url), className: "w-full px-4 py-2 text-sm rounded-md border border-accent/40 text-accent hover:bg-accent/10 transition-colors cursor-pointer flex items-center justify-center gap-2", children: isFree ? "📖 View Documentation" : "🔑 Get API Key" })
    ] }) : /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "flex-1 flex items-center justify-center text-fg-muted text-sm", children: "Select a provider to configure" })
  ] });
}
export {
  MarketDataProvidersPage
};
