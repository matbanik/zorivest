# Feature Intent Contract — MEU-132: Cross-Account Wash Sale Aggregation

> **Source**: implementation-plan.md ACs 132.1–132.7
> **MEU**: 132 (Matrix Item 59)

## Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-132.1 | `detect_wash_sales()` extended to accept lots from multiple accounts | Spec (B3: "Check ALL accounts") | — |
| AC-132.2 | Detection scans all accounts in user's filing scope (taxable + IRA + spousal when enabled) | Spec (B3: "taxable + IRA + spouse accounts") | Single-account → still works |
| AC-132.3 | When replacement is in IRA, chain status = DESTROYED + LOSS_DESTROYED entry | Research-backed (IRS Pub 550: "loss is permanently disallowed" for IRA) | Taxable-to-taxable → DISALLOWED (not DESTROYED) |
| AC-132.4 | `WashSaleChainManager.destroy_chain()`: sets DESTROYED + LOSS_DESTROYED entry, no basis adjustment | Research-backed (IRS Pub 550: "cannot add to cost basis in IRA") | Attempting absorb after destroy → BusinessRuleError |
| AC-132.5 | `TaxService.scan_cross_account_wash_sales()`: scans all accounts for wash sale violations for a tax year | Spec (B3) | No accounts → empty result |
| AC-132.6 | Cross-account detection identifies the account_id on each WashSaleEntry | Spec (B3: need account provenance) | — |
| AC-132.7 | Spousal accounts included when `TaxProfile.include_spousal_accounts = True` | Spec (B7: "spouse's accounts must be checked when filing jointly") | `include_spousal_accounts = False` → excluded |
