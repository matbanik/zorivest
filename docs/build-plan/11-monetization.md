# Phase 11: Monetization

> Part of [Zorivest Build Plan](../BUILD_PLAN.md) | Prerequisites: [Phase 2](02-infrastructure.md) (encryption), [Phase 4](04-rest-api.md) (REST API), [Phase 8](08-market-data.md) (API key infrastructure) | Outputs: Subscription enforcement, OAuth, Google integrations

---

## Goal

Add subscription infrastructure, license enforcement, OAuth integration, and usage metering to support a sustainable business model. All monetization respects the ethical baseline: local data is never held hostage, and BYOK AI keys are a permanent first-class feature.

### Design Principles

1. **License check in Python backend** — Not renderer localStorage; closes bypass vulnerability
2. **BYOK as permanent feature** — Users who bring their own AI provider keys are never locked out of AI features
3. **Never lock data behind lapsed subscription** — Read-only degradation, never data hostage
4. **Paddle + Keygen stack** — Not LemonSqueezy (acquisition uncertainty)
5. **No Lifetime SKU** — Subscription tiers only (Free / Pro / Team)

---

## 11.1: Subscription Domain

### Tier Architecture

| Tier | Price | Key Limits |
|------|-------|-----------|
| **Free** | $0 | 1 account, 50 trades/mo, 10 AI reviews/mo, basic dashboards |
| **Pro** | $19/mo or $179/yr | Unlimited trades, 3 accounts, 100 AI reviews OR unlimited BYOK, PDF OCR, TLH, cloud sync |
| **Team** | $39/user/mo | Pro + 10 seats, shared library, SSO, audit log |

### Permanently Free (Ethical Baseline)

- Local trade storage & import
- Basic performance dashboards
- CSV import/export (GDPR Article 20)
- Full data access regardless of subscription
- Position size calculator
- Manual trade entry & editing
- Basic analytics (win rate, P&L summary)

### Domain Entities

```python
# packages/core/src/zorivest_core/domain/monetization/

class SubscriptionTier(StrEnum):
    FREE = "free"
    PRO = "pro"
    TEAM = "team"

@dataclass
class License:
    """Ed25519-signed JWT license token."""
    id: str
    user_email: str
    tier: SubscriptionTier
    issued_at: datetime
    expires_at: datetime
    device_id: str
    signature: bytes  # Ed25519
    features: frozenset[str]  # Explicit feature grants

@dataclass
class UsageMeter:
    """Track per-period resource consumption."""
    id: str
    license_id: str
    period_start: date
    period_end: date
    trades_created: int = 0
    ai_reviews_used: int = 0
    pdf_ocr_pages: int = 0
    api_calls: int = 0
```

---

## 11.2: OAuth Integration — Google

### Google OAuth PKCE Flow

```
Electron Main Process                 Google Auth Server
────────────────────                 ────────────────────
1. Generate code_verifier + code_challenge (S256)
2. Open BrowserWindow → accounts.google.com/o/oauth2/v2/auth
   ├── client_id (public)
   ├── redirect_uri: http://localhost:{random_port}/callback
   ├── scope: calendar.events tasks openid email
   ├── code_challenge + code_challenge_method=S256
   └── response_type: code

3. User authenticates → redirect to localhost callback
4. Exchange auth code + code_verifier for tokens
5. Store tokens encrypted (existing Phase 2 Fernet pattern)
6. Start refresh timer (expires_in - 300s buffer)
```

### Token Storage

```python
# Reuses existing Phase 8 encryption pattern (MarketProviderSettingModel)
# Stored in settings table via SettingsResolver

OAUTH_SETTINGS = {
    "oauth.google.access_token": "encrypted",     # Fernet-encrypted
    "oauth.google.refresh_token": "encrypted",     # Fernet-encrypted
    "oauth.google.token_expiry": "datetime",
    "oauth.google.scopes": "list[str]",
    "oauth.google.user_email": "str",
}
```

---

## 11.3: Google Calendar & Tasks Integration

### Trade Plan Reminders → Google Calendar

```python
# packages/core/src/zorivest_core/services/google_calendar_service.py

class GoogleCalendarService:
    """Create/update/delete calendar events for TradePlan reminders."""

    async def create_plan_reminder(
        self, plan: TradePlan, reminder_minutes: int = 30
    ) -> str:
        """Create a Google Calendar event for a trade plan entry window."""
        event = {
            "summary": f"📈 {plan.ticker} — {plan.strategy_name}",
            "description": f"Conviction: {plan.conviction}\nEntry: {plan.entry_price}",
            "start": {"dateTime": plan.entry_window_start.isoformat()},
            "end": {"dateTime": plan.entry_window_end.isoformat()},
            "reminders": {
                "useDefault": False,
                "overrides": [{"method": "popup", "minutes": reminder_minutes}],
            },
        }
        # POST to Google Calendar API v3
        return await self._create_event(event)

    async def delete_plan_reminder(self, event_id: str) -> None:
        """Remove calendar event when plan is cancelled/executed."""
        await self._delete_event(event_id)
```

### Watchlist Actions → Google Tasks

```python
class GoogleTasksService:
    """Create task items for watchlist review actions."""

    async def create_watchlist_task(
        self, ticker: str, action: str, notes: str | None = None
    ) -> str:
        """Create a Google Tasks item for a watchlist action."""
        task = {
            "title": f"Review {ticker}: {action}",
            "notes": notes or "",
            "due": (datetime.now() + timedelta(days=1)).isoformat() + "Z",
        }
        return await self._create_task(task)
```

---

## 11.4: License Enforcement

### Ed25519 JWT Validation

```python
# packages/core/src/zorivest_core/services/license_service.py

import nacl.signing  # PyNaCl — Ed25519

class LicenseService:
    """Validate license JWTs using Ed25519 public key verification."""

    PUBLIC_KEY = b"..."  # Embedded Ed25519 verify key (32 bytes)

    def validate_license(self, token: str) -> License:
        """Verify JWT signature, decode claims, check expiry."""
        # 1. Split JWT header.payload.signature
        # 2. Verify Ed25519 signature against PUBLIC_KEY
        # 3. Decode claims → License entity
        # 4. Check: not expired, device_id matches, tier valid
        ...

    def get_current_tier(self) -> SubscriptionTier:
        """Return current tier, accounting for offline grace."""
        license = self._load_cached_license()
        if license is None:
            return SubscriptionTier.FREE
        if self._is_in_grace_period(license):
            return license.tier  # Honor tier during grace
        if license.expires_at < datetime.now(tz=UTC):
            return SubscriptionTier.FREE
        return license.tier
```

### Offline Grace Period

| Phase | Duration | Behavior |
|-------|----------|----------|
| **Soft grace** | Days 1–14 | Full Pro/Team features. Banner: "License check pending" |
| **Hard grace** | Days 15–30 | Features locked to Free tier. Banner: "Connect to verify license" |
| **Expired** | Day 31+ | Treated as Free tier. Data fully accessible (read-only degradation) |

### Device Binding

- `device_id` = SHA-256 of machine-specific identifiers (hostname + OS serial + install path)
- License bound to device on first activation
- Transfer requires deactivation on old device + reactivation on new device
- Maximum 2 concurrent device activations per license

---

## 11.5: BYOK AI Providers

> **BYOK = Bring Your Own Key.** Users supply their own API keys for AI providers. This extends the Phase 8 encrypted API key pattern.

### Key Management

```python
# Extends existing MarketProviderSettingModel pattern

class AIProviderKeyModel(Base):
    """Encrypted AI provider API keys (BYOK)."""
    __tablename__ = "ai_provider_keys"

    id: str
    provider: str           # "openai", "anthropic", "google"
    encrypted_api_key: str  # Fernet-encrypted
    created_at: datetime
    last_validated: datetime | None
    is_valid: bool
    usage_count: int = 0
```

### Supported Providers

| Provider | Models | Validation Endpoint |
|----------|--------|-------------------|
| OpenAI | GPT-4o, o1 | `GET /v1/models` |
| Anthropic | Claude 3.5/4 | `POST /v1/messages` (tiny prompt) |
| Google | Gemini 2.x | `POST /v1beta/models` |

### Usage Tracking

- BYOK keys bypass the tier's AI review limit (unlimited usage with own keys)
- Usage is tracked for analytics (not billing)
- Keys are validated on save and periodically (every 24h)

---

## 11.6: Usage Metering

### Counter Implementation

```python
class UsageMeteringService:
    """Track and enforce tier usage limits."""

    def check_limit(self, meter: UsageMeter, resource: str) -> bool:
        """Return True if the user has remaining quota."""
        tier = self._license_service.get_current_tier()
        limit = TIER_LIMITS[tier][resource]
        if limit is None:  # Unlimited
            return True
        return getattr(meter, resource) < limit

    def increment(self, meter: UsageMeter, resource: str, amount: int = 1) -> None:
        """Increment usage counter. Raises QuotaExceeded if over limit."""
        if not self.check_limit(meter, resource):
            raise QuotaExceeded(resource=resource, tier=meter.tier)
        setattr(meter, resource, getattr(meter, resource) + amount)
```

### Tier Limits

```python
TIER_LIMITS = {
    SubscriptionTier.FREE: {
        "accounts": 1,
        "trades_per_month": 50,
        "ai_reviews_per_month": 10,
        "pdf_ocr_pages_per_month": 0,
    },
    SubscriptionTier.PRO: {
        "accounts": 3,
        "trades_per_month": None,  # Unlimited
        "ai_reviews_per_month": 100,  # Or unlimited with BYOK
        "pdf_ocr_pages_per_month": 500,
    },
    SubscriptionTier.TEAM: {
        "accounts": None,  # Unlimited
        "trades_per_month": None,
        "ai_reviews_per_month": None,
        "pdf_ocr_pages_per_month": None,
    },
}
```

### Approach-to-Limit UX

| Usage % | Indicator | User Action |
|---------|-----------|-------------|
| 0–80% | Green meter bar | None |
| 80–95% | Yellow meter bar + banner | "Approaching limit" |
| 95–100% | Red meter bar + modal | "Upgrade" or "Add BYOK key" |
| 100% | Feature disabled | Clear message: "Limit reached. Upgrade or wait for reset" |

---

## 11.7: REST API Endpoints

```
POST /api/v1/monetization/activate       → Activate license JWT
GET  /api/v1/monetization/license        → Current license status + tier
POST /api/v1/monetization/deactivate     → Deactivate device binding
GET  /api/v1/monetization/usage          → Current period usage meters
POST /api/v1/monetization/oauth/google   → Initiate Google OAuth flow
GET  /api/v1/monetization/oauth/callback → OAuth callback handler
DELETE /api/v1/monetization/oauth/google → Revoke Google OAuth tokens
GET  /api/v1/monetization/byok           → List BYOK provider keys
POST /api/v1/monetization/byok           → Add/validate BYOK key
DELETE /api/v1/monetization/byok/{id}    → Remove BYOK key
```

---

## 11.8: GUI Components

### License Management (Settings > Subscription)

```
┌──────────────────────────────────────────────────────────┐
│  Settings > Subscription                                  │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Current Plan: Pro ($19/mo)                              │
│  Renews: May 15, 2026                                    │
│  Device: Mat-PC (1 of 2 slots)                           │
│                                                          │
│  ── Usage This Period ──────────────────────────          │
│                                                          │
│  Trades:     ████████████████████░░░ 847 / ∞             │
│  AI Reviews: ████████████░░░░░░░░░░ 62 / 100             │
│  PDF OCR:    ██░░░░░░░░░░░░░░░░░░░ 23 / 500 pages       │
│                                                          │
│  ── AI Provider Keys (BYOK) ─────────────────            │
│                                                          │
│  🟢 OpenAI       sk-...4f2a   Last checked: 2h ago      │
│  🟢 Anthropic    sk-...8b1c   Last checked: 2h ago      │
│  [+ Add Provider Key]                                    │
│                                                          │
│  ── Google Integration ──────────────────────             │
│                                                          │
│  🟢 Connected as mat@example.com                         │
│  Calendar reminders: ✅ Enabled                          │
│  Tasks integration:  ✅ Enabled                          │
│  [Disconnect Google]                                     │
│                                                          │
│  [Manage Subscription ↗]  (opens Paddle portal)          │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## 11.9: MCP Tools (Phase 11)

| Tool | Description |
|------|-------------|
| `zorivest_subscription_status` | Returns current tier, usage meters, and days until renewal |
| `zorivest_feature_check` | Check if a specific feature is available for the current tier |

> **No MCP tools for license activation/deactivation** — these are GUI-only operations requiring user interaction (PKCE flow, device confirmation).

---

## 11.10: Test Plan

### Unit Tests (Python)

```python
class TestLicenseService:
    def test_valid_license_returns_correct_tier(self):
        ...

    def test_expired_license_returns_free(self):
        ...

    def test_soft_grace_honors_tier(self):
        ...

    def test_hard_grace_downgrades_to_free(self):
        ...

    def test_invalid_signature_rejects_license(self):
        ...

class TestUsageMeteringService:
    def test_free_tier_50_trade_limit(self):
        ...

    def test_pro_tier_unlimited_trades(self):
        ...

    def test_byok_bypasses_ai_review_limit(self):
        ...

    def test_increment_raises_quota_exceeded(self):
        ...
```

### Integration Tests (Python)

```python
class TestMonetizationAPI:
    async def test_license_status_returns_current_tier(self, client):
        ...

    async def test_usage_endpoint_returns_meters(self, client):
        ...

    async def test_byok_crud_lifecycle(self, authed_client):
        ...
```

---

## Exit Criteria

- License validation via Ed25519 JWT (PyNaCl)
- Offline grace period (14-day soft / 30-day hard) with clear UX indicators
- Google OAuth PKCE flow with encrypted token storage
- Calendar reminders for Trade Plans (create/delete)
- Tasks integration for Watchlist actions
- BYOK API key CRUD with encrypted storage and periodic validation
- Usage metering with approach-to-limit UX (green → yellow → red)
- All permanently-free features accessible regardless of subscription state
- Data never locked behind lapsed subscription (read-only degradation only)

## Outputs

- **Domain**: `SubscriptionTier` enum, `License` entity, `UsageMeter` entity
- **Services**: `LicenseService`, `UsageMeteringService`, `GoogleCalendarService`, `GoogleTasksService`
- **Infrastructure**: `AIProviderKeyModel` (SQLAlchemy), `ai_provider_keys` table
- **REST API**: 11 endpoints under `/api/v1/monetization/`
- **MCP**: 2 tools (`zorivest_subscription_status`, `zorivest_feature_check`)
- **GUI**: Subscription settings page (license, usage, BYOK, Google integration)
- **Dependencies**: `PyNaCl` (Ed25519), `google-auth`, `google-api-python-client`
