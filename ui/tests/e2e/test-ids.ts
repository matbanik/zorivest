/**
 * Shared test IDs for E2E selectors.
 *
 * These map to `data-testid` attributes in React components.
 * Using constants prevents selector drift between tests and components.
 *
 * Convention: SCREAMING_SNAKE_CASE for the constant, kebab-case for the value.
 */

// ── Sidebar Navigation ─────────────────────────────────────────────────

export const SIDEBAR = {
    ROOT: 'sidebar',
    NAV_ACCOUNTS: 'nav-accounts',
    NAV_TRADES: 'nav-trades',
    NAV_PLANNING: 'nav-planning',
    NAV_SCHEDULING: 'nav-scheduling',
    NAV_SETTINGS: 'nav-settings',
} as const

// ── Page Headers ────────────────────────────────────────────────────────

export const PAGE_HEADER = {
    TITLE: 'page-title',
    SUBTITLE: 'page-subtitle',
} as const

// ── Accounts Page ───────────────────────────────────────────────────────

export const ACCOUNTS = {
    ROOT: 'accounts-page',
    ACCOUNT_LIST: 'account-list',
    ADD_BUTTON: 'add-account-btn',
} as const

// ── Trades Page ─────────────────────────────────────────────────────────

export const TRADES = {
    ROOT: 'trades-page',
    TRADE_LIST: 'trade-list',
    TRADE_ROW: 'trade-row',
    ADD_BUTTON: 'add-trade-btn',
    FORM: {
        SYMBOL: 'trade-symbol-input',
        QUANTITY: 'trade-quantity-input',
        PRICE: 'trade-price-input',
        SIDE: 'trade-side-select',
        SUBMIT: 'trade-submit-btn',
        CANCEL: 'trade-cancel-btn',
    },
} as const

// ── Settings Page ───────────────────────────────────────────────────────

export const SETTINGS = {
    ROOT: 'settings-page',
    MCP_GUARD: {
        LOCK_TOGGLE: 'mcp-guard-lock-toggle',
        STATUS: 'mcp-guard-status',
    },
    BACKUP: {
        CREATE_BUTTON: 'backup-create-btn',
        RESTORE_BUTTON: 'backup-restore-btn',
        PASSPHRASE_INPUT: 'backup-passphrase-input',
    },
} as const

// ── Import Flow ─────────────────────────────────────────────────────────

export const IMPORT = {
    FILE_INPUT: 'import-file-input',
    FORMAT_SELECT: 'import-format-select',
    SUBMIT: 'import-submit-btn',
    PROGRESS: 'import-progress',
    RESULT_COUNT: 'import-result-count',
} as const

// ── Calculator ──────────────────────────────────────────────────────────

export const CALCULATOR = {
    ROOT: 'calculator-modal',          // <div data-testid="calculator-modal">
    ACCOUNT_SIZE: 'calc-account-size',
    RISK_PERCENT: 'calc-risk-percent',
    ENTRY_PRICE: 'calc-entry-price',
    STOP_PRICE: 'calc-stop-price',
    TARGET_PRICE: 'calc-target-price',
    RESULT_SHARES: 'calc-shares-output',      // actual testid in component
    RESULT_DOLLAR_RISK: 'calc-dollar-risk-output',  // actual testid in component
    RESULT_RR: 'calc-rr-output',
    RESULT_POSITION_VALUE: 'calc-position-value-output',
    OVERSIZE_WARNING: 'calc-oversize-warning',
    COPY_SHARES_BTN: 'calc-copy-shares-btn',
    RESET_BTN: 'calc-reset-btn',
    CLOSE_BTN: 'close-calculator',
} as const

// ── Common ──────────────────────────────────────────────────────────────

export const COMMON = {
    LOADING_SPINNER: 'loading-spinner',
    ERROR_BANNER: 'error-banner',
    TOAST: 'toast-notification',
    CONFIRM_DIALOG: 'confirm-dialog',
    CONFIRM_YES: 'confirm-yes-btn',
    CONFIRM_NO: 'confirm-no-btn',
} as const

// ── Balance / Financial Data (for visual regression masking) ────────────

export const FINANCIAL = {
    BALANCE_AMOUNT: 'balance-amount',
    PNL_VALUE: 'pnl-value',
    ACCOUNT_EQUITY: 'account-equity',
} as const

// ── Market Data Providers (MEU-65) ───────────────────────────────────────────

export const MARKET_DATA_PROVIDERS = {
    ROOT: 'market-data-providers',
    PROVIDER_LIST: 'provider-list',
    PROVIDER_ITEM: 'provider-item',
    PROVIDER_DETAIL: 'provider-detail',
    PROVIDER_SAVE_BTN: 'provider-save-btn',
    PROVIDER_TEST_BTN: 'provider-test-btn',
    PROVIDER_TEST_ALL_BTN: 'provider-test-all-btn',
    PROVIDER_REMOVE_KEY_BTN: 'provider-remove-key-btn',
    PROVIDER_API_KEY_INPUT: 'provider-api-key-input',
    PROVIDER_API_SECRET_INPUT: 'provider-api-secret-input',
    PROVIDER_RATE_LIMIT_INPUT: 'provider-rate-limit-input',
    PROVIDER_TIMEOUT_INPUT: 'provider-timeout-input',
    PROVIDER_ENABLE_TOGGLE: 'provider-enable-toggle',
    PROVIDER_GET_API_KEY_BTN: 'provider-get-api-key-btn',
} as const
