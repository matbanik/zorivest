"""Account CRUD REST endpoints.

Source: 04b-api-accounts.md §Account Routes
MEU-71: Balance history + enriched AccountResponse
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from zorivest_core.application.commands import CreateAccount, UpdateBalance
from zorivest_core.domain.enums import AccountType
from zorivest_core.domain.exceptions import NotFoundError
from zorivest_api.dependencies import get_account_service, require_unlocked_db

account_router = APIRouter(prefix="/api/v1/accounts", tags=["accounts"])


# ── Request/Response schemas ────────────────────────────────────────────


class CreateAccountRequest(BaseModel):
    account_id: str
    name: str
    account_type: str  # BROKER | BANK | IRA | K401 etc.
    institution: str = ""
    currency: str = "USD"
    is_tax_advantaged: bool = False
    notes: Optional[str] = None


class UpdateAccountRequest(BaseModel):
    name: Optional[str] = None
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


def _enrich_account_response(account, service) -> AccountResponse:
    """Build AccountResponse with latest_balance enrichment (MEU-71 AC-3)."""
    latest = service.get_latest_balance(account.account_id)
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
    )


# ── Account CRUD routes ────────────────────────────────────────────────


@account_router.post("", status_code=201, dependencies=[Depends(require_unlocked_db)])
async def create_account(
    body: CreateAccountRequest, service=Depends(get_account_service)
):
    """Create a new account."""
    cmd = CreateAccount(
        account_id=body.account_id,
        name=body.name,
        account_type=AccountType(body.account_type.lower()),
        institution=body.institution,
        currency=body.currency,
        is_tax_advantaged=body.is_tax_advantaged,
        notes=body.notes or "",
    )
    account = service.create_account(cmd)
    return _enrich_account_response(account, service)


@account_router.get("", dependencies=[Depends(require_unlocked_db)])
async def list_accounts(service=Depends(get_account_service)):
    """List all accounts.

    Returns a bare Account[] array for backward compatibility with
    19 existing GUI consumers.
    """
    accounts = service.list_accounts()
    return [_enrich_account_response(a, service) for a in accounts]


@account_router.get("/{account_id}", dependencies=[Depends(require_unlocked_db)])
async def get_account(account_id: str, service=Depends(get_account_service)):
    """Get a single account (enriched with latest balance)."""
    try:
        account = service.get_account(account_id)
        return _enrich_account_response(account, service)
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
    except NotFoundError:
        raise HTTPException(404, f"Account not found: {account_id}")


@account_router.delete(
    "/{account_id}", status_code=204, dependencies=[Depends(require_unlocked_db)]
)
async def delete_account(account_id: str, service=Depends(get_account_service)):
    """Delete an account."""
    service.delete_account(account_id)


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
