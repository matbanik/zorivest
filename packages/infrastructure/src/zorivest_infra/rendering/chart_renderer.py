# packages/infrastructure/src/zorivest_infra/rendering/chart_renderer.py
"""Chart rendering with dual output (§9.7b).

Renders charts as HTML (interactive Plotly) + static PNG data URI.

Spec: 09-scheduling.md §9.7b
MEU: 87
"""

from __future__ import annotations

import base64
from typing import Any, Callable

# Force plotly to use stdlib json instead of orjson.
# The installed orjson 3.11.7 is a namespace stub (no dumps/loads/OPT_*)
# which causes plotly's auto-detection to crash at serialization time.
import plotly.io as pio

pio.json.config.default_engine = "json"

import plotly.graph_objects as go


def render_candlestick(data: dict[str, Any]) -> dict[str, str]:
    """Render a candlestick chart with dual output.

    Args:
        data: Dict with keys: dates, open, high, low, close.

    Returns:
        Dict with keys: html (interactive), png_data_uri (static).
    """
    fig = go.Figure(
        data=[
            go.Candlestick(
                x=data["dates"],
                open=data["open"],
                high=data["high"],
                low=data["low"],
                close=data["close"],
            )
        ]
    )

    fig.update_layout(
        xaxis_rangeslider_visible=False,
        margin=dict(l=40, r=20, t=30, b=30),
    )

    # HTML output (interactive)
    html = fig.to_html(full_html=False, include_plotlyjs="cdn")

    # PNG output (static data URI) — requires kaleido
    try:
        png_bytes = fig.to_image(format="png", width=800, height=400)
        png_b64 = base64.b64encode(png_bytes).decode("ascii")
        png_data_uri = f"data:image/png;base64,{png_b64}"
    except (ValueError, ImportError):
        png_data_uri = ""

    return {
        "html": html,
        "png_data_uri": png_data_uri,
    }


# Registry of chart renderers
CHART_RENDERERS: dict[str, Callable] = {
    "candlestick": render_candlestick,
}
