# packages/infrastructure/src/zorivest_infra/rendering/email_templates.py
"""Built-in email templates for pipeline SendStep (§9.8).

Provides a registry of HTML Jinja2 template strings keyed by template name.
The send step resolves `body_template` names against this registry,
renders with Jinja2 + pipeline context data, and uses the result as the
email HTML body.

Spec: 09-scheduling.md §9.8b
"""

from __future__ import annotations

# ── Template registry ────────────────────────────────────────────────────

EMAIL_TEMPLATES: dict[str, str] = {}


def _register(name: str, source: str) -> None:
    """Register a named template."""
    EMAIL_TEMPLATES[name] = source


# ── daily_quote_summary ──────────────────────────────────────────────────

_register(
    "daily_quote_summary",
    """\
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
         margin: 0; padding: 20px; background: #f5f5f5; color: #1a1a2e; }
  .container { max-width: 640px; margin: 0 auto; background: #fff;
               border-radius: 8px; padding: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
  h1 { font-size: 20px; color: #1a1a2e; margin: 0 0 4px; }
  .subtitle { font-size: 13px; color: #666; margin: 0 0 20px; }
  table { width: 100%; border-collapse: collapse; font-size: 14px; }
  th { background: #1a1a2e; color: #fff; padding: 8px 12px; text-align: left; }
  td { padding: 8px 12px; border-bottom: 1px solid #eee; }
  tr:nth-child(even) { background: #fafafa; }
  .positive { color: #22c55e; }
  .negative { color: #ef4444; }
  .footer { margin-top: 20px; font-size: 11px; color: #999; text-align: center; }
</style>
</head>
<body>
<div class="container">
  <h1>📊 Zorivest Daily Quote Report</h1>
  <p class="subtitle">Generated {{ generated_at }}</p>

  {% if quotes %}
  <table>
    <thead>
      <tr>
        <th>Symbol</th>
        <th>Price</th>
        <th>Change</th>
        <th>Change %</th>
        <th>Volume</th>
      </tr>
    </thead>
    <tbody>
      {% for q in quotes %}
      <tr>
        <td><strong>{{ q.symbol }}</strong></td>
        <td>{{ q.price | currency }}</td>
        <td class="{{ 'positive' if q.change >= 0 else 'negative' }}">
          {{ '%+.2f' | format(q.change) }}
        </td>
        <td class="{{ 'positive' if q.change_pct >= 0 else 'negative' }}">
          {{ '%+.2f' | format(q.change_pct) }}%
        </td>
        <td>{{ '{:,.0f}'.format(q.volume) }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
  {% else %}
  <p>No quote data available for this run.</p>
  {% endif %}

  <div class="footer">
    Zorivest &bull; Automated Pipeline Report
  </div>
</div>
</body>
</html>
""",
)


# ── Fallback: generic report ─────────────────────────────────────────────

_register(
    "generic_report",
    """\
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
         margin: 0; padding: 20px; background: #f5f5f5; color: #1a1a2e; }
  .container { max-width: 640px; margin: 0 auto; background: #fff;
               border-radius: 8px; padding: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
  h1 { font-size: 20px; color: #1a1a2e; margin: 0 0 4px; }
  .subtitle { font-size: 13px; color: #666; margin: 0 0 20px; }
  .footer { margin-top: 20px; font-size: 11px; color: #999; text-align: center; }
</style>
</head>
<body>
<div class="container">
  <h1>📋 {{ title | default('Zorivest Report') }}</h1>
  <p class="subtitle">Generated {{ generated_at }}</p>

  {% if records %}
  <table style="width:100%; border-collapse:collapse; font-size:14px;">
    <thead>
      <tr>
        {% for col in records[0].keys() %}
        <th style="background:#1a1a2e; color:#fff; padding:8px 12px; text-align:left;">{{ col }}</th>
        {% endfor %}
      </tr>
    </thead>
    <tbody>
      {% for row in records %}
      <tr>
        {% for val in row.values() %}
        <td style="padding:8px 12px; border-bottom:1px solid #eee;">{{ val }}</td>
        {% endfor %}
      </tr>
      {% endfor %}
    </tbody>
  </table>
  {% else %}
  <p>No data available for this run.</p>
  {% endif %}

  <div class="footer">
    Zorivest &bull; Automated Pipeline Report
  </div>
</div>
</body>
</html>
""",
)
