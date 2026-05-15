# Feature Intent Contract — MEU-131: Wash Sale Chain Tracking

> **Source**: implementation-plan.md ACs 131.1–131.8
> **MEU**: 131 (Matrix Item 58)

## Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-131.1 | `WashSaleChainManager` class with `start_chain()`, `absorb_loss()`, `release_chain()`, `continue_chain()` methods | Spec (B2: "disallowed → absorbed → released") | — |
| AC-131.2 | `start_chain()`: creates chain with DISALLOWED status + LOSS_DISALLOWED entry | Spec | — |
| AC-131.3 | `absorb_loss()`: adjusts replacement lot's `wash_sale_adjustment` field, adds BASIS_ADJUSTED entry, sets status to ABSORBED | Research-backed (IRS Pub 550: disallowed loss added to replacement basis) | — |
| AC-131.4 | `absorb_loss()` tacks holding period: sets replacement lot `open_date` to original lot `open_date` | Research-backed (IRS Pub 550: holding period tacking rule) | — |
| AC-131.5 | `release_chain()`: sets status to RELEASED + LOSS_RELEASED entry when replacement lot sold without new wash sale | Spec (B2: "released") | Cannot release a chain that is not ABSORBED → raises error |
| AC-131.6 | `continue_chain()`: extends chain when replacement lot sold at loss triggers another wash sale, adds CHAIN_CONTINUED entry | Spec (B2: "deferred losses that roll forward through repeated trades") | — |
| AC-131.7 | `get_trapped_losses()`: returns all chains in ABSORBED status (losses that can't be deducted this year) | Spec (B2: "Show trapped losses") | No active chains → empty list |
| AC-131.8 | TaxService integration: `detect_and_apply_wash_sales()` method on TaxService that orchestrates detection + chain creation + basis adjustment via UoW | Local Canon (TaxService orchestration pattern) | — |
