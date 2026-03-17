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
    ROOT: 'calculator-page',
    ACCOUNT_SIZE: 'calc-account-size',
    RISK_PERCENT: 'calc-risk-percent',
    ENTRY_PRICE: 'calc-entry-price',
    STOP_PRICE: 'calc-stop-price',
    RESULT_SHARES: 'calc-result-shares',
    RESULT_DOLLAR_RISK: 'calc-result-dollar-risk',
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
