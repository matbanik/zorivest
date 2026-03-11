"""Concrete SQLAlchemy repository implementations.

Source: 02-infrastructure.md §2.2
Implements: ports.TradeRepository, ImageRepository, AccountRepository,
            BalanceSnapshotRepository, RoundTripRepository,
            SettingsRepository, AppDefaultsRepository
"""

# pyright: reportArgumentType=false, reportReturnType=false, reportGeneralTypeIssues=false, reportAttributeAccessIssue=false
# SQLAlchemy Column[T] types are not directly assignable to T at type-check time,
# but are correctly resolved to T at runtime. This is a known pyright limitation.

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from zorivest_core.domain.entities import (
    Account,
    BalanceSnapshot,
    ImageAttachment,
    Trade,
)
from zorivest_core.domain.enums import (
    AccountType,
    BalanceSource,
    ImageOwnerType,
    TradeAction,
)
from zorivest_core.domain.market_provider_settings import MarketProviderSettings
from zorivest_infra.database.models import (
    AccountModel,
    AppDefaultModel,
    BalanceSnapshotModel,
    ImageModel,
    MarketProviderSettingModel,
    RoundTripModel,
    SettingModel,
    TradeModel,
)


# ── Mapping helpers ─────────────────────────────────────────────────────


def _trade_to_model(trade: Trade) -> TradeModel:
    return TradeModel(
        exec_id=trade.exec_id,
        time=trade.time,
        instrument=trade.instrument,
        action=trade.action.value,
        quantity=trade.quantity,
        price=trade.price,
        account_id=trade.account_id,
        commission=trade.commission,
        realized_pnl=trade.realized_pnl,
    )


def _model_to_trade(m: TradeModel) -> Trade:
    return Trade(
        exec_id=m.exec_id,
        time=m.time,
        instrument=m.instrument,
        action=TradeAction(m.action),
        quantity=float(m.quantity),
        price=float(m.price),
        account_id=m.account_id,
        commission=float(m.commission or 0),
        realized_pnl=float(m.realized_pnl or 0),
    )


def _account_to_model(account: Account) -> AccountModel:
    return AccountModel(
        account_id=account.account_id,
        name=account.name,
        account_type=account.account_type.value,
        institution=account.institution or None,
        currency=account.currency,
        is_tax_advantaged=account.is_tax_advantaged,
        notes=account.notes or None,
        created_at=datetime.now(),
    )


def _model_to_account(m: AccountModel) -> Account:
    return Account(
        account_id=m.account_id,
        name=m.name,
        account_type=AccountType(m.account_type),
        institution=m.institution or "",
        currency=m.currency or "USD",
        is_tax_advantaged=bool(m.is_tax_advantaged),
        notes=m.notes or "",
        balance_source=BalanceSource.MANUAL,
    )


def _model_to_image(m: ImageModel) -> ImageAttachment:
    return ImageAttachment(
        id=m.id,
        owner_type=ImageOwnerType(m.owner_type),
        owner_id=m.owner_id,
        data=m.data,
        width=m.width or 0,
        height=m.height or 0,
        file_size=m.file_size or 0,
        created_at=m.created_at,
        thumbnail=m.thumbnail or b"",
        mime_type=m.mime_type or "image/webp",
        caption=m.caption or "",
    )


def _model_to_snapshot(m: BalanceSnapshotModel) -> BalanceSnapshot:
    from decimal import Decimal

    return BalanceSnapshot(
        id=m.id,
        account_id=m.account_id,
        datetime=m.datetime,
        balance=Decimal(str(m.balance)),
    )


# ── Repository Implementations ──────────────────────────────────────────


class SqlAlchemyTradeRepository:
    """Concrete TradeRepository backed by SQLAlchemy Session."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, exec_id: str) -> Trade | None:
        m = self._session.get(TradeModel, exec_id)
        return _model_to_trade(m) if m else None

    def save(self, trade: Trade) -> None:
        self._session.add(_trade_to_model(trade))

    def list_all(self, limit: int = 100, offset: int = 0) -> list[Trade]:
        rows = (
            self._session.query(TradeModel)
            .order_by(TradeModel.time.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return [_model_to_trade(r) for r in rows]

    def exists(self, exec_id: str) -> bool:
        return self._session.get(TradeModel, exec_id) is not None

    def exists_by_fingerprint_since(
        self, fingerprint: str, lookback_days: int = 30
    ) -> bool:
        """Check existence by scanning trades in lookback window.

        Note: For production, a fingerprint column + index would be more
        efficient. This scan-based approach works for correctness.
        """
        from zorivest_core.domain.trades.identity import trade_fingerprint

        cutoff = datetime.now() - timedelta(days=lookback_days)
        recent = (
            self._session.query(TradeModel)
            .filter(TradeModel.time >= cutoff)
            .all()
        )
        for m in recent:
            trade = _model_to_trade(m)
            if trade_fingerprint(trade) == fingerprint:
                return True
        return False

    def list_for_account(self, account_id: str) -> list[Trade]:
        rows = (
            self._session.query(TradeModel)
            .filter(TradeModel.account_id == account_id)
            .order_by(TradeModel.time.asc())
            .all()
        )
        return [_model_to_trade(r) for r in rows]

    def list_filtered(
        self,
        limit: int = 100,
        offset: int = 0,
        account_id: str | None = None,
        sort: str = "-time",
    ) -> list[Trade]:
        """List trades with optional account filter and sort.

        Sort format: field name with optional '-' prefix for descending.
        Supported fields: time (default).
        """
        query = self._session.query(TradeModel)
        if account_id is not None:
            query = query.filter(TradeModel.account_id == account_id)

        # Parse sort direction
        if sort.startswith("-"):
            order_col = getattr(TradeModel, sort[1:], TradeModel.time)
            query = query.order_by(order_col.desc())
        else:
            order_col = getattr(TradeModel, sort, TradeModel.time)
            query = query.order_by(order_col.asc())

        rows = query.offset(offset).limit(limit).all()
        return [_model_to_trade(r) for r in rows]

    def update(self, trade: Trade) -> None:
        """Update existing trade via merge (upsert-safe)."""
        self._session.merge(_trade_to_model(trade))

    def delete(self, exec_id: str) -> None:
        """Delete a trade by exec_id."""
        m = self._session.get(TradeModel, exec_id)
        if m:
            self._session.delete(m)


class SqlAlchemyImageRepository:
    """Concrete ImageRepository backed by SQLAlchemy Session."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, owner_type: str, owner_id: str, image: ImageAttachment) -> int:
        m = ImageModel(
            owner_type=owner_type,
            owner_id=owner_id,
            data=image.data,
            thumbnail=image.thumbnail or None,
            mime_type=image.mime_type,
            caption=image.caption or None,
            width=image.width,
            height=image.height,
            file_size=image.file_size,
            created_at=image.created_at,
        )
        self._session.add(m)
        self._session.flush()  # assign id
        return m.id

    def get(self, image_id: int) -> ImageAttachment | None:
        m = self._session.get(ImageModel, image_id)
        return _model_to_image(m) if m else None

    def get_for_owner(
        self, owner_type: str, owner_id: str
    ) -> list[ImageAttachment]:
        rows = (
            self._session.query(ImageModel)
            .filter(ImageModel.owner_type == owner_type, ImageModel.owner_id == owner_id)
            .all()
        )
        return [_model_to_image(r) for r in rows]

    def delete(self, image_id: int) -> None:
        m = self._session.get(ImageModel, image_id)
        if m:
            self._session.delete(m)

    def get_thumbnail(self, image_id: int, max_size: int = 200) -> bytes:
        m = self._session.get(ImageModel, image_id)
        if m is None:
            return b""
        # Return stored thumbnail if available, otherwise return truncated data
        if m.thumbnail:
            return m.thumbnail
        return m.data[:max_size] if m.data else b""

    def get_full_data(self, image_id: int) -> bytes:
        """Return raw image bytes without thumbnail processing."""
        m = self._session.get(ImageModel, image_id)
        if m is None:
            return b""
        return m.data if m.data else b""


class SqlAlchemyAccountRepository:
    """Concrete AccountRepository backed by SQLAlchemy Session."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, account_id: str) -> Account | None:
        m = self._session.get(AccountModel, account_id)
        return _model_to_account(m) if m else None

    def save(self, account: Account) -> None:
        self._session.add(_account_to_model(account))

    def list_all(self, limit: int = 100, offset: int = 0) -> list[Account]:
        rows = (
            self._session.query(AccountModel)
            .offset(offset)
            .limit(limit)
            .all()
        )
        return [_model_to_account(r) for r in rows]

    def update(self, account: Account) -> None:
        """Update existing account via merge (upsert-safe)."""
        self._session.merge(_account_to_model(account))

    def delete(self, account_id: str) -> None:
        """Delete an account by account_id."""
        m = self._session.get(AccountModel, account_id)
        if m:
            self._session.delete(m)


class SqlAlchemyBalanceSnapshotRepository:
    """Concrete BalanceSnapshotRepository backed by SQLAlchemy Session."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, snapshot: BalanceSnapshot) -> None:
        m = BalanceSnapshotModel(
            account_id=snapshot.account_id,
            datetime=snapshot.datetime,
            balance=float(snapshot.balance),
        )
        self._session.add(m)

    def list_for_account(self, account_id: str) -> list[BalanceSnapshot]:
        rows = (
            self._session.query(BalanceSnapshotModel)
            .filter(BalanceSnapshotModel.account_id == account_id)
            .order_by(BalanceSnapshotModel.datetime.desc())
            .all()
        )
        return [_model_to_snapshot(r) for r in rows]


class SqlAlchemyRoundTripRepository:
    """Concrete RoundTripRepository backed by SQLAlchemy Session.

    Uses Any for entity type since RoundTrip entity is Phase 3.
    Stores/retrieves dict-based round trips via RoundTripModel.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, round_trip: Any) -> None:
        if isinstance(round_trip, dict):
            m = RoundTripModel(
                account_id=round_trip.get("account_id", ""),
                instrument=round_trip.get("instrument", ""),
                direction=round_trip.get("direction", "BOT"),
                entry_exec_ids=json.dumps(round_trip.get("trades", [])),
                exit_exec_ids=None,
                entry_avg_price=0.0,
                total_quantity=0.0,
                opened_at=datetime.now(),
                status="open",
            )
            self._session.add(m)
        else:
            # Future: accept RoundTrip entity directly
            self._session.add(round_trip)

    def list_for_account(
        self, account_id: str, status: str | None = None
    ) -> list[Any]:
        query = self._session.query(RoundTripModel).filter(
            RoundTripModel.account_id == account_id
        )
        if status is not None:
            query = query.filter(RoundTripModel.status == status)
        return list(query.all())


class SqlAlchemySettingsRepository:
    """Concrete SettingsRepository backed by SQLAlchemy Session.

    Operates on `settings` table (SettingModel): user-level key/value overrides.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, key: str) -> SettingModel | None:
        return self._session.get(SettingModel, key)

    def get_all(self) -> list[SettingModel]:
        return list(self._session.query(SettingModel).all())

    def bulk_upsert(self, settings: dict[str, Any]) -> None:
        from datetime import datetime as dt

        for k, v in settings.items():
            existing = self._session.get(SettingModel, k)
            if existing:
                existing.value = str(v)
                existing.updated_at = dt.now()
            else:
                self._session.add(
                    SettingModel(key=k, value=str(v), value_type="str", updated_at=dt.now())
                )

    def delete(self, key: str) -> None:
        m = self._session.get(SettingModel, key)
        if m:
            self._session.delete(m)


class SqlAlchemyAppDefaultsRepository:
    """Concrete AppDefaultsRepository backed by SQLAlchemy Session.

    Read-only access to `app_defaults` table (AppDefaultModel).
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, key: str) -> AppDefaultModel | None:
        return self._session.get(AppDefaultModel, key)

    def get_all(self) -> list[AppDefaultModel]:
        return list(self._session.query(AppDefaultModel).all())


# ── Market Provider Settings Mapping ────────────────────────────────────


def _setting_to_model(s: MarketProviderSettings) -> MarketProviderSettingModel:
    return MarketProviderSettingModel(
        provider_name=s.provider_name,
        encrypted_api_key=s.encrypted_api_key,
        encrypted_api_secret=s.encrypted_api_secret,
        rate_limit=s.rate_limit,
        timeout=s.timeout,
        is_enabled=s.is_enabled,
        last_tested_at=s.last_tested_at,
        last_test_status=s.last_test_status,
        created_at=s.created_at,
        updated_at=s.updated_at,
    )


def _model_to_setting(m: MarketProviderSettingModel) -> MarketProviderSettings:
    return MarketProviderSettings(
        provider_name=m.provider_name,
        encrypted_api_key=m.encrypted_api_key,
        encrypted_api_secret=m.encrypted_api_secret,
        rate_limit=m.rate_limit or 5,
        timeout=m.timeout or 30,
        is_enabled=bool(m.is_enabled),
        last_tested_at=m.last_tested_at,
        last_test_status=m.last_test_status,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


class SqlMarketProviderSettingsRepository:
    """Concrete MarketProviderSettingsRepository backed by SQLAlchemy Session.

    Maps between core ``MarketProviderSettings`` and ORM ``MarketProviderSettingModel``.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, provider_name: str) -> MarketProviderSettings | None:
        m = self._session.get(MarketProviderSettingModel, provider_name)
        return _model_to_setting(m) if m else None

    def save(self, settings: MarketProviderSettings) -> None:
        self._session.merge(_setting_to_model(settings))

    def list_all(self) -> list[MarketProviderSettings]:
        rows = self._session.query(MarketProviderSettingModel).all()
        return [_model_to_setting(r) for r in rows]

    def delete(self, provider_name: str) -> None:
        m = self._session.get(MarketProviderSettingModel, provider_name)
        if m:
            self._session.delete(m)

