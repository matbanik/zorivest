# tests/live/__init__.py
"""Live data tests — skipped by default, run with --run-live.

Convention: Tests in this directory make real HTTP calls to external
service providers (Yahoo Finance, Polygon, etc.). They are excluded
from the standard test battery to prevent:
  - CI failures due to network issues or rate limiting
  - Slow test suites (external API calls add seconds per test)
  - Flaky test results due to provider outages

Usage:
  pytest tests/live/                    # Skips all (default)
  pytest tests/live/ --run-live         # Runs all live tests
  pytest tests/live/ --run-live -k yahoo  # Only Yahoo live tests

Each test file targets a single provider and validates:
  1. Network connectivity to the provider endpoint
  2. Response structure matches expected envelope
  3. Field mapping produces canonical schema fields
  4. Rate limiting headers are respected
"""
