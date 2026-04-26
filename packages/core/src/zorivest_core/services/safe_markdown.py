# packages/core/src/zorivest_core/services/safe_markdown.py
"""safe_render_markdown — Markdown → sanitized HTML pipeline (§9E.4a).

Render chain:
  1. markdown-it-py converts Markdown → raw HTML (html=False for security)
  2. nh3 sanitizes the HTML (strips <script>, preserves safe tags)

Templates with body_format: "markdown" use this render chain.
"""

from __future__ import annotations

import nh3
from markdown_it import MarkdownIt

_md = MarkdownIt("commonmark", {"html": False})


def safe_render_markdown(md_source: str) -> str:
    """Convert Markdown to sanitized HTML.

    Args:
        md_source: Raw Markdown source string.

    Returns:
        Sanitized HTML string safe for email rendering.
    """
    raw_html = _md.render(md_source)
    return nh3.clean(raw_html)
