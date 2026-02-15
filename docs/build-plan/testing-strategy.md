# Testing Strategy

> Part of [Zorivest Build Plan](../BUILD_PLAN.md) — Referenced by [Phase 5](05-mcp-server.md), [Phase 1](01-domain-layer.md), [Phase 2](02-infrastructure.md)

---

## MCP Testing Without IDE Restart

Since the MCP server is now written in TypeScript, testing approaches are different from the Python-based workflow. Here are **three approaches**, from fastest to most comprehensive:

### Approach 1: Vitest + Mocked `fetch()` (Recommended for TDD)

```typescript
// Runs entirely in Node.js, no Python backend needed
vi.spyOn(global, 'fetch').mockResolvedValue(
  new Response(JSON.stringify({ status: 'created', exec_id: 'T001' }))
);
// ... call tool handler, verify fetch args and response
```

- **Speed**: ~50ms per test
- **IDE restart**: Never
- **What it tests**: Tool logic, Zod schema validation, response formatting
- **Limitation**: Doesn't test Python REST API integration

### Approach 2: MCP Inspector (Visual Development Tool)

```bash
npx @modelcontextprotocol/inspector
```

- **Speed**: Manual / interactive
- **IDE restart**: Never (separate browser UI)
- **What it tests**: Visual inspection, interactive debugging
- **Use for**: Exploring tool schemas, testing complex arguments

### Approach 3: Vitest with Live Python API (CI/CD)

```typescript
import { spawn, ChildProcess } from 'child_process';

let apiProcess: ChildProcess;

beforeAll(async () => {
  apiProcess = spawn('uv', ['run', '--package', 'zorivest-api',
    'uvicorn', 'zorivest_api.main:app', '--port', '8765']);
  // Poll health endpoint instead of fixed sleep
  const waitForApi = async (url: string, timeoutMs = 10000) => {
    const start = Date.now();
    while (Date.now() - start < timeoutMs) {
      try {
        const res = await fetch(`${url}/health`);
        if (res.ok) return;
      } catch { /* server not ready yet */ }
      await new Promise(r => setTimeout(r, 500));
    }
    throw new Error(`API failed to start within ${timeoutMs}ms`);
  };
  await waitForApi('http://localhost:8765');
});

afterAll(() => apiProcess?.kill());
```

- **Speed**: ~3s startup + test time
- **IDE restart**: Not needed (separate process)
- **What it tests**: Full TypeScript MCP → Python REST round-trip
- **Use for**: CI/CD pipeline and integration verification

### Live Integration Test Example

```typescript
describe('MCP tools against live API', () => {
  it('create_trade round-trip', async () => {
    const res = await fetch('http://localhost:8765/api/v1/trades', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        exec_id: 'INT-001', instrument: 'SPY', action: 'BOT',
        quantity: 100, price: 619.61, account_id: 'DU123',
      }),
    });
    const data = await res.json();
    expect(data.status).toBe('created');
  });
});
```

## Test Organization

```bash
# TypeScript MCP tests (fast, mocked)
npx vitest run tests/typescript/mcp/

# TypeScript UI tests
npx vitest run tests/typescript/ui/

# Python unit tests
pytest -m "unit" -x --tb=short

# Python integration tests
pytest -m "integration" -x

# Full suite before commit
pytest -m "not e2e" --tb=short && npx vitest run

# Full CI suite (includes live API integration)
pytest --tb=long -v && npx vitest run --reporter=verbose
```

## Test Infrastructure Setup

### `conftest.py` — Shared Fixtures

```python
# tests/conftest.py

import pytest
from datetime import datetime
from zorivest_core.domain.entities import Trade, ImageAttachment


@pytest.fixture
def sample_trade():
    return Trade(
        exec_id="TEST001",
        time=datetime(2025, 7, 2, 13, 25, 21),
        instrument="SPY STK (USD)",
        action="BOT",
        quantity=100.0,
        price=619.61,
        account_id="DU3584717",
    )


@pytest.fixture
def sample_image():
    # 1×1 pixel PNG
    PNG_1X1 = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00"
        b"\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00"
        b"\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    return ImageAttachment(
        data=PNG_1X1,
        mime_type="image/png",
        caption="Test image",
        width=1, height=1,
    )


def make_trade(exec_id="TEST001", **overrides):
    defaults = dict(
        exec_id=exec_id,
        time=datetime.now(),
        instrument="SPY STK (USD)",
        action="BOT",
        quantity=100.0,
        price=619.61,
        account_id="DU3584717",
    )
    defaults.update(overrides)
    return Trade(**defaults)


def make_image(data=None, **overrides):
    defaults = dict(
        data=data or b"\x89PNG_fake",
        mime_type="image/png",
        caption="Test",
        width=100, height=100,
    )
    defaults.update(overrides)
    return ImageAttachment(**defaults)
```

### `pyproject.toml` — Test Configuration

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
markers = [
    "unit: Pure unit tests",
    "integration: Integration tests with real DB",
    "mcp: MCP protocol tests",
    "e2e: End-to-end tests",
]
asyncio_mode = "auto"

[tool.coverage.run]
source = ["packages/*/src"]
omit = ["*/tests/*", "*/__pycache__/*"]
```
