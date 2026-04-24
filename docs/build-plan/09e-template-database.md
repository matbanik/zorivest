# 09e — Template Database Entity

> Phase: P2.5c · MEU-PH6, MEU-PH10
> Prerequisites: None (independent of SQL sandbox)
> Unblocks: Policy Emulator (09f), MCP template CRUD tools (05g)
> Resolves: [PIPE-NOTEMPLATEDB]
> Source: [retail-trader-policy-use-cases.md](../../_inspiration/policy_pipeline_wiring-research/retail-trader-policy-use-cases.md) Gap E
> Status: ⬜ planned

---

## 9E.0 Boundary Input Contract (Mandatory per AGENTS.md §195)

### Write Boundary Inventory

| Surface | Entry Point | Schema Owner |
|---------|-------------|-------------|
| MCP `create_email_template` | Tool handler → `EmailTemplateCreateRequest` | `EmailTemplateCreateRequest` (Pydantic) |
| MCP `update_email_template` | Tool handler → `EmailTemplateUpdateRequest` | `EmailTemplateUpdateRequest` (Pydantic) |
| REST `POST /scheduling/templates` | Route handler → `EmailTemplateCreateRequest` | Same Pydantic model (shared) |
| REST `PATCH /scheduling/templates/{name}` | Route handler → `EmailTemplateUpdateRequest` | Same Pydantic model (shared) |

### Schema Definitions

```python
class EmailTemplateCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=128, pattern=r"^[a-z0-9][a-z0-9_-]*$")
    body_html: str = Field(..., min_length=1, max_length=65536)  # 64 KiB source cap
    subject_template: str | None = Field(None, max_length=512)
    description: str | None = Field(None, max_length=1024)
    body_format: Literal["html", "markdown"] = "html"
    required_variables: list[str] = Field(default_factory=list, max_length=20)
    sample_data_json: str | None = Field(None, max_length=65536)  # 64 KiB
    created_by: str = Field(default="", max_length=128)


class EmailTemplateUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    body_html: str | None = Field(None, min_length=1, max_length=65536)
    subject_template: str | None = Field(None, max_length=512)
    description: str | None = Field(None, max_length=1024)
    body_format: Literal["html", "markdown"] | None = None
    required_variables: list[str] | None = Field(None, max_length=20)
    sample_data_json: str | None = Field(None, max_length=65536)
```

### Field Constraints

| Field | Create | Update | Constraint |
|-------|:------:|:------:|------------|
| `name` | Required | Path param (immutable) | `^[a-z0-9][a-z0-9_-]*$`, 1–128 chars |
| `body_html` | Required | Optional | 1–65536 bytes, validated by `HardenedSandbox` compile check |
| `subject_template` | Optional | Optional | Max 512 chars |
| `description` | Optional | Optional | Max 1024 chars |
| `body_format` | Default `"html"` | Optional | Enum: `"html"` \| `"markdown"` |
| `required_variables` | Default `[]` | Optional | Max 20 items |
| `sample_data_json` | Optional | Optional | Max 65536 bytes, must parse as valid JSON |
| `created_by` | Default `""` | Immutable | Max 128 chars |
| `is_default` | Server-set `False` | Immutable | Cannot be set by client |

### Extra-Field Policy

`extra="forbid"` on both request models. Unknown fields → 422 `Unprocessable Entity`.

### Error Mapping

| Condition | HTTP Status | Error Type |
|-----------|:-----------:|-----------|
| Unknown fields in request body | 422 | `VALIDATION_ERROR` |
| `name` already exists (create) | 409 | `CONFLICT` |
| `name` not found (update/delete) | 404 | `NOT_FOUND` |
| `body_html` fails HardenedSandbox compile | 422 | `TEMPLATE_INVALID` |
| `sample_data_json` not valid JSON | 422 | `VALIDATION_ERROR` |
| Attempt to delete default template | 403 | `FORBIDDEN` |
| `body_html` exceeds 64 KiB | 422 | `PAYLOAD_TOO_LARGE` |

### Create/Update Parity

The `body_html` field enforces the same `HardenedSandbox` compile check on both create and update paths. If `body_html` is provided in an update, it must pass the same validation as on create. All string length constraints are enforced identically on both paths.

---

## 9E.1 EmailTemplateModel (MEU-PH6)

### 9E.1a Purpose

Move email templates from hardcoded Python dictionaries to a database entity. Enables agent-authored templates via MCP CRUD, GUI template editor, and emulator validation.

### 9E.1b Current State

[`email_templates.py`](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/rendering/email_templates.py) has 2 hardcoded templates registered via `EMAIL_TEMPLATES` dict. No database storage exists.

### 9E.1c Design — SQLAlchemy Model

New model in `packages/infrastructure/src/zorivest_infra/persistence/models.py`:

```python
class EmailTemplateModel(Base):
    __tablename__ = "email_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), unique=True, nullable=False)   # Policy ref key
    description = Column(Text, nullable=True)                 # Human-readable purpose
    subject_template = Column(String(512), nullable=True)     # Jinja2 subject line
    body_html = Column(Text, nullable=False)                  # Jinja2 template source
    body_format = Column(String(10), default="html")          # "html" | "markdown"
    required_variables = Column(Text, nullable=True)          # JSON list: ["quotes", "accounts"]
    sample_data_json = Column(Text, nullable=True)            # Mock data for preview/emulator
    is_default = Column(Boolean, default=False)               # Ships with software
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)
    created_by = Column(String(128), default="")              # "user" | "agent:claude"
```

### 9E.1d Alembic Migration

New migration: `alembic/versions/xxxx_add_email_templates_table.py`

Creates `email_templates` table with the 12 columns above. Seeds 2 default templates migrated from the hardcoded `EMAIL_TEMPLATES` dict.

---

## 9E.2 EmailTemplateRepository (MEU-PH6)

### 9E.2a Design

New file: `packages/infrastructure/src/zorivest_infra/persistence/email_template_repository.py`

```python
class EmailTemplateRepository:
    def __init__(self, session: Session):
        self._session = session

    def get_by_name(self, name: str) -> EmailTemplateModel | None:
        return self._session.query(EmailTemplateModel).filter_by(name=name).first()

    def list_all(self) -> list[EmailTemplateModel]:
        return self._session.query(EmailTemplateModel).order_by(EmailTemplateModel.name).all()

    def create(self, template: EmailTemplateModel) -> EmailTemplateModel:
        self._session.add(template)
        self._session.flush()
        return template

    def update(self, name: str, **fields) -> EmailTemplateModel:
        template = self.get_by_name(name)
        if not template:
            raise ValueError(f"Template '{name}' not found")
        for k, v in fields.items():
            setattr(template, k, v)
        template.updated_at = datetime.utcnow()
        self._session.flush()
        return template

    def delete(self, name: str) -> None:
        template = self.get_by_name(name)
        if not template:
            raise ValueError(f"Template '{name}' not found")
        if template.is_default:
            raise ValueError("Cannot delete default templates")
        self._session.delete(template)
```

### 9E.2b UoW Integration

Add `email_templates: EmailTemplateRepository` to `SqlAlchemyUnitOfWork`.

---

## 9E.3 HardenedSandbox — Jinja2 Security (MEU-PH6)

### 9E.3a Purpose

All three independent security reviews agree: `ImmutableSandboxedEnvironment` with explicit overrides is the minimum Jinja2 defense against SSTI. This is the rendering engine for all agent-authored templates.

> [!CAUTION]
> **Never use vanilla `Environment` or default `SandboxedEnvironment`.** SSTI → RCE is a one-shot compromise.

### 9E.3b Design

New file: `packages/core/src/zorivest_core/services/secure_jinja.py`

```python
from jinja2.sandbox import ImmutableSandboxedEnvironment

ALLOWED_FILTERS = frozenset({
    "abs", "batch", "capitalize", "center", "count", "default", "d",
    "dictsort", "e", "escape", "filesizeformat", "first", "float",
    "format", "groupby", "indent", "int", "items", "join", "last",
    "length", "list", "lower", "map", "max", "min", "pprint",
    "reject", "rejectattr", "replace", "reverse", "round", "safe",
    "select", "selectattr", "slice", "sort", "string", "striptags",
    "sum", "title", "tojson", "trim", "truncate", "unique", "upper",
    "urlencode", "wordcount", "wordwrap", "xmlattr",
})

_DENY_ATTRS = frozenset({
    "__class__", "__subclasses__", "__mro__", "__bases__", "__init__",
    "__globals__", "__builtins__", "__import__", "__code__", "__func__",
    "__self__", "__module__", "__qualname__", "__reduce__", "__reduce_ex__",
    "__getattr__", "__setattr__", "__delattr__", "__dict__",
})

MAX_TEMPLATE_BYTES = 64 * 1024   # 64 KiB source cap
MAX_OUTPUT_BYTES = 256 * 1024    # 256 KiB render output cap

class HardenedSandbox(ImmutableSandboxedEnvironment):
    """Hardened Jinja2 sandbox for AI-authored email templates."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.filters = {k: v for k, v in self.filters.items()
                        if k in ALLOWED_FILTERS}

    def is_safe_attribute(self, obj, attr, value):
        if attr in _DENY_ATTRS:
            return False
        return super().is_safe_attribute(obj, attr, value)

    def render_safe(self, source: str, context: dict) -> str:
        if len(source.encode()) > MAX_TEMPLATE_BYTES:
            raise SecurityError(f"Template source exceeds {MAX_TEMPLATE_BYTES} bytes")
        template = self.from_string(source)
        safe_ctx = {k: v for k, v in context.items()
                    if isinstance(v, (str, int, float, bool, list, dict, type(None)))}
        rendered = template.render(safe_ctx)
        if len(rendered.encode()) > MAX_OUTPUT_BYTES:
            raise SecurityError(f"Rendered output exceeds {MAX_OUTPUT_BYTES} bytes")
        return rendered
```

### 9E.3c Tests

New file: `tests/unit/test_secure_jinja.py`

| Test | Assertion |
|------|-----------|
| `test_basic_render` | Simple template renders correctly |
| `test_filter_allowlist` | Allowed filter works (e.g., `upper`) |
| `test_blocked_filter` | Disallowed filter raises `SecurityException` |
| `test_mro_traversal_blocked` | `{{ ''.__class__.__mro__ }}` blocked |
| `test_globals_blocked` | `{{ config.__init__.__globals__ }}` blocked |
| `test_source_size_cap` | >64 KiB source raises `SecurityError` |
| `test_output_size_cap` | Rendered output >256 KiB raises `SecurityError` |
| `test_callable_stripped` | Callable values in context not passed through |

---

## 9E.4 Markdown Sanitization (MEU-PH6)

### 9E.4a Design

New file: `packages/core/src/zorivest_core/services/safe_markdown.py`

```python
import nh3
from markdown_it import MarkdownIt

_md = MarkdownIt("commonmark", {"html": False})

def safe_render_markdown(md_source: str) -> str:
    raw_html = _md.render(md_source)
    return nh3.clean(raw_html)
```

Templates with `body_format: "markdown"` use this render chain.

**New dependencies:** `nh3` (~0.5 MB, Rust-based), `markdown-it-py` (~0.3 MB)

### 9E.4b Tests

| Test | Assertion |
|------|-----------|
| `test_markdown_renders` | Basic Markdown → HTML |
| `test_html_injection_stripped` | `<script>` tags removed |
| `test_safe_tags_preserved` | `<strong>`, `<em>`, `<a>` preserved |

---

## 9E.5 Updated SendStep Resolution Chain (MEU-PH6)

### 9E.5a Design

Update `SendStep._resolve_body()` to add database lookup tier:

```python
def _resolve_body(self, p: Params, context: StepContext) -> str:
    # Tier 1: html_body (explicit)                    ← EXISTING ✅
    # Tier 2: body_template → DB lookup               ← NEW
    # Tier 3: body_template → hardcoded registry       ← EXISTING ✅
    # Tier 4: body_template_inline as raw Jinja2        ← EXISTING ✅
    # Tier 5: default fallback                         ← EXISTING ✅
```

### 9E.5b Tests

| Test | Assertion |
|------|-----------|
| `test_resolve_body_db_lookup` | Template found in DB renders correctly |
| `test_resolve_body_db_miss_falls_through` | Missing DB template falls through to registry |
| `test_resolve_body_inline_template` | Inline Jinja2 renders via HardenedSandbox |

---

## 9E.6 Default Morning Check-In Template (MEU-PH10)

### 9E.6a Purpose

Pre-loaded, customizable default template that demonstrates the policy v2 capabilities. Seeded via Alembic migration.

### 9E.6b Design

Template name: `morning-check-in`

Subject: `Morning Market Check-In — {{ date }}`

Body includes sections for:
- Watchlist quotes (from QueryStep)
- Portfolio summary (from QueryStep)
- Market news headlines (from FetchStep)

Required variables: `["date", "watchlist_name"]`

### 9E.6c Exit Criteria (MEU-PH6 + MEU-PH10 combined)

- [ ] `EmailTemplateModel` exists in `models.py`
- [ ] Alembic migration creates `email_templates` table
- [ ] `EmailTemplateRepository` exists with CRUD methods
- [ ] UoW has `email_templates` property
- [ ] `secure_jinja.py` exists with `HardenedSandbox`
- [ ] `safe_markdown.py` exists with `nh3` sanitization
- [ ] `SendStep._resolve_body()` includes DB lookup tier
- [ ] `nh3` and `markdown-it-py` added to dependencies
- [ ] All tests pass (8 + 3 + 3 + 3 = 17 tests)
- [ ] Morning Check-In default template seeded
