# tests/unit/test_mcp_pipeline_security.py
"""Cross-reference proxy tests for MCP pipeline-security tool contract (AC-33m).

The canonical MCP tool/resource tests are TypeScript (project convention):
    mcp-server/tests/pipeline-security-tools.test.ts

This Python test file satisfies the AC-33m path reference in task.md row 14
by verifying the TypeScript test infrastructure exists and covers the expected
tool/resource counts.

Run with: uv run pytest tests/unit/test_mcp_pipeline_security.py -x --tb=short -v
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

# ── Constants ───────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parents[2]
MCP_TEST_FILE = REPO_ROOT / "mcp-server" / "tests" / "pipeline-security-tools.test.ts"
MCP_SOURCE_FILE = (
    REPO_ROOT / "mcp-server" / "src" / "tools" / "pipeline-security-tools.ts"
)

EXPECTED_TOOL_COUNT = 12
EXPECTED_RESOURCE_URIS = [
    "pipeline://db-schema",
    "pipeline://templates",
    "pipeline://deny-tables",
    "pipeline://emulator/mock-data",
    "pipeline://emulator-phases",
    "pipeline://providers",
]

EXPECTED_TOOL_NAMES = [
    "emulate_policy",
    "validate_sql",
    "list_db_tables",
    "get_db_row_samples",
    "create_email_template",
    "get_email_template",
    "list_email_templates",
    "update_email_template",
    "delete_email_template",
    "preview_email_template",
    "list_step_types",
    "list_provider_capabilities",
]


# ── Infrastructure verification ─────────────────────────────────────────


class TestMcpPipelineSecurityInfrastructure:
    """Verify the TypeScript MCP test file exists and the source registers expected tools/resources."""

    def test_typescript_test_file_exists(self) -> None:
        """AC-33m: MCP pipeline-security test file exists at the canonical TS path."""
        assert MCP_TEST_FILE.exists(), (
            f"MCP test file not found at {MCP_TEST_FILE}. "
            "Pipeline-security MCP tests must be TypeScript per project convention."
        )

    def test_typescript_source_file_exists(self) -> None:
        """The MCP tool source file exists."""
        assert MCP_SOURCE_FILE.exists(), (
            f"MCP source file not found at {MCP_SOURCE_FILE}"
        )


# ── Source contract verification ─────────────────────────────────────────


class TestMcpPipelineSecurityContract:
    """Verify the TypeScript source registers expected tools and resources by scanning source text."""

    @pytest.fixture(autouse=True)
    def _load_source(self) -> None:
        """Load the TypeScript source file for contract verification."""
        self.source_text = MCP_SOURCE_FILE.read_text(encoding="utf-8")

    def test_all_tool_names_registered(self) -> None:
        """All 12 expected tool names appear in the source as registerTool calls."""
        for tool_name in EXPECTED_TOOL_NAMES:
            assert f'"{tool_name}"' in self.source_text, (
                f"Tool '{tool_name}' not found in pipeline-security-tools.ts"
            )

    def test_all_resource_uris_registered(self) -> None:
        """All 6 expected resource URIs appear in the source."""
        for uri in EXPECTED_RESOURCE_URIS:
            assert f'"{uri}"' in self.source_text, (
                f"Resource URI '{uri}' not found in pipeline-security-tools.ts"
            )

    def test_tool_count_matches_expected(self) -> None:
        """Source registers exactly 12 tools (count registerTool calls)."""
        # Count unique tool registrations by looking for the pattern
        count = self.source_text.count("server.registerTool(")
        assert count == EXPECTED_TOOL_COUNT, (
            f"Expected {EXPECTED_TOOL_COUNT} registerTool calls, found {count}"
        )

    def test_resource_count_matches_expected(self) -> None:
        """Source registers exactly 6 resources (count server.resource calls in registerPipelineSecurityResources)."""
        # Extract the resource registration function body
        resource_fn_start = self.source_text.find(
            "export function registerPipelineSecurityResources"
        )
        assert resource_fn_start != -1, (
            "registerPipelineSecurityResources function not found"
        )

        resource_section = self.source_text[resource_fn_start:]
        count = resource_section.count("server.resource(")
        assert count == len(EXPECTED_RESOURCE_URIS), (
            f"Expected {len(EXPECTED_RESOURCE_URIS)} resource registrations, found {count}"
        )
