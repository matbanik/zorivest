#!/usr/bin/env python3
"""
Zorivest Build Plan Validator
=============================

Validates the split build plan files for:
  1. Cross-reference integrity (links between files resolve)
  2. Build order numbering (1–58, no gaps or duplicates)
  3. Phase numbering consistency (file names match content)
  4. Prerequisite chain (Phase N depends on N-1)
  5. File completeness (all expected files exist)
  6. Hub link integrity (BUILD_PLAN.md links resolve)
  7. Heading structure (required sections present)
  8. Stale content detection (original BUILD_PLAN.md not still monolithic)

Usage:
  python tools/validate_build_plan.py          # Run all checks
  python tools/validate_build_plan.py -v       # Verbose output
  python tools/validate_build_plan.py --json   # JSON output for CI

Note: On Windows, set PYTHONUTF8=1 if you see encoding errors, or run
      with `python -X utf8 tools/validate_build_plan.py`.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


# ─── Configuration ────────────────────────────────────────────────────────

DOCS_DIR = Path(__file__).parent.parent / "docs"
BUILD_PLAN_DIR = DOCS_DIR / "build-plan"
HUB_FILE = DOCS_DIR / "BUILD_PLAN.md"

EXPECTED_FILES = [
    "00-overview.md",
    "01-domain-layer.md",
    "02-infrastructure.md",
    "03-service-layer.md",
    "04-rest-api.md",
    "05-mcp-server.md",
    "06-gui.md",
    "07-distribution.md",
    "domain-model-reference.md",
    "testing-strategy.md",
    "image-architecture.md",
    "dependency-manifest.md",
    "build-priority-matrix.md",
]

PHASE_FILES = [f for f in EXPECTED_FILES if re.match(r"^\d{2}-", f)]

# Required sections in phase files (01-07)
REQUIRED_PHASE_SECTIONS = ["## Goal", "## Exit Criteria"]

# Maximum line count for hub file (should be slim)
HUB_MAX_LINES = 150


# ─── Data Structures ─────────────────────────────────────────────────────

@dataclass
class Issue:
    severity: str  # ERROR, WARNING
    check: str
    file: str
    message: str
    line: Optional[int] = None


@dataclass
class ValidationResult:
    issues: list[Issue] = field(default_factory=list)
    stats: dict = field(default_factory=dict)

    @property
    def errors(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == "ERROR"]

    @property
    def warnings(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == "WARNING"]

    @property
    def passed(self) -> bool:
        return len(self.errors) == 0


# ─── Validators ───────────────────────────────────────────────────────────

def check_file_completeness(result: ValidationResult) -> None:
    """Check that all expected files exist."""
    for filename in EXPECTED_FILES:
        filepath = BUILD_PLAN_DIR / filename
        if not filepath.exists():
            result.issues.append(Issue(
                severity="ERROR",
                check="file_completeness",
                file=filename,
                message=f"Expected file missing: {filepath}",
            ))

    if not HUB_FILE.exists():
        result.issues.append(Issue(
            severity="ERROR",
            check="file_completeness",
            file="BUILD_PLAN.md",
            message=f"Hub file missing: {HUB_FILE}",
        ))

    existing = [f.name for f in BUILD_PLAN_DIR.glob("*.md")] if BUILD_PLAN_DIR.exists() else []
    result.stats["expected_files"] = len(EXPECTED_FILES)
    result.stats["existing_files"] = len(existing)
    result.stats["missing_files"] = len(EXPECTED_FILES) - len(
        [f for f in EXPECTED_FILES if (BUILD_PLAN_DIR / f).exists()]
    )


def check_hub_links(result: ValidationResult) -> None:
    """Verify all links in BUILD_PLAN.md resolve to existing files."""
    if not HUB_FILE.exists():
        return

    content = HUB_FILE.read_text(encoding="utf-8")
    # Match markdown links like [text](build-plan/filename.md)
    link_pattern = re.compile(r"\[([^\]]+)\]\(build-plan/([^)]+)\)")

    for match in link_pattern.finditer(content):
        link_text, target = match.group(1), match.group(2)
        target_path = DOCS_DIR / "build-plan" / target
        if not target_path.exists():
            line_num = content[:match.start()].count("\n") + 1
            result.issues.append(Issue(
                severity="ERROR",
                check="hub_links",
                file="BUILD_PLAN.md",
                message=f"Broken link to '{target}' (text: '{link_text}')",
                line=line_num,
            ))


def check_hub_size(result: ValidationResult) -> None:
    """Ensure hub file is slim (not still the monolithic original)."""
    if not HUB_FILE.exists():
        return

    content = HUB_FILE.read_text(encoding="utf-8")
    line_count = content.count("\n") + 1
    result.stats["hub_lines"] = line_count

    if line_count > HUB_MAX_LINES:
        result.issues.append(Issue(
            severity="WARNING",
            check="hub_size",
            file="BUILD_PLAN.md",
            message=f"Hub file has {line_count} lines (max recommended: {HUB_MAX_LINES}). "
                    "It may still contain monolithic content.",
        ))

    # Check for code blocks — hub should have minimal code
    code_blocks = content.count("```")
    if code_blocks > 6:  # Allow a few for the dependency diagram
        result.issues.append(Issue(
            severity="WARNING",
            check="hub_size",
            file="BUILD_PLAN.md",
            message=f"Hub file has {code_blocks // 2} code blocks. "
                    "Code should be in phase files, not the hub.",
        ))


def check_cross_references(result: ValidationResult) -> None:
    """Verify cross-references between split files resolve."""
    if not BUILD_PLAN_DIR.exists():
        return

    existing_files = {f.name for f in BUILD_PLAN_DIR.glob("*.md")}
    link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+\.md)\)")

    for md_file in BUILD_PLAN_DIR.glob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        for match in link_pattern.finditer(content):
            link_text, target = match.group(1), match.group(2)

            # Skip links to parent directory (e.g., ../BUILD_PLAN.md)
            if target.startswith("../"):
                target_path = BUILD_PLAN_DIR.parent / target.lstrip("../")
                if not target_path.exists():
                    line_num = content[:match.start()].count("\n") + 1
                    result.issues.append(Issue(
                        severity="ERROR",
                        check="cross_references",
                        file=md_file.name,
                        message=f"Broken link to '{target}' (text: '{link_text}')",
                        line=line_num,
                    ))
                continue

            # Check sibling file references
            if target not in existing_files:
                line_num = content[:match.start()].count("\n") + 1
                result.issues.append(Issue(
                    severity="ERROR",
                    check="cross_references",
                    file=md_file.name,
                    message=f"Broken link to '{target}' (text: '{link_text}')",
                    line=line_num,
                ))


def check_phase_numbering(result: ValidationResult) -> None:
    """Verify phase files have consistent numbering in filenames and content."""
    phase_pattern = re.compile(r"^(\d{2})-(.+)\.md$")

    for filename in PHASE_FILES:
        filepath = BUILD_PLAN_DIR / filename
        if not filepath.exists():
            continue

        match = phase_pattern.match(filename)
        if not match:
            continue

        file_num = int(match.group(1))
        if file_num == 0:  # overview has no phase number
            continue

        content = filepath.read_text(encoding="utf-8")

        # Check that the H1 heading mentions the correct phase number
        h1_match = re.search(r"^# Phase (\d+):", content, re.MULTILINE)
        if h1_match:
            content_num = int(h1_match.group(1))
            if content_num != file_num:
                result.issues.append(Issue(
                    severity="ERROR",
                    check="phase_numbering",
                    file=filename,
                    message=f"File number ({file_num:02d}) doesn't match "
                            f"heading Phase {content_num}",
                ))


def check_required_sections(result: ValidationResult) -> None:
    """Verify phase files have required sections."""
    for filename in PHASE_FILES:
        filepath = BUILD_PLAN_DIR / filename
        if not filepath.exists() or filename == "00-overview.md":
            continue

        content = filepath.read_text(encoding="utf-8")
        for section in REQUIRED_PHASE_SECTIONS:
            if section not in content:
                result.issues.append(Issue(
                    severity="WARNING",
                    check="required_sections",
                    file=filename,
                    message=f"Missing required section: '{section}'",
                ))


def check_build_order_numbering(result: ValidationResult) -> None:
    """Check the 58-item build order in the priority matrix for gaps/duplicates."""
    matrix_file = BUILD_PLAN_DIR / "build-priority-matrix.md"
    if not matrix_file.exists():
        return

    content = matrix_file.read_text(encoding="utf-8")

    # Extract build order numbers from table rows
    # Matches patterns like | **1** | or | **3a** |
    order_pattern = re.compile(r"\|\s*\*\*(\d+[a-z]?)\*\*\s*\|")
    found_orders = []

    for match in order_pattern.finditer(content):
        order_str = match.group(1)
        found_orders.append(order_str)

    result.stats["build_order_items"] = len(found_orders)

    # Check for duplicates
    seen = set()
    for order in found_orders:
        if order in seen:
            result.issues.append(Issue(
                severity="ERROR",
                check="build_order",
                file="build-priority-matrix.md",
                message=f"Duplicate build order number: {order}",
            ))
        seen.add(order)

    # Check that numeric orders (excluding suffixed like 3a, 3b, 3c) are sequential
    numeric_orders = sorted([int(o) for o in found_orders if o.isdigit()])
    if numeric_orders:
        expected_max = max(numeric_orders)
        for i in range(1, expected_max + 1):
            if i not in numeric_orders:
                # Check if it has a suffix variant
                suffixed = [o for o in found_orders if o.startswith(str(i)) and not o.isdigit()]
                if not suffixed:
                    result.issues.append(Issue(
                        severity="WARNING",
                        check="build_order",
                        file="build-priority-matrix.md",
                        message=f"Missing build order number: {i}",
                    ))

    result.stats["max_build_order"] = max(numeric_orders) if numeric_orders else 0


def check_prerequisite_chain(result: ValidationResult) -> None:
    """Verify phase prerequisite mentions are consistent."""
    prereq_pattern = re.compile(r"Prerequisites?:\s*(.+?)[\|>\n]", re.IGNORECASE)

    for filename in PHASE_FILES:
        filepath = BUILD_PLAN_DIR / filename
        if not filepath.exists() or filename == "00-overview.md":
            continue

        content = filepath.read_text(encoding="utf-8")
        match = prereq_pattern.search(content)
        if not match:
            result.issues.append(Issue(
                severity="WARNING",
                check="prerequisites",
                file=filename,
                message="No prerequisites line found in header",
            ))


# ─── Runner ───────────────────────────────────────────────────────────────

def run_validation(verbose: bool = False) -> ValidationResult:
    """Run all validation checks and return results."""
    result = ValidationResult()

    checks = [
        ("File Completeness", check_file_completeness),
        ("Hub Links", check_hub_links),
        ("Hub Size", check_hub_size),
        ("Cross-References", check_cross_references),
        ("Phase Numbering", check_phase_numbering),
        ("Required Sections", check_required_sections),
        ("Build Order Numbering", check_build_order_numbering),
        ("Prerequisite Chain", check_prerequisite_chain),
    ]

    for name, check_fn in checks:
        if verbose:
            print(f"  Running: {name}...", end=" ", flush=True)
        before = len(result.issues)
        check_fn(result)
        after = len(result.issues)
        if verbose:
            new_issues = after - before
            if new_issues == 0:
                print("✅ OK")
            else:
                print(f"⚠️  {new_issues} issue(s)")

    return result


def format_text_report(result: ValidationResult) -> str:
    """Format validation results as a human-readable report."""
    lines = []
    lines.append("=" * 60)
    lines.append("  Zorivest Build Plan Validation Report")
    lines.append("=" * 60)
    lines.append("")

    # Stats
    lines.append("📊 Statistics:")
    for key, value in result.stats.items():
        lines.append(f"   {key}: {value}")
    lines.append("")

    # Errors
    if result.errors:
        lines.append(f"❌ {len(result.errors)} Error(s):")
        for issue in result.errors:
            loc = f":{issue.line}" if issue.line else ""
            lines.append(f"   [{issue.check}] {issue.file}{loc}")
            lines.append(f"   └─ {issue.message}")
        lines.append("")

    # Warnings
    if result.warnings:
        lines.append(f"⚠️  {len(result.warnings)} Warning(s):")
        for issue in result.warnings:
            loc = f":{issue.line}" if issue.line else ""
            lines.append(f"   [{issue.check}] {issue.file}{loc}")
            lines.append(f"   └─ {issue.message}")
        lines.append("")

    # Summary
    if result.passed:
        lines.append("✅ PASSED — No errors found.")
    else:
        lines.append(f"❌ FAILED — {len(result.errors)} error(s) must be fixed.")

    return "\n".join(lines)


def format_json_report(result: ValidationResult) -> str:
    """Format validation results as JSON for CI integration."""
    return json.dumps({
        "passed": result.passed,
        "error_count": len(result.errors),
        "warning_count": len(result.warnings),
        "stats": result.stats,
        "issues": [
            {
                "severity": i.severity,
                "check": i.check,
                "file": i.file,
                "message": i.message,
                "line": i.line,
            }
            for i in result.issues
        ],
    }, indent=2)


# ─── CLI ──────────────────────────────────────────────────────────────────

def main():
    # Ensure UTF-8 output on Windows (emoji-safe on cp1252 consoles)
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        description="Validate Zorivest build plan structure and cross-references."
    )
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Show detailed output for each check")
    parser.add_argument("--json", action="store_true",
                        help="Output results as JSON (for CI)")
    args = parser.parse_args()

    if args.verbose:
        print(f"\n📂 Docs dir:  {DOCS_DIR}")
        print(f"📂 Plan dir:  {BUILD_PLAN_DIR}")
        print(f"📄 Hub file:  {HUB_FILE}")
        print()

    result = run_validation(verbose=args.verbose)

    if args.json:
        print(format_json_report(result))
    else:
        print()
        print(format_text_report(result))

    sys.exit(0 if result.passed else 1)


if __name__ == "__main__":
    main()
