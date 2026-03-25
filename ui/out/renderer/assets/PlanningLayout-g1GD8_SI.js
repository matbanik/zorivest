import { r as reactExports, u as useQueryClient, a as useStatusBar, b as useQuery, d as apiFetch, j as jsxRuntimeExports, T as TickerAutocomplete, c as compilerRuntimeExports } from "./index-BOpkIIp5.js";
const CONVICTION_ICONS = {
  high: "🟢",
  medium: "🟡",
  low: "🔴"
};
const STATUS_OPTIONS = ["draft", "active", "executed", "cancelled"];
const CONVICTION_OPTIONS = ["high", "medium", "low"];
const DIRECTION_OPTIONS = ["BOT", "SLD"];
const TIMEFRAME_OPTIONS = ["scalp", "intraday", "swing", "position"];
function convictionIcon(conviction) {
  return CONVICTION_ICONS[conviction.toLowerCase()] ?? "⚪";
}
const NEW_PLAN = {
  id: 0,
  ticker: "",
  direction: "BOT",
  conviction: "medium",
  strategy_name: "",
  strategy_description: "",
  entry_price: 0,
  stop_loss: 0,
  target_price: 0,
  entry_conditions: "",
  exit_conditions: "",
  timeframe: "intraday",
  status: "draft",
  linked_trade_id: null,
  account_id: null
};
function computeRiskReward(entry, stop, target) {
  const riskPerShare = Math.abs(entry - stop);
  const rewardPerShare = Math.abs(target - entry);
  const ratio = riskPerShare > 0 ? rewardPerShare / riskPerShare : 0;
  return {
    riskPerShare,
    rewardPerShare,
    ratio: Math.round(ratio * 100) / 100
  };
}
function formatTimestamp(iso) {
  if (!iso) return "";
  try {
    const d = new Date(iso);
    const mm = String(d.getMonth() + 1).padStart(2, "0");
    const dd = String(d.getDate()).padStart(2, "0");
    const yyyy = d.getFullYear();
    const hours = d.getHours();
    const minutes = String(d.getMinutes()).padStart(2, "0");
    const ampm = hours >= 12 ? "PM" : "AM";
    const h = hours % 12 || 12;
    return `${mm}-${dd}-${yyyy} ${h}:${minutes}${ampm}`;
  } catch {
    return iso;
  }
}
function TradePlanPage({
  onOpenCalculator
}) {
  const [selectedPlan, setSelectedPlan] = reactExports.useState(null);
  const [isCreating, setIsCreating] = reactExports.useState(false);
  const [statusFilter, setStatusFilter] = reactExports.useState("");
  const [convictionFilter, setConvictionFilter] = reactExports.useState("");
  const [form, setForm] = reactExports.useState(NEW_PLAN);
  const queryClient = useQueryClient();
  const {
    setStatus
  } = useStatusBar();
  const {
    data: plans = []
  } = useQuery({
    queryKey: ["trade-plans"],
    queryFn: async () => {
      try {
        const result = await apiFetch("/api/v1/trade-plans?limit=200");
        return result;
      } catch {
        return [];
      }
    },
    refetchInterval: 5e3
  });
  const {
    data: accounts = []
  } = useQuery({
    queryKey: ["accounts"],
    queryFn: async () => {
      try {
        return await apiFetch("/api/v1/accounts");
      } catch {
        return [];
      }
    }
  });
  const strategyNames = reactExports.useMemo(() => {
    const names = new Set(plans.map((p) => p.strategy_name).filter(Boolean));
    return Array.from(names).sort();
  }, [plans]);
  const [linkedTradeId, setLinkedTradeId] = reactExports.useState("");
  const [tradePickerSearch, setTradePickerSearch] = reactExports.useState("");
  const [tradePickerLabel, setTradePickerLabel] = reactExports.useState("");
  const [sharesPlanned, setSharesPlanned] = reactExports.useState("");
  const isExecutedStatus = form.status === "executed";
  const planTicker = form.ticker ?? "";
  const {
    data: linkableTrades = []
  } = useQuery({
    queryKey: ["trades-for-link", planTicker],
    queryFn: async () => {
      try {
        const result_0 = await apiFetch(`/api/v1/trades?ticker=${encodeURIComponent(planTicker)}&limit=50`);
        return result_0.items ?? [];
      } catch {
        return [];
      }
    },
    enabled: planTicker.length > 0
    // MEU-70b: always fetch when ticker set; picker is shown disabled
  });
  const filteredPlans = reactExports.useMemo(() => {
    let result_1 = plans;
    if (statusFilter) result_1 = result_1.filter((p_0) => p_0.status === statusFilter);
    if (convictionFilter) result_1 = result_1.filter((p_1) => p_1.conviction === convictionFilter);
    return result_1;
  }, [plans, statusFilter, convictionFilter]);
  const handleSelectPlan = reactExports.useCallback((plan) => {
    setSelectedPlan(plan);
    setIsCreating(false);
    setForm({
      ...plan
    });
    setLinkedTradeId(plan.linked_trade_id ?? "");
    setTradePickerLabel(plan.linked_trade_id ?? "");
    setSharesPlanned("");
  }, []);
  const handleNewPlan = reactExports.useCallback(() => {
    setSelectedPlan(null);
    setIsCreating(true);
    setForm({
      ...NEW_PLAN
    });
    setLinkedTradeId("");
    setTradePickerLabel("");
    setSharesPlanned("");
  }, []);
  const handleClose = reactExports.useCallback(() => {
    setSelectedPlan(null);
    setIsCreating(false);
  }, []);
  const updateField = reactExports.useCallback((key, value) => {
    setForm((prev) => ({
      ...prev,
      [key]: value
    }));
  }, []);
  const rr = reactExports.useMemo(() => {
    return computeRiskReward(form.entry_price ?? 0, form.stop_loss ?? 0, form.target_price ?? 0);
  }, [form.entry_price, form.stop_loss, form.target_price]);
  const handleSave = reactExports.useCallback(async () => {
    const payload = {
      ticker: form.ticker,
      direction: form.direction,
      conviction: form.conviction,
      strategy_name: form.strategy_name,
      strategy_description: form.strategy_description,
      entry_price: form.entry_price,
      stop_loss: form.stop_loss,
      target_price: form.target_price,
      entry_conditions: form.entry_conditions,
      exit_conditions: form.exit_conditions,
      timeframe: form.timeframe,
      account_id: form.account_id || null
    };
    try {
      if (isCreating) {
        setStatus("Creating plan...");
        await apiFetch("/api/v1/trade-plans", {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify(payload)
        });
        setStatus("Plan created");
      } else if (selectedPlan) {
        setStatus("Updating plan...");
        await apiFetch(`/api/v1/trade-plans/${selectedPlan.id}`, {
          method: "PUT",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify(payload)
        });
        setStatus("Plan updated");
      }
      await queryClient.invalidateQueries({
        queryKey: ["trade-plans"]
      });
      handleClose();
    } catch (err) {
      setStatus(`Error: ${err instanceof Error ? err.message : "Failed to save"}`);
    }
  }, [form, isCreating, selectedPlan, queryClient, setStatus, handleClose]);
  const handleStatusChange = reactExports.useCallback(async (planId, newStatus) => {
    try {
      setStatus(`Changing status to ${newStatus}...`);
      await apiFetch(`/api/v1/trade-plans/${planId}/status`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          status: newStatus
        })
      });
      setStatus(`Status → ${newStatus}`);
      await queryClient.invalidateQueries({
        queryKey: ["trade-plans"]
      });
    } catch (err_0) {
      setStatus(`Error: ${err_0 instanceof Error ? err_0.message : "Failed"}`);
    }
  }, [queryClient, setStatus]);
  const handleDelete = reactExports.useCallback(async () => {
    if (!selectedPlan) return;
    try {
      setStatus("Deleting plan...");
      await apiFetch(`/api/v1/trade-plans/${selectedPlan.id}`, {
        method: "DELETE"
      });
      setStatus("Plan deleted");
      await queryClient.invalidateQueries({
        queryKey: ["trade-plans"]
      });
      handleClose();
    } catch (err_1) {
      setStatus(`Error: ${err_1 instanceof Error ? err_1.message : "Failed"}`);
    }
  }, [selectedPlan, queryClient, setStatus, handleClose]);
  const handleCalculatePosition = reactExports.useCallback(() => {
    window.dispatchEvent(new CustomEvent("zorivest:open-calculator", {
      detail: {
        entry_price: form.entry_price ?? 0,
        stop_loss: form.stop_loss ?? 0,
        target_price: form.target_price ?? 0
      }
    }));
  }, [form.entry_price, form.stop_loss, form.target_price]);
  const isDetailOpen = isCreating || selectedPlan !== null;
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { "data-testid": "trade-plan-page", className: "flex h-full", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: `flex-1 min-w-0 transition-all ${isDetailOpen ? "w-[55%]" : "w-full"}`, children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "p-4", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center justify-between mb-4", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { className: "text-lg font-semibold text-fg", children: "Trade Plans" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2", children: [
          onOpenCalculator && /* @__PURE__ */ jsxRuntimeExports.jsx("button", { "data-testid": "open-calculator-btn", onClick: onOpenCalculator, className: "px-3 py-1.5 text-sm font-medium rounded-md border border-bg-subtle bg-bg hover:bg-bg-elevated text-fg transition-colors cursor-pointer", children: "🧮 Calculator" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("button", { "data-testid": "new-plan-btn", onClick: handleNewPlan, className: "px-4 py-1.5 text-sm font-medium rounded-md border border-bg-subtle bg-bg hover:bg-bg-elevated text-fg transition-colors cursor-pointer", children: "+ New Plan" })
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex gap-2 mb-4", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("select", { "data-testid": "plan-status-filter", "aria-label": "Filter by status", value: statusFilter, onChange: (e) => setStatusFilter(e.target.value), className: "px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "", children: "All Statuses" }),
          STATUS_OPTIONS.map((s) => /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: s, children: s.charAt(0).toUpperCase() + s.slice(1) }, s))
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("select", { "data-testid": "plan-conviction-filter", "aria-label": "Filter by conviction", value: convictionFilter, onChange: (e_0) => setConvictionFilter(e_0.target.value), className: "px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "", children: "All Convictions" }),
          CONVICTION_OPTIONS.map((c) => /* @__PURE__ */ jsxRuntimeExports.jsxs("option", { value: c, children: [
            convictionIcon(c),
            " ",
            c.charAt(0).toUpperCase() + c.slice(1)
          ] }, c))
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "space-y-2", "data-testid": "plan-list", children: [
        filteredPlans.length === 0 && /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-sm text-fg-muted py-4 text-center", children: "No plans found" }),
        filteredPlans.map((plan_0) => /* @__PURE__ */ jsxRuntimeExports.jsxs("button", { "data-testid": `plan-card-${plan_0.id}`, onClick: () => handleSelectPlan(plan_0), className: `w-full text-left px-4 py-3 rounded-md border cursor-pointer transition-colors ${selectedPlan?.id === plan_0.id ? "border-accent bg-accent/10" : "border-bg-subtle bg-bg hover:bg-bg-elevated"}`, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center justify-between", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2", children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("span", { "data-testid": "conviction-indicator", children: convictionIcon(plan_0.conviction) }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "font-medium text-fg", children: plan_0.ticker }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-xs text-fg-muted", children: plan_0.direction })
            ] }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2", children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: `text-xs px-2 py-0.5 rounded-full ${plan_0.status === "active" ? "bg-green-500/20 text-green-400" : plan_0.status === "executed" ? "bg-blue-500/20 text-blue-400" : plan_0.status === "cancelled" ? "bg-red-500/20 text-red-400" : "bg-bg-elevated text-fg-muted"}`, children: plan_0.status }),
              plan_0.risk_reward_ratio > 0 && /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: "text-xs text-fg-muted", children: [
                "R:R ",
                plan_0.risk_reward_ratio.toFixed(1)
              ] })
            ] })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-xs text-fg-muted mt-1", children: [
            plan_0.strategy_name,
            " · ",
            plan_0.timeframe
          ] })
        ] }, plan_0.id))
      ] })
    ] }) }),
    isDetailOpen && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-[45%] border-l border-bg-subtle overflow-y-auto", "data-testid": "plan-detail-panel", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "p-4", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center justify-between mb-4", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: "text-md font-semibold text-fg", children: isCreating ? "New Trade Plan" : `Plan #${selectedPlan?.id}` }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("button", { onClick: handleClose, className: "text-fg-muted hover:text-fg cursor-pointer", "data-testid": "close-plan-detail", children: "✕" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "space-y-3", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "grid grid-cols-2 gap-2", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("label", { className: "block text-xs text-fg-muted mb-1", children: "Ticker" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(TickerAutocomplete, { value: form.ticker ?? "", onChange: (val) => updateField("ticker", val), placeholder: "AAPL", "data-testid": "plan-ticker" })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("label", { className: "block text-xs text-fg-muted mb-1", children: "Direction" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("select", { "data-testid": "plan-direction", value: form.direction ?? "BOT", onChange: (e_1) => updateField("direction", e_1.target.value), className: "w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg", children: DIRECTION_OPTIONS.map((d) => /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: d, children: d === "BOT" ? "Buy" : "Sell" }, d)) })
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "grid grid-cols-2 gap-2", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("label", { className: "block text-xs text-fg-muted mb-1", children: "Conviction" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("select", { "data-testid": "plan-conviction", value: form.conviction ?? "medium", onChange: (e_2) => updateField("conviction", e_2.target.value), className: "w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg", children: CONVICTION_OPTIONS.map((c_0) => /* @__PURE__ */ jsxRuntimeExports.jsxs("option", { value: c_0, children: [
              convictionIcon(c_0),
              " ",
              c_0.charAt(0).toUpperCase() + c_0.slice(1)
            ] }, c_0)) })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("label", { className: "block text-xs text-fg-muted mb-1", children: "Timeframe" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("select", { "data-testid": "plan-timeframe", value: form.timeframe ?? "intraday", onChange: (e_3) => updateField("timeframe", e_3.target.value), className: "w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg", children: TIMEFRAME_OPTIONS.map((t) => /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: t, children: t.charAt(0).toUpperCase() + t.slice(1) }, t)) })
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("label", { className: "block text-xs text-fg-muted mb-1", children: "Strategy Name" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("input", { "data-testid": "plan-strategy-name", list: "strategy-suggestions", value: form.strategy_name ?? "", onChange: (e_4) => updateField("strategy_name", e_4.target.value), className: "w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg", placeholder: "Breakout above resistance" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("datalist", { id: "strategy-suggestions", children: strategyNames.map((name) => /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: name }, name)) })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("label", { className: "block text-xs text-fg-muted mb-1", children: "Strategy Description" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("textarea", { "data-testid": "plan-strategy-description", value: form.strategy_description ?? "", onChange: (e_5) => updateField("strategy_description", e_5.target.value), rows: 2, className: "w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg resize-y" })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "grid grid-cols-3 gap-2", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("label", { className: "block text-xs text-fg-muted mb-1", children: "Entry Price" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("input", { "data-testid": "plan-entry-price", type: "number", step: "0.01", value: form.entry_price ?? 0, onChange: (e_6) => updateField("entry_price", parseFloat(e_6.target.value) || 0), className: "w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg" })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("label", { className: "block text-xs text-fg-muted mb-1", children: "Stop Loss" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("input", { "data-testid": "plan-stop-loss", type: "number", step: "0.01", value: form.stop_loss ?? 0, onChange: (e_7) => updateField("stop_loss", parseFloat(e_7.target.value) || 0), className: "w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg" })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("label", { className: "block text-xs text-fg-muted mb-1", children: "Target" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("input", { "data-testid": "plan-target-price", type: "number", step: "0.01", value: form.target_price ?? 0, onChange: (e_8) => updateField("target_price", parseFloat(e_8.target.value) || 0), className: "w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg" })
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "grid grid-cols-3 gap-2 py-2 px-3 rounded-md bg-bg-elevated text-sm", "data-testid": "plan-rr-display", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-xs text-fg-muted", children: "Risk/Share" }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-fg font-mono", children: [
              "$",
              rr.riskPerShare.toFixed(2)
            ] })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-xs text-fg-muted", children: "Reward/Share" }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-fg font-mono", children: [
              "$",
              rr.rewardPerShare.toFixed(2)
            ] })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-xs text-fg-muted", children: "R:R Ratio" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: `font-mono font-semibold ${rr.ratio >= 2 ? "text-green-400" : rr.ratio >= 1 ? "text-yellow-400" : "text-red-400"}`, children: rr.ratio.toFixed(2) })
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("button", { "data-testid": "plan-calculate-position-btn", onClick: handleCalculatePosition, className: "w-full px-3 py-1.5 text-sm rounded-md border border-accent/30 bg-accent/5 text-accent hover:bg-accent/10 cursor-pointer transition-colors", children: "🧮 Calculate Position Size" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { "data-testid": "plan-shares-section", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("label", { className: "block text-xs text-fg-muted mb-1", children: [
            "Planned Shares",
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "ml-1 text-fg-muted/50 font-normal", children: "(optional — override calculator result)" })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex gap-2 items-center", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("input", { "data-testid": "plan-shares-planned", type: "number", min: "0", step: "1", value: sharesPlanned, onChange: (e_9) => setSharesPlanned(e_9.target.value === "" ? "" : parseInt(e_9.target.value) || 0), placeholder: "e.g. 100", className: "flex-1 px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("button", { "data-testid": "plan-copy-from-calc-btn", type: "button", onClick: handleCalculatePosition, title: "Open calculator and copy result into Planned Shares", className: "px-3 py-1.5 text-xs rounded-md border border-bg-subtle bg-bg text-fg-muted hover:bg-bg-elevated cursor-pointer transition-colors whitespace-nowrap", children: "📋 Copy from Calc" })
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("label", { className: "block text-xs text-fg-muted mb-1", children: "Entry Conditions" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("textarea", { "data-testid": "plan-entry-conditions", value: form.entry_conditions ?? "", onChange: (e_10) => updateField("entry_conditions", e_10.target.value), rows: 2, className: "w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg resize-y", placeholder: "What must be true before entering?" })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("label", { className: "block text-xs text-fg-muted mb-1", children: "Exit Conditions" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("textarea", { "data-testid": "plan-exit-conditions", value: form.exit_conditions ?? "", onChange: (e_11) => updateField("exit_conditions", e_11.target.value), rows: 2, className: "w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg resize-y", placeholder: "When to exit?" })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("label", { className: "block text-xs text-fg-muted mb-1", children: "Account" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("select", { "data-testid": "plan-account-select", value: form.account_id ?? "", onChange: (e_12) => updateField("account_id", e_12.target.value || null), className: "w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "", children: "None (no account)" }),
            accounts.map((acct) => /* @__PURE__ */ jsxRuntimeExports.jsxs("option", { value: acct.id, children: [
              acct.name,
              " (",
              acct.account_type,
              ")"
            ] }, acct.id))
          ] })
        ] }),
        selectedPlan?.linked_trade_id && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("label", { className: "block text-xs text-fg-muted mb-1", children: "Linked Trade" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("input", { "data-testid": "plan-linked-trade", value: selectedPlan.linked_trade_id, readOnly: true, className: "w-full px-3 py-1.5 text-sm rounded-md bg-bg-elevated border border-bg-subtle text-fg-muted cursor-not-allowed" })
        ] }),
        selectedPlan?.executed_at && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-xs text-fg-muted", "data-testid": "plan-executed-at", children: [
          "Executed on ",
          formatTimestamp(selectedPlan.executed_at)
        ] }),
        selectedPlan?.cancelled_at && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-xs text-fg-muted", "data-testid": "plan-cancelled-at", children: [
          "Cancelled on ",
          formatTimestamp(selectedPlan.cancelled_at)
        ] }),
        selectedPlan && !isCreating && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { "data-testid": "plan-status-section", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("label", { className: "block text-xs text-fg-muted mb-1", children: "Status" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "flex gap-1", "data-testid": "plan-status-buttons", role: "group", "aria-label": "Plan status", children: [{
            value: "draft",
            label: "Draft",
            active: "bg-bg-elevated text-fg border-bg-subtle"
          }, {
            value: "active",
            label: "Active",
            active: "bg-blue-500/20 text-blue-300 border-blue-500/40"
          }, {
            value: "executed",
            label: "Executed",
            active: "bg-green-500/20 text-green-300 border-green-500/40"
          }, {
            value: "cancelled",
            label: "Cancelled",
            active: "bg-red-500/15 text-red-400 border-red-500/30"
          }].map(({
            value: value_0,
            label,
            active
          }) => {
            const isCurrent = (form.status ?? selectedPlan.status) === value_0;
            return /* @__PURE__ */ jsxRuntimeExports.jsx("button", { type: "button", "data-testid": `plan-status-${value_0}`, onClick: async () => {
              updateField("status", value_0);
              await handleStatusChange(selectedPlan.id, value_0);
            }, className: `flex-1 px-2 py-1.5 text-xs rounded-md border cursor-pointer transition-colors font-medium ${isCurrent ? active : "bg-bg text-fg-muted border-bg-subtle hover:bg-bg-elevated"}`, "aria-pressed": isCurrent, children: label }, value_0);
          }) })
        ] }),
        selectedPlan && !isCreating && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { "data-testid": "plan-trade-picker", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2 mb-1", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: `text-xs font-medium ${isExecutedStatus ? "text-green-400" : "text-fg-muted"}`, children: "⚡ Execution" }),
            !isExecutedStatus && /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-xs text-fg-muted/60 italic", children: "— Set status to Executed to link an execution record" })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("label", { className: "block text-xs text-fg-muted mb-1", children: "Link to Trade" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "relative", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("input", { "data-testid": "trade-picker-search", type: "text", value: tradePickerLabel || tradePickerSearch, disabled: !isExecutedStatus, onChange: (e_13) => {
              setTradePickerLabel("");
              setTradePickerSearch(e_13.target.value);
            }, placeholder: isExecutedStatus ? "Filter trades..." : "Select Executed status first", title: !isExecutedStatus ? "Change plan status to Executed to link an execution record" : void 0, className: `w-full px-3 py-1.5 text-sm rounded-md border text-fg pr-8 transition-colors ${isExecutedStatus ? "bg-bg border-green-500/30 cursor-text" : "bg-bg-elevated border-bg-subtle text-fg-muted cursor-not-allowed opacity-50"}` }),
            isExecutedStatus && (linkedTradeId || form.linked_trade_id) && /* @__PURE__ */ jsxRuntimeExports.jsx("button", { type: "button", "data-testid": "trade-picker-clear", onClick: () => {
              setLinkedTradeId("");
              setTradePickerLabel("");
              setTradePickerSearch("");
              updateField("linked_trade_id", null);
            }, className: "absolute right-2 top-1/2 -translate-y-1/2 text-fg-muted hover:text-fg text-xs cursor-pointer", title: "Remove linked trade", children: "×" })
          ] }),
          isExecutedStatus && !tradePickerLabel && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "max-h-40 overflow-y-auto rounded-md border border-bg-subtle text-sm mt-1", children: [
            linkableTrades.filter((t_0) => {
              if (!tradePickerSearch) return true;
              const label_0 = `${formatTimestamp(t_0.time)} ${t_0.action} ${t_0.quantity}@${t_0.price} ${t_0.instrument}`.toLowerCase();
              return label_0.includes(tradePickerSearch.toLowerCase());
            }).map((t_1) => {
              const label_1 = `${formatTimestamp(t_1.time)} — ${t_1.action} ${t_1.quantity}@${t_1.price}`;
              const isSelected = (linkedTradeId || form.linked_trade_id) === t_1.exec_id;
              return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { role: "option", "aria-selected": isSelected, "data-testid": `trade-option-${t_1.exec_id}`, onClick: () => {
                setLinkedTradeId(t_1.exec_id);
                setTradePickerLabel(label_1);
                setTradePickerSearch("");
                updateField("linked_trade_id", t_1.exec_id);
              }, className: `px-3 py-1.5 cursor-pointer transition-colors flex items-center gap-2 ${isSelected ? "bg-accent/20 text-fg font-medium" : "text-fg hover:bg-bg-subtle"}`, children: [
                isSelected && /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-accent text-xs", children: "✓" }),
                label_1
              ] }, t_1.exec_id);
            }),
            linkableTrades.length === 0 && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "px-3 py-1.5 text-fg-muted", children: [
              "No trades found for ",
              planTicker
            ] })
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex gap-2 pt-3 border-t border-bg-subtle", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("button", { "data-testid": "plan-save-btn", onClick: handleSave, className: "px-4 py-1.5 text-sm rounded-md bg-accent text-accent-fg hover:bg-accent/90 border border-accent cursor-pointer", children: isCreating ? "Create Plan" : "Save Changes" }),
          selectedPlan && !isCreating && /* @__PURE__ */ jsxRuntimeExports.jsx("button", { "data-testid": "plan-delete-btn", onClick: handleDelete, className: "px-4 py-1.5 text-sm rounded-md bg-red-500/10 text-red-400 border border-red-500/20 hover:bg-red-500/20 cursor-pointer", children: "Delete" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("button", { onClick: handleClose, className: "px-4 py-1.5 text-sm rounded-md bg-bg text-fg-muted hover:text-fg border border-bg-subtle cursor-pointer", children: "Cancel" })
        ] })
      ] })
    ] }) })
  ] });
}
function useWatchlistQuotes(tickers) {
  const $ = compilerRuntimeExports.c(6);
  let t0;
  if ($[0] === /* @__PURE__ */ Symbol.for("react.memo_cache_sentinel")) {
    t0 = {};
    $[0] = t0;
  } else {
    t0 = $[0];
  }
  const [quotes, setQuotes] = reactExports.useState(t0);
  let t1;
  let t2;
  if ($[1] !== tickers) {
    t1 = () => {
      if (tickers.length === 0) {
        return;
      }
      let cancelled = false;
      setQuotes((prev) => {
        const next = {
          ...prev
        };
        tickers.forEach((t) => {
          if (!(t in next)) {
            next[t] = null;
          }
        });
        return next;
      });
      tickers.forEach((ticker) => {
        apiFetch(`/api/v1/market-data/quote?ticker=${encodeURIComponent(ticker)}`).then((q) => {
          if (!cancelled) {
            setQuotes((prev_0) => ({
              ...prev_0,
              [ticker]: q
            }));
          }
        }).catch(_temp$1);
      });
      return () => {
        cancelled = true;
      };
    };
    t2 = tickers.join(",");
    $[1] = tickers;
    $[2] = t1;
    $[3] = t2;
  } else {
    t1 = $[2];
    t2 = $[3];
  }
  let t3;
  if ($[4] !== t2) {
    t3 = [t2];
    $[4] = t2;
    $[5] = t3;
  } else {
    t3 = $[5];
  }
  reactExports.useEffect(t1, t3);
  return quotes;
}
function _temp$1() {
}
function WatchlistPage() {
  const $ = compilerRuntimeExports.c(59);
  const [selectedList, setSelectedList] = reactExports.useState(null);
  const [isCreating, setIsCreating] = reactExports.useState(false);
  const [nameInput, setNameInput] = reactExports.useState("");
  const [descInput, setDescInput] = reactExports.useState("");
  const [tickerInput, setTickerInput] = reactExports.useState("");
  const [notesInput, setNotesInput] = reactExports.useState("");
  const queryClient = useQueryClient();
  const {
    setStatus
  } = useStatusBar();
  let t0;
  if ($[0] !== selectedList?.items) {
    t0 = selectedList?.items.map(_temp2) ?? [];
    $[0] = selectedList?.items;
    $[1] = t0;
  } else {
    t0 = $[1];
  }
  const visibleTickers = t0;
  const quotes = useWatchlistQuotes(visibleTickers);
  let t1;
  if ($[2] === /* @__PURE__ */ Symbol.for("react.memo_cache_sentinel")) {
    t1 = {
      queryKey: ["watchlists"],
      queryFn: _temp3,
      refetchInterval: 5e3
    };
    $[2] = t1;
  } else {
    t1 = $[2];
  }
  const {
    data: t2
  } = useQuery(t1);
  let t3;
  if ($[3] !== t2) {
    t3 = t2 === void 0 ? [] : t2;
    $[3] = t2;
    $[4] = t3;
  } else {
    t3 = $[4];
  }
  const watchlists = t3;
  let t4;
  if ($[5] === /* @__PURE__ */ Symbol.for("react.memo_cache_sentinel")) {
    t4 = (wl) => {
      setSelectedList(wl);
      setIsCreating(false);
      setNameInput(wl.name);
      setDescInput(wl.description);
    };
    $[5] = t4;
  } else {
    t4 = $[5];
  }
  const handleSelect = t4;
  let t5;
  if ($[6] === /* @__PURE__ */ Symbol.for("react.memo_cache_sentinel")) {
    t5 = () => {
      setSelectedList(null);
      setIsCreating(true);
      setNameInput("");
      setDescInput("");
    };
    $[6] = t5;
  } else {
    t5 = $[6];
  }
  const handleNew = t5;
  let t6;
  if ($[7] === /* @__PURE__ */ Symbol.for("react.memo_cache_sentinel")) {
    t6 = () => {
      setSelectedList(null);
      setIsCreating(false);
    };
    $[7] = t6;
  } else {
    t6 = $[7];
  }
  const handleClose = t6;
  let t7;
  if ($[8] !== descInput || $[9] !== isCreating || $[10] !== nameInput || $[11] !== queryClient || $[12] !== selectedList || $[13] !== setStatus) {
    t7 = async () => {
      try {
        if (isCreating) {
          setStatus("Creating watchlist...");
          await apiFetch("/api/v1/watchlists/", {
            method: "POST",
            headers: {
              "Content-Type": "application/json"
            },
            body: JSON.stringify({
              name: nameInput,
              description: descInput
            })
          });
          setStatus("Watchlist created");
        } else {
          if (selectedList) {
            setStatus("Updating watchlist...");
            await apiFetch(`/api/v1/watchlists/${selectedList.id}`, {
              method: "PUT",
              headers: {
                "Content-Type": "application/json"
              },
              body: JSON.stringify({
                name: nameInput,
                description: descInput
              })
            });
            setStatus("Watchlist updated");
          }
        }
        await queryClient.invalidateQueries({
          queryKey: ["watchlists"]
        });
        handleClose();
      } catch (t82) {
        const err = t82;
        setStatus(`Error: ${err instanceof Error ? err.message : "Failed"}`);
      }
    };
    $[8] = descInput;
    $[9] = isCreating;
    $[10] = nameInput;
    $[11] = queryClient;
    $[12] = selectedList;
    $[13] = setStatus;
    $[14] = t7;
  } else {
    t7 = $[14];
  }
  const handleSave = t7;
  let t8;
  if ($[15] !== queryClient || $[16] !== selectedList || $[17] !== setStatus) {
    t8 = async () => {
      if (!selectedList) {
        return;
      }
      try {
        setStatus("Deleting watchlist...");
        await apiFetch(`/api/v1/watchlists/${selectedList.id}`, {
          method: "DELETE"
        });
        setStatus("Watchlist deleted");
        await queryClient.invalidateQueries({
          queryKey: ["watchlists"]
        });
        handleClose();
      } catch (t92) {
        const err_0 = t92;
        setStatus(`Error: ${err_0 instanceof Error ? err_0.message : "Failed"}`);
      }
    };
    $[15] = queryClient;
    $[16] = selectedList;
    $[17] = setStatus;
    $[18] = t8;
  } else {
    t8 = $[18];
  }
  const handleDelete = t8;
  let t9;
  if ($[19] !== notesInput || $[20] !== queryClient || $[21] !== selectedList || $[22] !== setStatus || $[23] !== tickerInput) {
    t9 = async () => {
      if (!selectedList || !tickerInput.trim()) {
        return;
      }
      try {
        setStatus("Adding ticker...");
        await apiFetch(`/api/v1/watchlists/${selectedList.id}/items`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            ticker: tickerInput.trim().toUpperCase(),
            notes: notesInput
          })
        });
        setStatus("Ticker added");
        setTickerInput("");
        setNotesInput("");
        await queryClient.invalidateQueries({
          queryKey: ["watchlists"]
        });
        const updated = await apiFetch(`/api/v1/watchlists/${selectedList.id}`);
        setSelectedList(updated);
      } catch (t102) {
        const err_1 = t102;
        setStatus(`Error: ${err_1 instanceof Error ? err_1.message : "Failed"}`);
      }
    };
    $[19] = notesInput;
    $[20] = queryClient;
    $[21] = selectedList;
    $[22] = setStatus;
    $[23] = tickerInput;
    $[24] = t9;
  } else {
    t9 = $[24];
  }
  const handleAddTicker = t9;
  let t10;
  if ($[25] !== queryClient || $[26] !== selectedList || $[27] !== setStatus) {
    t10 = async (ticker) => {
      if (!selectedList) {
        return;
      }
      try {
        setStatus("Removing ticker...");
        await apiFetch(`/api/v1/watchlists/${selectedList.id}/items/${ticker}`, {
          method: "DELETE"
        });
        setStatus("Ticker removed");
        await queryClient.invalidateQueries({
          queryKey: ["watchlists"]
        });
        const updated_0 = await apiFetch(`/api/v1/watchlists/${selectedList.id}`);
        setSelectedList(updated_0);
      } catch (t112) {
        const err_2 = t112;
        setStatus(`Error: ${err_2 instanceof Error ? err_2.message : "Failed"}`);
      }
    };
    $[25] = queryClient;
    $[26] = selectedList;
    $[27] = setStatus;
    $[28] = t10;
  } else {
    t10 = $[28];
  }
  const handleRemoveTicker = t10;
  const isDetailOpen = isCreating || selectedList !== null;
  const t11 = `flex-1 min-w-0 transition-all ${isDetailOpen ? "w-[40%]" : "w-full"}`;
  let t12;
  if ($[29] === /* @__PURE__ */ Symbol.for("react.memo_cache_sentinel")) {
    t12 = /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center justify-between mb-4", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { className: "text-lg font-semibold text-fg", children: "Watchlists" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("button", { "data-testid": "new-watchlist-btn", onClick: handleNew, className: "px-4 py-1.5 text-sm font-medium rounded-md border border-bg-subtle bg-bg hover:bg-bg-elevated text-fg transition-colors cursor-pointer", children: "+ New Watchlist" })
    ] });
    $[29] = t12;
  } else {
    t12 = $[29];
  }
  let t13;
  if ($[30] !== watchlists.length) {
    t13 = watchlists.length === 0 && /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-sm text-fg-muted py-4 text-center", children: "No watchlists yet" });
    $[30] = watchlists.length;
    $[31] = t13;
  } else {
    t13 = $[31];
  }
  let t14;
  if ($[32] !== selectedList?.id || $[33] !== watchlists) {
    let t152;
    if ($[35] !== selectedList?.id) {
      t152 = (wl_0) => /* @__PURE__ */ jsxRuntimeExports.jsxs("button", { "data-testid": `watchlist-card-${wl_0.id}`, onClick: () => handleSelect(wl_0), className: `w-full text-left px-4 py-3 rounded-md border cursor-pointer transition-colors ${selectedList?.id === wl_0.id ? "border-accent bg-accent/10" : "border-bg-subtle bg-bg hover:bg-bg-elevated"}`, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center justify-between", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "font-medium text-fg", children: wl_0.name }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-xs text-fg-muted", children: wl_0.items.length === 0 ? "0 items" : wl_0.items.length <= 5 ? wl_0.items.map(_temp4).join(", ") : `${wl_0.items.slice(0, 5).map(_temp5).join(", ")} +${wl_0.items.length - 5}` })
        ] }),
        wl_0.description && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-xs text-fg-muted mt-1", children: wl_0.description })
      ] }, wl_0.id);
      $[35] = selectedList?.id;
      $[36] = t152;
    } else {
      t152 = $[36];
    }
    t14 = watchlists.map(t152);
    $[32] = selectedList?.id;
    $[33] = watchlists;
    $[34] = t14;
  } else {
    t14 = $[34];
  }
  let t15;
  if ($[37] !== t13 || $[38] !== t14) {
    t15 = /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "p-4", children: [
      t12,
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "space-y-2", "data-testid": "watchlist-list", children: [
        t13,
        t14
      ] })
    ] });
    $[37] = t13;
    $[38] = t14;
    $[39] = t15;
  } else {
    t15 = $[39];
  }
  let t16;
  if ($[40] !== t11 || $[41] !== t15) {
    t16 = /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: t11, children: t15 });
    $[40] = t11;
    $[41] = t15;
    $[42] = t16;
  } else {
    t16 = $[42];
  }
  let t17;
  if ($[43] !== descInput || $[44] !== handleAddTicker || $[45] !== handleDelete || $[46] !== handleRemoveTicker || $[47] !== handleSave || $[48] !== isCreating || $[49] !== isDetailOpen || $[50] !== nameInput || $[51] !== notesInput || $[52] !== quotes || $[53] !== selectedList || $[54] !== tickerInput) {
    t17 = isDetailOpen && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-[60%] border-l border-bg-subtle overflow-y-auto", "data-testid": "watchlist-detail-panel", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "p-4", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center justify-between mb-4", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: "text-md font-semibold text-fg", children: isCreating ? "New Watchlist" : selectedList?.name }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("button", { onClick: handleClose, className: "text-fg-muted hover:text-fg cursor-pointer", "data-testid": "close-watchlist-detail", children: "✕" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "space-y-3 mb-4", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("label", { className: "block text-xs text-fg-muted mb-1", children: "Name" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("input", { "data-testid": "watchlist-name", value: nameInput, onChange: (e) => setNameInput(e.target.value), className: "w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg", placeholder: "My Watchlist" })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("label", { className: "block text-xs text-fg-muted mb-1", children: "Description" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("textarea", { "data-testid": "watchlist-description", value: descInput, onChange: (e_0) => setDescInput(e_0.target.value), rows: 2, className: "w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg resize-y" })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex gap-2", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("button", { "data-testid": "watchlist-save-btn", onClick: handleSave, className: "px-4 py-1.5 text-sm rounded-md bg-accent text-accent-fg hover:bg-accent/90 border border-accent cursor-pointer", children: isCreating ? "Create" : "Save" }),
          selectedList && !isCreating && /* @__PURE__ */ jsxRuntimeExports.jsx("button", { "data-testid": "watchlist-delete-btn", onClick: handleDelete, className: "px-4 py-1.5 text-sm rounded-md bg-red-500/10 text-red-400 border border-red-500/20 hover:bg-red-500/20 cursor-pointer", children: "Delete" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("button", { onClick: handleClose, className: "px-4 py-1.5 text-sm rounded-md bg-bg text-fg-muted hover:text-fg border border-bg-subtle cursor-pointer", children: "Cancel" })
        ] })
      ] }),
      selectedList && !isCreating && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "border-t border-bg-subtle pt-4", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h4", { className: "text-sm font-semibold text-fg mb-3", children: "Tickers" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex gap-2 mb-3", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-32", children: /* @__PURE__ */ jsxRuntimeExports.jsx(TickerAutocomplete, { value: tickerInput, onChange: setTickerInput, placeholder: "Ticker (e.g. AAPL)", "data-testid": "watchlist-ticker-input" }) }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("input", { "data-testid": "watchlist-notes-input", value: notesInput, onChange: (e_1) => setNotesInput(e_1.target.value), onKeyDown: (e_2) => {
            if (e_2.key === "Enter") {
              handleAddTicker();
            }
          }, placeholder: "Notes (optional)", className: "flex-1 px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("button", { "data-testid": "watchlist-add-ticker-btn", onClick: handleAddTicker, disabled: !tickerInput.trim(), className: "px-3 py-1.5 text-sm rounded-md border border-bg-subtle bg-bg hover:bg-bg-elevated text-fg transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed", children: "+ Add" })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "space-y-1", "data-testid": "watchlist-items", children: [
          selectedList.items.length === 0 && /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-xs text-fg-muted py-2 text-center", children: "No tickers yet" }),
          selectedList.items.map((item) => {
            const q = quotes[item.ticker];
            const hasPrice = q?.last_price != null;
            const priceText = hasPrice ? q.last_price.toFixed(2) : "—";
            const changePct = hasPrice && q?.change_pct != null ? q.change_pct : null;
            const changeText = changePct !== null ? `${changePct >= 0 ? "▲" : "▼"} ${Math.abs(changePct).toFixed(2)}%` : "—";
            const changeClass = changePct === null ? "text-fg-muted" : changePct >= 0 ? "text-gain" : "text-loss";
            return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { "data-testid": `watchlist-item-${item.ticker}`, className: "flex items-center justify-between px-3 py-2 rounded-md border border-bg-subtle bg-bg", children: [
              /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-3", children: [
                /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "font-medium text-fg text-sm", children: item.ticker }),
                item.notes && /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-xs text-fg-muted", children: item.notes })
              ] }),
              /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-3", children: [
                /* @__PURE__ */ jsxRuntimeExports.jsx("span", { "data-testid": `watchlist-price-${item.ticker}`, className: "text-sm font-mono text-fg", children: priceText }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("span", { "data-testid": `watchlist-change-${item.ticker}`, className: `text-xs font-mono ${changeClass}`, children: changeText }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("button", { "data-testid": `remove-ticker-${item.ticker}`, onClick: () => handleRemoveTicker(item.ticker), className: "text-xs text-red-400 hover:text-red-300 cursor-pointer", title: "Remove", children: "✕" })
              ] })
            ] }, item.id);
          })
        ] })
      ] })
    ] }) });
    $[43] = descInput;
    $[44] = handleAddTicker;
    $[45] = handleDelete;
    $[46] = handleRemoveTicker;
    $[47] = handleSave;
    $[48] = isCreating;
    $[49] = isDetailOpen;
    $[50] = nameInput;
    $[51] = notesInput;
    $[52] = quotes;
    $[53] = selectedList;
    $[54] = tickerInput;
    $[55] = t17;
  } else {
    t17 = $[55];
  }
  let t18;
  if ($[56] !== t16 || $[57] !== t17) {
    t18 = /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { "data-testid": "watchlist-page", className: "flex h-full", children: [
      t16,
      t17
    ] });
    $[56] = t16;
    $[57] = t17;
    $[58] = t18;
  } else {
    t18 = $[58];
  }
  return t18;
}
function _temp5(i_1) {
  return i_1.ticker;
}
function _temp4(i_0) {
  return i_0.ticker;
}
async function _temp3() {
  try {
    return await apiFetch("/api/v1/watchlists/");
  } catch {
    return [];
  }
}
function _temp2(i) {
  return i.ticker;
}
const TABS = ["Trade Plans", "Watchlists"];
function PlanningLayout() {
  const $ = compilerRuntimeExports.c(14);
  const [activeTab, setActiveTab] = reactExports.useState("Trade Plans");
  const handleOpenCalculator = _temp;
  let t0;
  if ($[0] !== activeTab) {
    t0 = TABS.map((tab) => /* @__PURE__ */ jsxRuntimeExports.jsx("button", { "data-testid": `planning-tab-${tab.toLowerCase().replace(" ", "-")}`, onClick: () => setActiveTab(tab), className: `px-4 py-2.5 text-sm font-medium border-b-2 transition-colors cursor-pointer ${activeTab === tab ? "text-accent border-accent" : "text-fg-muted border-transparent hover:text-fg"}`, children: tab }, tab));
    $[0] = activeTab;
    $[1] = t0;
  } else {
    t0 = $[1];
  }
  let t1;
  if ($[2] !== t0) {
    t1 = /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "flex border-b border-bg-subtle px-4", "data-testid": "planning-tabs", children: t0 });
    $[2] = t0;
    $[3] = t1;
  } else {
    t1 = $[3];
  }
  let t2;
  if ($[4] !== activeTab) {
    t2 = activeTab === "Trade Plans" && /* @__PURE__ */ jsxRuntimeExports.jsx(TradePlanPage, { onOpenCalculator: handleOpenCalculator });
    $[4] = activeTab;
    $[5] = t2;
  } else {
    t2 = $[5];
  }
  let t3;
  if ($[6] !== activeTab) {
    t3 = activeTab === "Watchlists" && /* @__PURE__ */ jsxRuntimeExports.jsx(WatchlistPage, {});
    $[6] = activeTab;
    $[7] = t3;
  } else {
    t3 = $[7];
  }
  let t4;
  if ($[8] !== t2 || $[9] !== t3) {
    t4 = /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex-1 overflow-hidden", children: [
      t2,
      t3
    ] });
    $[8] = t2;
    $[9] = t3;
    $[10] = t4;
  } else {
    t4 = $[10];
  }
  let t5;
  if ($[11] !== t1 || $[12] !== t4) {
    t5 = /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "h-full flex flex-col", "data-testid": "planning-layout", children: [
      t1,
      t4
    ] });
    $[11] = t1;
    $[12] = t4;
    $[13] = t5;
  } else {
    t5 = $[13];
  }
  return t5;
}
function _temp() {
  window.dispatchEvent(new CustomEvent("zorivest:open-calculator"));
}
export {
  PlanningLayout as default
};
