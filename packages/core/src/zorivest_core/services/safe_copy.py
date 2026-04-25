"""Safe deep-copy utilities for StepContext isolation (§9C.1b-c).

Provides:
    Secret  — Opaque credential wrapper that blocks str(), format(), deepcopy().
    safe_deepcopy — Deep-copy with depth, byte-size, and Secret guards.
    _estimate_size_recursive — Walk object graph to estimate total size.
"""

from __future__ import annotations

import copy
import sys
from typing import Any


class Secret:
    """Opaque credential wrapper — prevents leakage into StepContext or logs.

    Per §9C.1b: credentials must never traverse StepContext.
    Injected via closure at FetchStep call time only.
    """

    __slots__ = ("_value",)

    def __init__(self, value: str) -> None:
        object.__setattr__(self, "_value", value)

    def reveal(self) -> str:
        """Explicitly retrieve the secret value."""
        return self._value

    def __str__(self) -> str:
        raise RuntimeError("Secret must not be stringified — use .reveal() explicitly")

    def __repr__(self) -> str:
        return "Secret(***)"

    def __format__(self, format_spec: str) -> str:
        return "<REDACTED>"

    def __deepcopy__(self, memo: dict) -> Secret:
        raise RuntimeError("Secret must not be deep-copied into StepContext")


MAX_DEEPCOPY_DEPTH = 64
MAX_DEEPCOPY_BYTES = 10 * 1024 * 1024  # 10 MB


def _estimate_size_recursive(
    obj: object,
    depth: int = 0,
    seen: set[int] | None = None,
) -> int:
    """Walk object graph to estimate total size with cycle and depth protection."""
    if depth > MAX_DEEPCOPY_DEPTH:
        raise ValueError(f"Object nesting depth exceeds {MAX_DEEPCOPY_DEPTH}")
    if seen is None:
        seen = set()
    obj_id = id(obj)
    if obj_id in seen:
        return 0  # cycle — already counted
    seen.add(obj_id)
    total = sys.getsizeof(obj)
    if isinstance(obj, dict):
        for k, v in obj.items():
            total += _estimate_size_recursive(k, depth + 1, seen)
            total += _estimate_size_recursive(v, depth + 1, seen)
    elif isinstance(obj, (list, tuple, set, frozenset)):
        for item in obj:
            total += _estimate_size_recursive(item, depth + 1, seen)
    elif hasattr(obj, "__dict__"):
        total += _estimate_size_recursive(vars(obj), depth + 1, seen)
    return total


def safe_deepcopy(obj: Any) -> Any:
    """Deep-copy with recursive depth, aggregate byte, and Secret guards.

    Raises:
        ValueError: If the object graph exceeds MAX_DEEPCOPY_BYTES or
                    MAX_DEEPCOPY_DEPTH.
        RuntimeError: If a Secret is encountered during deepcopy.
    """
    total_bytes = _estimate_size_recursive(obj)
    if total_bytes > MAX_DEEPCOPY_BYTES:
        raise ValueError(
            f"Object too large for deep-copy: {total_bytes} bytes > {MAX_DEEPCOPY_BYTES}"
        )
    return copy.deepcopy(obj)
