# packages/infrastructure/src/zorivest_infra/database/wash_sale_models.py
"""SQLAlchemy ORM models for wash sale chain tracking.

MEU-130 AC-130.9: WashSaleChainModel + WashSaleEntryModel.
Source: domain-model-reference.md B1, B2.
"""

from __future__ import annotations

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
)
from sqlalchemy.orm import relationship

from zorivest_infra.database.models import Base


class WashSaleChainModel(Base):
    """Wash sale chain — tracks a disallowed loss through its lifecycle.

    MEU-130 AC-130.9. 8 stored columns.
    """

    __tablename__ = "wash_sale_chains"
    __table_args__ = (
        Index("ix_ws_chains_ticker", "ticker"),
        Index("ix_ws_chains_status", "status"),
    )

    chain_id = Column(String, primary_key=True)
    ticker = Column(String, nullable=False)
    loss_lot_id = Column(String, nullable=False)  # FK logical ref to tax_lots.lot_id
    loss_date = Column(DateTime, nullable=False)
    loss_amount = Column(Numeric(15, 6), nullable=False)
    disallowed_amount = Column(Numeric(15, 6), nullable=False)
    status = Column(String(20), nullable=False)  # WashSaleStatus
    loss_open_date = Column(
        DateTime, nullable=True
    )  # For holding period tacking (AC-131.4)

    entries = relationship(
        "WashSaleEntryModel",
        back_populates="chain",
        cascade="all, delete-orphan",
        order_by="WashSaleEntryModel.event_date",
    )


class WashSaleEntryModel(Base):
    """Single event in a wash sale chain's audit trail.

    MEU-130 AC-130.9. 7 stored columns.
    """

    __tablename__ = "wash_sale_entries"
    __table_args__ = (Index("ix_ws_entries_chain_id", "chain_id"),)

    entry_id = Column(String, primary_key=True)
    chain_id = Column(String, ForeignKey("wash_sale_chains.chain_id"), nullable=False)
    event_type = Column(String(30), nullable=False)  # WashSaleEventType
    lot_id = Column(String, nullable=False)
    amount = Column(Numeric(15, 6), nullable=False)
    event_date = Column(DateTime, nullable=False)
    account_id = Column(String, nullable=False)

    chain = relationship("WashSaleChainModel", back_populates="entries")
