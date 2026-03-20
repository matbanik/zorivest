#!/usr/bin/env python3
"""Export the live FastAPI OpenAPI spec to JSON.

Usage:
    uv run python tools/export_openapi.py              # print to stdout
    uv run python tools/export_openapi.py -o openapi.committed.json  # write file
    uv run python tools/export_openapi.py --check openapi.committed.json  # diff check
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def get_openapi_spec() -> dict:
    """Generate the OpenAPI spec from the live FastAPI app."""
    from zorivest_api.main import create_app

    app = create_app()
    return app.openapi()


def main() -> None:
    parser = argparse.ArgumentParser(description="Export FastAPI OpenAPI spec")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Write spec to file (default: stdout)",
    )
    parser.add_argument(
        "--check",
        type=Path,
        metavar="COMMITTED",
        help="Compare live spec against committed file, exit 1 on drift",
    )
    args = parser.parse_args()

    spec = get_openapi_spec()
    live_json = json.dumps(spec, indent=2, sort_keys=True) + "\n"

    if args.check:
        if not args.check.exists():
            print(f"ERROR: committed spec not found: {args.check}", file=sys.stderr)
            sys.exit(2)

        committed_json = args.check.read_text(encoding="utf-8")
        if live_json == committed_json:
            print("[OK] OpenAPI spec matches committed snapshot.")
            sys.exit(0)
        else:
            print("[FAIL] OpenAPI spec DRIFT detected!", file=sys.stderr)
            print(f"   Committed: {args.check}", file=sys.stderr)
            print(
                "   Run: uv run python tools/export_openapi.py -o openapi.committed.json",
                file=sys.stderr,
            )
            sys.exit(1)

    if args.output:
        args.output.write_text(live_json, encoding="utf-8")
        print(f"[OK] OpenAPI spec written to {args.output}")
    else:
        print(live_json, end="")


if __name__ == "__main__":
    main()
