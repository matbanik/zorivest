# packages/core/src/zorivest_core/services/secure_jinja.py
"""HardenedSandbox — Hardened Jinja2 sandbox for AI-authored email templates (§9E.3b).

Security layers:
  1. ImmutableSandboxedEnvironment base (prevents template modification)
  2. Filter allowlist (only safe, non-side-effect filters)
  3. Attribute deny-list (blocks SSTI traversal chains)
  4. Source size cap (64 KiB)
  5. Output size cap (256 KiB)
  6. Context sanitization (strips callables)
"""

from __future__ import annotations

from jinja2.sandbox import ImmutableSandboxedEnvironment

ALLOWED_FILTERS = frozenset(
    {
        "abs",
        "batch",
        "capitalize",
        "center",
        "count",
        "default",
        "d",
        "dictsort",
        "e",
        "escape",
        "filesizeformat",
        "first",
        "float",
        "format",
        "groupby",
        "indent",
        "int",
        "items",
        "join",
        "last",
        "length",
        "list",
        "lower",
        "map",
        "max",
        "min",
        "pprint",
        "reject",
        "rejectattr",
        "replace",
        "reverse",
        "round",
        "safe",
        "select",
        "selectattr",
        "slice",
        "sort",
        "string",
        "striptags",
        "sum",
        "title",
        "tojson",
        "trim",
        "truncate",
        "unique",
        "upper",
        "urlencode",
        "wordcount",
        "wordwrap",
        "xmlattr",
    }
)

_DENY_ATTRS = frozenset(
    {
        "__class__",
        "__subclasses__",
        "__mro__",
        "__bases__",
        "__init__",
        "__globals__",
        "__builtins__",
        "__import__",
        "__code__",
        "__func__",
        "__self__",
        "__module__",
        "__qualname__",
        "__reduce__",
        "__reduce_ex__",
        "__getattr__",
        "__setattr__",
        "__delattr__",
        "__dict__",
    }
)

MAX_TEMPLATE_BYTES = 64 * 1024  # 64 KiB source cap
MAX_OUTPUT_BYTES = 256 * 1024  # 256 KiB render output cap

# Sentinel for values removed during recursive sanitization
_REMOVED = object()


class SecurityError(Exception):
    """Raised when a template violates security constraints."""


def _pipeline_safe_dumps(obj: object, **kwargs: object) -> str:
    """JSON serializer for Jinja2's |tojson filter.

    Handles types that appear in pipeline step outputs but are not
    natively JSON-serializable:
    - bytes  → decoded to str (UTF-8)
    - datetime/date → ISO 8601 string

    Registered via env.policies['json.dumps_function'] in HardenedSandbox.
    """
    import json
    from datetime import date, datetime

    def _default(o: object) -> object:
        if isinstance(o, bytes):
            return o.decode("utf-8", errors="replace")
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, date):
            return o.isoformat()
        raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")

    return json.dumps(obj, default=_default, **kwargs)  # type: ignore[arg-type]


class HardenedSandbox(ImmutableSandboxedEnvironment):
    """Hardened Jinja2 sandbox for AI-authored email templates.

    Extends ImmutableSandboxedEnvironment with:
    - Filter allowlist (rejects unknown filters)
    - Attribute deny-list (blocks SSTI traversal)
    - Source/output size caps
    - Context sanitization (strips callables)
    """

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        # Strip filters not in the allowlist
        self.filters = {k: v for k, v in self.filters.items() if k in ALLOWED_FILTERS}

        # Configure |tojson filter to use a pipeline-safe JSON serializer.
        # Jinja2's tojson calls json.dumps() via env.policies['json.dumps_function'].
        # The default json.dumps cannot serialize bytes or datetime — both of which
        # appear in pipeline step outputs (HTTP responses, CriteriaResolver dates).
        # Without this, tojson crashes even if _sanitize_value cleaned the context.
        self.policies["json.dumps_function"] = _pipeline_safe_dumps

    def is_safe_attribute(self, obj: object, attr: str, value: object) -> bool:
        """Block access to dangerous dunder attributes."""
        if attr in _DENY_ATTRS:
            return False
        return super().is_safe_attribute(obj, attr, value)

    @staticmethod
    def _sanitize_value(value: object) -> object:
        """Recursively sanitize a context value, stripping callables at any depth.

        Returns _REMOVED sentinel for top-level callables so the caller
        can filter them out of the context dict.

        Security contract: every callable — including type/class objects —
        is stripped unless explicitly allowlisted. There is currently no
        allowlist; all callables are removed unconditionally.
        """
        if callable(value):
            return _REMOVED
        # Bytes are not JSON-serializable (Jinja2's |tojson filter calls
        # json.dumps). Decode to str to prevent serialization failures.
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")
        if isinstance(value, dict):
            sanitized = {}
            for k, v in value.items():
                clean = HardenedSandbox._sanitize_value(v)
                if clean is not _REMOVED:
                    sanitized[k] = clean
            return sanitized
        if isinstance(value, (list, tuple, set, frozenset)):
            # Convert all sequence-like containers to list for Jinja compat
            return [
                item
                for item in (HardenedSandbox._sanitize_value(v) for v in value)
                if item is not _REMOVED
            ]
        return value

    def render_safe(self, source: str, context: dict) -> str:
        """Render a template with full security enforcement.

        Args:
            source: Jinja2 template source string.
            context: Template variables dict.

        Returns:
            Rendered output string.

        Raises:
            SecurityError: If source or output exceeds size limits.
        """
        if len(source.encode()) > MAX_TEMPLATE_BYTES:
            raise SecurityError(f"Template source exceeds {MAX_TEMPLATE_BYTES} bytes")

        template = self.from_string(source)

        # Recursively strip callable values from context to prevent function injection
        safe_ctx = {k: self._sanitize_value(v) for k, v in context.items()}
        safe_ctx = {k: v for k, v in safe_ctx.items() if v is not _REMOVED}

        rendered = template.render(safe_ctx)

        if len(rendered.encode()) > MAX_OUTPUT_BYTES:
            raise SecurityError(f"Rendered output exceeds {MAX_OUTPUT_BYTES} bytes")

        return rendered
