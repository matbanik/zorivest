# Feature Intent Contract — MEU-130: Wash Sale Detection

> **Source**: implementation-plan.md ACs 130.1–130.11
> **MEU**: 130 (Matrix Item 57)

## Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-130.1 | `WashSaleChain` mutable dataclass with 8 fields: `chain_id`, `ticker`, `loss_lot_id`, `loss_date`, `loss_amount`, `disallowed_amount`, `status`, `entries` | Spec (domain-model-reference.md B1) | Missing required fields raise TypeError |
| AC-130.2 | `WashSaleEntry` frozen dataclass with 7 fields: `entry_id`, `chain_id`, `event_type`, `lot_id`, `amount`, `event_date`, `account_id` | Spec (domain-model-reference.md B1) | — |
| AC-130.3 | `WashSaleStatus` enum: `DISALLOWED`, `ABSORBED`, `RELEASED`, `DESTROYED` | Spec ("disallowed → absorbed → released") + Research-backed (IRA destruction) | Invalid status string raises ValueError |
| AC-130.4 | `WashSaleEventType` enum: `LOSS_DISALLOWED`, `BASIS_ADJUSTED`, `CHAIN_CONTINUED`, `LOSS_RELEASED`, `LOSS_DESTROYED` | Spec (B2 chain events) | — |
| AC-130.5 | `detect_wash_sales()` pure function: given a loss lot + candidate replacement lots, returns `list[WashSaleMatch]` for securities purchased within ±30 calendar days (61-day window) | Research-backed (IRS Pub 550: 30 days before + sale day + 30 days after) | Sale with no repurchase within window → empty list |
| AC-130.6 | Detection matches by ticker (same symbol = substantially identical for this MEU) | Spec (B1: "substantially identical") | Different tickers → no match |
| AC-130.7 | Partial wash sale support: sell 100 shares at loss, buy 50 back → 50 shares' loss disallowed, 50 allowed | Research-backed (IRS Pub 550 proportional rule) | Full quantity → full disallowance |
| AC-130.8 | `WashSaleChainRepository` protocol with `get`, `save`, `update`, `list_for_ticker`, `list_active` | Local Canon (ports.py pattern) | — |
| AC-130.9 | `WashSaleChainModel` + `WashSaleEntryModel` SQLAlchemy models in `database/wash_sale_models.py` | Local Canon (database/ package pattern) | — |
| AC-130.10 | `SqlWashSaleChainRepository` in `database/wash_sale_repository.py` with full CRUD | Local Canon (database/ package pattern) | Non-existent chain_id returns None |
| AC-130.11 | UoW wired: `wash_sale_chains` attribute on `UnitOfWork` | Local Canon (ports.py UoW pattern) | — |
