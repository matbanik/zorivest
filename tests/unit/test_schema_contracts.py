"""Schema-Domain Contract Tests — automated mock-boundary enforcement.

Validates that API request schema fields are subsets of domain model fields.
Catches the 'notes crash' class: API schema accepts a field the domain model rejects.

Source: Cross-Layer Testing Strategy (2026-03-19)
"""

from __future__ import annotations

import dataclasses

import pytest

from zorivest_api.routes.trades import (
    CreateTradeRequest,
    TradeResponse,
    UpdateTradeRequest,
)
from zorivest_api.routes.accounts import (
    CreateAccountRequest,
    AccountResponse,
    UpdateAccountRequest,
)
from zorivest_api.routes.reports import (
    CreateReportRequest,
    ReportResponse,
    UpdateReportRequest,
)
from zorivest_core.domain.entities import Account, Trade, TradeReport


# ── Helpers ─────────────────────────────────────────────────────────────


def _domain_fields(entity_cls: type) -> set[str]:
    """Get the set of field names from a dataclass."""
    return {f.name for f in dataclasses.fields(entity_cls)}


def _schema_fields(schema_cls: type) -> set[str]:
    """Get the set of field names from a Pydantic BaseModel."""
    return set(schema_cls.model_fields.keys())


# Fields that are intentionally on the API schema but NOT on the domain model.
# These must be documented with a reason and handled (filtered) in the route/service layer.
KNOWN_EXCEPTIONS: dict[str, set[str]] = {
    # ReportResponse has 'id', 'created_at', 'trade_id' which are DB-generated, not on the domain dataclass
    "ReportResponse": {"id", "created_at", "trade_id"},
}


# ── Trade Schema Contracts ──────────────────────────────────────────────


class TestTradeSchemaContracts:
    """Validate Trade API schemas align with Trade domain entity."""

    def test_update_trade_fields_subset_of_domain(self) -> None:
        """UpdateTradeRequest fields ⊆ Trade fields (+ documented exceptions)."""
        api_fields = _schema_fields(UpdateTradeRequest)
        domain_fields = _domain_fields(Trade)
        exceptions = KNOWN_EXCEPTIONS.get("UpdateTradeRequest", set())
        extra = api_fields - domain_fields - exceptions
        assert extra == set(), (
            f"UpdateTradeRequest has fields not in Trade and not in KNOWN_EXCEPTIONS: {extra}. "
            f"Either add them to Trade, filter in service layer, and add to KNOWN_EXCEPTIONS."
        )

    def test_create_trade_fields_subset_of_domain(self) -> None:
        """CreateTradeRequest fields ⊆ Trade fields (+ documented exceptions)."""
        api_fields = _schema_fields(CreateTradeRequest)
        domain_fields = _domain_fields(Trade)
        exceptions = KNOWN_EXCEPTIONS.get("CreateTradeRequest", set())
        extra = api_fields - domain_fields - exceptions
        assert extra == set(), (
            f"CreateTradeRequest has fields not in Trade and not in KNOWN_EXCEPTIONS: {extra}. "
            f"Either add them to Trade, filter in service layer, and add to KNOWN_EXCEPTIONS."
        )

    def test_trade_response_fields_subset_of_domain(self) -> None:
        """TradeResponse fields ⊆ Trade fields (response should be renderable from entity)."""
        api_fields = _schema_fields(TradeResponse)
        domain_fields = _domain_fields(Trade)
        exceptions = KNOWN_EXCEPTIONS.get("TradeResponse", set())
        extra = api_fields - domain_fields - exceptions
        assert extra == set(), (
            f"TradeResponse has fields not in Trade: {extra}. "
            f"How will model_validate(trade) populate them?"
        )

    def test_known_exceptions_are_documented(self) -> None:
        """Every KNOWN_EXCEPTION field must still exist on the API schema."""
        for schema_name, fields in KNOWN_EXCEPTIONS.items():
            schema_cls = {
                "UpdateTradeRequest": UpdateTradeRequest,
                "CreateTradeRequest": CreateTradeRequest,
                "TradeResponse": TradeResponse,
                "ReportResponse": ReportResponse,
            }.get(schema_name)
            if schema_cls is None:
                continue
            actual = _schema_fields(schema_cls)
            stale = fields - actual
            assert stale == set(), (
                f"KNOWN_EXCEPTIONS[{schema_name!r}] lists {stale} "
                f"but those fields no longer exist on the schema. Remove them."
            )


# ── Account Schema Contracts ────────────────────────────────────────────


class TestAccountSchemaContracts:
    """Validate Account API schemas align with Account domain entity."""

    def test_update_account_fields_subset_of_domain(self) -> None:
        api_fields = _schema_fields(UpdateAccountRequest)
        domain_fields = _domain_fields(Account)
        extra = api_fields - domain_fields
        assert extra == set(), (
            f"UpdateAccountRequest has fields not in Account: {extra}"
        )

    def test_create_account_fields_subset_of_domain(self) -> None:
        api_fields = _schema_fields(CreateAccountRequest)
        domain_fields = _domain_fields(Account)
        extra = api_fields - domain_fields
        assert extra == set(), (
            f"CreateAccountRequest has fields not in Account: {extra}"
        )

    def test_account_response_fields_subset_of_domain(self) -> None:
        api_fields = _schema_fields(AccountResponse)
        domain_fields = _domain_fields(Account)
        extra = api_fields - domain_fields
        assert extra == set(), (
            f"AccountResponse has fields not in Account: {extra}"
        )


# ── Report Schema Contracts ─────────────────────────────────────────────


class TestReportSchemaContracts:
    """Validate TradeReport API schemas align with TradeReport domain entity."""

    def test_update_report_fields_subset_of_domain(self) -> None:
        api_fields = _schema_fields(UpdateReportRequest)
        domain_fields = _domain_fields(TradeReport)
        extra = api_fields - domain_fields
        assert extra == set(), (
            f"UpdateReportRequest has fields not in TradeReport: {extra}"
        )

    def test_create_report_fields_subset_of_domain(self) -> None:
        api_fields = _schema_fields(CreateReportRequest)
        domain_fields = _domain_fields(TradeReport)
        extra = api_fields - domain_fields
        assert extra == set(), (
            f"CreateReportRequest has fields not in TradeReport: {extra}"
        )

    def test_report_response_fields_subset_of_domain(self) -> None:
        api_fields = _schema_fields(ReportResponse)
        domain_fields = _domain_fields(TradeReport)
        exceptions = KNOWN_EXCEPTIONS.get("ReportResponse", set())
        extra = api_fields - domain_fields - exceptions
        assert extra == set(), (
            f"ReportResponse has fields not in TradeReport: {extra}"
        )
