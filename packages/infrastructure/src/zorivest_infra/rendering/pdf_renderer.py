# packages/infrastructure/src/zorivest_infra/rendering/pdf_renderer.py
"""PDF rendering via Playwright (§9.7c).

Converts HTML content to PDF using Playwright's Chromium-based
headless browser. Playwright auto-downloads Chromium on first use —
no system dependencies (GTK/Pango) required.

Spec: 09-scheduling.md §9.7c
MEU: 87
"""

from __future__ import annotations

from pathlib import Path


def render_pdf(*, html_content: str, output_path: str) -> str:
    """Render HTML content to a PDF file via headless Chromium.

    Creates the output directory if it does not exist.
    Uses Playwright's synchronous API for simplicity.

    Args:
        html_content: HTML string to convert.
        output_path: Absolute path for the output PDF file.

    Returns:
        Absolute path to the generated PDF file.

    Raises:
        ImportError: If Playwright is not installed or Chromium not downloaded.
    """
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    try:
        from playwright.sync_api import sync_playwright  # type: ignore[import-untyped]
    except ImportError:
        raise ImportError(
            "Playwright is required for PDF rendering. "
            "Install it with: pip install playwright && playwright install chromium"
        )

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_content(html_content, wait_until="networkidle")
        page.pdf(path=str(out), format="A4", print_background=True)
        browser.close()

    return str(out)
