"""Zorivest service layer — orchestrates domain logic through UoW.

MEU-12 delivers four services per build-priority-matrix item 6:
- TradeService: trade lifecycle, dedup, round-trip matching
- AccountService: account CRUD, balance snapshots
- ImageService: chart/screenshot attach, retrieve, thumbnail
- SystemService: calculator wrapper

Phase 3A adds:
- TaxService: tax lot lifecycle, gains, carryforward, option pairing, YTD P&L
"""

from zorivest_core.services.account_service import AccountService
from zorivest_core.services.image_service import ImageService
from zorivest_core.services.system_service import SystemService
from zorivest_core.services.tax_service import TaxService
from zorivest_core.services.trade_service import TradeService

__all__ = [
    "AccountService",
    "ImageService",
    "SystemService",
    "TaxService",
    "TradeService",
]
