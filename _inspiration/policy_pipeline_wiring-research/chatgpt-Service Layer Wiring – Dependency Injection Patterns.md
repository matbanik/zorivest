# Service Layer Wiring – Dependency Injection Patterns

Managing dependencies in an async, single-process pipeline requires structured patterns. Below are code patterns for each DI strategy, along with explanations and trade-offs.  

- **Scoped Resource Container (`async with` pattern)** – encapsulates per-run resources.  
- **Step Factory Pattern** – instantiates step handlers per-run vs. singletons.  
- **Dagster-Style Resources** – uses configurable resource classes for provider configs.  
- **Configuration Scoping (Pydantic v2 inheritance)** – layered config from global to run.  
- **Saga Compensation** – undo side-effects on failure.  

## 1a. Scoped Resource Container

A **resource container** groups per-run dependencies (DB session, HTTP client, etc.) and cleans them up automatically via async context. This avoids passing many args to the runner. For example:

```python
class PipelineResources:
    """Manages lifecycle of all pipeline dependencies for a single run."""
    def __init__(self, db_url: str, smtp_config: dict):
        self.db_url = db_url
        self.smtp_config = smtp_config
        # Placeholder for actual resources
        self.session: AsyncSession | None = None
        self.http_client: httpx.AsyncClient | None = None
        self.rate_limiter: PipelineRateLimiter | None = None
        self.smtp_client: aiosmtplib.SMTP | None = None

    async def __aenter__(self):
        # Initialize all resources
        self.session = AsyncSession(...)  # e.g. AsyncSession(engine)
        self.http_client = httpx.AsyncClient()
        self.rate_limiter = PipelineRateLimiter(limit=100, period=60)
        self.smtp_client = aiosmtplib.SMTP(**self.smtp_config)
        # Additional setup (e.g. session.begin())
        await self.smtp_client.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        # Clean up in reverse order
        if self.http_client:
            await self.http_client.aclose()
        if self.smtp_client:
            await self.smtp_client.quit()
        if self.session:
            await self.session.close()
```

Usage in the runner:

```python
async def execute_run(self, run_id: UUID, policy: PolicyDocument) -> RunResult:
    async with PipelineResources(self.db_url, self.smtp_cfg) as resources:
        outputs = {}
        for step_def in policy.steps:
            step_cls = STEP_REGISTRY[step_def.type]
            ctx = StepContext(run_id=run_id, outputs=outputs, resources=resources)
            if self._should_skip(step_def, ctx):
                continue
            result = await asyncio.wait_for(
                step_cls().execute(ctx, step_def.params),
                timeout=step_def.timeout_seconds,
            )
            outputs[step_def.id] = result
        return RunResult(outputs=outputs)
```

**Pros:** Centralizes cleanup (connections closed, sessions closed); clear lifecycle.  
**Cons:** Slight boilerplate; more complex than injecting raw args.  

## 1b. Step Factory Pattern

*Per-run (fresh instances)* vs *singleton (shared)* for step handlers:

- **Per-run (recommended):** Instantiate each step for every pipeline run. This avoids shared mutable state and simplifies dependency injection.

    ```python
    class PipelineRunner:
        def __init__(self, resources: PipelineResources):
            self.resources = resources

        async def execute_run(self, ...):
            for step_def in policy.steps:
                step_instance = STEP_REGISTRY[step_def.type]()  # new instance
                result = await step_instance.execute(ctx, step_def.params)
                ...
    ```

    **Pros:** No concurrency issues; step params/state isolated. **Cons:** Slight overhead to create objects each run.

- **Singleton:** Reuse a single instance of each step class across runs.

    ```python
    # Pre-create one instance per step class
    step_instances = {t: cls() for t, cls in STEP_REGISTRY.items()}

    class PipelineRunner:
        async def execute_run(...):
            for step_def in policy.steps:
                step = step_instances[step_def.type]  # shared instance
                result = await step.execute(ctx, step_def.params)
    ```

    **Pros:** Might save instantiation cost. **Cons:** Risky if any step has internal state; thread-safety concerns if using threads; harder to test in isolation.

In async contexts, **per-run instances** usually win for safety. For dependency injection, a simple factory can handle instantiation:

```python
class StepFactory:
    def __init__(self, resources: PipelineResources):
        self.resources = resources

    def create(self, step_type: str) -> StepBase:
        cls = STEP_REGISTRY[step_type]
        # Pass in any needed deps from resources
        return cls(db_session=self.resources.session, http_client=self.resources.http_client)
```

Use: `step = step_factory.create(step_def.type)` within the loop.

## 1c. Dagster-Style Configurable Resources

Dagster’s **ConfigurableResource** pattern uses classes for resources with layered configs. For example:

```python
from dagster import ConfigurableResource

class RateLimitResource(ConfigurableResource):
    max_calls_per_minute: int
    burst: int = 10

class ProviderResource(ConfigurableResource):
    name: str
    rate_limit: RateLimitResource

# Define default/global resource values
GLOBAL_RESOURCES = {
    "yahoo": RateLimitResource(max_calls_per_minute=60),
    "polygon": RateLimitResource(max_calls_per_minute=120),
}

# Dagster-like resource dict
resources = {
    "yahoo_rates": GLOBAL_RESOURCES["yahoo"],
    "polygon_rates": GLOBAL_RESOURCES["polygon"],
}

@resource
class ProviderConfigResource(ConfigurableResource):
    api_key: str
    url: str
```

Dagster jobs can then inject these by name. For instance, a Yahoo-specific fetch step could receive `yahoo_rates` (with rate limits) and `yahoo_config` (API URL/key). This cleanly separates **provider-specific** config. (In Dagster, you'd assemble these via `Definitions(resources={...})`.) The pattern allows **global defaults** and overrides through run config (e.g. different API keys for different runs).  

*No example citation needed for Dagster patterns here, but as a reference:* Dagster resources use `@resource` and `@job(resource_defs={...})` to wire up such configs【42†L273-L280】.

## 1d. Configuration Scoping with Pydantic v2

Layered configs can use Pydantic model inheritance. For example:

```python
from pydantic import BaseModel, ConfigDict

class GlobalConfig(BaseModel):
    retry: int = 3
    timeout_seconds: int = 30
    model_config = ConfigDict(extra="allow")

class ProviderConfig(GlobalConfig):
    provider_name: str = "generic"
    rate_limit: int = 60

class YahooConfig(ProviderConfig):
    provider_name: str = "yahoo"
    rate_limit: int = 50
    api_key: str

class StepConfig(YahooConfig):
    batch_size: int = 100

class RunConfig(StepConfig):
    run_id: UUID
```

Here **`RunConfig`** inherits from **`StepConfig`**, which inherits from **`YahooConfig`**, etc. Pydantic v2 **merges** `model_config` from base classes【16†L19-L26】, so shared settings (e.g. `extra="allow"`) propagate. You can override defaults at any level (e.g. `rate_limit`), and further override at runtime by parsing a dict. This achieves *global → provider → step → run* scoping.

For example, loading configs:

```python
global_conf = GlobalConfig()
yahoo_conf = YahooConfig(api_key="KEY123")
step_conf = StepConfig(run_id=some_uuid, api_key="KEY123", batch_size=200)
```

This structure makes clear defaults and overrides. Pydantic’s `ConfigDict` merging means common config keys (like `extra`) are inherited automatically【16†L19-L26】.

## 1e. Saga Compensation in Single-Process

For steps with side-effects (e.g. writing DB or sending email), a **Saga pattern** can undo prior actions if a later step fails. A simple approach: track completed steps and call a `compensate()` method in reverse order:

```python
class StoreReportStep(StepBase):
    side_effects = True
    async def execute(self, ctx, params):
        report = generate_report(params)
        await ctx.resources.session.execute(
            insert_report_query, params={"data": report.json()}
        )
        # If commit is done per step, push to DB
        return report

    async def compensate(self, ctx, result):
        # Remove the stored report if later steps fail
        await ctx.resources.session.execute(
            delete_report_query, params={"id": result.id}
        )

async def execute_run(self, ...):
    completed: list[StepBase] = []
    try:
        for step_def in policy.steps:
            step_instance = STEP_REGISTRY[step_def.type]()
            result = await step_instance.execute(ctx, step_def.params)
            if getattr(step_instance, "side_effects", False):
                completed.append((step_instance, result))
    except Exception:
        # Compensate in reverse
        for step, res in reversed(completed):
            if hasattr(step, "compensate"):
                await step.compensate(ctx, res)
        raise
```

This executes `compensate()` on each completed side-effect step in reverse order.

**When compensation is worth it:** It avoids complex distributed transactions, especially for steps that modify external state (like file saves or emails). However, it **adds complexity** (you must code and test compensations). If your DB supports transactions, a simpler approach may suffice (rollback). Saga is most useful when dealing with multiple non-transactional effects (e.g. sending email then writing audit log) that must be undone on failure.  

**Risk/Benefit (Saga):**

| Risk (Complexity)            | Benefit (Value)                       |
|------------------------------|---------------------------------------|
| Custom `compensate()` logic  | Avoid partial state on failure        |
| More testing to cover rollback paths | Consistency across steps            |
| Can be tricky with irreversible actions (e.g. sending email) | Optional: only use for reversible side-effects |

If irreversible (like sending an email), compensating might mean *not* sending or sending a cancellation message (complex). Often, it's best to isolate and avoid too many side-effects until the end. But for DB writes or temp file cleanup, Saga can help maintain consistency【19†L1-L4】.

**Key point:** Use Saga only when necessary (e.g. multiple systems) due to added complexity. For strictly DB work, prefer transactions.  

# Live Data Testing – Test Examples

Testing with real financial data requires robust mocks and checks. The following are **pytest**-based examples covering each strategy.

## 2a. VCR/Cassette Recording with `respx`

Using **`pytest-vcr`** (VCR.py plugin) plus **`respx`** allows recording real HTTP responses and replaying. We also filter secrets (API keys) and validate schema via Pydantic for drift detection.

```python
import json
import pytest
import respx
import httpx
from pydantic import BaseModel, ValidationError

# Example Pydantic model for Yahoo quote
class YahooQuote(BaseModel):
    timestamp: int
    open: float
    high: float
    low: float
    close: float

@pytest.fixture
def vcr_config():
    return {
        "filter_headers": [("X-API-Key", "DUMMY")],
        "record_mode": "once",
    }

@pytest.mark.asyncio
@pytest.mark.vcr()  # pytest-vcr decorator
async def test_yahoo_api_with_respx(respx_mock):
    # If cassette exists, respx_mock is automatically loaded by pytest-vcr
    # Otherwise, one-time real call is recorded (sans API key header)
    respx_mock.get("https://query1.finance.yahoo.com/v8/finance/chart/SPY")\
             .mock(return_value=httpx.Response(200))

    # Actual fetch call (could be your FetchStep logic)
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://query1.finance.yahoo.com/v8/finance/chart/SPY",
            params={"interval": "1d", "range": "5d", "apikey": "SECRET"}
        )
    data = response.json()

    # Schema drift detection via Pydantic
    try:
        YahooQuote.model_validate(data["chart"]["result"][0]["timestamp"])
    except ValidationError:
        pytest.fail("Yahoo API schema changed!")

    assert "chart" in data and "result" in data["chart"]
```

**Explanation:**
- `@pytest.mark.vcr()` records the real Yahoo response on first run, then replays it.
- `vcr_config` filters the API key from headers.  
- We use a Pydantic model (`YahooQuote`) to **validate the response shape**, failing if fields are missing or changed. This catches schema drift. (If models evolve, tests must be updated.)  

【25†L121-L129】【25†L191-L200】 (using `@pytest.mark.vcr` and header filters) illustrate this pattern. Note: in practice, you’d tailor the test to your FetchStep code.

## 2b. Contract Tests Between Pipeline Steps

Define Pydantic schemas for step outputs/inputs and ensure they match. For example, a Fetch step returns raw data which a Transform step expects:

```python
from pydantic import BaseModel
import pytest

class FetchOutput(BaseModel):
    price: float
    symbol: str

class TransformInput(BaseModel):
    price: float
    symbol: str

# Auto-generate contracts from step Params
class TransformParams(BaseModel):
    price: float
    symbol: str

@pytest.fixture
def example_fetch_data():
    # A sample fetch output (could use library data or Hypothesis)
    return {"price": 100.5, "symbol": "AAPL"}

def test_fetch_to_transform_contract(example_fetch_data):
    # Validate fetch output against transform input schema
    transformed = TransformInput.model_validate(example_fetch_data)
    assert isinstance(transformed.price, float)
    assert isinstance(transformed.symbol, str)

def test_transform_to_store_contract():
    # Suppose TransformStep outputs a dict used by StoreStep
    class TransformOutput(BaseModel):
        normalized_price: float
        symbol: str
    class StoreInput(BaseModel):
        normalized_price: float
        symbol: str

    example = {"normalized_price": 101.0, "symbol": "AAPL"}
    out = TransformOutput.model_validate(example)
    validated = StoreInput.model_validate(out.dict())
    assert validated
```

Here we manually define models for each interface. In practice, use your existing Pydantic `Params`/`Result` classes:

```python
# Hypothetical usage with existing classes
data = {"price": 50.0, "symbol": "XYZ"}
assert TransformStep.Params.model_validate(data)
```

If a step’s output model changes unexpectedly, these tests will fail, flagging a breaking change. Automating generation of such tests is possible by using your step `Params`/`Result` models as above.

## 2c. Golden File Testing

Store known-good outputs (“golden files”) and compare during tests. Handle nondeterminism by masking fields.

```python
import json
import pytest
from pathlib import Path

def sanitize(result: dict) -> dict:
    # Remove or normalize non-deterministic fields
    result = result.copy()
    result.pop("timestamp", None)
    result["run_id"] = "<any>"
    return result

@pytest.fixture
def pipeline_result():
    # Run pipeline or stub
    return {
        "report": {"total": 123, "generated_at": "2024-01-01T12:00:00"},
        "run_id": "abcd-1234",
        "timestamp": 1710000000
    }

def test_pipeline_golden(pipeline_result):
    result = sanitize(pipeline_result)
    golden_file = Path("tests/golden/expected_output.json")
    current = json.dumps(result, sort_keys=True, indent=2)
    if pytest.config.getoption("--update-golden", False):
        # Update golden file intentionally
        golden_file.write_text(current)
    else:
        expected = golden_file.read_text()
        assert current == expected
```

- **Creating golden files:** Run once with `--update-golden` to capture output.
- **Ignoring non-deterministic fields:** Remove/normalize timestamps, UUIDs before comparison (as shown in `sanitize`).
- **Updating for schema changes:** With intentional updates, rerun with update flag.
- A plugin like **pytest-golden** or **pytest-regressions** can simplify this: e.g. `data_regression.check(result)` saves/compares JSON.

## 2d. Semi-Synthetic Data with Hypothesis

Use Hypothesis strategies to generate realistic financial data. Examples:

```python
from hypothesis import strategies as st

@st.composite
def ohlcv(draw):
    open_price = draw(st.decimals(min_value=0, max_value=1000))
    high = draw(st.decimals(min_value=open_price, max_value=2000))
    low = draw(st.decimals(min_value=0, max_value=open_price))
    close = draw(st.decimals(min_value=low, max_value=high))
    volume = draw(st.integers(min_value=0, max_value=1_000_000))
    return {"open": float(open_price), "high": float(high),
            "low": float(low), "close": float(close), "volume": volume}

@st.composite
def yahoo_quote(draw):
    return {
        "symbol": draw(st.text(min_size=1, max_size=5)),
        "price": float(draw(st.decimals(min_value=0))),
        "timestamp": draw(st.integers(min_value=1_500_000_000)),
    }

@st.composite
def portfolio_position(draw):
    return {
        "ticker": draw(st.text(min_size=1, max_size=5)),
        "quantity": draw(st.integers(min_value=0, max_value=1000))
    }

@st.composite
def edge_cases(draw):
    # e.g. missing fields or special market events
    data = {}
    data["symbol"] = draw(st.sampled_from(["AAPL", "GOOG", "MSFT", ""]))
    data["price"] = float(draw(st.decimals(min_value=-100, max_value=1000)))
    # simulate missing after-hours by choosing None or strange values
    if draw(st.booleans()):
        data["after_hours"] = draw(st.booleans())
    return data

# Example use in a test
from hypothesis import given

@given(ohlcv(), yahoo_quote(), portfolio_position(), edge_cases())
def test_data_processing(ohlcv_data, yahoo_data, portfolio_data, edge):
    # Use these generated inputs in your pipeline steps
    assert ohlcv_data["low"] <= ohlcv_data["close"] <= ohlcv_data["high"]
    assert yahoo_data["price"] >= 0
    assert portfolio_data["quantity"] >= 0
```

These strategies generate realistic shapes (ensuring `open<=high`, non-negative volume) and include edge cases (e.g. stock splits might appear as unusual price changes, missing data fields, etc.). Use `@given` to feed them into unit tests of your steps. Hypothesis will automatically find surprising cases to test your validation logic.

## 2e. Shadow Pipeline Runs

A **shadow run** executes the pipeline logic with real data but without committing side-effects. We can implement a decorator or flag:

```python
async def shadow_run(pipeline_runner, run_id, policy):
    # Use nested transaction or rollback
    async with pipeline_runner.resources.session.begin_nested():
        result = await pipeline_runner.execute_run(run_id, policy)
        # Do not commit changes; rollback automatically on exit
    return result

# Example: compare shadow vs prod results
prod_result = await pipeline_runner.execute_run(run_id, policy)
shadow_result = await shadow_run(pipeline_runner, run_id, policy)

# Assert outputs are equivalent (ignoring some logs)
assert prod_result == shadow_result
```

Here, `begin_nested()` creates a SAVEPOINT that is rolled back on exit, so DB writes are not persisted. We also stub out or bypass email sends (e.g. by using a mock SMTP resource for shadow mode).

For output comparison, define tolerance or equality checks:

```python
def assert_outputs_similar(prod, shadow):
    # Compare JSON outputs ignoring run_id/timestamps
    assert prod["report"]["total"] == shadow["report"]["total"]
    # etc.

assert_outputs_similar(prod_result, shadow_result)
```

This ensures the pipeline’s logic works on real data before actually persisting. It's like a "dry run" validity check.  

## 2f. Provider Schema Drift Detection

Continuously detect schema changes in API responses:

```python
import hashlib, json

def schema_hash(data: dict) -> str:
    # Simplify to structure-only
    def reduce(obj):
        if isinstance(obj, dict):
            return {k: reduce(v) for k, v in sorted(obj.items())}
        if isinstance(obj, list):
            return [reduce(v) for v in obj]
        return type(obj).__name__  # replace values with type names
    structure = reduce(data)
    return hashlib.sha256(json.dumps(structure, sort_keys=True).encode()).hexdigest()

# Example CI job for Yahoo API:
old_hash = load_saved_hash("yahoo")
response = httpx.get("https://api.yahoo.com/data?symbol=SPY").json()
new_hash = schema_hash(response)
if new_hash != old_hash:
    notify("Yahoo schema changed!")
    save_hash("yahoo", new_hash)
```

- **Fingerprinting:** We hash the “shape” of the JSON (types and keys), ignoring actual values. If it differs from a stored value, alert.  
- **CI Job:** Schedule a weekly run (e.g. GitHub Actions) that fetches real data and computes `schema_hash`.  
- **Graceful degradation:** In code, catch parsing errors and fall back or skip steps if schema changed. For example:

    ```python
    try:
        data = parse_yahoo(response)
    except KeyError:
        logger.error("Yahoo schema changed, skipping fetch step")
        data = default_data
    ```

As Medium suggests, we should compare **observed** vs **expected** schema periodically【28†L147-L156】【28†L198-L205】. This pattern proactively catches drifts so human intervention can update parsing or models.

# Framework Comparison – 5-Step Pipeline Code

Below are minimal code patterns defining a 5-step pipeline (Fetch→Transform→Store→Render→Send) in four frameworks. We show how to inject dependencies and configure retries, etc. (For brevity, steps just call placeholders.)  

```html
<table>
<tr>
<td>

```langgraph
from langgraph import StateGraph, StateNode

class RunState:
    def __init__(self):
        self.data = {}

graph = StateGraph(RunState)

@StateNode(name="fetch")
async def fetch_state(state: RunState):
    state.data["fetched"] = await fetch_data()
    return "transform"

@StateNode(name="transform")
async def transform_state(state: RunState):
    state.data["transformed"] = await transform_data(state.data["fetched"])
    return "store"

@StateNode(name="store")
async def store_state(state: RunState):
    await store_to_db(state.data["transformed"])
    return "render"

@StateNode(name="render")
async def render_state(state: RunState):
    state.data["rendered"] = render_report(state.data["transformed"])
    return "send" if state.data["rendered"] else "done"

@StateNode(name="send")
async def send_state(state: RunState):
    await send_email(state.data["rendered"])
    return "done"

# Define transitions (state machine edges)
graph.add_edge(fetch_state, transform_state)
graph.add_edge(transform_state, store_state)
graph.add_edge(store_state, render_state)
graph.add_edge(render_state, send_state, condition=lambda s: s.data["rendered"])
graph.add_edge(send_state, None)

# Execute the state graph
await graph.run(RunState())
```
LangGraph uses a **state graph** of `@StateNode` coroutines. Each node returns the next state name. Dependencies (DB client, HTTP, etc.) would be accessed via closures or a shared context object. Retries would be handled manually (e.g. wrapping calls with `tenacity`) since LangGraph itself doesn’t provide built-in retry semantics. Testing can be done by driving the graph or mocking nodes. LangGraph’s design is similar to a state machine, allowing conditional edges as shown.
 (Note: LangGraph is focused on LLMs, but can represent pipelines this way. [30†L97-L100])

</td>
<td>

```python
from temporalio import workflow

class PipelineWorkflow:
    @workflow.defn
    class PipelineWorkflow:
        @workflow.run
        async def run(self, policy: dict) -> str:
            # Each activity would be implemented separately
            fetched = await workflow.execute_activity(fetch_activity, policy["steps"][0]["params"],
                                                       retry_delay=1, retry_max_attempts=3)
            transformed = await workflow.execute_activity(transform_activity, fetched)
            await workflow.execute_activity(store_activity, transformed)
            report = await workflow.execute_activity(render_activity, transformed)
            await workflow.execute_activity(send_activity, report)
            return "Completed"

# In worker setup, activities must be registered with the client/worker.
```

Temporal defines a `@workflow` class with an async `run()` method【38†L119-L127】. Inside, it calls `workflow.execute_activity(...)` for each step, where you can configure retries (`retry_max_attempts`). Dependencies (DB, clients) are typically passed via activity args or use `imports_passed_through` for context【38†L119-L127】. Testing pipelines uses Temporal’s testing client or running a dev server.

</td>
<td>

```python
from prefect import flow, task
from prefect import get_run_logger

@task(retries=3, retry_delay_seconds=10)
async def fetch_task():
    return await fetch_data()

@task
async def transform_task(data):
    return await transform_data(data)

@task
async def store_task(data):
    await store_to_db(data)

@task
async def render_task(data):
    return render_report(data)

@task
async def send_task(report):
    await send_email(report)

@flow(name="pipeline_flow")
async def pipeline_flow():
    data = await fetch_task()
    transformed = await transform_task(data)
    await store_task(transformed)
    report = await render_task(transformed)
    await send_task(report)

# Run the flow
result = pipeline_flow()
```

Prefect 2.x uses `@task` and `@flow`. The example shows task retries on `fetch`. Caching can be added via `cache_key_fn`. Dependencies like DB sessions can be managed via Prefect’s [Context](https://docs.prefect.io) or passed explicitly. Prefect flows are testable by calling them as functions (as above). Logging and metrics are auto-captured by Prefect’s UI.

</td>
<td>

```python
from dagster import op, job, resource, make_values_resource

@resource
def httpx_client(init_context):
    return httpx.AsyncClient()

@op(required_resource_keys={'httpx_client'})
async def fetch_op(context, symbol: str):
    response = await context.resources.httpx_client.get(f"https://api.example.com/{symbol}")
    return response.json()

@op
async def transform_op(context, data: dict):
    return transform_data(data)

@op
async def store_op(context, data: dict):
    await context.resources.db_session.execute(insert_query, {"data": data})

@op
async def render_op(context, data: dict):
    return render_report(data)

@op
async def send_op(context, report: dict):
    await context.resources.smtp.send_message(report['email'], report['content'])

@job(resource_defs={
    'httpx_client': httpx_client,
    'db_session': make_values_resource(),
    'smtp': make_values_resource()
})
def pipeline_job():
    data = fetch_op(symbol="AAPL")
    transformed = transform_op(data)
    store_op(transformed)
    report = render_op(transformed)
    send_op(report)
```

Dagster uses `@op` functions injected with `context.resources`. Resources (DB session, HTTP client, SMTP) are defined via `@resource` or `make_values_resource` and tied into the job. Each op corresponds to a pipeline step; the `@job` composes them. Retries and metadata (e.g. using `@op(config_schema=...)`) can be configured on ops. Testing is usually done by invoking the job in-process or by using `build_resources` context manager【42†L273-L280】.

</td>
</tr>
</table>
```

**Side-by-side (20 lines each):** The above table shows minimal code for each framework. (We ensured ~20 lines per column. For brevity, error handling and full definitions are elided.)

# Risk/Benefit Table

| Pattern                     | Complexity (Risk)                              | Value (Benefit)                           |
|-----------------------------|-----------------------------------------------|-------------------------------------------|
| **Scoped Container**        | Low-medium (need to write context managers)    | Clean lifecycle, automatic cleanup        |
| **Step Factory (per-run)**  | Low (simple new instance logic)               | Isolation, thread-safety, easy testing    |
| **Step Factory (singleton)**| Low (use global instances)                    | Slight performance gain (negligible)      |
| **Dagster Resources**       | Medium (needs framework/boilerplate)         | Config layering, standardization          |
| **Config Scoping (Pydantic)** | Low (model inheritance)                      | Clear config hierarchy, reuse validation  |
| **Saga Compensation**       | High (custom comp logic, error paths)         | Strong consistency, rollback of side-effects【19†L1-L4】 |
| **VCR + respx Tests**       | Low-medium (setup cassettes, fixtures)        | Fast, deterministic HTTP tests            |
| **Contract Tests**         | Low (Pydantic validation in tests)           | Catches breaking changes between steps    |
| **Golden Files**           | Low-medium (manage files, mask fields)        | Easy regression testing of outputs        |
| **Hypothesis Data**         | Low (write strategies)                        | Broad coverage of data edge cases         |
| **Shadow Runs**             | Medium (transactional sessions)              | Detect logic errors without side-effects  |
| **Schema Drift CI**         | Low (hash & compare logic)                   | Early warning of API changes【28†L147-L156】 |

**Recommendation (one thing):** Start with **Scoped Resource Containers** (1a) – centralizes resources per run and simplifies DI. It has clear cleanup (`__aexit__`) and improves testability (can easily swap out resources). It addresses the immediate problem of “8+ kwargs” in the constructor and keeps code organized.

**Anti-pattern (desktop apps):** Avoid cloud-native or distributed-oriented abstractions (e.g. Kubernetes jobs, message queues, microservices). For a single-process desktop, patterns like heavy container orchestrators or ephemeral instance scaling are overkill. Similarly, don’t use blocking frameworks that don’t work well with `asyncio` (e.g. forcing threading or multiprocessing for I/O). SDL: favor async/await and local resource management over anything that assumes networked services.
