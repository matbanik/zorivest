/**
 * Test ID constants for Tax feature.
 *
 * These match the registry in ui/tests/e2e/test-ids.ts TAX export.
 * Components use these directly; E2E tests import from test-ids.ts.
 *
 * MEU: MEU-154 (gui-tax), Wave 11
 */

export const TAX_TEST_IDS = {
    ROOT: 'tax-page',
    DISCLAIMER: 'tax-disclaimer',

    // Tab bar
    TAB: 'tax-tab',

    // Help card (MEU-218i)
    HELP_CARD: 'tax-help-card',

    // Dashboard
    DASHBOARD: 'tax-dashboard',
    SUMMARY_CARD: 'tax-summary-card',
    YTD_TABLE: 'tax-ytd-table',
    YEAR_SELECTOR: 'tax-year-selector',
    SYNC_BUTTON: 'tax-sync-button',

    // Lot Viewer
    LOT_VIEWER: 'tax-lot-viewer',
    LOT_ROW: 'tax-lot-row',
    LOT_CLOSE_BTN: 'tax-lot-close-btn',
    LOT_REASSIGN_BTN: 'tax-lot-reassign-btn',
    LOT_FILTER_STATUS: 'tax-lot-filter-status',
    LOT_FILTER_TICKER: 'tax-lot-filter-ticker',

    // Wash Sale Monitor
    WASH_SALE_MONITOR: 'wash-sale-monitor',
    WASH_SALE_CHAIN: 'wash-sale-chain',
    WASH_SALE_CHAIN_DETAIL: 'wash-sale-chain-detail',

    // What-If Simulator
    WHAT_IF_SIMULATOR: 'what-if-simulator',
    WHAT_IF_TICKER_INPUT: 'what-if-ticker-input',
    WHAT_IF_QUANTITY: 'what-if-quantity',
    WHAT_IF_PRICE: 'what-if-price',
    WHAT_IF_SUBMIT: 'what-if-submit',
    WHAT_IF_RESULT: 'what-if-result',

    // Loss Harvesting
    LOSS_HARVESTING_TOOL: 'loss-harvesting-tool',
    HARVEST_OPPORTUNITY_ROW: 'harvest-opportunity-row',

    // Quarterly Payments
    QUARTERLY_TRACKER: 'quarterly-tracker',
    QUARTERLY_CARD: 'quarterly-card',
    QUARTERLY_PAYMENT_INPUT: 'quarterly-payment-input',
    QUARTERLY_PAYMENT_SUBMIT: 'quarterly-payment-submit',

    // Transaction Audit
    TX_AUDIT_PANEL: 'tx-audit-panel',
    TX_AUDIT_FINDING_ROW: 'tx-audit-finding-row',
    TX_AUDIT_RUN_BTN: 'tx-audit-run-btn',

    // Tax Profile Manager (MEU-218f)
    PROFILE_MANAGER: 'tax-profile-manager',
    PROFILE_LIST: 'tax-profile-list',
    PROFILE_CARD: 'tax-profile-card',
    PROFILE_NEW_BTN: 'tax-profile-new-btn',
    PROFILE_DETAIL: 'tax-profile-detail',
    PROFILE_SAVE_BTN: 'tax-profile-save-btn',
    PROFILE_DELETE_BTN: 'tax-profile-delete-btn',
    PROFILE_YEAR_INPUT: 'tax-profile-year',
    PROFILE_SEARCH: 'tax-profile-search',
} as const
