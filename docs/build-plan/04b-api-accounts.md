# Phase 4b: REST API — Accounts & Ingest

> Part of [Phase 4: REST API](04-rest-api.md) | Tag: `accounts`
>
> Broker adapters, bank accounts, CSV/PDF import, identifier resolution, positions.

---

## Account Routes

> Source: [GUI Accounts](06d-gui-accounts.md), [Domain Model Reference](domain-model-reference.md)

```python
# packages/api/src/zorivest_api/routes/accounts.py

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

account_router = APIRouter(prefix="/api/v1/accounts", tags=["accounts"])

class CreateAccountRequest(BaseModel):
    name: str
    account_type: str  # BROKER | BANK | REVOLVING | INSTALLMENT | IRA | K401
    institution: str
    currency: str = "USD"
    is_tax_advantaged: bool = False
    notes: Optional[str] = None

@account_router.post("", status_code=201)
async def create_account(body: CreateAccountRequest,
                         service=Depends(get_account_service)):
    """Create a new brokerage/bank account."""
    ...

@account_router.get("")
async def list_accounts(service=Depends(get_account_service)):
    """List all accounts."""
    ...

@account_router.get("/{account_id}")
async def get_account(account_id: str,
                      service=Depends(get_account_service)):
    """Get single account details."""
    ...

@account_router.put("/{account_id}")
async def update_account(account_id: str, body: CreateAccountRequest,
                         service=Depends(get_account_service)):
    """Update account details."""
    ...

@account_router.delete("/{account_id}")
async def delete_account(account_id: str,
                         service=Depends(get_account_service)):
    """Delete an account."""
    ...

@account_router.post("/{account_id}/balances")
async def record_balance(account_id: str,
                         balance: float,
                         service=Depends(get_account_service)):
    """Record a balance snapshot for the account."""
    ...
```

## Broker Routes (§1, §2, §24, §25)

```python
# packages/api/src/zorivest_api/routes/brokers.py

broker_router = APIRouter(prefix="/api/v1/brokers", tags=["brokers"])

@broker_router.get("/")
async def list_brokers(service = Depends(get_import_service)):
    """List configured broker adapters with sync status."""
    ...

@broker_router.post("/{broker_id}/sync", status_code=200)
async def sync_broker(broker_id: str, service = Depends(get_import_service)):
    """Trigger full account sync from broker API."""
    ...

@broker_router.get("/{broker_id}/positions")
async def get_broker_positions(broker_id: str, service = Depends(get_import_service)):
    """Fetch current positions from broker."""
    ...
```

## Banking Routes (§26)

```python
# packages/api/src/zorivest_api/routes/banking.py

banking_router = APIRouter(prefix="/api/v1/banking", tags=["banking"])

@banking_router.post("/import")
async def import_bank_statement(file: UploadFile = File(...),
                                 account_id: str = Form(...),
                                 format_hint: str = Form("auto"),
                                 service = Depends(get_import_service)):
    """Import bank statement file (CSV, OFX, QIF). Returns import summary."""
    ...

@banking_router.get("/accounts")
async def list_bank_accounts(service = Depends(get_import_service)):
    """List bank accounts with balance and last updated."""
    ...

@banking_router.post("/transactions")
async def submit_bank_transactions(body: list,
                                    service = Depends(get_import_service)):
    """Submit bank transactions (agent bypass path)."""
    ...

@banking_router.put("/accounts/{account_id}/balance")
async def update_bank_balance(account_id: str, body: dict,
                               service = Depends(get_import_service)):
    """Manual balance update for bank account."""
    ...
```

## Import Routes (§18, §19)

```python
# packages/api/src/zorivest_api/routes/import_.py

import_router = APIRouter(prefix="/api/v1/import", tags=["import"])

@import_router.post("/csv")
async def import_broker_csv(file: UploadFile = File(...),
                             broker_hint: str = Form("auto"),
                             account_id: str = Form(...),
                             service = Depends(get_import_service)):
    """Import broker CSV file. Auto-detects broker format."""
    ...

@import_router.post("/pdf")
async def import_broker_pdf(file: UploadFile = File(...),
                              account_id: str = Form(...),
                              service = Depends(get_import_service)):
    """Import broker PDF statement. Extracts tables via pdfplumber."""
    ...
```

## Identifier Resolution (§5)

```python
# packages/api/src/zorivest_api/routes/identifiers.py

from fastapi import APIRouter, Depends
from zorivest_core.services.market_data_service import MarketDataService

identifiers_router = APIRouter(prefix="/api/v1/identifiers", tags=["accounts"])

@identifiers_router.post("/resolve")
async def resolve_identifiers(body: dict,
                               service = Depends(get_market_data_service)):
    """Batch resolve ticker/CUSIP/ISIN identifiers.
    Input: {"identifiers": ["AAPL", "US0378331005", "037833100"]}
    Returns: list of resolved records with canonical ticker, CUSIP, ISIN, name, exchange.
    """
    return service.resolve_identifiers(body.get("identifiers", []))
```

## Consumer Notes

- **MCP tools:** `sync_broker`, `import_broker_csv`, `import_broker_pdf` ([05f](05f-mcp-accounts.md)), `disconnect_market_provider` ([05e](05e-mcp-market-data.md))
- **GUI pages:** [06d-gui-accounts.md](06d-gui-accounts.md) — account list, broker sync, import wizard
