"""Tests for MarketProviderSettingsRepository — MEU-60 (AC-28/29/30).

Isolated repository CRUD tests using in-memory SQLite.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from zorivest_infra.database.models import Base, MarketProviderSettingModel
from zorivest_infra.database.repositories import SqlMarketProviderSettingsRepository


def _make_session() -> Session:
    """Create an in-memory SQLite session with tables."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


class TestMarketProviderSettingsRepoCRUD:
    """AC-28/29/30: Repository CRUD operations."""

    def test_save_and_get_round_trip(self) -> None:
        session = _make_session()
        repo = SqlMarketProviderSettingsRepository(session)
        model = MarketProviderSettingModel(
            provider_name="Alpha Vantage",
            encrypted_api_key="ENC:abc123",
            rate_limit=5,
            timeout=30,
            is_enabled=True,
            created_at=datetime.now(),
        )
        repo.save(model)
        session.commit()

        result = repo.get("Alpha Vantage")
        assert result is not None
        assert result.provider_name == "Alpha Vantage"
        assert result.encrypted_api_key == "ENC:abc123"
        assert result.is_enabled is True

    def test_get_unknown_returns_none(self) -> None:
        session = _make_session()
        repo = SqlMarketProviderSettingsRepository(session)
        assert repo.get("NonexistentProvider") is None

    def test_list_all_returns_all(self) -> None:
        session = _make_session()
        repo = SqlMarketProviderSettingsRepository(session)
        for name in ["Alpha Vantage", "Finnhub", "Tradier"]:
            repo.save(
                MarketProviderSettingModel(
                    provider_name=name,
                    rate_limit=5,
                    timeout=30,
                    is_enabled=False,
                    created_at=datetime.now(),
                )
            )
        session.commit()

        result = repo.list_all()
        assert len(result) == 3
        names = {m.provider_name for m in result}
        assert names == {"Alpha Vantage", "Finnhub", "Tradier"}

    def test_delete_removes_entry(self) -> None:
        session = _make_session()
        repo = SqlMarketProviderSettingsRepository(session)
        repo.save(
            MarketProviderSettingModel(
                provider_name="Finnhub",
                rate_limit=60,
                timeout=30,
                is_enabled=True,
                created_at=datetime.now(),
            )
        )
        session.commit()

        repo.delete("Finnhub")
        session.commit()
        assert repo.get("Finnhub") is None

    def test_delete_nonexistent_is_noop(self) -> None:
        session = _make_session()
        repo = SqlMarketProviderSettingsRepository(session)
        repo.delete("NonexistentProvider")  # Should not raise

    def test_save_updates_existing(self) -> None:
        session = _make_session()
        repo = SqlMarketProviderSettingsRepository(session)
        repo.save(
            MarketProviderSettingModel(
                provider_name="Tradier",
                rate_limit=120,
                timeout=30,
                is_enabled=False,
                created_at=datetime.now(),
            )
        )
        session.commit()

        # Update
        model = repo.get("Tradier")
        assert model is not None
        model.is_enabled = True
        repo.save(model)
        session.commit()

        updated = repo.get("Tradier")
        assert updated is not None
        assert updated.is_enabled is True
