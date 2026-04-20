"""Shared test configuration and fixtures for Zorivest."""

import os

import pytest


# ── DB Isolation ────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _isolate_db_url(tmp_path):
    """Set ZORIVEST_DB_URL to a per-test temp file so tests never touch the real DB.

    MEU-90a: The lifespan now creates a real SQLAlchemy engine from
    ZORIVEST_DB_URL.  Without this fixture, ``create_app()`` + ``TestClient``
    would create ``zorivest.db`` in the project root, polluting the workspace
    and leaking state across runs.

    Function-scoped (via tmp_path) to prevent cross-test data pollution.
    """
    url = f"sqlite:///{tmp_path / 'test.db'}"
    old = os.environ.get("ZORIVEST_DB_URL")
    os.environ["ZORIVEST_DB_URL"] = url
    yield
    if old is None:
        os.environ.pop("ZORIVEST_DB_URL", None)
    else:
        os.environ["ZORIVEST_DB_URL"] = old


# ── Phase 2.75: Broker Import Test Fixtures ──────────────────────────────

SAMPLE_FLEXQUERY_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<FlexQueryResponse queryName="TestQuery" type="AF">
  <FlexStatements count="1">
    <FlexStatement accountId="U1234567" fromDate="20260101" toDate="20260131">
      <Trades>
        <Trade accountId="U1234567" symbol="AAPL" description="APPLE INC"
               dateTime="20260115;093015" quantity="100" tradePrice="185.50"
               ibCommission="-1.00" ibOrderRef="ORDER001"
               assetCategory="STK" currency="USD" fxRateToBase="1"
               buySell="BOT" />
        <Trade accountId="U1234567" symbol="MSFT" description="MICROSOFT CORP"
               dateTime="20260116;140530" quantity="-50" tradePrice="405.25"
               ibCommission="-0.65" ibOrderRef="ORDER002"
               assetCategory="STK" currency="USD" fxRateToBase="1"
               buySell="SLD" />
        <Trade accountId="U1234567" symbol="AAPL  260320C00200000" description="AAPL 20MAR26 200 C"
               dateTime="20260117;100000" quantity="5" tradePrice="3.50"
               ibCommission="-3.50" ibOrderRef="ORDER003"
               assetCategory="OPT" currency="USD" fxRateToBase="1"
               buySell="BOT" multiplier="100" />
      </Trades>
    </FlexStatement>
  </FlexStatements>
</FlexQueryResponse>
"""

SAMPLE_FLEXQUERY_FX_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<FlexQueryResponse queryName="TestQuery" type="AF">
  <FlexStatements count="1">
    <FlexStatement accountId="U1234567" fromDate="20260101" toDate="20260131">
      <Trades>
        <Trade accountId="U1234567" symbol="BMW" description="BMW AG"
               dateTime="20260115;093015" quantity="50" tradePrice="95.20"
               ibCommission="-2.00" ibOrderRef="ORDER004"
               assetCategory="STK" currency="EUR" fxRateToBase="1.08"
               buySell="BOT" />
      </Trades>
    </FlexStatement>
  </FlexStatements>
</FlexQueryResponse>
"""

SAMPLE_FLEXQUERY_EMPTY_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<FlexQueryResponse queryName="TestQuery" type="AF">
  <FlexStatements count="1">
    <FlexStatement accountId="U1234567" fromDate="20260101" toDate="20260131">
      <Trades />
    </FlexStatement>
  </FlexStatements>
</FlexQueryResponse>
"""

SAMPLE_FLEXQUERY_MALFORMED_ROW_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<FlexQueryResponse queryName="TestQuery" type="AF">
  <FlexStatements count="1">
    <FlexStatement accountId="U1234567" fromDate="20260101" toDate="20260131">
      <Trades>
        <Trade accountId="U1234567" symbol="AAPL" description="APPLE INC"
               dateTime="20260115;093015" quantity="100" tradePrice="185.50"
               ibCommission="-1.00" ibOrderRef="ORDER001"
               assetCategory="STK" currency="USD" fxRateToBase="1"
               buySell="BOT" />
        <Trade accountId="U1234567" symbol="" description=""
               dateTime="INVALID" quantity="" tradePrice=""
               ibCommission="" ibOrderRef=""
               assetCategory="UNKNOWN" currency="USD" fxRateToBase="1"
               buySell="BOT" />
      </Trades>
    </FlexStatement>
  </FlexStatements>
</FlexQueryResponse>
"""

SAMPLE_FLEXQUERY_FUTURE_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<FlexQueryResponse queryName="TestQuery" type="AF">
  <FlexStatements count="1">
    <FlexStatement accountId="U1234567" fromDate="20260101" toDate="20260131">
      <Trades>
        <Trade accountId="U1234567" symbol="ESH6" description="E-MINI S&amp;P 500"
               dateTime="20260120;143000" quantity="2" tradePrice="5250.50"
               ibCommission="-4.12" ibOrderRef="ORDER005"
               assetCategory="FUT" currency="USD" fxRateToBase="1"
               buySell="BOT" multiplier="50" />
      </Trades>
    </FlexStatement>
  </FlexStatements>
</FlexQueryResponse>
"""

SAMPLE_FLEXQUERY_FOREX_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<FlexQueryResponse queryName="TestQuery" type="AF">
  <FlexStatements count="1">
    <FlexStatement accountId="U1234567" fromDate="20260101" toDate="20260131">
      <Trades>
        <Trade accountId="U1234567" symbol="EUR.USD" description="EUR.USD"
               dateTime="20260120;090000" quantity="100000" tradePrice="1.0850"
               ibCommission="-2.00" ibOrderRef="ORDER006"
               assetCategory="CASH" currency="USD" fxRateToBase="1"
               buySell="BOT" />
      </Trades>
    </FlexStatement>
  </FlexStatements>
</FlexQueryResponse>
"""

SAMPLE_TOS_CSV = """\
Account Statement for XXXXXXX123

Trade History
Exec Time,Spread,Side,Qty,Pos Effect,Symbol,Exp,Strike,Type,Price,Net Price,Order Type
01/15/2026 09:30:15,STOCK,BUY,100,TO OPEN,AAPL,,,,185.50,185.51,LMT
01/15/2026 10:00:00,SINGLE,BUY,5,TO OPEN,.AAPL260320C200,260320,200,CALL,3.50,3.51,LMT
01/16/2026 14:05:30,STOCK,SELL,-50,TO CLOSE,MSFT,,,,405.25,405.24,MKT

Cash Balance
"""

SAMPLE_NINJATRADER_CSV = """\
Trade-#,Instrument,Account,Strategy,Market pos.,Quantity,Entry price,Exit price,Entry time,Exit time,Profit,Cum. profit,Commission,MAE,MFE
1,ES 03-26,Sim101,MyStrategy,Long,2,5250.50,5260.75,3/10/2026 9:31:00 AM,3/10/2026 10:15:00 AM,1025.00,1025.00,8.24,125.00,1250.00
2,NQ 03-26,Sim101,ScalpBot,Short,1,18500.25,18475.50,3/10/2026 11:00:00 AM,3/10/2026 11:30:00 AM,495.00,1520.00,4.12,75.00,550.00
"""


@pytest.fixture
def flexquery_xml_file(tmp_path):
    """Write sample FlexQuery XML to a temp file."""
    f = tmp_path / "flexquery.xml"
    f.write_text(SAMPLE_FLEXQUERY_XML, encoding="utf-8")
    return f


@pytest.fixture
def flexquery_fx_xml_file(tmp_path):
    """Write multi-currency FlexQuery XML to a temp file."""
    f = tmp_path / "flexquery_fx.xml"
    f.write_text(SAMPLE_FLEXQUERY_FX_XML, encoding="utf-8")
    return f


@pytest.fixture
def flexquery_empty_xml_file(tmp_path):
    """Write empty-trades FlexQuery XML to a temp file."""
    f = tmp_path / "flexquery_empty.xml"
    f.write_text(SAMPLE_FLEXQUERY_EMPTY_XML, encoding="utf-8")
    return f


@pytest.fixture
def flexquery_malformed_xml_file(tmp_path):
    """Write FlexQuery XML with one valid and one malformed trade."""
    f = tmp_path / "flexquery_malformed.xml"
    f.write_text(SAMPLE_FLEXQUERY_MALFORMED_ROW_XML, encoding="utf-8")
    return f


@pytest.fixture
def flexquery_future_xml_file(tmp_path):
    """Write futures trade FlexQuery XML to a temp file."""
    f = tmp_path / "flexquery_future.xml"
    f.write_text(SAMPLE_FLEXQUERY_FUTURE_XML, encoding="utf-8")
    return f


@pytest.fixture
def flexquery_forex_xml_file(tmp_path):
    """Write forex trade FlexQuery XML to a temp file."""
    f = tmp_path / "flexquery_forex.xml"
    f.write_text(SAMPLE_FLEXQUERY_FOREX_XML, encoding="utf-8")
    return f


@pytest.fixture
def tos_csv_file(tmp_path):
    """Write sample TOS CSV to a temp file."""
    f = tmp_path / "tos_export.csv"
    f.write_text(SAMPLE_TOS_CSV, encoding="utf-8")
    return f


@pytest.fixture
def ninjatrader_csv_file(tmp_path):
    """Write sample NinjaTrader CSV to a temp file."""
    f = tmp_path / "ninjatrader_export.csv"
    f.write_text(SAMPLE_NINJATRADER_CSV, encoding="utf-8")
    return f


@pytest.fixture
def malformed_xml_file(tmp_path):
    """Write non-XML content to a file for error handling tests."""
    f = tmp_path / "bad.xml"
    f.write_text("this is not xml at all <broken>", encoding="utf-8")
    return f


@pytest.fixture
def xxe_attack_xml_file(tmp_path):
    """Write XXE attack payload for security testing."""
    f = tmp_path / "xxe_attack.xml"
    f.write_text(
        '<?xml version="1.0"?>'
        '<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>'
        "<FlexQueryResponse>&xxe;</FlexQueryResponse>",
        encoding="utf-8",
    )
    return f


# ── Pipeline E2E Test Harness Fixtures (MEU-PW8) ────────────────────────


# Mock step types that need cleanup tracking
_MOCK_STEP_TYPE_NAMES = [
    "mock_fetch",
    "mock_transform",
    "mock_store",
    "mock_fail",
    "mock_slow",
    "mock_side_effect",
]


@pytest.fixture(scope="session", autouse=True)
def _register_mock_steps():
    """Register mock steps at session start; clean up at session end.

    Importing mock_steps triggers __init_subclass__ auto-registration.
    On teardown, mock type_names are removed from STEP_REGISTRY to
    prevent pollution of other test modules.

    Spec: §9B.8 — "Scoped registration in conftest; cleanup after test session"
    """
    from zorivest_core.domain.step_registry import STEP_REGISTRY

    import tests.fixtures.mock_steps  # noqa: F401 — triggers registration

    yield

    for name in _MOCK_STEP_TYPE_NAMES:
        STEP_REGISTRY.pop(name, None)


@pytest.fixture()
def pipeline_engine():
    """Function-scoped in-memory SQLite engine with all tables for pipeline E2E.

    Separate from integration/conftest.py engine to avoid coupling.
    """
    from sqlalchemy import create_engine

    from zorivest_infra.database.models import Base

    eng = create_engine(
        "sqlite://", echo=False, connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(eng)
    return eng


@pytest.fixture()
def pipeline_uow(pipeline_engine):
    """Pre-entered UoW for pipeline E2E tests.

    The UoW is entered via context manager so repos are initialized.
    Caller gets a live UoW with an open session.
    """
    from zorivest_infra.database.unit_of_work import SqlAlchemyUnitOfWork

    uow = SqlAlchemyUnitOfWork(pipeline_engine)
    with uow:
        yield uow


@pytest.fixture()
def pipeline_runner(pipeline_uow):
    """PipelineRunner wired to real UoW, RefResolver, and ConditionEvaluator."""
    from zorivest_core.services.condition_evaluator import ConditionEvaluator
    from zorivest_core.services.pipeline_runner import PipelineRunner
    from zorivest_core.services.ref_resolver import RefResolver

    return PipelineRunner(
        uow=pipeline_uow,
        ref_resolver=RefResolver(),
        condition_evaluator=ConditionEvaluator(),
    )


class _StubScheduler:
    """Minimal scheduler stub — APScheduler is out of scope for pipeline E2E."""

    def schedule_policy(self, **kwargs):
        pass

    def unschedule_policy(self, policy_id):
        pass

    def get_status(self):
        return {"running": False, "jobs": 0}


@pytest.fixture()
def scheduling_service(pipeline_uow, pipeline_runner):
    """Full SchedulingService stack wired to real adapters and UoW."""
    from zorivest_api.scheduling_adapters import (
        AuditCounterAdapter,
        PolicyStoreAdapter,
        RunStoreAdapter,
        StepStoreAdapter,
    )
    from zorivest_core.services.pipeline_guardrails import PipelineGuardrails
    from zorivest_core.services.scheduling_service import SchedulingService

    policy_store = PolicyStoreAdapter(pipeline_uow)
    run_store = RunStoreAdapter(pipeline_uow)
    step_store = StepStoreAdapter(pipeline_uow)
    audit_adapter = AuditCounterAdapter(pipeline_uow)

    guardrails = PipelineGuardrails(
        audit_counter=audit_adapter,
        policy_lookup=policy_store,
    )

    return SchedulingService(
        policy_store=policy_store,
        run_store=run_store,
        step_store=step_store,
        pipeline_runner=pipeline_runner,
        scheduler_service=_StubScheduler(),
        guardrails=guardrails,
        audit_logger=audit_adapter,
    )
