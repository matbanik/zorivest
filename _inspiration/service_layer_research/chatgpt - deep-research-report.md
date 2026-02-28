# Skeptical Review of Zorivest Service Layer and Testing

## Scope and premises

You’re building a single-user, local desktop app with a entity["company","TypeScript","programming language"] MCP server above a Python service layer, plus a entity["company","SQLite","embedded database engine"] database and significant math/analytics and tax logic. That combination is “small deployment footprint” but “high domain complexity,” which is exactly the case where architecture can either save you or quietly become the product. citeturn2search0turn6search23turn1search0

Your stated pattern set (Service Layer + Unit of Work + Repository, “Cosmic Python style”) is a real, defensible pattern family—but it comes with sharp edges if you copy it mechanically (especially “a service for everything” and “mock away all state”). citeturn2search0turn6search23turn1search0turn1search1

One critical limitation: your “Full Service Layer Document” wasn’t actually provided (it’s a placeholder), so I can’t critique your exact class/method boundaries, dependency graph, or how the MCP routing constrains your API surface. Everything below is therefore a *design review based on your summary* and on the failure modes these patterns commonly create. citeturn2search0turn6search23turn1search0

## Service layer structure and over-engineering risk

**Q1 — Over-engineering risk (25+ services in a single-user desktop app)**

**Honest assessment:** The raw number (“25+”) isn’t the problem; the smell is *what the number implies*: you may be defining “service” as “any coherent pile of functions” instead of “a stable, user-meaningful use case boundary.” Cosmic Python describes the service layer as an orchestration/use-case layer: fetch state, check invariants, call domain logic, persist changes. If you have a separate class for every sub-capability (expectancy, drawdown, dedup hashing, etc.), you’re likely paying a high indirection tax without getting proportional decoupling. citeturn2search0turn1search0

In a desktop app, your “controller” isn’t Flask—it’s GUI handlers + MCP tool-call handlers. If those handlers are thin and the service layer is the stable API, that’s good. But if services are so granular that workflows require choreography across many services, you’ve recreated the complexity you were trying to hide. That’s the “layers everywhere, clarity nowhere” failure mode. citeturn1search0turn2search0

A **minimum viable architecture** that still preserves testability usually looks like:
- a *functional core* (pure domain + analytics functions),
- a thin orchestration layer (a small number of use-case functions/handlers),
- infrastructure adapters (SQLite repos, file storage, broker import adapters, AI client).  
This aligns with both the intent of the Service Layer pattern and the “functional core, imperative shell” approach: keep side effects at the edge, keep logic pure. citeturn2search0turn6search22turn6search7

**Trade-off (follow vs ignore):**  
If you **follow** (reduce service granularity; make “services” map to user workflows), you’ll likely cut boilerplate, reduce dependency injection noise, and make tests less mock-heavy—at the cost of having fewer, bigger orchestration functions that require discipline to keep thin. citeturn2search0turn6search22turn1search1  
If you **ignore** (keep proliferating services), the likely outcome is (a) harder navigation, (b) more “pass-through” code, and (c) tests that verify wiring rather than behavior—especially when each service exists mainly to hold a `uow`. citeturn1search1turn0search1

**Concrete example (what “minimum viable” can look like):**
```python
# application/use_cases/import_trades.py
def import_trades(command, uow_factory, importer_registry, clock):
    with uow_factory() as uow:
        raw_rows = importer_registry.parse(command.source)
        trades = normalize_rows_to_domain_trades(raw_rows, clock=clock)  # pure
        deduped = deduplicate_trades(trades)  # pure
        uow.trades.add_many(deduped)
        uow.commit()

# domain/analytics/expectancy.py (pure)
def expectancy(win_rate: float, avg_win: float, avg_loss: float) -> float:
    return win_rate * avg_win - (1.0 - win_rate) * abs(avg_loss)
```

**Priority:** **should-fix** — unless you already feel friction (lots of cross-service calls, lots of constructor plumbing, lots of “where does this logic live?” moments), in which case it becomes **must-fix**. citeturn1search0aturn2search0

**Q2 — UoW in every service (including pure computations)**

**Honest assessment:** Injecting a UoW into *pure computation* services is architectural self-harm. It couples math to persistence and forces tests into a mocking posture even when the logic is inherently deterministic. Cosmic Python’s description of the service layer is orchestration + persistence boundaries; the domain logic stays in the domain. Your expectancy/SQN/drawdown Monte Carlo are domain computations; they should not *need* a transaction handle to exist. citeturn2search0turn6search23

This is exactly where “functional core, imperative shell” is a better mental model than “everything is a service class”: make calculations pure, then have one orchestration function decide what to fetch and how to store results. citeturn6search22turn6search7

**Trade-off (follow vs ignore):**  
If you **follow** (pure functions or stateless modules for analytics), tests become trivial and far more meaningful (“given X trades, compute Y”), and you reduce the object graph. The trade-off is you lose the uniformity of “every capability is a service with a UoW,” but uniformity is not a virtue if it’s forcing bad coupling. citeturn6search22turn1search1  
If you **ignore**, you will keep writing tests that assert “called repo.list() once” rather than “produced the right analytics,” which is precisely the false-confidence trap mock-heavy suites fall into. citeturn1search1turn0search1

**Concrete example (separating orchestration from math):**
```python
# application/use_cases/compute_expectancy.py
def compute_expectancy_for_strategy(strategy_id: int, uow_factory):
    with uow_factory() as uow:
        trades = uow.trades.list_for_strategy(strategy_id)
    # after leaving UoW: pure compute, no DB
    stats = expectancy_metrics(trades)
    return stats

# domain/analytics/expectancy_metrics.py
def expectancy_metrics(trades):
    # compute win_rate, avg_win, avg_loss, kelly, etc. purely
    ...
```

**Priority:** **must-fix** — because it directly drags your testing strategy into the “mock everything” corner and makes the architecture harder to evolve. citeturn6search22turn2search0turn1search1

## Unit of Work boundaries and missing patterns

**Q3 — Missing patterns (Saga, Specification, Strategy, Observer/Event)**

**Honest assessment:** You’re not “missing patterns” so much as you risk applying them where transactions + good boundaries already suffice.

- **Saga pattern:** A saga is defined for business transactions spanning multiple services, coordinated via local transactions and compensations. That is a distributed-systems pattern, and in your app you generally *have one database* and one process. For “import → dedup → persist → enrich,” a single SQLite transaction is usually the right primitive for the DB part; a saga becomes relevant only when side effects (files, network, AI calls) must be coordinated with DB state. citeturn4search0turn4search8turn6search23  
  In other words: if you adopt saga concepts, it should be narrowly as “workflow with compensation for non-DB side effects,” not as microservice-style saga orchestration. citeturn4search0turn4search8

- **Specification pattern:** This *can* be useful for tax lot filtering because it explicitly exists to recombine business rules using Boolean logic (and is commonly associated with DDD). If you keep finding yourself writing deeply nested `if` logic across many tax scenarios (“wash sale candidate lots,” “holding period,” “lot dispose ordering,” etc.), a specification-style predicate layer can make rules composable and testable. But it can also become an abstraction maze if your rules are not reused. citeturn4search14

- **Strategy pattern:** A “registry dict” for broker adapters is already strategy *in spirit*. Whether you need the formal pattern depends on variability and shared lifecycle/state. Strategy is meant to make multiple algorithms interchangeable behind a shared interface. If your adapters all implement `detect()` and `parse()`, you’re already there; wrapping it in classes is only justified if you need shared configuration, caching, or complex detection heuristics. citeturn3search9turn2search0

- **Observer/Event pattern:** In-process observer/event is a classic way to decouple “something happened” from “who reacts.” It’s common in GUIs and event-driven programming, but it creates its own complexity (ordering, retries, idempotency, debugging). In your case, events can be valuable if you keep seeing cross-service coordination (“trade imported → recompute analytics → refresh portfolio widgets → invalidate caches”). Otherwise, direct orchestration is simpler. citeturn3search6turn4search1turn2search0

**Trade-off (follow vs ignore):**  
If you **follow** (apply these patterns selectively), you can reduce coupling for the truly cross-cutting workflows (imports, tax reconciliations) while keeping day-to-day code simple. The trade-off is you must enforce strong conventions (event names, payload schemas, idempotency rules) or you will create an implicit control flow that’s hard to reason about. citeturn3search6turn4search1  
If you **ignore** (never use them), you’ll likely end up with large orchestration functions that call many services directly. That can be perfectly fine in a desktop app—until it isn’t. The failure mode is “God workflow function” that no one wants to touch. citeturn2search0turn1search0

**Concrete example (Specification for tax lots without ceremony):**
```python
from dataclasses import dataclass
from typing import Callable

LotPredicate = Callable[["Lot"], bool]

def and_(*preds: LotPredicate) -> LotPredicate:
    return lambda lot: all(p(lot) for p in preds)

def holding_period_is_long_term(as_of_date) -> LotPredicate:
    return lambda lot: (as_of_date - lot.open_date).days >= 365

def same_symbol(symbol: str) -> LotPredicate:
    return lambda lot: lot.symbol == symbol

# usage
pred = and_(same_symbol("AAPL"), holding_period_is_long_term(as_of))
eligible = [lot for lot in lots if pred(lot)]
```

**Priority:**  
- Saga (distributed-style): **nice-to-have** (and often “don’t do it”). citeturn4search0turn4search8  
- Specification for tax rules: **should-fix** once rule reuse/complexity is clearly painful. citeturn4search14  
- Strategy formalization for broker adapters: **should-fix** if adapter growth is expected. citeturn3search9  
- Observer/event inside the app: **nice-to-have** unless coordination complexity is already biting you. citeturn3search6turn4search1

**Q4 — Service vs Domain Logic boundary (e.g., dedup hash computation)**

**Honest assessment:** If `DeduplicationService.compute_dedup_hash` encodes “what counts as the same trade” (business meaning), it’s domain logic and belongs with the domain model/analytics logic—not inside an orchestration/service layer. Cosmic Python is explicit that orchestration belongs in the service layer and “domain logic stays in the domain.” Keeping business rules out of the domain is how you drift into the anemic domain antipattern. citeturn2search0

If, however, the hash is purely a technical artifact of an import pipeline (e.g., hash of a broker CSV row for idempotent import bookkeeping), then it’s arguably infrastructure/adapter logic, not domain. The key is whether the hash is stable across brokers and semantically grounded, or whether it’s “whatever makes this import idempotent.” citeturn2search0turn1search0

**Trade-off (follow vs ignore):**  
If you **follow** (move business definitions into domain), you get a more maintainable model where “trade equality/identity” is testable and reusable, and orchestration stays thin. The cost is refactoring: you’ll touch callers, and you must define the boundary carefully. citeturn2search0turn6search22  
If you **ignore**, you’ll keep scattering business meaning into service utilities. That tends to produce brittle change dynamics: small rule changes require hunting across services and mocks. citeturn1search1turn2search0

**Concrete example (make it domain, not service):**
```python
# domain/trades/identity.py
def trade_fingerprint(trade) -> str:
    # explicitly define what fields define "same trade"
    # (and version it if you ever change semantics)
    ...

# application/use_cases/import_trades.py
fp = trade_fingerprint(trade)
if uow.import_log.seen(fp):
    ...
```

**Priority:** **should-fix** (becomes **must-fix** if dedup bugs would corrupt tax/analytics correctness). citeturn2search0

## Testing strategy critique

image_group{"layout":"carousel","aspect_ratio":"16:9","query":["practical test pyramid diagram unit integration e2e","Martin Fowler practical test pyramid diagram"],"num_per_query":1}

**Q5 — Mock-only tests with “no database or network” exit criteria**

**Honest assessment:** Yes—this is classic false confidence. A mock-heavy suite can prove that “service X calls repo.save()” but not that the SQL is correct, transactions are real, constraints behave, file paths work, or imports actually parse. entity["people","Martin Fowler","software engineer"] distinguishes mocks (behavior verification) from other doubles; mockist testing tends to over-specify interactions, making refactors painful and leaving real integration untested. citeturn1search1

Also: your app’s persistence layer isn’t “an external dependency” in the way a network call is. It’s literally the core of a local app. Treating SQLite as untestable “because database” is an overcorrection. Well-scoped integration tests against SQLite are typically fast enough to run frequently, especially with `:memory:` or temp-file databases. citeturn4search3turn4search7turn0search1

Finally, test strategy guidance like the “practical test pyramid” acknowledges that DB/filesystem integration tests are slower and more complex than pure unit tests—but it doesn’t say “avoid them entirely.” It says “use them intentionally.” citeturn0search1turn0search29

**Trade-off (follow vs ignore):**  
If you **follow** (introduce real-SQLite integration tests), you’ll catch schema mistakes, transaction boundary bugs, and import/persistence mismatches early. The cost is test setup complexity and some runtime overhead—but SQLite integration tests are often measured in milliseconds to low seconds per suite, not minutes, if designed well. citeturn0search1turn4search3turn0search10  
If you **ignore**, you are betting that (a) your repositories are perfect, (b) your UoW always commits/rolls back as intended, and (c) imports never face real-world weirdness. That bet is not rational given you’re doing tax lots and broker imports. citeturn1search1turn1search6turn0search1

**Concrete example (fast SQLite integration test setup):**
```python
# conftest.py
import sqlite3
import tempfile
from pathlib import Path

import pytest

@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "test.db"

@pytest.fixture
def conn(db_path: Path):
    c = sqlite3.connect(db_path)
    c.execute("PRAGMA foreign_keys = ON;")
    # run schema/migrations here
    yield c
    c.close()

@pytest.fixture
def uow_factory(conn):
    # Build a UoW factory that uses the existing connection (or opens per UoW)
    ...

def test_uow_rolls_back_on_exception(uow_factory):
    try:
        with uow_factory() as uow:
            uow.trades.add(...)
            raise RuntimeError("boom")
    except RuntimeError:
        pass
    # assert not persisted
```
Caveat: `:memory:` databases are per-connection; if your code opens multiple connections, you won’t see the same in-memory DB unless you use a shared-cache URI or keep one connection. A temp file is often closer to production behavior. citeturn4search3turn4search7turn0search33

**Priority:** **must-fix** — because you’re currently not testing the parts most likely to break in production (SQL/transactions/files/parsers). citeturn0search1turn1search1turn0search10

**Q6 — Math service testing strategy (example vs property vs golden/snapshot)**

**Honest assessment:** Your current example-based tests are necessary but not sufficient. Example tests prove you got *some* cases right. Property-based tests prove the implementation respects invariants across a broad range of inputs, and tools like Hypothesis explicitly aim to generate edge cases you didn’t think about. citeturn5search0turn5search20

A skeptical take: if your Monte Carlo and drawdown code is only tested with hand-picked cases, you’re testing your intuition, not your algorithm. For deterministic formulas (expectancy, Kelly fraction, SQN), property tests can quickly reveal divide-by-zero, sign errors, and boundary mistakes. For stochastic simulations, you’ll need reproducibility (seeded RNG) and tests that assert distributional properties or bounds rather than exact values. citeturn5search0turn5search20turn0search1

**Recommended combination:**  
- **Example-based** for clarity and documentation of canonical scenarios. citeturn5search0  
- **Property-based** for invariants (“no NaNs,” “drawdown is never negative,” “win_rate stays in [0,1],” “Kelly respects constraints given bounded inputs”). citeturn5search0turn5search20  
- **Golden/snapshot** for *published or externally validated* outputs: e.g., compare to a trusted spreadsheet, or lock a known result for a known dataset (especially for tax and lot matching, where “close enough” is not acceptable). Contract-test thinking also applies here: the *shape* of results often matters. citeturn1search6turn0search1

**Trade-off (follow vs ignore):**  
If you **follow**, you’ll spend more effort defining invariants and managing seeds/tolerances, but you will uncover corner cases that example tests won’t cover. citeturn5search0turn5search20  
If you **ignore**, your simulations may still be “plausible” while being subtly wrong—a dangerous state for portfolio analytics and anything tax-adjacent. citeturn0search1turn1search1

**Concrete example (property-based sanity tests with Hypothesis):**
```python
from hypothesis import given, strategies as st
import math

@given(
    win_rate=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    avg_win=st.floats(min_value=0.0, max_value=1e6, allow_nan=False, allow_infinity=False),
    avg_loss=st.floats(min_value=-1e6, max_value=0.0, allow_nan=False, allow_infinity=False),
)
def test_expectancy_is_finite(win_rate, avg_win, avg_loss):
    e = expectancy(win_rate, avg_win, avg_loss)
    assert math.isfinite(e)
```

**Priority:** **should-fix** for deterministic metrics; **must-fix** for Monte Carlo/drawdown if those numbers will be user-facing and relied upon. citeturn5search0turn0search1

**Q7 — Missing test categories (contract, fuzz, integration, regression, performance)**

**Honest assessment:** You are missing at least three categories that matter *specifically* for your app:
- **Integration tests with real SQLite** (to validate repositories, schema constraints, and transaction behavior). citeturn0search1turn4search3turn0search10  
- **Fuzz/property tests for imports** (because you ingest messy external data). Hypothesis broadens input coverage; coverage-guided fuzzing (e.g., Google’s Atheris) is designed for exactly “parse untrusted input” classes of bugs. citeturn5search0turn5search2turn5search6turn5search26  
- **Contract tests** at boundaries you don’t control: MCP tool schemas (TypeScript ↔ Python), broker formats (CSV/PDF), and AI provider response shape. Contract tests are explicitly about validating the *format/contract* rather than exact data. citeturn1search6turn2search10turn2search3  

Performance tests are also relevant because Monte Carlo can quietly become “works on my machine” slow. Tools like `pytest-benchmark` exist specifically to benchmark functions and track regressions. citeturn5search1turn5search25

**Trade-off (follow vs ignore):**  
If you **follow**, you’ll add test suite complexity (markers, fixtures, baseline data) but you’ll substantially increase real confidence and reduce production surprises. citeturn0search1turn5search2turn1search6  
If you **ignore**, you’ll keep paying the cost later as bug reports and “why did this import break?” regressions—particularly because file/format parsing failures are often data-dependent and not caught by mocks. citeturn5search2turn5search26turn1search23

**Concrete example (how to phase it without boiling the ocean):**  
- Start with integration tests for **UoW + one repository + one schema constraint** (foreign keys, unique constraints). citeturn6search23turn0search10turn0search33  
- Add fuzz/property tests for **header detection** and **row parsing** (CSV) before you tackle PDFs. citeturn5search0turn5search2  
- Add contract tests around MCP tool schemas once the tool surface is stabilizing; MCP is JSON-RPC-based and schema-driven, so schema drift is an actual risk. citeturn2search10turn2search3  

**Priority:**  
- Integration tests (SQLite): **must-fix**. citeturn0search1turn4search3  
- Fuzz/property tests for imports: **should-fix** (becomes **must-fix** if imports are a flagship feature). citeturn5search2turn5search26turn5search0  
- Contract tests (MCP + AI + import outputs): **should-fix**. citeturn1search6turn2search10  
- Regression tests: **must-fix as you find bugs** (this is how you stop repeats). citeturn0search1  
- Performance tests (Monte Carlo): **should-fix** if runtime matters; otherwise **nice-to-have** until you see slowness. citeturn5search1turn5search25  

**Q8 — Test organization (one test file per service; TaxService becoming huge)**

**Honest assessment:** One-file-per-service is a mechanical rule that breaks down when one “service” contains multiple domains (wash sales, lots, quarterly estimates). Test structure should represent *behavioral surfaces and risk*, not class names. When tests mirror classes too closely, refactoring becomes expensive because moving a method forces moving a test file even if the behavior didn’t change—this is the same coupling problem mockist tests can create, but at the file-system level. citeturn1search1turn0search1

For tax logic, “scenario-based” organization usually wins: group tests by IRS-rule concept or workflow (“wash sale disallowance scenarios,” “lot selection strategy,” “quarterly estimate computation”), and use parametrization for variations. Pytest’s parametrization exists specifically to avoid duplicative boilerplate across many input/output combinations. citeturn5search39

**Trade-off (follow vs ignore):**  
If you **follow** (organize by behavior), it becomes easier to find coverage gaps and to add regression tests when a bug is discovered (“this is a wash sale edge case”). The cost is you must define and maintain a naming convention and avoid duplicating fixtures across modules. citeturn5search39turn0search1  
If you **ignore**, your tax test module will become an unreviewable blob, which increases the odds that future changes get under-tested because adding one more scenario feels painful. citeturn0search1

**Concrete example (taxonomy-based test modules):**
- `test_tax_wash_sales.py`
- `test_tax_lot_matching.py`
- `test_tax_holding_periods.py`
- `test_tax_quarterly_estimates.py`
- `test_tax_regressions.py` (bugs live forever here)

**Priority:** **should-fix** (it’s a maintainability multiplier). citeturn5search39turn0search1

## Fragile adapters and AI integration

**Q9 — Import services fragility (CSV header autodetect; PDF table extraction)**

**Honest assessment:** Your import layer is your highest “entropy interface.” CSVs in the wild have header changes, extra columns, locale-dependent number formats, and inconsistent quoting. PDFs are worse: table extraction depends on layout heuristics and often fails when borders disappear or spacing changes—pdfplumber is built on pdfminer.six and is fundamentally about interpreting layout, not consuming a true semantic table model. citeturn1search23turn1search11turn1search3

Trying to make this reliable without fixtures is unrealistic. The real question is: how do you reduce fixture count *while still testing reality*?

A reliable strategy is layered:
1) **Unit tests of normalization/detection** using *generated or minimal tabular inputs* (not full broker files).  
2) **Property-based tests** that mutate headers/columns/whitespace and assert stable detection + parsing. Hypothesis is designed to generate edge cases over described input ranges. citeturn5search0turn5search20  
3) **A small, curated corpus of real fixtures** per broker per format version (you don’t need 50+, but you do need *at least a few*).  
4) **Fuzzing harnesses** for parsers that must withstand malformed input; Atheris is explicitly a coverage-guided fuzzing engine for Python. citeturn5search2turn5search6turn5search26  

For PDFs specifically, add one more principle: test the **intermediate representation** you actually rely on (words/lines/boxes extracted) rather than only the final “list of rows,” because debugging table extraction failures requires visibility into layout interpretation. The existence of multiple community reports about table extraction failing when borders are missing is a warning: you need regression fixtures for those specific failure modes. citeturn1search11turn1search23

**Trade-off (follow vs ignore):**  
If you **follow**, you’ll invest in a “fixtures + generators + fuzz” harness that catches format drift early, and you’ll dramatically reduce brittleness shocks when brokers update exports. The cost is you must maintain the fixture corpus and commit to stable normalization outputs (a good thing). citeturn5search0turn5search2turn1search6  
If you **ignore**, your imports will fail unpredictably for users, and you’ll be forced into reactive debugging with user-provided files—exactly the kind of slow, confidence-killing loop tests are meant to prevent. citeturn1search23turn5search26turn0search1

**Concrete example (property-based testing for header detection stability):**
```python
from hypothesis import given, strategies as st

# imagine detect_broker(headers: list[str]) -> str | None
KNOWN_HEADERS = ["Date", "Symbol", "Quantity", "Price"]

@given(st.permutations(KNOWN_HEADERS))
def test_detection_ignores_column_order(permuted):
    assert detect_broker(list(permuted)) == "MyBroker"

@given(st.lists(st.text(min_size=1), min_size=1, max_size=20))
def test_detection_never_crashes_on_weird_headers(headers):
    detect_broker(headers)  # should not throw
```

**Priority:** **must-fix** — because import failures are user-visible and data-dependent, and mocks cannot protect you here. citeturn1search23turn5search0turn5search26

**Q10 — AI service budget cap (`budget_cap: float = 0.10`) without real API calls**

**Honest assessment:** Mocking is sufficient *only if you stop using mocks to verify method calls and instead validate real budget behavior as state changes*. The right design is to separate:
- request planning (what you want to ask),
- provider call (side effect),
- cost accounting + budget enforcement (pure-ish logic that you can test deterministically).

This is exactly where “contract tests” and “self-initializing fakes” are useful: you want a fake AI client that returns realistic payload shapes (including token usage / cost fields) so you can validate parsing and enforcement without hitting the network. Contract tests focus on validating format/contract rather than real data. citeturn1search6turn1search1

Given you’re routing through MCP, you also have *another* contract boundary: the MCP tool schema and JSON-RPC message format. MCP specs explicitly state JSON-RPC 2.0 message structure requirements, and MCP servers expose tools with specified parameters. A schema drift here can break calls even if Python code is “correct.” citeturn2search10turn2search3turn2search26

A fake LLM server is usually overkill for a local desktop app unless:
- you need to test streaming behavior and cancellation,
- you rely on provider retries/backoff semantics,
- you want to validate “real HTTP client + serialization” as part of your integration suite.  
Otherwise, a fake client + a couple of contract tests based on captured real responses is the pragmatic middle. citeturn1search6turn0search1

**Trade-off (follow vs ignore):**  
If you **follow**, you’ll have deterministic tests for budget enforcement and fewer flaky failures; the cost is designing a stable `AIClient` interface and maintaining representative fake responses. citeturn1search6turn1search1  
If you **ignore**, budget caps are the kind of feature that “looks fine in code review” and then fails in production due to small shape changes in provider responses or because cost is computed in multiple places. citeturn1search6turn0search1

**Concrete example (fake AI client that makes budget enforcement testable):**
```python
class FakeAIClient:
    def __init__(self, responses):
        self._responses = list(responses)

    def complete(self, prompt):
        # returns (text, cost_usd) in this simplified example
        return self._responses.pop(0)

def test_budget_cap_blocks_calls():
    fake = FakeAIClient([
        ("ok", 0.06),
        ("ok", 0.05),
    ])
    svc = AIReviewService(ai_client=fake, budget_cap=0.10)

    svc.review_trade(trade_id=1)  # spends 0.06
    with pytest.raises(BudgetExceeded):
        svc.review_trade(trade_id=2)  # would take total to 0.11
```

**Priority:** **should-fix** (becomes **must-fix** if you market budget control as a safety feature). citeturn1search6turn2search3turn0search1

## Synthesis of priorities

Your biggest current risks aren’t “missing patterns.” They’re:
- **Coupling pure computation to UoW/persistence** (driving you into mock-only tests). citeturn6search22turn2search0turn1search1  
- **A test strategy that refuses to test SQLite / parsing / file I/O**, which are core to a local analytics app. citeturn0search1turn4search3turn1search23  
- **Fragile import boundaries** where reality will outperform your mocks every time. citeturn1search23turn5search2turn5search0  

If you fix those, the rest (spec/strategy/events, file organization) becomes tractable incremental engineering rather than architectural debt compounding interest. citeturn1search0turn2search0turn0search1