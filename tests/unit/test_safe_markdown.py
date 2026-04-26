# tests/unit/test_safe_markdown.py
"""FIC: safe_render_markdown (MEU-PH6) — Spec §9E.4a–b.

Acceptance Criteria:
  AC-6.15: Basic Markdown → HTML conversion          [Spec §9E.4a]
  AC-6.16: `<script>` tags stripped (XSS)            [Spec §9E.4b]
  AC-6.17: Safe tags (`<strong>`, `<em>`, `<a>`) preserved  [Spec §9E.4b]
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# AC-6.15: Basic Markdown → HTML conversion
# ---------------------------------------------------------------------------


def test_markdown_renders() -> None:
    """AC-6.15: Basic Markdown converts to HTML correctly."""
    from zorivest_core.services.safe_markdown import safe_render_markdown

    result = safe_render_markdown("**bold** and *italic*")
    assert "<strong>bold</strong>" in result
    assert "<em>italic</em>" in result


# ---------------------------------------------------------------------------
# AC-6.16: `<script>` tags stripped
# ---------------------------------------------------------------------------


def test_html_injection_stripped() -> None:
    """AC-6.16: `<script>` tags are not rendered as executable HTML."""
    from zorivest_core.services.safe_markdown import safe_render_markdown

    result = safe_render_markdown("text <script>alert('xss')</script> end")
    # With html=False, markdown-it escapes HTML → &lt;script&gt;
    # Then nh3 ensures no actual script tags exist
    assert "<script>" not in result
    # The text content "alert" may appear as escaped text — that's safe


# ---------------------------------------------------------------------------
# AC-6.17: Safe tags preserved
# ---------------------------------------------------------------------------


def test_safe_tags_preserved() -> None:
    """AC-6.17: Safe HTML tags are preserved through sanitization."""
    from zorivest_core.services.safe_markdown import safe_render_markdown

    result = safe_render_markdown("**bold** and [link](https://example.com)")
    assert "<strong>" in result
    assert "<a " in result
