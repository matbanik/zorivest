# Commit Messages — Market Data Foundation

## Commit 1: MEU-56/57/58 implementation

```
feat(core,infra): market data foundation (MEU-56/57/58)

Domain:
- AuthMethod StrEnum (4 members) in enums.py
- ProviderConfig frozen dataclass in domain/market_data.py
- MarketDataPort Protocol with typed DTO returns in ports.py

Application:
- MarketQuote, MarketNewsItem, TickerSearchResult, SecFiling
  Pydantic DTOs in application/market_dtos.py

Infrastructure:
- api_key_encryption.py: Fernet encrypt/decrypt + PBKDF2 480K
- encrypted_api_secret column on MarketProviderSettingModel
- security/ subpackage

Dependencies:
- pydantic>=2.0 (core), cryptography>=44.0.0 (infra)

Tests: 48 new (20 + 16 + 10 + 2 model)
Integrity: enums 14→15, ports 11→12
Regression: 696 passed, 1 skipped
```

## Commit 2: validator fix

```
fix(tools): validate_codebase.py TypeScript cwd + Windows shell

- TS checks now gated on tsconfig.json presence
- Run tsc/eslint/vitest from each TS project directory
- shell=True on Windows for npx.cmd resolution
```

## Commit 3: project artifacts

```
docs: market data foundation project closeout

- Handoffs 044/045/046 with correction rounds
- BUILD_PLAN: Phase 5 ✅, Phase 8 🟡, MEU-56/57/58 ✅
- meu-registry: Phase 8 section added
- Reflection, metrics, session state
```
