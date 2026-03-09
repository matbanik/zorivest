"""Version resolution for Zorivest.

Resolution order:
1. Frozen constant (_VERSION) for bundled releases
2. importlib.metadata for installed packages
3. Fallback to "0.0.0-dev"

Source: 04g-api-system.md §Version
"""

from __future__ import annotations

import importlib.metadata

_VERSION: str | None = None  # Set by build/freeze process


def get_version() -> str:
    """Return the current application version string (SemVer)."""
    if _VERSION is not None:
        return _VERSION

    try:
        return importlib.metadata.version("zorivest-core")
    except importlib.metadata.PackageNotFoundError:
        return "0.0.0-dev"


def get_version_context() -> str:
    """Return the version resolution context.

    Returns:
        "frozen" — version from frozen constant (_VERSION)
        "installed" — version from importlib.metadata
        "dev" — fallback (package not installed)
    """
    if _VERSION is not None:
        return "frozen"

    try:
        importlib.metadata.version("zorivest-core")
        return "installed"
    except importlib.metadata.PackageNotFoundError:
        return "dev"
