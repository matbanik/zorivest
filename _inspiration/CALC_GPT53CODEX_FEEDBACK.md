# Position Calculator Spec Critical Feedback (GPT-5 Codex)

Reviewed file: `docs/_position-calculator-features.md`  
Review style: defect-focused (calculation correctness, contradictions, implementation risk)  
Date: 2026-02-14

## Critical Findings

1. Futures direction and stop-placement rules are reversed.
Evidence: `docs/_position-calculator-features.md:76`, `docs/_position-calculator-features.md:77`, `docs/_position-calculator-features.md:56`, `docs/_position-calculator-features.md:57`.
Impact: The spec currently encodes invalid trade logic (`Long` with stop above entry), which will invert validation and risk calculations.
Recommendation: Define direction rules unambiguously:
- Long: `stop < entry < target`
- Short: `target < entry < stop`
Also fix the futures example so it matches the direction.

2. The universal sizing formula contradicts instrument-specific sizing rules.
Evidence: `docs/_position-calculator-features.md:15`, `docs/_position-calculator-features.md:24`, `docs/_position-calculator-features.md:25`, `docs/_position-calculator-features.md:35`, `docs/_position-calculator-features.md:152`, `docs/_position-calculator-features.md:207`.
Impact: The document claims one universal `floor(...)` approach, but forex and crypto require fractional sizing. Different teams will implement different rounding behavior.
Recommendation: Replace one-size-fits-all sizing with explicit per-instrument rounding rules:
- Stocks/Futures/Options: whole-unit floor
- Forex: floor to broker lot step (for example `0.01`)
- Crypto: floor to exchange quantity increment (for example `0.0001` or market-specific)

3. Final position size is not constrained by executable capital/margin limits across instruments.
Evidence: `docs/_position-calculator-features.md:65`, `docs/_position-calculator-features.md:69`, `docs/_position-calculator-features.md:104`, `docs/_position-calculator-features.md:208`, `docs/_position-calculator-features.md:281`, `docs/_position-calculator-features.md:289`.
Impact: Risk-based size can exceed buying power, margin availability, or strategy prerequisites (for example covered calls require 100 shares per contract).
Recommendation: Define `final_size = min(risk_size, capital_size, margin_size, strategy_constraints)` for every instrument and make this a mandatory output.

4. Forex pip-value conversion logic is incomplete and can be wrong for common cross-currency cases.
Evidence: `docs/_position-calculator-features.md:165`, `docs/_position-calculator-features.md:166`, `docs/_position-calculator-features.md:167`.
Impact: Incorrect pip value yields incorrect risk and lot size, which is a direct monetary error.
Recommendation: Specify a full conversion algorithm for:
- account currency equals quote
- account currency equals base
- account currency is neither base nor quote (requires conversion pair selection and rate direction)

## High Findings

5. Profit formulas use `ABS(...)` without direction-safe target validation.
Evidence: `docs/_position-calculator-features.md:72`, `docs/_position-calculator-features.md:106`, `docs/_position-calculator-features.md:155`, `docs/_position-calculator-features.md:210`.
Impact: Invalid targets can still produce positive-looking profit numbers, hiding invalid trade setups.
Recommendation: Add strict validation:
- Long: `target > entry`, `stop < entry`
- Short: `target < entry`, `stop > entry`
and reject calculation when invalid.

6. Vertical spread breakeven formulas are ambiguous.
Evidence: `docs/_position-calculator-features.md:262`.
Impact: `Long Strike +/- Debit` and `Short Strike +/- Credit` are not implementation-ready and can be interpreted differently.
Recommendation: Provide explicit formulas per variant:
- Bull Call, Bear Put, Bull Put, Bear Call each with exact signed equation.

7. Global GUI validation rules conflict with options strategy behavior.
Evidence: `docs/_position-calculator-features.md:342`, `docs/_position-calculator-features.md:343`.
Impact: "All calculators support Long/Short" and global stop-side validation does not fit option strategy workflows where risk is premium/spread-defined.
Recommendation: Move to instrument-specific validation schemas instead of one global rule.

8. Risk-percent input representation is undefined and error-prone.
Evidence: `docs/_position-calculator-features.md:14`, `docs/_position-calculator-features.md:34`, `docs/_position-calculator-features.md:55`, `docs/_position-calculator-features.md:91`, `docs/_position-calculator-features.md:137`, `docs/_position-calculator-features.md:194`.
Impact: Implementations may treat `2%` as `2` or `0.02`, causing 100x sizing differences.
Recommendation: Declare canonical input format (`percent points`, e.g. `2`) and normalization rule (`risk_fraction = risk_percent / 100`) once in the common section.

9. Rounding policy is inconsistent across outputs.
Evidence: `docs/_position-calculator-features.md:73`, `docs/_position-calculator-features.md:107`, `docs/_position-calculator-features.md:156`, `docs/_position-calculator-features.md:211`, `docs/_position-calculator-features.md:323`.
Impact: Mixed `floor` vs raw division will produce non-reproducible ratios between calculators.
Recommendation: Standardize:
- internal calculations at full precision
- explicit final display rounding per field (for example money 2 dp, ratio 2 dp, quantities per instrument step)

## Medium Findings

10. Input guardrails for divide-by-zero and invalid ranges are missing.
Evidence: `docs/_position-calculator-features.md:15`, `docs/_position-calculator-features.md:35`, `docs/_position-calculator-features.md:67`, `docs/_position-calculator-features.md:102`, `docs/_position-calculator-features.md:150`, `docs/_position-calculator-features.md:206`, `docs/_position-calculator-features.md:289`.
Impact: Edge cases (`entry == stop`, zero/negative values) can crash calculations or return undefined outputs.
Recommendation: Add a common validation contract with explicit errors for all denominator and sign constraints.

11. Tick/pip granularity rules are underspecified.
Evidence: `docs/_position-calculator-features.md:53`, `docs/_position-calculator-features.md:67`, `docs/_position-calculator-features.md:127`, `docs/_position-calculator-features.md:169`.
Impact: Non-increment-compatible prices produce silent rounding discrepancies and broker rejection risk.
Recommendation: Define increment validation and rounding behavior (reject vs snap-to-increment) for tick, pip, lot, and coin quantity.

12. Unresolved TODOs leave core behavior unspecified for implementation handoff.
Evidence: `docs/_position-calculator-features.md:5`, `docs/_position-calculator-features.md:143`, `docs/_position-calculator-features.md:180`.
Impact: Developers cannot implement deterministic behavior for cross-currency forex calculations without fallback rules.
Recommendation: Add mandatory interim behavior for "no live rates" mode (required manual conversion inputs, validation, and error messages).

## Suggested Remediation Order

1. Correct futures direction logic and direction validation rules globally.
2. Resolve universal formula contradictions by defining per-instrument rounding and feasibility constraints.
3. Replace forex pip-value logic with a full currency-conversion algorithm.
4. Make options formulas implementation-ready (variant-specific breakevens and validation schema).
5. Add common validation/rounding contracts and remove unresolved behavioral placeholders.
