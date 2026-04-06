"""Account CRUD REST endpoints.

Source: 04b-api-accounts.md §Account Routes
MEU-37: Block-only delete, archive, reassign, metrics, is_archived/is_system
MEU-71: Balance history + enriched AccountResponse
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from pydantic.functional_validators import BeforeValidator
from typing import Annotated, Optional

from zorivest_core.application.commands import CreateAccount, UpdateBalance
from zorivest_core.domain.enums import AccountType
from zorivest_core.domain.exceptions import ConflictError, ForbiddenError, NotFoundError
from zorivest_api.dependencies import get_account_service, require_unlocked_db


def _strip_whitespace(v: object) -> object:
    """Strip leading/trailing whitespace so min_length=1 rejects blank strings."""
    return v.strip() if isinstance(v, str) else v


StrippedStr = Annotated[str, BeforeValidator(_strip_whitespace)]

account_router = APIRouter(prefix="/api/v1/accounts", tags=["accounts"])


# Case-insensitive AccountType: normalize input to lowercase before enum validation
def _normalize_account_type(v: object) -> object:
    return v.lower() if isinstance(v, str) else v


CIAccountType = Annotated[AccountType, BeforeValidator(_normalize_account_type)]


# ── Request/Response schemas ────────────────────────────────────────────


class CreateAccountRequest(BaseModel):
    model_config = {"extra": "forbid"}

    account_id: Optional[str] = None  # MEU-37 AC-13: auto-assigned if omitted
    name: StrippedStr = Field(min_length=1)
    account_type: CIAccountType  # Pydantic validates against StrEnum members
    institution: str = ""
    currency: str = "USD"
    is_tax_advantaged: bool = False
    notes: Optional[str] = None


class UpdateAccountRequest(BaseModel):
    model_config = {"extra": "forbid"}

    name: Optional[StrippedStr] = Field(default=None, min_length=1)
    account_type: Optional[CIAccountType] = None
    institution: Optional[str] = None
    currency: Optional[str] = None
    is_tax_advantaged: Optional[bool] = None
    notes: Optional[str] = None


class AccountResponse(BaseModel):
    account_id: str
    name: str
    account_type: str
    institution: str
    currency: str
    is_tax_advantaged: bool
    notes: str
    latest_balance: Optional[float] = None
    latest_balance_date: Optional[str] = None
    is_archived: bool = False  # MEU-37 AC-1
    is_system: bool = False  # MEU-37 AC-2
    trade_count: Optional[int] = None  # MEU-37 AC-12
    round_trip_count: Optional[int] = None  # MEU-37 AC-12
    win_rate: Optional[float] = None  # MEU-37 AC-12
    total_realized_pnl: Optional[float] = None  # MEU-37 AC-12

    model_config = {"from_attributes": True}


class BalanceSnapshotResponse(BaseModel):
    id: int
    account_id: str
    balance: float
    datetime: Optional[str] = None


class PaginatedBalanceResponse(BaseModel):
    items: list[BalanceSnapshotResponse]
    total: int


class BalanceRequest(BaseModel):
    balance: float
    snapshot_datetime: Optional[datetime] = None


# ── Helpers ─────────────────────────────────────────────────────────────


def _enrich_account_response(
    account, service, include_metrics: bool = False
) -> AccountResponse:
    """Build AccountResponse with latest_balance enrichment (MEU-71 AC-3).

    If include_metrics is True, also compute trade-based metrics (AC-12).
    """
    latest = service.get_latest_balance(account.account_id)

    metrics: dict = {}
    if include_metrics:
        metrics = service.get_account_metrics(account.account_id)

    return AccountResponse(
        account_id=account.account_id,
        name=account.name,
        account_type=account.account_type.value
        if hasattr(account.account_type, "value")
        else str(account.account_type),
        institution=account.institution,
        currency=account.currency,
        is_tax_advantaged=account.is_tax_advantaged,
        notes=account.notes,
        latest_balance=float(latest.balance) if latest else None,
        latest_balance_date=latest.datetime.isoformat()
        if latest and latest.datetime
        else None,
        is_archived=account.is_archived,
        is_system=account.is_system,
        trade_count=metrics.get("trade_count"),
        round_trip_count=metrics.get("round_trip_count"),
        win_rate=metrics.get("win_rate"),
        total_realized_pnl=metrics.get("total_realized_pnl"),
    )


# ── Account CRUD routes ────────────────────────────────────────────────


@account_router.post("", status_code=201, dependencies=[Depends(require_unlocked_db)])
async def create_account(
    body: CreateAccountRequest, service=Depends(get_account_service)
):
    """Create a new account."""
    try:
        # MEU-37 AC-13: auto-assign account_id if not provided
        account_id = body.account_id or str(uuid.uuid4())
        cmd = CreateAccount(
            account_id=account_id,
            name=body.name,
            account_type=body.account_type,  # Already validated as AccountType by Pydantic
            institution=body.institution,
            currency=body.currency,
            is_tax_advantaged=body.is_tax_advantaged,
            notes=body.notes or "",
        )
        account = service.create_account(cmd)
        return _enrich_account_response(account, service)
    except ValueError as e:
        raise HTTPException(422, str(e))


@account_router.get("", dependencies=[Depends(require_unlocked_db)])
async def list_accounts(
    include_archived: bool = Query(default=False),
    include_system: bool = Query(default=False),
    service=Depends(get_account_service),
):
    """List all accounts.

    By default, archived and system accounts are excluded.
    Returns a bare Account[] array for backward compatibility.
    """
    accounts = service.list_accounts(
        include_archived=include_archived,
        include_system=include_system,
    )
    return [_enrich_account_response(a, service) for a in accounts]


@account_router.get("/{account_id}", dependencies=[Depends(require_unlocked_db)])
async def get_account(account_id: str, service=Depends(get_account_service)):
    """Get a single account (enriched with latest balance + metrics)."""
    try:
        account = service.get_account(account_id)
        return _enrich_account_response(account, service, include_metrics=True)
    except NotFoundError:
        raise HTTPException(404, f"Account not found: {account_id}")


@account_router.put("/{account_id}", dependencies=[Depends(require_unlocked_db)])
async def update_account(
    account_id: str,
    body: UpdateAccountRequest,
    service=Depends(get_account_service),
):
    """Update account fields."""
    try:
        kwargs = body.model_dump(exclude_unset=True)
        account = service.update_account(account_id, **kwargs)
        return _enrich_account_response(account, service)
    except ValueError as e:
        raise HTTPException(422, str(e))
    except ForbiddenError as e:
        raise HTTPException(403, str(e))
    except NotFoundError:
        raise HTTPException(404, f"Account not found: {account_id}")


@account_router.delete(
    "/{account_id}", status_code=204, dependencies=[Depends(require_unlocked_db)]
)
async def delete_account(account_id: str, service=Depends(get_account_service)):
    """Delete an account (block-only: fails if trades exist)."""
    try:
        service.delete_account(account_id)
    except ForbiddenError as e:
        raise HTTPException(403, str(e))
    except ConflictError as e:
        raise HTTPException(409, str(e))
    except NotFoundError:
        raise HTTPException(404, f"Account not found: {account_id}")


# ── Action endpoints (D2: separate from DELETE) ────────────────────────


@account_router.post(
    "/{account_id}:archive",
    status_code=200,
    dependencies=[Depends(require_unlocked_db)],
)
async def archive_account(account_id: str, service=Depends(get_account_service)):
    """Soft-delete: set is_archived=True. Trades remain unchanged."""
    try:
        service.archive_account(account_id)
        return {"status": "archived", "account_id": account_id}
    except ForbiddenError as e:
        raise HTTPException(403, str(e))
    except NotFoundError:
        raise HTTPException(404, f"Account not found: {account_id}")


@account_router.post(
    "/{account_id}:reassign-trades",
    status_code=200,
    dependencies=[Depends(require_unlocked_db)],
)
async def reassign_trades(account_id: str, service=Depends(get_account_service)):
    """Move all trades to SYSTEM_DEFAULT, then hard-delete the account."""
    try:
        count = service.reassign_trades_and_delete(account_id)
        return {"trades_reassigned": count, "account_id": account_id}
    except ForbiddenError as e:
        raise HTTPException(403, str(e))
    except NotFoundError:
        raise HTTPException(404, f"Account not found: {account_id}")


# ── Balance snapshot ────────────────────────────────────────────────────


@account_router.post(
    "/{account_id}/balances",
    status_code=201,
    dependencies=[Depends(require_unlocked_db)],
)
async def record_balance(
    account_id: str,
    body: BalanceRequest,
    service=Depends(get_account_service),
):
    """Record a balance snapshot for the account."""
    try:
        cmd = UpdateBalance(
            account_id=account_id,
            balance=Decimal(str(body.balance)),
            snapshot_datetime=body.snapshot_datetime or datetime.now(),
        )
        snapshot = service.add_balance_snapshot(cmd)
        return {
            "id": snapshot.id,
            "account_id": snapshot.account_id,
            "balance": float(snapshot.balance),
            "datetime": snapshot.datetime.isoformat() if snapshot.datetime else None,
        }
    except NotFoundError:
        raise HTTPException(404, f"Account not found: {account_id}")


# ── MEU-71: Balance history ─────────────────────────────────────────────


@account_router.get(
    "/{account_id}/balances", dependencies=[Depends(require_unlocked_db)]
)
async def list_balance_history(
    account_id: str,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    service=Depends(get_account_service),
):
    """List balance history for an account with pagination (P1 wrapper).

    Returns paginated response with items + total count.
    """
    try:
        snapshots = service.list_balance_history(
            account_id,
            limit=limit,
            offset=offset,
        )
        total = service.count_balance_history(account_id)
        return PaginatedBalanceResponse(
            items=[
                BalanceSnapshotResponse(
                    id=s.id,
                    account_id=s.account_id,
                    balance=float(s.balance),
                    datetime=s.datetime.isoformat() if s.datetime else None,
                )
                for s in snapshots
            ],
            total=total,
        )
    except NotFoundError:
        raise HTTPException(404, f"Account not found: {account_id}")
