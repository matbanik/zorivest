# 09h — Pipeline Markdown Migration

> Phase: P2.5b (addition) · MEU-PW14
> Prerequisites: MEU-PW9 ✅ (SendStep template wiring), MEU-87 ✅ (RenderStep)
> Resolves: [PIPE-DROPPDF]
> Status: ⬜ planned

---

## 9H.1 Decision

PDF output is dropped from the pipeline. Markdown is the replacement format:
- AI-agent consumable (MCP-friendly, structured text)
- Lightweight (no Playwright/Chromium dependency)
- Email-compatible (Markdown → HTML conversion for email body)

---

## 9H.2 Files to Remove / Modify

### Remove entirely
- `packages/infrastructure/src/zorivest_infra/rendering/pdf_renderer.py`
- Playwright rendering dependency from `pyproject.toml` extras

### Modify: `render_step.py`
- Remove `_render_pdf()` method
- Remove `output_format` enum values `"pdf"` and `"both"`
- Remove PDF failure handling
- Add `_render_markdown()` method (Markdown table formatter)

### Modify: `send_step.py`
- Remove `pdf_path` parameter from `_send_emails()` call
- Remove `_save_local()` method (PDF copy to disk)
- Replace with `_save_local_markdown()` (writes `.md` file)

### Modify: `email_sender.py`
- Remove `pdf_path` parameter
- Remove MIME PDF attachment logic (`MIMEApplication` block)
- Add optional `.md` attachment support

### Modify: `models.py`
- Change `ReportModel.format` column default from `"pdf"` to `"html"`

### Modify: `scheduling_repositories.py`
- Change `format: str = "pdf"` default to `"html"`

---

## 9H.3 New: `_render_markdown()` Method

```python
def _render_markdown(self, data: dict, template_name: str | None) -> str:
    """Convert report data to structured Markdown tables."""
    lines: list[str] = []
    lines.append(f"# {data.get('report_name', 'Report')}")
    lines.append(f"*Generated: {data.get('date', 'N/A')}*\n")

    records = data.get("records", data.get("quotes", []))
    if not records:
        lines.append("*No data available.*")
        return "\n".join(lines)

    # Auto-detect columns from first record
    if isinstance(records[0], dict):
        headers = list(records[0].keys())
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        for row in records:
            values = [str(row.get(h, "")) for h in headers]
            lines.append("| " + " | ".join(values) + " |")

    return "\n".join(lines)
```

---

## 9H.4 Updated `RenderStep.output_format` Values

| Value | Behavior |
|-------|----------|
| `"html"` | Default. Jinja2 template rendering (for email body) |
| `"markdown"` | Markdown table rendering (for MCP/file/AI consumption) |

---

## 9H.5 Tests

Modify: `tests/unit/test_render_step.py`

| Test | Assertion |
|------|-----------|
| `test_render_markdown_produces_table` | Markdown output contains table headers and rows |
| `test_render_markdown_empty_data` | Returns "*No data available.*" |
| `test_render_html_still_works` | HTML rendering unchanged |
| `test_pdf_format_rejected` | `output_format="pdf"` raises ValueError |
| `test_send_local_writes_md_file` | Local file channel produces `.md` file |
| `test_email_no_pdf_attachment` | Email sent without PDF MIME part |

---

## 9H.6 Exit Criteria

- [ ] `pdf_renderer.py` deleted
- [ ] `_render_pdf()` removed from RenderStep
- [ ] `_render_markdown()` added to RenderStep
- [ ] `output_format` enum: `"html"` (default), `"markdown"` only
- [ ] `SendStep.local_file` writes `.md` not PDF
- [ ] Email attachments: optional `.md`, no PDF
- [ ] `ReportModel.format` default updated
- [ ] Playwright rendering dependency removed from pyproject.toml
- [ ] All 6 tests pass
