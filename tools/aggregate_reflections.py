#!/usr/bin/env python3
"""
aggregate_reflections.py — Instruction Coverage Analysis aggregator.

Reads N session reflection YAMLs and emits a pruning-candidate report.
Safety: rules tagged `priority: P0` in registry.yaml are never auto-pruned.

Based on the Claude Deep Research reference implementation (§3) with
adaptations for the Zorivest monorepo structure.

Usage:
    python tools/aggregate_reflections.py --input .agent/reflections/ --registry .agent/schemas/registry.yaml
    python tools/aggregate_reflections.py --help
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import yaml  # pip install pyyaml

# --- Config ---------------------------------------------------------------
DECAY_WINDOW_DAYS = 30
RECENT_DAYS = 7
SILENT_GUARD_MIN_INFLUENCE = 1  # influence>=1 without citation
LOW_FREQ_THRESHOLD = 0.05  # cited in <5% of sessions
DECAY_RATIO_THRESHOLD = 0.25  # recent freq < 25% of baseline freq
P0_NEVER_PRUNE = True  # hard safety gate


# --- IO -------------------------------------------------------------------
def load_reflections(directory: str) -> list[dict]:
    """Load all .yaml reflection files from a directory.

    AC-3.1: Reads all .yaml files from a configurable reflections directory.
    Returns empty list for empty directories (graceful exit).
    """
    paths = sorted(glob.glob(os.path.join(directory, "*.yaml")))
    out: list[dict] = []
    for p in paths:
        try:
            with open(p, encoding="utf-8") as f:
                doc = yaml.safe_load(f)
            if doc is None:
                continue
            doc["_path"] = p
            doc["_mtime"] = datetime.fromtimestamp(os.path.getmtime(p))
            out.append(doc)
        except Exception as e:
            print(f"[skip] {p}: {e}", file=sys.stderr)
    return out


def load_registry(path: str) -> dict:
    """Load the instruction registry from a YAML file.

    AC-3.7: Loads registry.yaml for priority/safety tags.
    Missing registry → FileNotFoundError with instructions.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Registry not found: {path}. "
            f'Create it with: python -c "... extract AGENTS.md H2 ..." '
            f"or copy from .agent/schemas/registry.yaml"
        )
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    # Normalize: if sections is a list, convert to dict keyed by section_id
    sections = data.get("sections", {})
    if isinstance(sections, list):
        data["sections"] = {s["section_id"]: s for s in sections}

    return data


# --- Core analyses --------------------------------------------------------
def frequency_heatmap(refs: list[dict]) -> dict[str, dict]:
    """Per-section citation rate, influence histogram.

    AC-3.2: Outputs a frequency heatmap (section_id × citation_count).
    """
    n = max(len(refs), 1)
    sect: dict[str, dict] = defaultdict(
        lambda: {"cited": 0, "infl_sum": 0, "infl_dist": Counter()}
    )
    for r in refs:
        for s in r.get("sections") or []:
            row = sect[s["id"]]
            row["cited"] += 1 if s.get("cited") else 0
            row["infl_sum"] += int(s.get("influence", 0))
            row["infl_dist"][int(s.get("influence", 0))] += 1
    return {
        sid: {
            "cite_rate": v["cited"] / n,
            "citation_count": v["cited"],
            "avg_influence": v["infl_sum"] / n,
            "influence_distribution": dict(v["infl_dist"]),
            "n_sessions": n,
        }
        for sid, v in sect.items()
    }


def decay_curves(refs: list[dict]) -> dict[str, dict]:
    """Compare recent (last 7d) vs baseline (last 30d) citation rates."""
    now = datetime.now()
    recent_cut = now - timedelta(days=RECENT_DAYS)
    baseline_cut = now - timedelta(days=DECAY_WINDOW_DAYS)
    recent: dict[str, list[int]] = defaultdict(list)
    baseline: dict[str, list[int]] = defaultdict(list)

    for r in refs:
        ts = r.get("_mtime", now)
        if ts < baseline_cut:
            continue
        bucket = recent if ts >= recent_cut else baseline
        for s in r.get("sections") or []:
            bucket[s["id"]].append(1 if s.get("cited") else 0)

    out: dict[str, dict] = {}
    for sid in set(list(recent) + list(baseline)):
        b = sum(baseline[sid]) / max(len(baseline[sid]), 1)
        r = sum(recent[sid]) / max(len(recent[sid]), 1)
        ratio = (r / b) if b > 0 else None
        out[sid] = {
            "baseline": b,
            "recent": r,
            "ratio": ratio,
            "decaying": (
                b > 0.10 and ratio is not None and ratio < DECAY_RATIO_THRESHOLD
            ),
        }
    return out


def silent_guards(refs: list[dict]) -> dict[str, dict]:
    """Sections with influence>=1 but cited=False — present but not quoted.

    AC-3.3: Identifies silent guards.
    """
    n_total: dict[str, int] = defaultdict(int)
    n_silent: dict[str, int] = defaultdict(int)

    for r in refs:
        for s in r.get("sections") or []:
            n_total[s["id"]] += 1
            if (not s.get("cited")) and int(
                s.get("influence", 0)
            ) >= SILENT_GUARD_MIN_INFLUENCE:
                n_silent[s["id"]] += 1

    return {
        sid: {
            "silent_rate": n_silent[sid] / n_total[sid],
            "silent_count": n_silent[sid],
            "n": n_total[sid],
        }
        for sid in n_total
    }


def conflict_signal(refs: list[dict]) -> Counter:
    """Aggregate conflict reports across all sessions."""
    c: Counter = Counter()
    for r in refs:
        for pair in r.get("conflicts") or []:
            c[pair] += 1
    return c


def pruning_candidates(
    freq: dict[str, dict],
    decay: dict[str, dict],
    silent: dict[str, dict],
    registry: dict,
) -> list[dict]:
    """Combine signals into actionable candidates with safety gates.

    AC-3.4: P0 sections → KEEP_ALWAYS (never auto-pruned).
    AC-3.5: Low-frequency non-P0 → PRUNING_CANDIDATE.
    AC-3.6: Low-frequency but high-influence → RAREBUT_DECISIVE.
    """
    sect_meta = registry.get("sections", {})
    out: list[dict] = []

    for sid, f in freq.items():
        meta = sect_meta.get(sid, {})
        priority = meta.get("priority", "P2")
        is_safety = (priority == "P0") or meta.get("safety", False)

        low_freq = f["cite_rate"] < LOW_FREQ_THRESHOLD
        low_infl = f["avg_influence"] < 0.5
        decaying = decay.get(sid, {}).get("decaying", False)
        silent_rate = silent.get(sid, {}).get("silent_rate", 0.0)
        is_silent = silent_rate > 0.20

        # SAFETY GATE: never auto-prune P0/safety rules
        if is_safety and P0_NEVER_PRUNE:
            if low_freq and not is_silent:
                out.append(
                    {
                        "id": sid,
                        "priority": priority,
                        "action": "KEEP_ALWAYS",
                        "rationale": (
                            "P0/safety rule with low cite rate; "
                            "run counterfactual ablation before any change."
                        ),
                        "metrics": f,
                        "decay": decay.get(sid),
                        "silent": silent.get(sid),
                    }
                )
            continue

        if is_silent:
            out.append(
                {
                    "id": sid,
                    "priority": priority,
                    "action": "KEEP_AS_SILENT_GUARD",
                    "rationale": (
                        f"Silent guard rate {silent_rate:.0%}; "
                        "shapes output without citation. Keep."
                    ),
                    "metrics": f,
                }
            )
        elif low_freq and low_infl and not decaying:
            out.append(
                {
                    "id": sid,
                    "priority": priority,
                    "action": "PRUNING_CANDIDATE",
                    "rationale": "Low cite rate + low influence + not decaying.",
                    "metrics": f,
                }
            )
        elif decaying:
            out.append(
                {
                    "id": sid,
                    "priority": priority,
                    "action": "INVESTIGATE_DECAY",
                    "rationale": "Citation rate dropped >75% in last 7d.",
                    "metrics": f,
                    "decay": decay.get(sid),
                }
            )
        elif low_freq and not low_infl:
            out.append(
                {
                    "id": sid,
                    "priority": priority,
                    "action": "RAREBUT_DECISIVE",
                    "rationale": (
                        "Rarely cited but high influence when used. "
                        "Move to on-demand workflow file."
                    ),
                    "metrics": f,
                }
            )

    return out


def render_report(
    refs: list[dict],
    freq: dict[str, dict],
    decay: dict[str, dict],
    silent: dict[str, dict],
    conflicts: Counter,
    candidates: list[dict],
) -> str:
    """Render a human-readable markdown coverage report."""
    lines = [
        "# Instruction Coverage Report",
        f"_Generated {datetime.now().isoformat(timespec='seconds')} "
        f"from {len(refs)} sessions_\n",
        "## Top sections by citation rate",
        "| Section | Cite rate | Avg influence | Silent rate |",
        "|---|---:|---:|---:|",
    ]
    for sid in sorted(freq, key=lambda s: -freq[s]["cite_rate"])[:20]:
        f = freq[sid]
        sr = silent.get(sid, {}).get("silent_rate", 0.0)
        lines.append(
            f"| `{sid}` | {f['cite_rate']:.1%} | {f['avg_influence']:.2f} | {sr:.1%} |"
        )
    lines += ["", "## Pruning candidates (with safety gates)"]
    for c in candidates:
        lines.append(
            f"- **{c['action']}** `{c['id']}` ({c['priority']}): {c['rationale']}"
        )
    if conflicts:
        lines += ["", "## Reported conflicts (top 10)"]
        for pair, n in conflicts.most_common(10):
            lines.append(f"- `{pair}` × {n}")
    return "\n".join(lines)


def run_analysis(
    reflections_dir: str,
    registry_path: str,
    output_dir: str | None = None,
) -> dict | None:
    """Run the full analysis pipeline and return results.

    AC-3.8: Outputs JSON report to stdout or configurable output file.
    """
    refs = load_reflections(reflections_dir)
    if not refs:
        print("no reflections found", file=sys.stderr)
        return None

    registry = load_registry(registry_path)
    freq = frequency_heatmap(refs)
    decay_data = decay_curves(refs)
    silent = silent_guards(refs)
    conflicts = conflict_signal(refs)
    cands = pruning_candidates(freq, decay_data, silent, registry)

    result = {
        "frequency": freq,
        "decay": decay_data,
        "silent_guards": silent,
        "conflicts": dict(conflicts),
        "candidates": cands,
        "n_sessions": len(refs),
    }

    if output_dir:
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        (out_path / f"coverage_{stamp}.md").write_text(
            render_report(refs, freq, decay_data, silent, conflicts, cands),
            encoding="utf-8",
        )
        (out_path / f"coverage_{stamp}.json").write_text(
            json.dumps(result, indent=2, default=str),
            encoding="utf-8",
        )
        print(f"[ok] wrote {out_path}/coverage_{stamp}.{{md,json}}")

    return result


# --- CLI ------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Instruction Coverage Analysis aggregator",
        epilog="Safety: P0/safety sections are never auto-pruned.",
    )
    parser.add_argument(
        "--input",
        default=".agent/reflections",
        help="Directory containing .yaml reflection files",
    )
    parser.add_argument(
        "--registry",
        default=".agent/schemas/registry.yaml",
        help="Path to registry.yaml",
    )
    parser.add_argument(
        "--output",
        default=".agent/reports",
        help="Output directory for reports",
    )
    parser.add_argument(
        "--json-stdout",
        action="store_true",
        help="Print JSON result to stdout instead of writing files",
    )

    args = parser.parse_args(argv)
    result = run_analysis(
        args.input, args.registry, args.output if not args.json_stdout else None
    )

    if result is None:
        return 1

    if args.json_stdout:
        print(json.dumps(result, indent=2, default=str))

    return 0


if __name__ == "__main__":
    sys.exit(main())
