#!/usr/bin/env python3
"""Schemathesis API fuzzing runner.

Runs property-based fuzzing against the Zorivest API using its OpenAPI spec.
Requires a running API server at the target URL.

Usage:
    # Start server first:
    uv run uvicorn zorivest_api.main:create_app --factory --port 8765

    # Then run fuzzing:
    uv run python tools/fuzz_api.py                    # default: http://localhost:8765
    uv run python tools/fuzz_api.py --url http://localhost:9000
    uv run python tools/fuzz_api.py --dry-run          # validate spec only
    uv run python tools/fuzz_api.py --endpoints /health /version  # target specific
"""

from __future__ import annotations

import argparse
import subprocess
import sys


def main() -> None:
    parser = argparse.ArgumentParser(description="Schemathesis API fuzzer")
    parser.add_argument(
        "--url",
        default="http://localhost:8765",
        help="Base URL of running API server (default: http://localhost:8765)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate OpenAPI spec without running tests",
    )
    parser.add_argument(
        "--endpoints",
        nargs="*",
        metavar="PATH",
        help="Only fuzz specific endpoints (e.g., /health /v1/trades)",
    )
    parser.add_argument(
        "--max-examples",
        type=int,
        default=50,
        help="Max Hypothesis examples per endpoint (default: 50)",
    )
    args = parser.parse_args()

    spec_url = f"{args.url}/openapi.json"

    cmd = ["uv", "run", "schemathesis", "run", spec_url]

    if args.dry_run:
        cmd.append("--dry-run")

    if args.endpoints:
        for ep in args.endpoints:
            cmd.extend(["--endpoint", ep])

    cmd.extend(["--hypothesis-max-examples", str(args.max_examples)])

    print(f"🔍 Running Schemathesis against {spec_url}")
    print(f"   Command: {' '.join(cmd)}")
    print()

    result = subprocess.run(cmd)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
