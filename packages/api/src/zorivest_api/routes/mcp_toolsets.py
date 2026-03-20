"""MCP toolset and diagnostics REST endpoints.

Provides static tool catalog data from zorivest-tools.json manifest
and API diagnostics (uptime, version).

Source: 06f §6f.9 L743, [PD-46a]
MEU: 46a (mcp-rest-proxy)
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request

mcp_toolsets_router = APIRouter(prefix="/api/v1/mcp", tags=["system"])

# ── Load manifest at module import (cached) ─────────────────────────────

# Walk up from this file to find the repo root, then locate the manifest.
# This file:  packages/api/src/zorivest_api/routes/mcp_toolsets.py
# Repo root:  5 levels up
_REPO_ROOT = Path(__file__).resolve().parents[5]
_MANIFEST_PATH = _REPO_ROOT / "mcp-server" / "zorivest-tools.json"

_manifest_data: dict[str, Any] | None = None


def _load_manifest() -> dict[str, Any]:
    """Load and cache the tools manifest. Returns fallback on failure."""
    global _manifest_data  # noqa: PLW0603
    if _manifest_data is not None:
        return _manifest_data

    try:
        with open(_MANIFEST_PATH, encoding="utf-8") as f:
            _manifest_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Graceful fallback: return empty catalog (not 500)
        _manifest_data = {
            "total_tools": 0,
            "toolset_count": 0,
            "toolsets": [],
            "generated_at": None,
        }
    assert _manifest_data is not None  # type narrowing for pyright
    return _manifest_data


# ── GET /api/v1/mcp/toolsets ────────────────────────────────────────────


@mcp_toolsets_router.get("/toolsets")
async def get_mcp_toolsets() -> dict[str, Any]:
    """Return MCP toolset catalog from static manifest.

    Per [PD-46a]: provides static catalog only (tool names, counts).
    Runtime `loaded` state deferred until [MCP-HTTPBROKEN] resolved.
    """
    data = _load_manifest()
    return {
        "total_tools": data.get("total_tools", 0),
        "toolset_count": data.get("toolset_count", 0),
        "toolsets": [
            {
                "name": ts["name"],
                "description": ts.get("description", ""),
                "tool_count": ts.get("tool_count", 0),
                "always_loaded": ts.get("always_loaded", False),
            }
            for ts in data.get("toolsets", [])
        ],
    }


# ── GET /api/v1/mcp/diagnostics ────────────────────────────────────────


@mcp_toolsets_router.get("/diagnostics")
async def get_mcp_diagnostics(request: Request) -> dict[str, Any]:
    """Return API diagnostics.

    Per [PD-46a]: provides API process uptime (not MCP server uptime).
    """
    start_time = getattr(request.app.state, "start_time", None)
    uptime = time.time() - start_time if start_time is not None else 0.0
    return {
        "api_uptime_seconds": round(uptime, 1),
        "api_version": request.app.version,
    }
