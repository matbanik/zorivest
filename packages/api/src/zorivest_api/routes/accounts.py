"""Account CRUD REST endpoints.

Source: 04b-api-accounts.md §Account Routes
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
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

    model_config = {"from_attributes": True}


class BalanceRequest(BaseModel):
    balance: float
    snapshot_datetime: Optional[datetime] = None


# ── Account CRUD routes ────────────────────────────────────────────────

@account_router.post("", status_code=201, dependencies=[Depends(require_unlocked_db)])
async def create_account(body: CreateAccountRequest, service=Depends(get_account_service)):
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
    return AccountResponse.model_validate(account)


@account_router.get("", dependencies=[Depends(require_unlocked_db)])
async def list_accounts(service=Depends(get_account_service)):
    """List all accounts."""
    accounts = service.list_accounts()
    return [AccountResponse.model_validate(a) for a in accounts]


@account_router.get("/{account_id}", dependencies=[Depends(require_unlocked_db)])
async def get_account(account_id: str, service=Depends(get_account_service)):
    """Get a single account."""
    try:
        account = service.get_account(account_id)
        return AccountResponse.model_validate(account)
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
        return AccountResponse.model_validate(account)
    except NotFoundError:
        raise HTTPException(404, f"Account not found: {account_id}")


@account_router.delete("/{account_id}", status_code=204, dependencies=[Depends(require_unlocked_db)])
async def delete_account(account_id: str, service=Depends(get_account_service)):
    """Delete an account."""
    service.delete_account(account_id)


# ── Balance snapshot ────────────────────────────────────────────────────

@account_router.post("/{account_id}/balances", status_code=201, dependencies=[Depends(require_unlocked_db)])
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
