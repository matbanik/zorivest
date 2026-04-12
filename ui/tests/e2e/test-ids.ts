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
    DETAIL_PANEL: 'account-detail-panel',
    // Form fields
    FORM: {
        NAME: 'account-name-input',
        TYPE: 'account-type-select',
        INSTITUTION: 'account-institution-input',
        // DEFERRED: Multi-currency support — see AccountDetailPanel.tsx DEFERRED comment
        // CURRENCY: 'account-currency-select',
        TAX_ADVANTAGED: 'account-tax-advantaged-checkbox',
        NOTES: 'account-notes-textarea',
        SUBMIT: 'account-submit-btn',
        DELETE: 'account-delete-btn',
    },
    // Balance controls
    BALANCE: {
        UPDATE_BTN: 'balance-update-btn',
        INPUT: 'balance-input',
        SAVE_BTN: 'balance-save-btn',
        CANCEL_BTN: 'balance-cancel-btn',
        LATEST: 'balance-latest-value',
    },
    // Table
    TABLE: {
        PORTFOLIO_PCT: 'account-portfolio-pct',
    },
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

// ── Screenshot Panel ────────────────────────────────────────────────────

export const SCREENSHOTS = {
    PANEL: 'screenshot-panel',
    THUMBNAIL: 'screenshot-thumbnail',
    UPLOAD_BTN: 'screenshot-upload-btn',
    DELETE_BTN: 'screenshot-delete-btn',
    LIGHTBOX: 'screenshot-lightbox',
    FILE_INPUT: 'screenshot-file-input',
    LOADING: 'screenshot-loading',
    ERROR: 'screenshot-error',
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

// ── Scheduling & Pipeline (MEU-72) ──────────────────────────────────────────

export const SCHEDULING = {
    ROOT: 'scheduling-root',
    POLICY_LIST: 'scheduling-policy-list',
    POLICY_ITEM: 'scheduling-policy-item',
    POLICY_NAME: 'scheduling-policy-name',
    POLICY_STATUS: 'scheduling-policy-status',
    POLICY_DETAIL: 'scheduling-policy-detail',
    POLICY_JSON_EDITOR: 'scheduling-json-editor',
    POLICY_CRON_PREVIEW: 'scheduling-cron-preview',
    POLICY_ENABLE_TOGGLE: 'scheduling-enable-toggle',
    POLICY_APPROVE_BTN: 'scheduling-approve-btn',
    POLICY_NAME_INPUT: 'scheduling-policy-name-input',
    POLICY_STATE_PILL: 'scheduling-state-pill',
    CRON_PICKER: 'scheduling-cron-picker',
    CRON_FREQUENCY: 'scheduling-cron-frequency',
    CRON_HOUR: 'scheduling-cron-hour',
    CRON_MINUTE: 'scheduling-cron-minute',
    CRON_RAW_INPUT: 'scheduling-cron-raw-input',
    CRON_GENERATED: 'scheduling-cron-generated',
    POLICY_SAVE_BTN: 'scheduling-save-btn',
    POLICY_DELETE_BTN: 'scheduling-delete-btn',
    POLICY_CREATE_BTN: 'scheduling-create-btn',
    RUN_NOW_BTN: 'scheduling-run-now-btn',
    TEST_RUN_BTN: 'scheduling-test-run-btn',
    RUN_HISTORY_TABLE: 'scheduling-run-history',
    RUN_HISTORY_ROW: 'scheduling-run-history-row',
    RUN_DETAIL_PANEL: 'scheduling-run-detail',
    STEP_STATUS: 'scheduling-step-status',
    SCHEDULER_STATUS: 'scheduling-scheduler-status',
    EMPTY_STATE: 'scheduling-empty-state',
    ERROR_STATE: 'scheduling-error-state',
    LOADING_STATE: 'scheduling-loading-state',
} as const
