# MEU Registry — Phase 1 + 1A + 2

> Source: [BUILD_PLAN.md](../docs/BUILD_PLAN.md) | [build-priority-matrix.md](../docs/build-plan/build-priority-matrix.md)

## Phase 1: Domain Layer (P0)

| MEU | Slug | Matrix | Description | Status |
|-----|------|:------:|-------------|:------:|
| MEU-1 | `calculator` | 1 | Position size calculator (pure math) | ✅ approved |
| MEU-2 | `enums` | 2 | All domain enums (AccountType, TradeAction, etc.) | ✅ approved |
| MEU-3 | `entities` | 3 | Domain entities (Trade, Account, Image, BalanceSnapshot) | ✅ approved |
| MEU-4 | `value-objects` | 4 | Value objects (Money, PositionSize, Ticker, ImageData, Conviction) | ✅ approved |
| MEU-5 | `ports` | 5 | Port interfaces (Protocols) | ✅ approved |
| MEU-6 | `commands-dtos` | 6 | Commands & DTOs | ✅ approved |
| MEU-7 | `events` | 7 | Domain events | ✅ approved |
| MEU-8 | `analytics` | 8 | Pure analytics functions + result types | ✅ approved |
| MEU-9 | `portfolio-balance` | 3a | TotalPortfolioBalance pure fn (sum latest balances) | ✅ approved |
| MEU-10 | `display-mode` | 3b | DisplayMode service ($, %, mask fns) | ✅ approved |
| MEU-11 | `account-review` | 3c | Account Review workflow (guided balance update) | ✅ approved |

## Phase 1A: Logging Infrastructure (P0 — Parallel)

| MEU | Slug | Matrix | Description | Status |
|-----|------|:------:|-------------|:------:|
| MEU-1A | `logging-manager` | 1A | LoggingManager, QueueHandler/Listener, JSONL | ✅ approved |
| MEU-2A | `logging-filters` | 1A | FeatureFilter, CatchallFilter + JsonFormatter | ✅ approved |
| MEU-3A | `logging-redaction` | 1A | RedactionFilter (API key masking, PII redaction) | ✅ approved |

## Phase 2: Infrastructure (P0)

| MEU | Slug | Matrix | Description | Status |
|-----|------|:------:|-------------|:------:|
| MEU-12 | `service-layer` | 6 | Core services (Trade, Account, Image, System) + domain exceptions + trade fingerprint | ✅ approved |
| MEU-13 | `sqlalchemy-models` | 7 | All 21 SQLAlchemy ORM models | ✅ approved |
| MEU-14 | `repositories` | 8 | Repository implementations (Trade, Image, Account, BalanceSnapshot, RoundTrip) | ✅ approved |
| MEU-15 | `unit-of-work` | 9 | SqlAlchemyUnitOfWork (5 repos) + WAL engine factory | ✅ approved |
| MEU-16 | `sqlcipher` | 10 | SQLCipher encrypted connection + Argon2/PBKDF2 KDF | ✅ approved |

## Execution Order

Phase 1: MEU-1 → MEU-2 → MEU-3 → MEU-4 → MEU-5 → MEU-6 → MEU-7 → MEU-8 → MEU-9 → MEU-10 → MEU-11
Phase 1A: MEU-2A → MEU-3A → MEU-1A (dependency order, parallel with Phase 1)
Phase 2: MEU-12 → MEU-13 → MEU-14 → MEU-15 → MEU-16

## Phase-Exit Criteria

- Phase 1: All 11 MEUs ✅ + `.\tools\validate.ps1` passes → Phase 2 unblocked
- Phase 1A: All 3 MEUs ✅ → logging available for outer-layer modules
- Phase 2: All 5 MEUs ✅ → Phase 2A unblocked
