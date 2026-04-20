/**
 * Test ID constants for Scheduling feature.
 *
 * These match the registry in ui/tests/e2e/test-ids.ts SCHEDULING export.
 * Components use these directly; E2E tests import from test-ids.ts.
 *
 * MEU: MEU-72 (gui-scheduling)
 */

export const SCHEDULING_TEST_IDS = {
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
    POLICY_NEXT_RUN_TIME: 'scheduling-policy-next-run-time',
} as const
