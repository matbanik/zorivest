# tests/unit/test_secure_jinja.py
"""FIC: HardenedSandbox (MEU-PH6) — Spec §9E.3b–c.

Acceptance Criteria:
  AC-6.7:  Basic template renders correctly                  [Spec §9E.3c]
  AC-6.8:  Allowed filter works (e.g., `upper`)              [Spec §9E.3b]
  AC-6.9:  Blocked filter raises SecurityException           [Spec §9E.3c]
  AC-6.10: `__class__.__mro__` traversal blocked             [Spec §9E.3c]
  AC-6.11: `__init__.__globals__` access blocked              [Spec §9E.3c]
  AC-6.12: >64 KiB source raises SecurityError               [Spec §9E.3b]
  AC-6.13: >256 KiB rendered output raises SecurityError      [Spec §9E.3b]
  AC-6.14: Callable values in context not passed through      [Spec §9E.3b]
"""

from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# AC-6.7: Basic template renders correctly
# ---------------------------------------------------------------------------


def test_basic_render() -> None:
    """AC-6.7: Simple template with variable substitution renders correctly."""
    from zorivest_core.services.secure_jinja import HardenedSandbox

    sandbox = HardenedSandbox()
    result = sandbox.render_safe("Hello {{ name }}!", {"name": "Zorivest"})
    assert result == "Hello Zorivest!"


# ---------------------------------------------------------------------------
# AC-6.8: Allowed filter works (e.g., `upper`)
# ---------------------------------------------------------------------------


def test_allowed_filter() -> None:
    """AC-6.8: Allowed filter (upper) works in templates."""
    from zorivest_core.services.secure_jinja import HardenedSandbox

    sandbox = HardenedSandbox()
    result = sandbox.render_safe("{{ name | upper }}", {"name": "test"})
    assert result == "TEST"


# ---------------------------------------------------------------------------
# AC-6.9: Blocked filter raises SecurityException
# ---------------------------------------------------------------------------


def test_blocked_filter() -> None:
    """AC-6.9: Disallowed filter raises exception."""
    from zorivest_core.services.secure_jinja import HardenedSandbox

    sandbox = HardenedSandbox()
    # `attr` filter can be used for SSTI and is NOT in ALLOWED_FILTERS
    with pytest.raises(Exception):
        sandbox.render_safe("{{ name | attr('__class__') }}", {"name": "test"})


# ---------------------------------------------------------------------------
# AC-6.10: __class__.__mro__ traversal blocked
# ---------------------------------------------------------------------------


def test_mro_traversal_blocked() -> None:
    """AC-6.10: Accessing __class__.__mro__ is blocked by deny-list."""
    from zorivest_core.services.secure_jinja import HardenedSandbox

    sandbox = HardenedSandbox()
    # Should block attribute access to __class__
    with pytest.raises(Exception):
        sandbox.render_safe("{{ ''.__class__.__mro__ }}", {})


# ---------------------------------------------------------------------------
# AC-6.11: __init__.__globals__ access blocked
# ---------------------------------------------------------------------------


def test_globals_blocked() -> None:
    """AC-6.11: Accessing __init__.__globals__ is blocked."""
    from zorivest_core.services.secure_jinja import HardenedSandbox

    sandbox = HardenedSandbox()
    with pytest.raises(Exception):
        sandbox.render_safe("{{ ''.__class__.__init__.__globals__ }}", {})


# ---------------------------------------------------------------------------
# AC-6.12: >64 KiB source raises SecurityError
# ---------------------------------------------------------------------------


def test_source_size_cap() -> None:
    """AC-6.12: Template source >64 KiB raises SecurityError."""
    from zorivest_core.services.secure_jinja import HardenedSandbox

    sandbox = HardenedSandbox()
    big_source = "x" * (65 * 1024)  # 65 KiB > 64 KiB limit
    with pytest.raises(Exception, match="exceeds"):
        sandbox.render_safe(big_source, {})


# ---------------------------------------------------------------------------
# AC-6.13: >256 KiB rendered output raises SecurityError
# ---------------------------------------------------------------------------


def test_output_size_cap() -> None:
    """AC-6.13: Rendered output >256 KiB raises SecurityError."""
    from zorivest_core.services.secure_jinja import HardenedSandbox

    sandbox = HardenedSandbox()
    # Create a template that generates >256 KiB of output via loop
    # A string of 260 KiB output triggered by a repeated variable
    big_val = "A" * 1024  # 1 KiB
    template = "{% for i in range(300) %}{{ big }}{% endfor %}"
    with pytest.raises(Exception, match="exceeds"):
        sandbox.render_safe(template, {"big": big_val})


# ---------------------------------------------------------------------------
# AC-6.14: Callable values in context not passed through
# ---------------------------------------------------------------------------


def test_callable_stripped() -> None:
    """AC-6.14: Callable values are stripped from context before rendering."""
    from zorivest_core.services.secure_jinja import HardenedSandbox

    sandbox = HardenedSandbox()

    def dangerous_fn() -> str:
        return "pwned"

    # Callable should be stripped from context by safe_ctx filtering
    result = sandbox.render_safe(
        "func={{ func }}", {"func": dangerous_fn, "safe": "ok"}
    )
    # The callable should be stripped, rendering as empty or undefined
    assert "pwned" not in result


# ---------------------------------------------------------------------------
# AC-6.14b: Nested callable values in dicts stripped (Codex finding #1)
# ---------------------------------------------------------------------------


def test_nested_callable_in_dict_stripped() -> None:
    """AC-6.14b: Callable nested inside a dict is stripped before rendering.

    Regression: Codex repro — HardenedSandbox().render_safe(
        '{{ nested.fn() }}', {'nested': {'fn': lambda: 'PWNED'}})
    printed 'PWNED'. This violates PH6 security intent.

    After fix: callable is recursively removed from context. Jinja may raise
    UndefinedError (strict mode) or render empty — either is safe. The key
    assertion is that 'PWNED' never appears in output.
    """
    from jinja2.exceptions import UndefinedError

    from zorivest_core.services.secure_jinja import HardenedSandbox

    sandbox = HardenedSandbox()
    try:
        result = sandbox.render_safe(
            "{{ nested.fn() }}",
            {"nested": {"fn": lambda: "PWNED", "safe_key": "ok"}},
        )
        # If it renders without error, callable must NOT have executed
        assert "PWNED" not in result
    except UndefinedError:
        pass  # Expected — key was removed, Jinja can't find it


def test_nested_callable_in_list_stripped() -> None:
    """AC-6.14c: Callable inside a list within context is stripped."""
    from jinja2.exceptions import UndefinedError

    from zorivest_core.services.secure_jinja import HardenedSandbox

    sandbox = HardenedSandbox()
    try:
        result = sandbox.render_safe(
            "{% for item in items %}{{ item() }}{% endfor %}",
            {"items": [lambda: "PWNED", "safe_string"]},
        )
        assert "PWNED" not in result
    except (UndefinedError, TypeError):
        pass  # Callable removed from list, remaining items aren't callable


def test_deeply_nested_callable_stripped() -> None:
    """AC-6.14d: Callable 3 levels deep is stripped."""
    from jinja2.exceptions import UndefinedError

    from zorivest_core.services.secure_jinja import HardenedSandbox

    sandbox = HardenedSandbox()
    try:
        result = sandbox.render_safe(
            "{{ level1.level2.level3() }}",
            {"level1": {"level2": {"level3": lambda: "DEEP_PWNED"}}},
        )
        assert "DEEP_PWNED" not in result
    except UndefinedError:
        pass  # Callable removed at depth 3, Jinja raises


def test_safe_nested_values_preserved() -> None:
    """AC-6.14e: Normal dict/list values pass through recursive sanitization."""
    from zorivest_core.services.secure_jinja import HardenedSandbox

    sandbox = HardenedSandbox()
    result = sandbox.render_safe(
        "{{ data.name }}-{{ data.tags | join(',') }}",
        {"data": {"name": "report", "tags": ["a", "b", "c"]}},
    )
    assert result == "report-a,b,c"


# ---------------------------------------------------------------------------
# AC-6.14f–h: Tuple/type callable sanitization (Codex recheck R1)
# ---------------------------------------------------------------------------


def test_tuple_contained_callable_stripped() -> None:
    """AC-6.14f: Callable inside a tuple is stripped before rendering.

    Regression: Codex recheck — {{ xs[0]() }} with {"xs": (lambda: "PWNED",)}
    printed 'PWNED' because _sanitize_value only walked dict/list, not tuple.
    """
    from jinja2.exceptions import UndefinedError

    from zorivest_core.services.secure_jinja import HardenedSandbox

    sandbox = HardenedSandbox()
    try:
        result = sandbox.render_safe(
            "{{ xs[0]() }}",
            {"xs": (lambda: "PWNED",)},
        )
        assert "PWNED" not in result
    except (UndefinedError, TypeError):
        pass  # Callable removed, Jinja can't call it


def test_type_callable_stripped() -> None:
    """AC-6.14g: Type/class objects are stripped (they are callable).

    Regression: Codex recheck — {{ C(123) }} with {"C": str} printed '123'
    because _sanitize_value exempted isinstance(value, type).
    """
    from jinja2.exceptions import UndefinedError

    from zorivest_core.services.secure_jinja import HardenedSandbox

    sandbox = HardenedSandbox()
    try:
        result = sandbox.render_safe(
            "{{ C(123) }}",
            {"C": str},
        )
        assert "123" not in result
    except (UndefinedError, TypeError):
        pass  # Type stripped, Jinja can't find it


def test_tuple_safe_values_preserved() -> None:
    """AC-6.14h: Safe tuples pass through sanitization as lists."""
    from zorivest_core.services.secure_jinja import HardenedSandbox

    sandbox = HardenedSandbox()
    result = sandbox.render_safe(
        "{{ coords | join(',') }}",
        {"coords": (1, 2, 3)},
    )
    assert result == "1,2,3"


# ---------------------------------------------------------------------------
# AC-6.15: |tojson filter handles bytes without serialization crash
# ---------------------------------------------------------------------------
# Root cause: Jinja2's tojson filter calls json.dumps() via
# env.policies['json.dumps_function']. The default json.dumps cannot
# serialize bytes.  _sanitize_value converts bytes to str in the context,
# but if any bytes survive (or are created by step references), tojson
# crashes with "Object of type bytes is not JSON serializable".
# Fix: Register a custom json.dumps_function on the HardenedSandbox
# that handles bytes → str and datetime → isoformat.
# ---------------------------------------------------------------------------


def test_tojson_with_top_level_bytes() -> None:
    """AC-6.15a: tojson filter handles top-level bytes values.

    Reproduces the production failure: bytes from HTTP responses passed
    to {{ data|tojson }} in email templates.
    """
    from zorivest_core.services.secure_jinja import HardenedSandbox

    sandbox = HardenedSandbox()
    # Simulate raw HTTP response content that leaked as bytes
    result = sandbox.render_safe(
        "{{ data | tojson }}",
        {"data": b'{"price": 123.45}'},
    )
    # bytes should be decoded to str, then JSON-encoded with quotes
    assert "price" in result
    assert "123.45" in result


def test_tojson_with_nested_bytes_in_dict() -> None:
    """AC-6.15b: tojson filter handles bytes nested inside dicts.

    Reproduces: {{ fundamentals|tojson(indent=2) }} where one field
    value is still bytes from the provider API response.
    """
    from zorivest_core.services.secure_jinja import HardenedSandbox

    sandbox = HardenedSandbox()
    result = sandbox.render_safe(
        "{{ data | tojson }}",
        {"data": {"MarketCap": b"1000000", "Name": "Apple Inc."}},
    )
    assert "1000000" in result
    assert "Apple Inc." in result


def test_tojson_with_datetime() -> None:
    """AC-6.15c: tojson filter handles datetime objects.

    Pipeline steps store datetime in resolved_criteria and timestamps.
    """
    from datetime import datetime, timezone

    from zorivest_core.services.secure_jinja import HardenedSandbox

    sandbox = HardenedSandbox()
    now = datetime(2026, 5, 5, 12, 0, 0, tzinfo=timezone.utc)
    result = sandbox.render_safe(
        "{{ data | tojson }}",
        {"data": {"timestamp": now, "value": 42}},
    )
    assert "2026-05-05" in result
    assert "42" in result


def test_tojson_pipeline_context_simulation() -> None:
    """AC-6.15d: Full pipeline context with mixed types renders via tojson.

    Simulates the exact context shape from Full Fundamentals Research
    Pipeline: compose step output with records from multiple providers,
    some containing bytes or datetime values.
    """
    from datetime import date

    from zorivest_core.services.secure_jinja import HardenedSandbox

    sandbox = HardenedSandbox()
    ctx = {
        "quote": {"price": 195.5, "volume": 12345678},
        "fundamentals": {
            "MarketCap": b"3000000000000",
            "PERatio": "28.5",
            "raw_header": b"Content-Type: application/json",
        },
        "earnings": [
            {"period": b"Q1-2026", "actual": 1.53, "estimate": 1.48},
        ],
        "profile": {"name": "Apple Inc.", "ipo_date": date(1980, 12, 12)},
        "clean_data": "no bytes here",
    }
    # Template that exercises tojson on multiple context values
    template = """
    Quote: {{ quote|tojson(indent=2) }}
    Fundamentals: {{ fundamentals|tojson(indent=2) }}
    Earnings: {{ earnings|tojson(indent=2) }}
    Profile: {{ profile|tojson(indent=2) }}
    """
    result = sandbox.render_safe(template, ctx)
    # Verify all sections rendered without TypeError
    assert "195.5" in result
    assert "3000000000000" in result
    assert "Q1-2026" in result
    assert "Apple Inc." in result
    assert "1980-12-12" in result
