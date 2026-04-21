# MCP Template Discoverability Gap — Pre-Implementation Research

> **Date:** 2026-04-20
> **Issue:** [MCP-TOOLDISCOVERY] — sub-issue: template registry not exposed to MCP layer
> **Status:** Open — needs resolution before or during MEU-TD1 implementation
> **Relates to:** [PIPE-TMPLVAR], [PIPE-QUOTEFIELD] (data flow fixes in MEU-PW12)

---

## 1. Problem Statement

An AI agent using the Zorivest MCP `create_policy` tool has **zero visibility** into:

1. What email template names are available (`daily_quote_summary`, `generic_report`)
2. What Jinja2 variables each template expects (`quotes`, `records`, `generated_at`)
3. What field shapes those variables require (`q.symbol`, `q.price`, `q.change`, `q.change_pct`, `q.volume`)
4. How pipeline steps must be wired together for data to flow into the template
5. What step types exist (`fetch`, `transform`, `send`) and their parameter schemas

This makes it impossible for an AI agent to autonomously construct a working pipeline policy that produces a meaningful email report.

---

## 2. Current State (What the AI Agent Sees)

### 2.1 `create_policy` Tool Description

```typescript
// scheduling-tools.ts:31-38
description: "Create a new pipeline policy from a JSON document. Validates structure,
              step types, ref integrity, and cron expression."
inputSchema: {
    policy_json: z.record(z.unknown())
        .describe("Full PolicyDocument JSON object")
}
```

**Critique:** `z.record(z.unknown())` is a completely opaque type. The description gives no structural guidance, no example, and no reference to where to learn the schema.

### 2.2 MCP Resources (Passive — Agent Must Proactively Read)

| Resource URI | Content | Discoverable? |
|---|---|---|
| `pipeline://policies/schema` | JSON Schema for PolicyDocument | ❌ Not referenced in any tool description |
| `pipeline://step-types` | Step type parameter schemas | ❌ Not referenced in any tool description |

These exist but are **passive** — no tool description tells the agent to read them. Most AI agents only read MCP resources when explicitly directed.

### 2.3 Template Registry (Completely Invisible)

The `EMAIL_TEMPLATES` dict lives in Python infrastructure:

```
packages/infrastructure/src/zorivest_infra/rendering/email_templates.py
```

It is never exposed to the MCP layer. No endpoint, no resource, no documentation surfaces it.

---

## 3. Impact — Failure Modes for AI Agents

| Failure Mode | What Happens |
|---|---|
| Agent invents template name | `body_template: "quote_report"` → SendStep tier 3 fallback → raw string rendered as HTML body |
| Agent omits `body_template` | SendStep tier 4 → `"<p>Report attached</p>"` (empty fallback) |
| Agent uses correct name but wrong step wiring | Data flows but template variable `quotes` is undefined → "No quote data available" |
| Agent hardcodes `"fetch_result"` as step ID | Matches the current buggy hardcode, not the real runner output key |
| Agent doesn't set `source_step_id` | After MEU-PW12 fix, TransformStep won't know which step's output to read |

---

## 4. Proposed Solutions

### 4.1 New MCP Resource: `pipeline://templates` (Recommended)

Add a new MCP resource that exposes the template registry with variable contracts:

```json
{
  "templates": {
    "daily_quote_summary": {
      "description": "Styled HTML table showing daily quote data per ticker",
      "required_variables": {
        "quotes": {
          "type": "list[dict]",
          "fields": {
            "symbol": "str — ticker symbol (e.g., 'AAPL')",
            "price": "float — current market price",
            "change": "float — absolute price change",
            "change_pct": "float — percentage change",
            "volume": "int — trading volume"
          }
        }
      },
      "auto_provided_variables": ["generated_at", "policy_id", "run_id"],
      "example_steps": [
        {"id": "fetch_quotes", "type": "fetch", "params": {"provider": "Yahoo Finance", "data_type": "quote", "criteria": {"tickers": ["AAPL", "MSFT"]}}},
        {"id": "transform", "type": "transform", "params": {"source_step_id": "fetch_quotes", "target_table": "market_quotes", "validation_rules": "quote"}},
        {"id": "send", "type": "send", "params": {"body_template": "daily_quote_summary", "channel": "email", "recipients": ["user@example.com"], "subject": "Daily Quotes"}}
      ]
    },
    "generic_report": {
      "description": "Auto-tables any records list by introspecting dict keys",
      "required_variables": {
        "records": {
          "type": "list[dict]",
          "fields": "dynamic — columns auto-detected from first record's keys"
        }
      },
      "auto_provided_variables": ["generated_at", "policy_id", "run_id"],
      "optional_variables": {"title": "str — report title (default: 'Zorivest Report')"}
    }
  }
}
```

### 4.2 Enriched `create_policy` Tool Description

Update the tool description to include:

```typescript
description: `Create a new pipeline policy from a JSON document.

IMPORTANT: Before constructing policy_json, read these MCP resources:
- pipeline://policies/schema — full JSON Schema for PolicyDocument
- pipeline://step-types — available step types and their parameter schemas
- pipeline://templates — available email templates, required variables, and example step chains

A typical quote report pipeline requires 3 steps:
1. fetch — retrieves market data from a provider
2. transform — maps provider fields to canonical schema (requires source_step_id pointing to fetch step)
3. send — renders an email template with the transformed data

Available templates: daily_quote_summary (requires 'quotes' variable with symbol/price/change/change_pct/volume),
                     generic_report (requires 'records' variable with any dict list)
`
```

### 4.3 Backend API Endpoint for Template Registry

Add `GET /api/v1/scheduling/templates` that returns the template metadata from `EMAIL_TEMPLATES` with:
- Template name
- Description
- Required variables (manually annotated or introspected from Jinja2 AST `{% for q in quotes %}` → `quotes` is a required iterable)
- Example step chain

This endpoint would be consumed by the `pipeline://templates` MCP resource.

---

## 5. Implementation Considerations

### Where in the build order?

| Option | MEU | Pros | Cons |
|---|---|---|---|
| Fold into MEU-TD1 | `mcp-tool-discovery-audit` | Natural home — TD1 already audits tool descriptions | TD1 scope grows; template metadata requires backend endpoint |
| New MEU after PW12 | `mcp-template-registry` | Clean separation; PW12 fixes define the final variable contracts | Extra MEU overhead for ~2h of work |
| Split: backend in PW12, MCP in TD1 | Hybrid | Each MEU owns its layer | Cross-MEU coordination |

**Recommendation:** Split approach. MEU-PW12 defines the template variable contracts (since it's fixing the data flow). TD1 then exposes those contracts through MCP resources and enriched tool descriptions. The backend `GET /templates` endpoint goes in PW12 since it's a thin wrapper over `EMAIL_TEMPLATES`.

### Template Metadata Annotation Pattern

Rather than a separate metadata file, annotate `EMAIL_TEMPLATES` entries with metadata:

```python
_register(
    "daily_quote_summary",
    source="...",
    metadata={
        "description": "Styled HTML table showing daily quote data per ticker",
        "required_variables": {"quotes": {"type": "list[dict]", "fields": {...}}},
        "auto_provided": ["generated_at", "policy_id", "run_id"],
    }
)
```

This keeps template source and contract co-located.

---

## 6. Dependencies

- **MEU-PW12** must land first — it defines `source_step_id`, the template variable wiring, and the final field mappings. The template metadata would be wrong if written before these fixes.
- The `pipeline://templates` resource depends on the backend endpoint.
- TD1 enriched descriptions depend on knowing the final template contracts.

---

## 7. Files Referenced

| File | Purpose |
|---|---|
| [scheduling-tools.ts](file:///p:/zorivest/mcp-server/src/tools/scheduling-tools.ts) | MCP tool definitions — `create_policy` description |
| [email_templates.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/rendering/email_templates.py) | Template registry — `EMAIL_TEMPLATES` dict |
| [template_engine.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/rendering/template_engine.py) | Jinja2 environment with financial filters |
| [send_step.py](file:///p:/zorivest/packages/core/src/zorivest_core/pipeline_steps/send_step.py) | `_resolve_body()` four-tier chain + context merging |
| [zorivest-tools.json](file:///p:/zorivest/mcp-server/zorivest-tools.json) | Tool manifest (6 scheduling tools listed) |
