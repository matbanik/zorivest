#!/usr/bin/env python3
"""Zorivest Codebase Quality Gate.

Runs blocking and advisory checks for the Zorivest monorepo.
Replaces the former tools/validate.ps1 with cross-platform Python.

Usage:
    uv run python tools/validate_codebase.py              # Full phase gate
    uv run python tools/validate_codebase.py --scope meu   # MEU-scoped (touched files only)
    uv run python tools/validate_codebase.py --json         # Machine-readable output
    uv run python tools/validate_codebase.py --files f1 f2  # Explicit file list for MEU scope
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PYTHON_PKG_DIR = "packages/"
TYPESCRIPT_DIRS = ("mcp-server/", "ui/")
SCAN_DIRS = ("packages/", "src/", "tests/")

PLACEHOLDER_PATTERN = r"TODO|FIXME|NotImplementedError"
DEFERRAL_PATTERN = (
    r"pass\s+#\s*placeholder|\.\.\.\s+#\s*placeholder|raise\s+NotImplementedError"
)

HANDOFF_DIR = ".agent/context/handoffs/"
HANDOFF_EVIDENCE_PATTERNS = [
    (
        r"Evidence bundle location|FAIL_TO_PASS Evidence|### FAIL_TO_PASS",
        "Evidence/FAIL_TO_PASS",
    ),
    (r"Pass/fail matrix|Commands Executed", "Pass-fail/Commands"),
    (r"Commands run|Codex Validation Report", "Commands/Codex Report"),
]


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class CheckResult:
    """Result of a single quality check."""

    name: str
    passed: bool
    blocking: bool
    duration_s: float
    message: str = ""
    skipped: bool = False


@dataclass
class GateResult:
    """Aggregated result of all checks."""

    checks: list[CheckResult] = field(default_factory=list)

    @property
    def all_blocking_passed(self) -> bool:
        return all(c.passed for c in self.checks if c.blocking and not c.skipped)

    @property
    def summary(self) -> dict:
        blocking = [c for c in self.checks if c.blocking and not c.skipped]
        advisory = [c for c in self.checks if not c.blocking and not c.skipped]
        skipped = [c for c in self.checks if c.skipped]
        return {
            "passed": self.all_blocking_passed,
            "blocking_passed": sum(1 for c in blocking if c.passed),
            "blocking_failed": sum(1 for c in blocking if not c.passed),
            "advisory_count": len(advisory),
            "skipped_count": len(skipped),
            "total_duration_s": round(sum(c.duration_s for c in self.checks), 2),
        }

    def to_json(self) -> str:
        return json.dumps(
            {
                "summary": self.summary,
                "checks": [
                    {
                        "name": c.name,
                        "passed": c.passed,
                        "blocking": c.blocking,
                        "skipped": c.skipped,
                        "duration_s": round(c.duration_s, 2),
                        "message": c.message,
                    }
                    for c in self.checks
                ],
            },
            indent=2,
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# ANSI color codes (works in modern terminals including Windows Terminal)
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
GRAY = "\033[90m"
RESET = "\033[0m"
BOLD = "\033[1m"


def _color(text: str, color: str) -> str:
    """Wrap text in ANSI color codes."""
    if not sys.stdout.isatty():
        return text
    return f"{color}{text}{RESET}"


def _run(cmd: list[str], *, cwd: str | None = None) -> subprocess.CompletedProcess[str]:
    """Run a command and return the result."""
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=cwd or os.getcwd(),
        shell=sys.platform == "win32",  # npx.cmd needs shell on Windows
    )


def _timed_check(
    name: str,
    cmd: list[str],
    *,
    blocking: bool = True,
    scope_files: list[str] | None = None,
) -> CheckResult:
    """Run a command as a quality check with timing."""
    # Replace last arg with scoped files if provided
    actual_cmd = list(cmd)
    if scope_files:
        # Replace the directory arg (last element) with specific files
        actual_cmd = cmd[:-1] + scope_files

    start = time.monotonic()
    result = _run(actual_cmd)
    duration = time.monotonic() - start

    passed = result.returncode == 0
    message = ""
    if not passed:
        # Capture first 5 lines of stderr or stdout for context
        output = result.stderr.strip() or result.stdout.strip()
        lines = output.split("\n")[:5]
        message = "\n".join(lines)

    return CheckResult(
        name=name,
        passed=passed,
        blocking=blocking,
        duration_s=duration,
        message=message,
    )


def _scan_check(
    name: str,
    pattern: str,
    dirs: list[str],
    *,
    blocking: bool = True,
    exclude_comment: str | None = None,
) -> CheckResult:
    """Run a ripgrep scan as a quality check.

    Args:
        exclude_comment: If set, lines containing this exact comment are
            excluded from the match count.  This allows base-class contracts
            (e.g. ``raise NotImplementedError  # noqa: placeholder``) to
            coexist with a blocking anti-placeholder gate.
    """
    start = time.monotonic()

    if exclude_comment:
        # Two-pass: find matches, then subtract lines with the exclusion tag
        result = _run(["rg", "-n", pattern] + dirs)
        duration = time.monotonic() - start

        if result.returncode != 0 or not result.stdout.strip():
            # No matches at all — pass
            return CheckResult(
                name=name, passed=True, blocking=blocking, duration_s=duration
            )

        # Filter out excluded lines
        raw_lines = result.stdout.strip().split("\n")
        filtered = [ln for ln in raw_lines if exclude_comment not in ln]

        if not filtered:
            # All matches were excluded — pass
            return CheckResult(
                name=name,
                passed=True,
                blocking=blocking,
                duration_s=duration,
                message=f"All matches excluded by '{exclude_comment}'",
            )

        return CheckResult(
            name=name,
            passed=False,
            blocking=blocking,
            duration_s=duration,
            message="\n".join(filtered[:10]),
        )

    result = _run(["rg", "-c", pattern] + dirs)
    duration = time.monotonic() - start

    # rg returns 0 if matches found, 1 if no matches
    has_matches = result.returncode == 0 and result.stdout.strip()

    if has_matches:
        # Get detailed output
        detail = _run(["rg", "-n", pattern] + dirs)
        lines = detail.stdout.strip().split("\n")[:10]
        return CheckResult(
            name=name,
            passed=False,
            blocking=blocking,
            duration_s=duration,
            message="\n".join(lines),
        )

    return CheckResult(
        name=name,
        passed=True,
        blocking=blocking,
        duration_s=duration,
    )


def _evidence_check() -> CheckResult:
    """Check latest handoff for evidence fields."""
    start = time.monotonic()
    handoff_path = Path(HANDOFF_DIR)

    if not handoff_path.exists():
        return CheckResult(
            name="Evidence Bundle",
            passed=True,
            blocking=False,
            duration_s=time.monotonic() - start,
            message="No handoff directory found (expected during early development)",
            skipped=True,
        )

    handoffs = sorted(
        [
            f
            for f in handoff_path.glob("*.md")
            if f.name not in ("README.md", "TEMPLATE.md")
            and not f.name.endswith("-critical-review.md")
        ],
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )

    if not handoffs:
        return CheckResult(
            name="Evidence Bundle",
            passed=True,
            blocking=False,
            duration_s=time.monotonic() - start,
            message="No handoff files found",
            skipped=True,
        )

    latest = handoffs[0]
    content = latest.read_text(encoding="utf-8", errors="replace")
    import re

    missing = []
    for pattern, label in HANDOFF_EVIDENCE_PATTERNS:
        if not re.search(pattern, content):
            missing.append(label)

    duration = time.monotonic() - start

    if missing:
        return CheckResult(
            name="Evidence Bundle",
            passed=True,  # Advisory, not blocking
            blocking=False,
            duration_s=duration,
            message=f"{latest.name} missing: {', '.join(missing)}",
        )

    return CheckResult(
        name="Evidence Bundle",
        passed=True,
        blocking=False,
        duration_s=duration,
        message=f"All evidence fields present in {latest.name}",
    )


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------


def run_quality_gate(
    *,
    scope: str = "phase",
    files: list[str] | None = None,
    json_output: bool = False,
) -> GateResult:
    """Run the full quality gate pipeline.

    Args:
        scope: "phase" for full repo, "meu" for scoped checks.
        files: Explicit file list for MEU scope.
        json_output: If True, suppress text output.
    """
    gate = GateResult()
    has_python = Path(PYTHON_PKG_DIR).exists()
    scan_dirs = [d for d in SCAN_DIRS if Path(d).exists()]
    scope_files = files if scope == "meu" and files else None

    if not json_output:
        print(_color("=" * 44, CYAN))
        print(_color("  Zorivest Codebase Quality Gate", CYAN))
        print(_color(f"  Scope: {scope}", CYAN))
        print(_color("=" * 44, CYAN))
        print()

    # ---- BLOCKING CHECKS ----

    # Python type check
    if has_python:
        target = PYTHON_PKG_DIR
        check = _timed_check(
            "Python Type Check (pyright)",
            ["uv", "run", "pyright", target],
            scope_files=[f for f in (scope_files or []) if f.endswith(".py")] or None,
        )
        gate.checks.append(check)
        if not json_output:
            status = _color("PASS", GREEN) if check.passed else _color("FAIL", RED)
            print(f"  [1/8] {check.name}: {status} ({check.duration_s:.1f}s)")
            if not check.passed:
                print(f"         {check.message}")
    else:
        gate.checks.append(
            CheckResult("Python Type Check", True, True, 0, skipped=True)
        )
        if not json_output:
            print(_color("  [1/8] Python Type Check: SKIPPED", GRAY))

    # Python lint
    if has_python:
        check = _timed_check(
            "Python Lint (ruff)",
            ["uv", "run", "ruff", "check", PYTHON_PKG_DIR],
            scope_files=[f for f in (scope_files or []) if f.endswith(".py")] or None,
        )
        gate.checks.append(check)
        if not json_output:
            status = _color("PASS", GREEN) if check.passed else _color("FAIL", RED)
            print(f"  [2/8] {check.name}: {status} ({check.duration_s:.1f}s)")
            if not check.passed:
                print(f"         {check.message}")
    else:
        gate.checks.append(CheckResult("Python Lint", True, True, 0, skipped=True))
        if not json_output:
            print(_color("  [2/8] Python Lint: SKIPPED", GRAY))

    # Python tests
    if has_python:
        check = _timed_check(
            "Python Unit Tests (pytest)",
            ["uv", "run", "pytest", "-x", "--tb=short", "-m", "unit", "-q"],
        )
        gate.checks.append(check)
        if not json_output:
            status = _color("PASS", GREEN) if check.passed else _color("FAIL", RED)
            print(f"  [3/8] {check.name}: {status} ({check.duration_s:.1f}s)")
            if not check.passed:
                print(f"         {check.message}")
    else:
        gate.checks.append(
            CheckResult("Python Unit Tests", True, True, 0, skipped=True)
        )
        if not json_output:
            print(_color("  [3/8] Python Unit Tests: SKIPPED", GRAY))

    # TypeScript type check — run per-directory from each TS project root
    ts_dirs_with_tsconfig = [
        d for d in TYPESCRIPT_DIRS if (Path(d) / "tsconfig.json").exists()
    ]
    if ts_dirs_with_tsconfig:
        # Run tsc from within the TS project directory
        ts_cwd = ts_dirs_with_tsconfig[0]
        start = time.monotonic()
        result = _run(["npx", "tsc", "--noEmit"], cwd=ts_cwd)
        duration = time.monotonic() - start
        passed = result.returncode == 0
        message = ""
        if not passed:
            output = result.stderr.strip() or result.stdout.strip()
            lines = output.split("\n")[:5]
            message = "\n".join(lines)
        check = CheckResult(
            name="TypeScript Type Check (tsc)",
            passed=passed,
            blocking=True,
            duration_s=duration,
            message=message,
        )
        gate.checks.append(check)
        if not json_output:
            status = _color("PASS", GREEN) if check.passed else _color("FAIL", RED)
            print(f"  [4/8] {check.name}: {status} ({check.duration_s:.1f}s)")
    else:
        gate.checks.append(
            CheckResult("TypeScript Type Check", True, True, 0, skipped=True)
        )
        if not json_output:
            print(_color("  [4/8] TypeScript Type Check: SKIPPED", GRAY))

    # TypeScript lint
    if ts_dirs_with_tsconfig:
        ts_cwd = ts_dirs_with_tsconfig[0]
        start = time.monotonic()
        result = _run(
            ["npx", "eslint", "src/", "--max-warnings", "0"],
            cwd=ts_cwd,
        )
        duration = time.monotonic() - start
        passed = result.returncode == 0
        message = ""
        if not passed:
            output = result.stderr.strip() or result.stdout.strip()
            lines = output.split("\n")[:5]
            message = "\n".join(lines)
        check = CheckResult(
            name="TypeScript Lint (eslint)",
            passed=passed,
            blocking=True,
            duration_s=duration,
            message=message,
        )
        gate.checks.append(check)
        if not json_output:
            status = _color("PASS", GREEN) if check.passed else _color("FAIL", RED)
            print(f"  [5/8] {check.name}: {status} ({check.duration_s:.1f}s)")
    else:
        gate.checks.append(CheckResult("TypeScript Lint", True, True, 0, skipped=True))
        if not json_output:
            print(_color("  [5/8] TypeScript Lint: SKIPPED", GRAY))

    # TypeScript tests
    if ts_dirs_with_tsconfig:
        ts_cwd = ts_dirs_with_tsconfig[0]
        start = time.monotonic()
        result = _run(["npx", "vitest", "run"], cwd=ts_cwd)
        duration = time.monotonic() - start
        passed = result.returncode == 0
        message = ""
        if not passed:
            output = result.stderr.strip() or result.stdout.strip()
            lines = output.split("\n")[:5]
            message = "\n".join(lines)
        check = CheckResult(
            name="TypeScript Unit Tests (vitest)",
            passed=passed,
            blocking=True,
            duration_s=duration,
            message=message,
        )
        gate.checks.append(check)
        if not json_output:
            status = _color("PASS", GREEN) if check.passed else _color("FAIL", RED)
            print(f"  [6/8] {check.name}: {status} ({check.duration_s:.1f}s)")
    else:
        gate.checks.append(
            CheckResult("TypeScript Unit Tests", True, True, 0, skipped=True)
        )
        if not json_output:
            print(_color("  [6/8] TypeScript Unit Tests: SKIPPED", GRAY))

    # Anti-placeholder scan
    if scan_dirs:
        check = _scan_check(
            "Anti-Placeholder Scan",
            PLACEHOLDER_PATTERN,
            scan_dirs,
            exclude_comment="# noqa: placeholder",
        )
        gate.checks.append(check)
        if not json_output:
            status = _color("PASS", GREEN) if check.passed else _color("FAIL", RED)
            print(f"  [7/8] {check.name}: {status} ({check.duration_s:.1f}s)")
            if not check.passed:
                print(f"         {check.message}")
    else:
        gate.checks.append(
            CheckResult("Anti-Placeholder Scan", True, True, 0, skipped=True)
        )

    # Anti-deferral scan
    if scan_dirs:
        check = _scan_check("Anti-Deferral Scan", DEFERRAL_PATTERN, scan_dirs)
        gate.checks.append(check)
        if not json_output:
            status = _color("PASS", GREEN) if check.passed else _color("FAIL", RED)
            print(f"  [8/8] {check.name}: {status} ({check.duration_s:.1f}s)")
            if not check.passed:
                print(f"         {check.message}")
    else:
        gate.checks.append(
            CheckResult("Anti-Deferral Scan", True, True, 0, skipped=True)
        )

    if not json_output:
        print()

    # ---- ADVISORY CHECKS ----

    if not json_output:
        print(_color("  --- Advisory (non-blocking) ---", CYAN))

    # Coverage
    if has_python:
        check = _timed_check(
            "Coverage Report",
            ["uv", "run", "pytest", "--cov=packages/core", "--cov-report=term", "-q"],
            blocking=False,
        )
        gate.checks.append(check)
        if not json_output:
            status = _color("PASS", GREEN) if check.passed else _color("WARN", YELLOW)
            print(f"  [A1]  {check.name}: {status} ({check.duration_s:.1f}s)")

    # Security
    if has_python:
        check = _timed_check(
            "Security Scan (bandit)",
            ["uv", "run", "bandit", "-r", "packages/", "-q"],
            blocking=False,
        )
        gate.checks.append(check)
        if not json_output:
            status = _color("PASS", GREEN) if check.passed else _color("WARN", YELLOW)
            print(f"  [A2]  {check.name}: {status} ({check.duration_s:.1f}s)")

    # Evidence bundle
    evidence = _evidence_check()
    gate.checks.append(evidence)
    if not json_output:
        if evidence.skipped:
            print(_color(f"  [A3]  {evidence.name}: SKIPPED", GRAY))
        else:
            print(f"  [A3]  {evidence.name}: {evidence.message}")

    # ---- SUMMARY ----

    if not json_output:
        print()
        s = gate.summary
        if gate.all_blocking_passed:
            print(_color("=" * 44, GREEN))
            print(
                _color(
                    f"  All blocking checks passed! ({s['total_duration_s']}s)", GREEN
                )
            )
            print(_color("=" * 44, GREEN))
        else:
            print(_color("=" * 44, RED))
            print(
                _color(
                    f"  {s['blocking_failed']} blocking check(s) FAILED ({s['total_duration_s']}s)",
                    RED,
                )
            )
            print(_color("=" * 44, RED))
    else:
        print(gate.to_json())

    return gate


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Zorivest Codebase Quality Gate",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Scope levels:
  phase   Full repo validation (default). Run when all MEUs in a phase are complete.
  meu     Scoped to touched files. Run after each MEU's implementation.

Examples:
  uv run python tools/validate_codebase.py
  uv run python tools/validate_codebase.py --scope meu --files packages/core/src/zorivest_core/domain/portfolio_balance.py
  uv run python tools/validate_codebase.py --json
        """,
    )
    parser.add_argument(
        "--scope",
        choices=["phase", "meu"],
        default="phase",
        help="Validation scope: 'phase' (full repo) or 'meu' (touched files)",
    )
    parser.add_argument(
        "--files",
        nargs="*",
        help="Explicit file list for MEU scope",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output results as JSON (for agent parsing)",
    )
    args = parser.parse_args()

    gate = run_quality_gate(
        scope=args.scope,
        files=args.files,
        json_output=args.json_output,
    )

    sys.exit(0 if gate.all_blocking_passed else 1)


if __name__ == "__main__":
    main()
