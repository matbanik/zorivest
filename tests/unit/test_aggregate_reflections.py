"""
Tests for tools/aggregate_reflections.py — Instruction Coverage Aggregator.

Red-phase tests: written BEFORE the implementation.
Each test maps to an Acceptance Criterion (AC-3.x) from the implementation plan.

These tests use synthetic reflection data and a minimal registry to validate
the aggregator's core behaviors.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pytest
import yaml

# The module under test — will fail to import until Green phase
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import aggregate_reflections as agg  # noqa: E402  # pyright: ignore[reportMissingImports]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_dir(tmp_path: Path) -> Path:
    """Create a temporary directory for test reflections."""
    return tmp_path


@pytest.fixture
def minimal_registry(tmp_dir: Path) -> Path:
    """Create a minimal registry.yaml with P0 and P2 sections."""
    registry = {
        "sections": [
            {
                "section_id": "p0_safety",
                "priority": "P0",
                "safety": True,
                "auto_prune": False,
            },
            {
                "section_id": "p1_quality",
                "priority": "P1",
                "safety": False,
                "auto_prune": False,
            },
            {
                "section_id": "p2_workflow",
                "priority": "P2",
                "safety": False,
                "auto_prune": True,
            },
            {
                "section_id": "p3_convenience",
                "priority": "P3",
                "safety": False,
                "auto_prune": True,
            },
        ]
    }
    path = tmp_dir / "registry.yaml"
    path.write_text(yaml.dump(registry), encoding="utf-8")
    return path


def _write_reflection(directory: Path, name: str, data: dict) -> Path:
    """Write a reflection YAML file to the given directory."""
    path = directory / name
    path.write_text(yaml.dump(data), encoding="utf-8")
    return path


def _make_reflection(
    sections: list[dict] | None = None,
    decisive_rules: list[str] | None = None,
    conflicts: list[str] | None = None,
) -> dict:
    """Create a synthetic reflection document."""
    return {
        "schema": "v1",
        "session": {
            "id": "test-session-001",
            "task_class": "tdd",
            "outcome": "success",
            "tokens_in": 10000,
            "tokens_out": 5000,
            "turns": 5,
        },
        "sections": sections or [],
        "loaded": {"workflows": [], "roles": [], "skills": [], "refs": []},
        "decisive_rules": decisive_rules or [],
        "conflicts": conflicts or [],
        "note": "test reflection",
    }


# ---------------------------------------------------------------------------
# AC-3.1: Script reads all .yaml files from a configurable reflections directory
# ---------------------------------------------------------------------------


class TestAC31ReadReflections:
    """AC-3.1: Script reads all .yaml files from a configurable directory."""

    def test_reads_yaml_files_from_directory(self, tmp_dir: Path):
        """Multiple .yaml files in the directory are all loaded."""
        reflections_dir = tmp_dir / "reflections"
        reflections_dir.mkdir()
        for i in range(3):
            _write_reflection(
                reflections_dir,
                f"SESSION_{i:03d}.yaml",
                _make_reflection(
                    sections=[{"id": "p2_workflow", "cited": True, "influence": 2}]
                ),
            )
        result = agg.load_reflections(str(reflections_dir))
        assert len(result) == 3

    def test_reads_arbitrarily_named_yaml_files(self, tmp_dir: Path):
        """F2: Files not matching SESSION_*.yaml must also be loaded (AC-3.1)."""
        reflections_dir = tmp_dir / "reflections"
        reflections_dir.mkdir()
        _write_reflection(
            reflections_dir,
            "arbitrary_name.yaml",
            _make_reflection(
                sections=[{"id": "p2_workflow", "cited": True, "influence": 1}]
            ),
        )
        result = agg.load_reflections(str(reflections_dir))
        assert len(result) == 1

    def test_empty_directory_returns_empty_list(self, tmp_dir: Path):
        """Empty directory returns an empty list (graceful exit)."""
        empty_dir = tmp_dir / "empty"
        empty_dir.mkdir()
        result = agg.load_reflections(str(empty_dir))
        assert result == []


# ---------------------------------------------------------------------------
# AC-3.2: Outputs a frequency heatmap (section_id × citation_count)
# ---------------------------------------------------------------------------


class TestAC32FrequencyHeatmap:
    """AC-3.2: Frequency heatmap with citation rates and influence distribution."""

    def test_frequency_heatmap_structure(self):
        """Heatmap returns cite_rate, citation_count, and avg_influence per section."""
        refs = [
            _make_reflection(
                sections=[
                    {"id": "p0_safety", "cited": True, "influence": 3},
                    {"id": "p2_workflow", "cited": False, "influence": 0},
                ]
            ),
            _make_reflection(
                sections=[
                    {"id": "p0_safety", "cited": True, "influence": 2},
                    {"id": "p2_workflow", "cited": True, "influence": 1},
                ]
            ),
        ]
        heatmap = agg.frequency_heatmap(refs)
        assert "p0_safety" in heatmap
        assert heatmap["p0_safety"]["cite_rate"] == 1.0  # cited in 2/2 sessions
        assert heatmap["p0_safety"]["citation_count"] == 2  # F5: explicit count
        assert heatmap["p2_workflow"]["cite_rate"] == 0.5  # cited in 1/2 sessions
        assert heatmap["p2_workflow"]["citation_count"] == 1  # F5: explicit count
        assert "influence_distribution" in heatmap["p0_safety"]


# ---------------------------------------------------------------------------
# AC-3.3: Identifies silent guards (influence>=1 but cited=false)
# ---------------------------------------------------------------------------


class TestAC33SilentGuards:
    """AC-3.3: Silent guard detection — influence>=1 but cited=false."""

    def test_detects_silent_guard(self):
        """Section with influence>=1 and cited=false is flagged as silent guard."""
        refs = [
            _make_reflection(
                sections=[
                    {"id": "p0_safety", "cited": False, "influence": 2},
                ]
            )
        ] * 10
        silent = agg.silent_guards(refs)
        assert "p0_safety" in silent
        assert silent["p0_safety"]["silent_rate"] > 0

    def test_detects_silent_guard_single_session(self):
        """F4: Silent guard detected even with a single session (no hidden threshold)."""
        refs = [
            _make_reflection(
                sections=[
                    {"id": "p0_safety", "cited": False, "influence": 2},
                ]
            )
        ]
        silent = agg.silent_guards(refs)
        assert "p0_safety" in silent
        assert silent["p0_safety"]["silent_rate"] == 1.0

    def test_no_silent_guard_when_cited(self):
        """Section that is always cited is not a silent guard."""
        refs = [
            _make_reflection(
                sections=[
                    {"id": "p0_safety", "cited": True, "influence": 3},
                ]
            )
        ] * 10
        silent = agg.silent_guards(refs)
        # Either not present or silent_rate == 0
        if "p0_safety" in silent:
            assert silent["p0_safety"]["silent_rate"] == 0


# ---------------------------------------------------------------------------
# AC-3.4: Routes P0 sections to KEEP_ALWAYS regardless of frequency
# ---------------------------------------------------------------------------


class TestAC34P0NeverPruned:
    """AC-3.4: P0 sections route to KEEP_ALWAYS per plan contract."""

    def test_p0_section_routes_to_keep_always(self, minimal_registry: Path):
        """F1: P0 section with 0 citations → KEEP_ALWAYS (not ABLATION_TEST_REQUIRED)."""
        registry = yaml.safe_load(minimal_registry.read_text(encoding="utf-8"))
        sect_meta = {s["section_id"]: s for s in registry["sections"]}
        registry_dict = {"sections": sect_meta}

        freq = {
            "p0_safety": {
                "cite_rate": 0.0,
                "avg_influence": 0.0,
                "citation_count": 0,
                "influence_distribution": {0: 10},
                "n_sessions": 10,
            },
        }
        decay = {}
        silent = {}
        candidates = agg.pruning_candidates(freq, decay, silent, registry_dict)
        actions = {c["id"]: c["action"] for c in candidates}
        # P0 must never be PRUNING_CANDIDATE
        assert actions.get("p0_safety") != "PRUNING_CANDIDATE"
        # It must be KEEP_ALWAYS per AC-3.4 plan contract
        assert actions.get("p0_safety") == "KEEP_ALWAYS"


# ---------------------------------------------------------------------------
# AC-3.5: Routes low-frequency non-P0 sections to PRUNING_CANDIDATE
# ---------------------------------------------------------------------------


class TestAC35PruningCandidates:
    """AC-3.5: Low-frequency non-P0 sections are PRUNING_CANDIDATE."""

    def test_low_freq_non_p0_is_pruning_candidate(self, minimal_registry: Path):
        """F1: Non-P0 section with low frequency → PRUNING_CANDIDATE (not PRUNE_CANDIDATE)."""
        registry = yaml.safe_load(minimal_registry.read_text(encoding="utf-8"))
        sect_meta = {s["section_id"]: s for s in registry["sections"]}
        registry_dict = {"sections": sect_meta}

        freq = {
            "p3_convenience": {
                "cite_rate": 0.01,
                "avg_influence": 0.1,
                "citation_count": 0,
                "influence_distribution": {0: 9, 1: 1},
                "n_sessions": 10,
            },
        }
        decay = {}
        silent = {}
        candidates = agg.pruning_candidates(freq, decay, silent, registry_dict)
        actions = {c["id"]: c["action"] for c in candidates}
        assert actions.get("p3_convenience") == "PRUNING_CANDIDATE"


# ---------------------------------------------------------------------------
# AC-3.6: Routes influence>=2 but cited<5% to RAREBUT_DECISIVE
# ---------------------------------------------------------------------------


class TestAC36RareButDecisive:
    """AC-3.6: Sections with high influence but low citation are RAREBUT_DECISIVE."""

    def test_rare_but_decisive(self, minimal_registry: Path):
        """Section with low cite rate but high avg influence is RAREBUT_DECISIVE."""
        registry = yaml.safe_load(minimal_registry.read_text(encoding="utf-8"))
        sect_meta = {s["section_id"]: s for s in registry["sections"]}
        registry_dict = {"sections": sect_meta}

        freq = {
            "p2_workflow": {
                "cite_rate": 0.03,
                "avg_influence": 2.5,
                "citation_count": 0,
                "influence_distribution": {3: 1, 0: 9},
                "n_sessions": 10,
            },
        }
        decay = {}
        silent = {}
        candidates = agg.pruning_candidates(freq, decay, silent, registry_dict)
        actions = {c["id"]: c["action"] for c in candidates}
        assert actions.get("p2_workflow") == "RAREBUT_DECISIVE"


# ---------------------------------------------------------------------------
# AC-3.7: Loads registry.yaml for priority/safety tags
# ---------------------------------------------------------------------------


class TestAC37LoadsRegistry:
    """AC-3.7: Loads registry.yaml and uses priority/safety tags."""

    def test_loads_registry_from_path(self, minimal_registry: Path):
        """Registry loads successfully from a given path."""
        registry = agg.load_registry(str(minimal_registry))
        assert "sections" in registry
        sect = registry["sections"]
        assert len(sect) > 0

    def test_missing_registry_raises_error(self, tmp_dir: Path):
        """F3: Missing registry → FileNotFoundError (not silent empty dict)."""
        with pytest.raises(FileNotFoundError):
            agg.load_registry(str(tmp_dir / "nonexistent.yaml"))


# ---------------------------------------------------------------------------
# AC-3.8: Outputs JSON report to stdout or configurable output file
# ---------------------------------------------------------------------------


class TestAC38OutputReport:
    """AC-3.8: Outputs JSON report."""

    def test_outputs_json_report(self, tmp_dir: Path, minimal_registry: Path):
        """End-to-end: reads reflections, outputs JSON with expected keys."""
        reflections_dir = tmp_dir / "reflections"
        reflections_dir.mkdir()

        for i in range(5):
            _write_reflection(
                reflections_dir,
                f"SESSION_{i:03d}.yaml",
                _make_reflection(
                    sections=[
                        {"id": "p0_safety", "cited": True, "influence": 3},
                        {"id": "p2_workflow", "cited": False, "influence": 0},
                    ]
                ),
            )

        output_dir = tmp_dir / "output"
        output_dir.mkdir()

        result = agg.run_analysis(
            reflections_dir=str(reflections_dir),
            registry_path=str(minimal_registry),
            output_dir=str(output_dir),
        )

        assert result is not None
        assert "frequency" in result
        assert "candidates" in result
        assert "n_sessions" in result
        assert result["n_sessions"] == 5

    def test_json_output_is_strict_json(self, tmp_dir: Path, minimal_registry: Path):
        """F6: JSON output contains no NaN/Infinity — strict JSON parsers must accept it."""
        reflections_dir = tmp_dir / "reflections"
        reflections_dir.mkdir()

        _write_reflection(
            reflections_dir,
            "SESSION_001.yaml",
            _make_reflection(
                sections=[
                    {"id": "p0_safety", "cited": True, "influence": 3},
                ]
            ),
        )

        result = agg.run_analysis(
            reflections_dir=str(reflections_dir),
            registry_path=str(minimal_registry),
        )

        assert result is not None
        # Serialize and re-parse with strict decoder — must not raise
        json_str = json.dumps(result, default=str)
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)

        # Additionally verify no NaN values exist in decay data
        for sid, decay_data in parsed.get("decay", {}).items():
            ratio = decay_data.get("ratio")
            if isinstance(ratio, float):
                assert not math.isnan(ratio), f"NaN found in decay ratio for {sid}"
                assert not math.isinf(ratio), f"Infinity found in decay ratio for {sid}"
