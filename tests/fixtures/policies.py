# tests/fixtures/policies.py
"""Reusable test policy documents for pipeline integration testing.

Each fixture is a valid PolicyDocument JSON dict ready for use with
SchedulingService.create_policy() or PipelineRunner.run().

Spec: 09b-pipeline-hardening.md §9B.6b
"""

# Happy path: mock fetch → transform → store (3 step types)
SMOKE_POLICY_BASIC = {
    "schema_version": 1,
    "name": "smoke-basic",
    "trigger": {"cron_expression": "0 9 * * 1-5", "timezone": "UTC", "enabled": True},
    "steps": [
        {"id": "fetch_data", "type": "mock_fetch", "params": {"data": [1, 2, 3]}},
        {
            "id": "transform_data",
            "type": "mock_transform",
            "params": {"source": {"ref": "ctx.fetch_data.data"}},
        },
        {
            "id": "store_result",
            "type": "mock_store",
            "params": {"data": {"ref": "ctx.transform_data.result"}},
        },
    ],
}

# Error mode: fail_pipeline (default)
POLICY_ERROR_FAIL = {
    "schema_version": 1,
    "name": "smoke-error-fail",
    "trigger": {"cron_expression": "0 0 * * *", "timezone": "UTC", "enabled": True},
    "steps": [
        {
            "id": "will_fail",
            "type": "mock_fail",
            "params": {"error_msg": "intentional"},
        },
        {"id": "never_reached", "type": "mock_fetch", "params": {}},
    ],
}

# Error mode: log_and_continue
POLICY_ERROR_CONTINUE = {
    "schema_version": 1,
    "name": "smoke-error-continue",
    "trigger": {"cron_expression": "0 0 * * *", "timezone": "UTC", "enabled": True},
    "steps": [
        {
            "id": "will_fail",
            "type": "mock_fail",
            "params": {"error_msg": "non-fatal"},
            "on_error": "log_and_continue",
        },
        {"id": "should_run", "type": "mock_fetch", "params": {"data": [42]}},
    ],
}

# Dry-run: side-effect step should be skipped
POLICY_DRY_RUN = {
    "schema_version": 1,
    "name": "smoke-dry-run",
    "trigger": {"cron_expression": "0 0 * * *", "timezone": "UTC", "enabled": True},
    "steps": [
        {"id": "fetch", "type": "mock_fetch", "params": {"data": [1]}},
        {"id": "side_effect", "type": "mock_side_effect", "params": {}},
    ],
}

# Skip condition
POLICY_SKIP_CONDITION = {
    "schema_version": 1,
    "name": "smoke-skip",
    "trigger": {"cron_expression": "0 0 * * *", "timezone": "UTC", "enabled": True},
    "steps": [
        {"id": "fetch", "type": "mock_fetch", "params": {"data": []}},
        {
            "id": "conditional",
            "type": "mock_transform",
            "params": {},
            "skip_if": {"field": "ctx.fetch.count", "operator": "eq", "value": 0},
        },
    ],
}

# Cancel: deliberately slow step
POLICY_CANCELLABLE = {
    "schema_version": 1,
    "name": "smoke-cancel",
    "trigger": {"cron_expression": "0 0 * * *", "timezone": "UTC", "enabled": True},
    "steps": [
        {"id": "slow_step", "type": "mock_slow", "params": {"delay_seconds": 60}},
        {"id": "after_cancel", "type": "mock_fetch", "params": {}},
    ],
}

# Unicode resilience (PW4 regression)
POLICY_UNICODE_ERROR = {
    "schema_version": 1,
    "name": "smoke-unicode",
    "trigger": {"cron_expression": "0 0 * * *", "timezone": "UTC", "enabled": True},
    "steps": [
        {
            "id": "unicode_fail",
            "type": "mock_fail",
            "params": {"error_msg": "Résumé: ñ, ü, ™, 日本語 — error with non-ASCII"},
        },
    ],
}
