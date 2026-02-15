# Critical Review: Position Calculator GUI + MCP Specs

Date: 2026-02-14
Scope:
- `docs/_position-calculator-gui-mcp.md`
- `docs/_position-calculator-features.md`

## Critical Findings

1. **Options strategy model is not executable as written (Long Call/Put and Covered Call are underspecified).**  
Evidence: `docs/_position-calculator-features.md:368`, `docs/_position-calculator-features.md:375`, `docs/_position-calculator-features.md:447`, `docs/_position-calculator-gui-mcp.md:178`, `docs/_position-calculator-gui-mcp.md:184`, `docs/_position-calculator-gui-mcp.md:188`.  
Impact: `Long Call/Put` merges two different payoff models (unlimited vs capped reward), but no field distinguishes call vs put; strike is also not required for Long Call/Put/Covered Call in the inputs despite formulas requiring it for breakeven/max-profit.  
Recommendation: Split `Long Call/Put` into `long_call` and `long_put`; require strike for long options and covered call; update GUI conditional fields, API schema, MCP enum, and validators accordingly.

2. **Iron Condor cannot be represented by the current request schema.**  
Evidence: `docs/_position-calculator-gui-mcp.md:187`, `docs/_position-calculator-gui-mcp.md:324`, `docs/_position-calculator-gui-mcp.md:325`, `docs/_position-calculator-gui-mcp.md:326`, `docs/_position-calculator-gui-mcp.md:327`, `docs/_position-calculator-gui-mcp.md:328`, `docs/_position-calculator-gui-mcp.md:329`, `docs/_position-calculator-gui-mcp.md:530`, `docs/_position-calculator-gui-mcp.md:531`, `docs/_position-calculator-gui-mcp.md:532`, `docs/_position-calculator-gui-mcp.md:533`, `docs/_position-calculator-gui-mcp.md:534`, `docs/_position-calculator-gui-mcp.md:535`.  
Impact: Spec says Iron Condor needs 4 premiums and 4 strikes (or separate put/call widths), but API/MCP only provide two leg premiums, two strikes, and one width. This blocks implementation and creates inevitable data loss.  
Recommendation: Add explicit fields for all four legs (or a structured `legs[]` payload) and separate put/call widths for net mode.

3. **Advanced input contract is inconsistent across GUI, REST, MCP, and Pydantic models.**  
Evidence: `docs/_position-calculator-gui-mcp.md:333`, `docs/_position-calculator-gui-mcp.md:334`, `docs/_position-calculator-gui-mcp.md:337`, `docs/_position-calculator-gui-mcp.md:338`, `docs/_position-calculator-gui-mcp.md:339`, `docs/_position-calculator-gui-mcp.md:340`, `docs/_position-calculator-gui-mcp.md:341`, `docs/_position-calculator-gui-mcp.md:730`, `docs/_position-calculator-gui-mcp.md:731`, `docs/_position-calculator-gui-mcp.md:732`, `docs/_position-calculator-gui-mcp.md:539`, `docs/_position-calculator-gui-mcp.md:540`, `docs/_position-calculator-gui-mcp.md:541`.  
Impact: REST example uses nested `advanced` object with many fields, but models and MCP expose only flat `leverage` and `commission`. UI and MCP clients will send incompatible payloads.  
Recommendation: Choose one canonical shape (nested or flat), mirror it in Pydantic + MCP schema, and include every advanced field documented in GUI.

4. **Futures capital/risk source is contradictory and can produce divergent 1R.**  
Evidence: `docs/_position-calculator-features.md:136`, `docs/_position-calculator-features.md:158`, `docs/_position-calculator-gui-mcp.md:99`, `docs/_position-calculator-gui-mcp.md:120`, `docs/_position-calculator-gui-mcp.md:125`, `docs/_position-calculator-gui-mcp.md:694`, `docs/_position-calculator-gui-mcp.md:704`.  
Impact: Feature spec computes futures 1R from buying power, while request model globally requires `account_balance` and only optionally accepts `buying_power`. Two capital inputs with unclear precedence creates inconsistent outputs and test ambiguity.  
Recommendation: For futures, make `buying_power` required and define whether `account_balance` is forbidden, aliased, or ignored.

5. **Covered call strategy constraint is impossible to enforce with current inputs.**  
Evidence: `docs/_position-calculator-features.md:363`, `docs/_position-calculator-features.md:408`, `docs/_position-calculator-features.md:418`, `docs/_position-calculator-gui-mcp.md:330`, `docs/_position-calculator-gui-mcp.md:331`, `docs/_position-calculator-gui-mcp.md:536`, `docs/_position-calculator-gui-mcp.md:537`.  
Impact: Constraint requires owned shares (>=100 per contract), but there is no `owned_shares` input in GUI/API/MCP. Final contracts cannot be correctly capped by strategy limit.  
Recommendation: Add `owned_shares` and compute `strategy_constraint = floor(owned_shares / contract_multiplier)`.

6. **Long call “unlimited reward” conflicts with fixed numeric common outputs and ratio field.**  
Evidence: `docs/_position-calculator-features.md:374`, `docs/_position-calculator-features.md:460`, `docs/_position-calculator-gui-mcp.md:74`, `docs/_position-calculator-gui-mcp.md:363`.  
Impact: Contract currently implies `potential_profit` and `reward_risk_ratio` are numeric for all instruments, but long call max reward is unbounded. This creates serialization ambiguity (`Infinity`, `null`, string).  
Recommendation: Explicitly allow `null`/`"unbounded"` for max-profit and R:R in unbounded strategies, and define response typing.

## High Findings

1. **Feasibility formula is internally inconsistent.**  
Evidence: `docs/_position-calculator-features.md:73`, `docs/_position-calculator-features.md:101`.  
Impact: One section includes `strategy_constraint`, another omits it. Implementations can diverge.  
Recommendation: Publish one canonical final-size formula and define N/A constraints as `+inf`.

2. **Forex custom pair support is incomplete in the input contract.**  
Evidence: `docs/_position-calculator-gui-mcp.md:794`, `docs/_position-calculator-gui-mcp.md:796`, `docs/_position-calculator-gui-mcp.md:797`, `docs/_position-calculator-gui-mcp.md:495`, `docs/_position-calculator-gui-mcp.md:500`, `docs/_position-calculator-gui-mcp.md:503`, `docs/_position-calculator-gui-mcp.md:710`, `docs/_position-calculator-gui-mcp.md:711`, `docs/_position-calculator-gui-mcp.md:712`.  
Impact: Spec allows custom pairs with manual pip size, but no `pip_size` input exists in API/MCP/model.  
Recommendation: Add `pip_size` (required when pair is custom) and validate against pair format.

3. **Forex sizing formula references `margin_lots` without defining it.**  
Evidence: `docs/_position-calculator-features.md:277`, `docs/_position-calculator-features.md:287`, `docs/_position-calculator-features.md:288`.  
Impact: Final lot size cannot be reproduced deterministically from the spec.  
Recommendation: Define exact `margin_lots` formula and required leverage/margin inputs; define fallback when leverage is not supplied.

4. **MCP tool transport/error handling is incomplete.**  
Evidence: `docs/_position-calculator-gui-mcp.md:543`, `docs/_position-calculator-gui-mcp.md:544`, `docs/_position-calculator-gui-mcp.md:549`.  
Impact: No `response.ok` handling and no mapped error envelope means API/network failures surface as opaque MCP errors.  
Recommendation: Add explicit status handling for `422`/`5xx`/network exceptions and return structured tool error content.

5. **Request example is labeled JSON but contains comment keys and non-JSON constructs.**  
Evidence: `docs/_position-calculator-gui-mcp.md:306`, `docs/_position-calculator-gui-mcp.md:312`, `docs/_position-calculator-gui-mcp.md:317`, `docs/_position-calculator-gui-mcp.md:320`, `docs/_position-calculator-gui-mcp.md:333`.  
Impact: Copy/paste into clients/parsers will fail, increasing integration friction.  
Recommendation: Replace with valid JSON examples per instrument, or label as JSONC explicitly.

6. **Pydantic model uses mutable list defaults for warnings/notices.**  
Evidence: `docs/_position-calculator-gui-mcp.md:757`, `docs/_position-calculator-gui-mcp.md:758`.  
Impact: Shared mutable defaults can cause cross-request contamination if implemented verbatim.  
Recommendation: Use `Field(default_factory=list)` for list fields.

7. **Options request typing is too loose for a “strict validation” spec.**  
Evidence: `docs/_position-calculator-gui-mcp.md:720`, `docs/_position-calculator-gui-mcp.md:721`, `docs/_position-calculator-gui-mcp.md:722`, `docs/_position-calculator-gui-mcp.md:725`.  
Impact: `input_mode` is plain string and key numeric fields are unconstrained in the model; invalid payloads can bypass schema-level validation.  
Recommendation: Use enums + constrained fields (`gt=0`, etc.) and strategy-specific validators.

## Medium Findings

1. **Cross-reference pointers in GUI spec point to sections not defined in that document.**  
Evidence: `docs/_position-calculator-gui-mcp.md:106`, `docs/_position-calculator-gui-mcp.md:642`.  
Impact: Implementation teams may follow broken references and miss required rule sets.  
Recommendation: Replace with explicit links to `docs/_position-calculator-features.md` sections.

2. **Snap-to-nearest rule can reduce stop distance and understate risk.**  
Evidence: `docs/_position-calculator-features.md:89`, `docs/_position-calculator-features.md:90`.  
Impact: `round()` may move stop toward entry depending direction/increment, resulting in optimistic risk sizing.  
Recommendation: Define direction-aware conservative snapping policy for risk-critical fields.

## Open Questions

1. Should futures use only `buying_power`, or should `account_balance` remain a required shared field for UI consistency?  
2. For long call (unbounded reward), should API return `null`, `"unbounded"`, or omit `potential_profit`/`reward_risk_ratio`?  
3. For iron condor net mode, do you want explicit put/call wing widths or full per-leg strike inputs only?

## Residual Risk If Unchanged

The current spec set is not fully implementable without assumptions in options and advanced input modeling. If coding starts before resolving the critical items above, API/UI/MCP will likely diverge and require a contract-breaking revision.
