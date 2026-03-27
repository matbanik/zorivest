"""Log redaction audit — systematic sweep for unredacted secrets in logging.

This test scans all logging calls across the codebase to verify that
sensitive data (API keys, tokens, passwords) is never logged in plaintext.
Unlike unit tests that verify individual redaction functions, this test
audits the usage patterns to catch accidental leaks.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

# Root of the packages directory
PACKAGES_ROOT = Path(__file__).resolve().parents[2] / "packages"

# Patterns that indicate sensitive data being logged without redaction
SENSITIVE_PATTERNS: list[re.Pattern[str]] = [
    # Direct key/token/secret/password in f-strings or format calls
    re.compile(
        r"""(?:api[_-]?key|token|secret|password|passphrase|credential)""", re.I
    ),
]

# Allowlist: known safe redaction wrappers
SAFE_WRAPPERS = {
    "mask_api_key",
    "sanitize_url_for_logging",
    "[REDACTED]",
    "mask_",
    "redact",
}


def _find_python_files() -> list[Path]:
    """Find all Python source files in packages/ (exclude tests)."""
    return sorted(
        p
        for p in PACKAGES_ROOT.rglob("*.py")
        if "test" not in p.name.lower() and "__pycache__" not in str(p)
    )


def _extract_logging_calls(filepath: Path) -> list[tuple[int, str]]:
    """Extract all logging call lines from a Python file.

    Returns list of (line_number, source_line) tuples for lines
    that contain logging calls (logger.info/debug/warning/error/critical).
    """
    try:
        source = filepath.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(filepath))
    except (SyntaxError, UnicodeDecodeError):
        return []

    lines = source.splitlines()
    logging_lines: list[tuple[int, str]] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            # Match logger.info(), logger.debug(), etc.
            if (
                isinstance(func, ast.Attribute)
                and func.attr
                in {"debug", "info", "warning", "error", "critical", "exception"}
                and isinstance(func.value, ast.Name)
                and func.value.id in {"logger", "log", "logging"}
            ):
                lineno = node.lineno
                if 0 < lineno <= len(lines):
                    logging_lines.append((lineno, lines[lineno - 1]))

    return logging_lines


class TestLogRedactionAudit:
    """Audit logging calls for unredacted sensitive data."""

    @pytest.fixture(autouse=True)
    def _setup(self) -> None:
        self.files = _find_python_files()
        # Ensure we actually found files to scan
        assert len(self.files) > 0, f"No Python files found in {PACKAGES_ROOT}"

    def test_no_sensitive_data_in_logging_calls(self) -> None:
        """No logging call should contain raw sensitive variable names
        without a known redaction wrapper.
        """
        violations: list[str] = []

        for filepath in self.files:
            for lineno, line in _extract_logging_calls(filepath):
                # Skip lines that use known safe wrappers
                if any(wrapper in line for wrapper in SAFE_WRAPPERS):
                    continue

                # Check if the line references sensitive variables in f-strings
                # Look for f"...{api_key}..." or f"...{token}..." patterns
                fstring_vars = re.findall(r"\{(\w+)\}", line)
                for var in fstring_vars:
                    for pattern in SENSITIVE_PATTERNS:
                        if pattern.search(var):
                            rel = filepath.relative_to(PACKAGES_ROOT.parent)
                            violations.append(
                                f"  {rel}:{lineno} — '{var}' in logging call"
                            )

        if violations:
            msg = (
                f"Found {len(violations)} potential unredacted secret(s) in logging:\n"
                + "\n".join(violations)
            )
            pytest.fail(msg)

    def test_no_format_string_with_key_or_token(self) -> None:
        """No .format() call in logging should reference key/token variables."""
        violations: list[str] = []

        for filepath in self.files:
            for lineno, line in _extract_logging_calls(filepath):
                # Skip lines with safe wrappers
                if any(wrapper in line for wrapper in SAFE_WRAPPERS):
                    continue

                # Check for .format() with sensitive named args
                if ".format(" in line:
                    format_args = re.findall(r"(\w+)\s*=", line)
                    for arg in format_args:
                        for pattern in SENSITIVE_PATTERNS:
                            if pattern.search(arg):
                                rel = filepath.relative_to(PACKAGES_ROOT.parent)
                                violations.append(
                                    f"  {rel}:{lineno} — '{arg}' in .format() logging"
                                )

        if violations:
            msg = (
                f"Found {len(violations)} .format() call(s) with sensitive args:\n"
                + "\n".join(violations)
            )
            pytest.fail(msg)

    def test_no_percent_format_with_sensitive_names(self) -> None:
        """No %-format logging should include sensitive variable names."""
        violations: list[str] = []

        for filepath in self.files:
            for lineno, line in _extract_logging_calls(filepath):
                if any(wrapper in line for wrapper in SAFE_WRAPPERS):
                    continue

                # Check for % formatting with sensitive variable references
                # Pattern: logger.info("... %s", api_key)
                if "%" in line:
                    # Look at trailing args after the format string
                    parts = line.split(",")
                    for part in parts[1:]:  # Skip the format string
                        stripped = part.strip().rstrip(")")
                        for pattern in SENSITIVE_PATTERNS:
                            if pattern.search(stripped):
                                rel = filepath.relative_to(PACKAGES_ROOT.parent)
                                violations.append(
                                    f"  {rel}:{lineno} — '{stripped}' in %-format logging"
                                )

        if violations:
            msg = (
                f"Found {len(violations)} %-format logging call(s) with sensitive args:\n"
                + "\n".join(violations)
            )
            pytest.fail(msg)
