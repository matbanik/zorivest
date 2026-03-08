# Proposed Commit Messages — infra-services (MEU 12–16)

## Per-MEU commits

```
feat: add domain exception hierarchy and trade fingerprint (MEU-12 prereqs)

feat: implement service layer — Trade, Account, Image, System services (MEU-12)

feat: add 21 SQLAlchemy ORM models per database schema spec (MEU-13)

feat: implement 5 SQLAlchemy repository classes with entity mapping (MEU-14)

feat: add SqlAlchemyUnitOfWork with WAL engine factory (MEU-15)

feat: add SQLCipher connection factory with Argon2/PBKDF2 key derivation (MEU-16)
```

## Single squash commit (alternative)

```
feat: implement infrastructure layer — services, ORM, repos, UoW, SQLCipher (MEU 12-16)

- Service layer: TradeService, AccountService, ImageService, SystemService
- Domain: 6 exception classes, SHA-256 trade fingerprint
- Ports: 3 new repo Protocols, UoW extended with 3 attrs
- ORM: 21 SQLAlchemy models (Numeric(15,6) for financials)
- Repos: Trade, Image, Account, BalanceSnapshot, RoundTrip
- UoW: SqlAlchemyUnitOfWork + create_engine_with_wal
- SQLCipher: derive_key (Argon2/PBKDF2), encrypted connection
- Tests: 67 pass (unit + integration)
```
