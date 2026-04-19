# Monetizing Zorivest without becoming a broker

**Bottom line up front.** Zorivest should ship a three-tier freemium model (Free / Pro / Team) with a *volume-metered* free tier (50 trades and 10 AI reviews per month), BYOK as a permanent pressure-valve on AI features, and a one-time "Lifetime" SKU that no current competitor offers. Licensing should use **Ed25519-signed JWTs with short server-issued expiries plus a 14-day offline grace period**, verified in the Python main process — never in the renderer. For payments, **pair Paddle (merchant-of-record, 5% + $0.50) with Keygen (licensing API, $49/mo) for the first ~$30k MRR**, then reconsider moving to Stripe direct once VAT-compliance labor is worth absorbing. Because Zorivest does not execute trades, the regulatory perimeter is narrow: **no broker-dealer, no RIA, no FINRA, no Reg BI, no MiFID II investment-firm authorization** — only GDPR, general consumer law, and carefully drafted disclaimers apply. The practical risks are copying OpenWhispr's `localStorage`-based subscription checks (trivially bypassed), storing OpenAI keys in the renderer, and over-complying with rules written for entities that hold customer funds.

The rest of this report walks through the design in five parts: tier architecture, BYOK key security, subscription enforcement, referrals/growth, and usage metering — each grounded in what OpenWhispr actually ships, what the regulatory perimeter actually allows, and what a solo developer can realistically build and maintain.

> **Note on source access.** The `matbanik/zorivest` repository and some specific OpenWhispr file paths listed in the brief were not retrievable by the research tooling at the time of this report (likely because the repo is new/unindexed, and `raw.githubusercontent.com` URLs are gated to prior-seen URLs). Patterns cited from OpenWhispr below are drawn from its public README, CHANGELOG, CLAUDE.md, and Mintlify documentation, which describe the features in detail (usage tracking with color-coded thresholds, referral program with 2,000-word completion, Cloud Notes with sync, Stripe billing for Free/Pro/Business). Where exact code is cited, it is marked as illustrative of the pattern rather than verbatim.

---

## 1. What OpenWhispr actually does — and where it leaks

OpenWhispr is the relevant monetization analogue because it ships the same primitives Zorivest needs: a local-first Electron app with a managed-cloud option, BYOK for model providers, usage-metered free tier, Stripe-backed subscriptions, and a referral flywheel. Its public documentation confirms **a 2,000-word/week free cap on Cloud transcription, Pro with unlimited usage, a 7-day free trial, referral rewards of one free Pro month per completed invite where "completed" means the invitee has transcribed ≥2,000 words, and an upgrade dialog at the cap offering three paths: upgrade, BYOK, or switch to local inference**. API keys are stated to be stored in the OS keychain via Electron `safeStorage`, which is the correct pattern; Stripe handles Free/Pro/Business billing and "past-due" state is enforced for Business.

The instructive weakness is the subscription-gate style shown in the brief:

```ts
canSync(): boolean {
  return (
    localStorage.getItem("isSignedIn") === "true" &&
    localStorage.getItem("cloudBackupEnabled") === "true" &&
    localStorage.getItem("isSubscribed") === "true"
  );
}
```

Three strings in localStorage are not a subscription check — they are a suggestion. DevTools can flip them in seconds. For a $15/month transcription utility this is probably fine; the server-side sync endpoint is presumably the real gate. For a financial tool where a cracked "Pro" build would happily run AI reviews against the user's own OpenAI key, the weak check is not sufficient and we replace it below.

## 2. Tier architecture for Zorivest

### The shape of the tiers

Zorivest's feature set splits cleanly into three bands that map onto the retail-trader willingness-to-pay curve observed across TradingView ($13–$200), TraderVue ($30–$50), TradesViz ($15–$23 annual), and Chartlog ($15–$40). The trade-journal category anchors at **$14–20/mo entry, $25–35/mo mid, $40–50/mo power** with ~20% annual discounts, and no competitor currently offers a true desktop-native product or a credit-denominated AI meter. Edgewonk's fading lifetime license leaves that pricing slot unoccupied.

| Tier | Price (2026) | Who it's for | What unlocks |
|---|---|---|---|
| **Free** | $0 | Evaluating / light journalers | 1 connected account, 50 trades/month imported, 10 AI reviews/month (Zorivest-managed or BYOK), manual CSV import, local SQLCipher storage, Monte Carlo (deterministic, no AI narration), basic performance dashboards |
| **Pro** | **$19/mo** or **$179/yr** (saves 21%) | Active retail trader | Unlimited trades imported, 3 connected broker accounts, 100 AI reviews/month OR unlimited with BYOK, PDF statement OCR import, Tax-Loss Harvesting Scanner, Execution Quality Scoring (NBBO), encrypted cloud backup + sync across 2 devices, multi-persona AI (Risk Manager / Tax Advisor / Devil's Advocate), priority email support |
| **Team / Prop** | **$39/user/mo** or **$389/user/yr** | Small prop desks, trading groups (2–10) | Everything in Pro + up to 10 seats, shared trade library, per-seat audit log, SSO (Google/Microsoft), 10 connected accounts/user, advanced market data aggregation, dedicated Slack support |
| **Lifetime Pro** | **$349 one-time** (desktop-only, no cloud sync, no AI credits — BYOK only) | Privacy-conscious retail | Perpetual Pro desktop features, offline-capable, major-version upgrades for 2 years, no metered AI — you bring your own key |

The Lifetime SKU deserves its own note. Edgewonk's $169 one-time offering built that community's trust; walking away from it in the move to v3 is treated as a downgrade in reviews. A higher-priced lifetime aimed squarely at the "I don't want another subscription" retail segment is credible *because* Zorivest is desktop-native and because the lifetime plan deliberately excludes cloud sync and managed AI — the two features whose ongoing server costs make lifetime pricing untenable. BYOK covers the AI path.

### What is permanently free

Three things must never be gated. **Local trade storage and import** is table-stakes trust — a trader importing last year's statements must never lose that data to a lapsed subscription. **Basic performance dashboards** (win rate, P&L, drawdown) are commodity analytics; charging for them signals distrust. **CSV import and export** must be free forever because GDPR Article 20 gives EU users the right to portability regardless of payment status, and making portability a paid feature invites regulatory scrutiny and community backlash. Zorivest should treat these as "habit-formers" — the features that make a trader open the app every Sunday — and put the upgrade pressure on *volume* and *AI*, not on baseline functionality.

### What is usage-limited (analogous to OpenWhispr's word count)

OpenWhispr's natural unit is words transcribed; Zorivest's natural unit is **trades imported plus AI reviews generated**, measured on a calendar month with reset on the first. Weekly windows, which OpenWhispr uses, make sense for a productivity tool with daily cadence; for a trade journal where a swing trader might have three trades one week and thirty the next, monthly is less punitive. TradesViz caps free at 3,000 executions/month and TraderVue at 30 trades/month; 50 trades + 10 AI reviews fits between these two anchors and intentionally pressures toward upgrade once the user becomes a real daily trader.

Monte Carlo simulations are *not* a good metering unit. They run locally in milliseconds on NumPy, cost Zorivest nothing, and feel punitive to cap. Gate them on AI narration (LLM call) and advanced scenario depth (user-defined return distributions, regime switching) instead.

### What is strictly premium

The features that cost Zorivest real server money or create real differentiation should be Pro-only with no free-tier crumbs: PDF OCR (Tesseract or Textract cost per page), Execution Quality Scoring against NBBO (requires expensive market data feed and server compute), Tax-Loss Harvesting Scanner (requires cost-basis reconciliation across accounts), cloud backup/sync, multi-persona AI, and advanced market data aggregation.

### Where BYOK makes sense

BYOK makes sense **only for the AI features**, not for cloud sync, market data, NBBO, or anything else that requires Zorivest to run paid server infrastructure. The decision rule: if the cost is variable and dominated by a third-party API the user could sign up for themselves, offer BYOK. If the cost is fixed infrastructure Zorivest operates (servers, market data licenses, storage), don't — that path leads to razor-thin margins and unbounded support burden.

Offering BYOK on OpenAI/Anthropic/Google API keys is strictly upside: it removes the ceiling on heavy users (Raycast's model), lets privacy-conscious traders keep their prompts out of Zorivest's infrastructure, and drains the most cost-variable demand away from Zorivest's managed AI credits. The AI-credit pool on Pro then sizes for median users, not outliers.

### Is encrypted cloud backup as a Pro feature ethically problematic?

This is the only ethically debatable choice in the tier structure, and it deserves a direct answer. The case *for* gating it: cloud sync has real marginal cost (storage, bandwidth, server-side encryption key management, cross-device conflict resolution), and the free tier already gets encrypted local SQLCipher storage, which is durable against disk theft and sufficient for most users. The case *against*: financial data is high-consequence, users who lose a laptop and didn't pay for sync lose everything, and "your data is held hostage" is a fair critique when the hostage is tax-relevant records.

The resolution: **encrypted cloud backup should be Pro, but free-tier users must have first-class local backup UX** — one-click export of the full SQLCipher database (password-protected), automatic reminders to back up weekly, and explicit instructions in the free-tier onboarding that local storage is not a substitute for backup. This mirrors how 1Password and Bitwarden handle it: a free local-only vault is offered, but users are constantly nudged to either pay for sync or take manual responsibility. The ethical failure mode is silent data loss; the ethical baseline is clear informed choice.

### BYOK for AI features — security implications

Storing a user's OpenAI key alongside their trade data creates a specific threat: a single compromise exposes both the user's API bill (monetary loss) and their trade history (privacy loss). This is why keys must not be stored the way OpenWhispr stores them (Electron `safeStorage` in the renderer/main process, tied to a file in `app.getPath('userData')`) — or rather, OpenWhispr's approach is acceptable for transcription but not for a financial tool. Zorivest needs stronger separation, which we build in Part 3.

The prompt-engineering/tool-orchestration layer also matters. When Zorivest constructs a prompt like "Review these trades: [JSON of user trades]" and sends it via the user's OpenAI key, Zorivest is a GDPR processor moving personal financial data to OpenAI, creating a sub-processing relationship users should be able to inspect. Three mitigations: (a) log only prompt *metadata* (token counts, model, timestamp), never prompt content; (b) expose a "preview prompt" UI before sending so users see what leaves their machine; (c) publish a list of sub-processors in the privacy policy even when the user's own API key is used.

---

## 3. BYOK key security — the right implementation

### Why OpenWhispr's `localStorage` / renderer pattern is wrong for Zorivest

`localStorage` in an Electron renderer is a plaintext file on disk (`Local Storage/leveldb/`) and is readable by any malware running as the user. `safeStorage` is better — it uses DPAPI on Windows, Keychain on macOS, and `kwallet`/`gnome-libsecret` on Linux — but it still holds the decrypted key in the renderer process's memory, where a compromised preload script or XSS against the renderer can exfiltrate it. For a financial tool, the correct separation is:

- **Keys live in the Python backend, never the renderer.**
- **Keys are encrypted at rest in a SQLCipher database** whose master key lives in the OS keychain.
- **The renderer never sees a key** — it calls Python over a localhost REST/IPC endpoint to "run an AI review," and Python holds the key, builds the prompt, calls OpenAI, and returns the result.
- **Logs are scrubbed** via a custom log filter that matches `sk-*`/`sk-ant-*`/Bearer patterns and redacts them before any write.

### Schema and storage

```sql
-- Inside the SQLCipher-encrypted main.db
CREATE TABLE api_keys (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    provider        TEXT NOT NULL CHECK (provider IN ('openai','anthropic','google','groq')),
    label           TEXT NOT NULL,                -- user-chosen display name
    ciphertext      BLOB NOT NULL,                -- AES-256-GCM of the raw key
    nonce           BLOB NOT NULL,                -- 12-byte GCM nonce
    key_fingerprint TEXT NOT NULL,                -- SHA-256 of the raw key, first 8 hex (display only)
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_validated  TIMESTAMP,                    -- last time provider accepted the key
    last_used       TIMESTAMP,
    status          TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','invalid','revoked')),
    UNIQUE(provider, label)
);

CREATE TABLE api_usage (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    key_id          INTEGER REFERENCES api_keys(id) ON DELETE CASCADE,
    ts              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    model           TEXT NOT NULL,
    prompt_tokens   INTEGER NOT NULL,
    completion_tokens INTEGER NOT NULL,
    estimated_cost_usd NUMERIC(10,6) NOT NULL
);
```

Two layers of encryption are intentional. SQLCipher encrypts the whole database file (AES-256-CBC with per-page HMAC-SHA512) against disk-level theft. The per-row AES-GCM ciphertext for the key material means that even an in-memory dump of the decrypted SQLite page exposes only ciphertext; the wrapping-key lives in a *second* keychain entry and is fetched only at the moment of use, then zeroed. This is paranoid for a retail tool and mandatory for a future institutional tier.

### The Python implementation (FastAPI + SQLCipher + keyring)

```python
# key_store.py
import os, secrets, keyring, json
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlcipher3 import dbapi2 as sqlcipher
from contextlib import contextmanager

SERVICE = "com.zorivest.desktop"
DB_MASTER_KEY_ITEM = "db.masterkey"         # 32-byte hex — SQLCipher key
KEY_WRAPPING_KEY_ITEM = "keys.wrappingkey"  # 32-byte hex — per-row AES-GCM key
DB_PATH = os.path.join(os.environ["ZORIVEST_DATA"], "main.db")

def _load_or_create_keychain_secret(item: str) -> bytes:
    hex_val = keyring.get_password(SERVICE, item)
    if hex_val is None:
        raw = secrets.token_bytes(32)
        keyring.set_password(SERVICE, item, raw.hex())
        return raw
    return bytes.fromhex(hex_val)

@contextmanager
def db_conn():
    db_key = _load_or_create_keychain_secret(DB_MASTER_KEY_ITEM)
    conn = sqlcipher.connect(DB_PATH)
    # raw 32-byte key — skips PBKDF2, fast open
    conn.execute(f"PRAGMA key = \"x'{db_key.hex()}'\"")
    conn.execute("PRAGMA cipher_page_size = 4096")
    conn.execute("PRAGMA kdf_iter = 256000")
    conn.execute("PRAGMA cipher_hmac_algorithm = HMAC_SHA512")
    conn.execute("PRAGMA cipher_kdf_algorithm = PBKDF2_HMAC_SHA512")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    try:
        yield conn
    finally:
        conn.close()

def _wrap_key(plaintext: str) -> tuple[bytes, bytes]:
    wk = _load_or_create_keychain_secret(KEY_WRAPPING_KEY_ITEM)
    nonce = secrets.token_bytes(12)
    ct = AESGCM(wk).encrypt(nonce, plaintext.encode("utf-8"), associated_data=b"api_key:v1")
    return ct, nonce

def _unwrap_key(ct: bytes, nonce: bytes) -> str:
    wk = _load_or_create_keychain_secret(KEY_WRAPPING_KEY_ITEM)
    return AESGCM(wk).decrypt(nonce, ct, associated_data=b"api_key:v1").decode("utf-8")
```

### The REST surface (FastAPI, bound to 127.0.0.1 only)

```python
# api/keys.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
import hashlib, httpx
from .key_store import db_conn, _wrap_key, _unwrap_key
from .auth import require_local_ipc_token  # shared secret between Electron main and Python

router = APIRouter(prefix="/v1/keys", dependencies=[Depends(require_local_ipc_token)])

class AddKey(BaseModel):
    provider: str = Field(pattern="^(openai|anthropic|google|groq)$")
    label:    str = Field(min_length=1, max_length=64)
    secret:   str = Field(min_length=20, max_length=500)  # never logged

class KeyView(BaseModel):
    id: int; provider: str; label: str; fingerprint: str
    status: str; last_validated: str | None

VALIDATORS = {
    "openai":    ("https://api.openai.com/v1/models",              "Authorization", "Bearer {k}"),
    "anthropic": ("https://api.anthropic.com/v1/models",           "x-api-key",     "{k}"),
    "google":    ("https://generativelanguage.googleapis.com/v1beta/models?key={k}", None, None),
}

async def _validate(provider: str, secret: str) -> bool:
    url, hdr, hdr_val = VALIDATORS[provider]
    async with httpx.AsyncClient(timeout=10) as c:
        try:
            if hdr is None:
                r = await c.get(url.replace("{k}", secret))
            else:
                r = await c.get(url, headers={hdr: hdr_val.format(k=secret),
                                              "anthropic-version": "2023-06-01"})
            return r.status_code == 200
        except Exception:
            return False

@router.post("", response_model=KeyView)
async def add_key(body: AddKey):
    if not await _validate(body.provider, body.secret):
        raise HTTPException(400, "Key validation failed against provider")
    fp = hashlib.sha256(body.secret.encode()).hexdigest()[:8]
    ct, nonce = _wrap_key(body.secret)
    with db_conn() as c:
        cur = c.execute(
          """INSERT INTO api_keys(provider,label,ciphertext,nonce,key_fingerprint,last_validated,status)
             VALUES(?,?,?,?,?,CURRENT_TIMESTAMP,'active') RETURNING id,created_at""",
          (body.provider, body.label, ct, nonce, fp))
        row = cur.fetchone(); c.commit()
    return KeyView(id=row[0], provider=body.provider, label=body.label,
                   fingerprint=fp, status="active", last_validated=row[1])

@router.get("", response_model=list[KeyView])
def list_keys():
    with db_conn() as c:
        rows = c.execute("""SELECT id,provider,label,key_fingerprint,status,last_validated
                            FROM api_keys ORDER BY created_at DESC""").fetchall()
    return [KeyView(id=r[0], provider=r[1], label=r[2], fingerprint=r[3],
                    status=r[4], last_validated=r[5]) for r in rows]

@router.post("/{key_id}/test")
async def test_key(key_id: int):
    with db_conn() as c:
        row = c.execute("SELECT provider,ciphertext,nonce FROM api_keys WHERE id=?", (key_id,)).fetchone()
    if not row: raise HTTPException(404)
    ok = await _validate(row[0], _unwrap_key(row[1], row[2]))
    with db_conn() as c:
        c.execute("UPDATE api_keys SET status=?, last_validated=CURRENT_TIMESTAMP WHERE id=?",
                  ("active" if ok else "invalid", key_id)); c.commit()
    return {"ok": ok}

@router.delete("/{key_id}")
def delete_key(key_id: int):
    with db_conn() as c:
        c.execute("DELETE FROM api_keys WHERE id=?", (key_id,)); c.commit()
    return {"deleted": True}
```

Three non-obvious properties matter. First, the FastAPI server binds to `127.0.0.1` and requires a per-launch random token that the Electron main process passes via an environment variable and attaches as `Authorization: Bearer <token>` to every IPC call — this prevents other localhost processes from hitting the API. Second, the `AddKey` Pydantic model deliberately has no `Config.extra = "allow"` and the `secret` field is never included in response models — the key can never accidentally serialize back to the renderer. Third, every log handler uses a filter that redacts anything matching `sk-proj-...`, `sk-ant-...`, and `AIza...`:

```python
import logging, re
_KEY_PATTERNS = re.compile(r"(sk-(?:proj-)?[A-Za-z0-9_\-]{20,}|sk-ant-[A-Za-z0-9_\-]{20,}|AIza[0-9A-Za-z_\-]{35})")
class RedactKeysFilter(logging.Filter):
    def filter(self, record):
        if isinstance(record.msg, str):
            record.msg = _KEY_PATTERNS.sub("[REDACTED_API_KEY]", record.msg)
        if record.args:
            record.args = tuple(_KEY_PATTERNS.sub("[REDACTED_API_KEY]", str(a)) if isinstance(a,str) else a
                                for a in record.args)
        return True
for h in logging.getLogger().handlers: h.addFilter(RedactKeysFilter())
```

### Key lifecycle and graceful degradation

**Add → validate → store**: the `POST /v1/keys` flow always round-trips to the provider before writing. A `401` from OpenAI returns a user-facing "key rejected — check for typos or trailing whitespace" message *without* the full HTTP response body (which can echo the key back).

**Expired / revoked**: when an inference call returns `401` or `invalid_api_key`, Python flips `status='invalid'` on the key row, fires a background validation retry 24h later, and surfaces a non-blocking banner in the UI: "Your OpenAI key was rejected. Update it or switch to BYOK-off to use your included AI credits." This is graceful degradation — the app keeps working, AI features are paused for that key, other keys and non-AI features continue.

**User deletes key**: features that depended on that key check `SELECT COUNT(*) FROM api_keys WHERE provider='openai' AND status='active'` — if zero, the AI Trade Review card in the UI shows the tier-appropriate fallback (managed credits if Pro, upgrade prompt if Free).

**Usage tracking**: every LLM call inserts an `api_usage` row with token counts and an estimated-cost calculation against a local pricing table (refreshed monthly via signed update). Users see "This month you've spent $3.42 on GPT-4o through your key" in the Settings panel — a meaningful feature because users routinely underestimate their own API spend, and transparency is a retention moat.

### Should Zorivest offer managed AI, or be BYOK-only?

Offer both, with BYOK as the power-user relief valve. Managed AI (Zorivest passes prompts through its own OpenAI account and meters credits inside the subscription) is necessary because most retail traders will never set up an OpenAI account and will bounce at the BYOK wall — TradesViz's numbers implicitly support this, since they sell AI bundled and don't expose keys.

**Regulatory implications are modest.** Under the Investment Advisers Act publisher's exclusion (§ 202(a)(11)(D)), as interpreted by *Lowe v. SEC* (472 U.S. 181, 1985) and reinforced by the August 2024 Seeking Alpha dismissal, software that produces impersonal analysis against the user's own data is excluded from "investment adviser" status. The *Seeking Alpha* court explicitly drew the excluded/non-excluded line at **auto-executing trades on behalf of subscribers** — Zorivest sits firmly on the excluded side. AI-generated trade reviews do not cross into "investment advice" under ESMA's five-test definition because Zorivest is not providing a **personal recommendation presented as suitable for that person** — it is providing general statistical analysis of the user's own trade history. The SEC's proposed Predictive Data Analytics rule, which would have bitten closest, was **formally withdrawn on June 12, 2025** (Release 33-11377), and in any case applied only to registered BDs and IAs. FINRA Rule 2214 (Investment Analysis Tools) applies to FINRA members, not software vendors — but its hypothetical-projections disclosure language is worth adopting voluntarily as a template.

The operational implication: frame AI outputs as analysis of the user's *own history*, avoid suitability-profile intake (risk tolerance questionnaires, net-worth prompts), don't issue forward picks keyed to user characteristics, and include the Rule 2214-style disclosure verbatim in the AI Review UI: *"IMPORTANT: The projections or other information generated by Zorivest regarding the likelihood of various investment outcomes are hypothetical in nature, do not reflect actual investment results and are not guarantees of future results."*

---

## 4. Subscription enforcement — the cryptographic backbone

### Ed25519 JWT license tokens

Ed25519 beats RS256 on every relevant axis for desktop licenses: 32-byte public key (trivial to embed as a hex constant in the Python binary), 64-byte signatures (a full license fits in ~250 bytes of base64url), faster verify on cold start, and deterministic signatures that don't require a secure RNG at sign time. PyJWT ≥2.0 supports EdDSA natively via the `cryptography` library, and `jose` in TypeScript handles it in Electron main and renderer.

**Claim schema** (short-lived tokens + monotonic state):

```json
{
  "iss": "https://licenses.zorivest.com",
  "sub": "user_01HXYZ...",
  "aud": "zorivest-desktop",
  "jti": "lic_01HXYZABCDEF",
  "iat": 1776000000,
  "nbf": 1776000000,
  "exp": 1778592000,                           // 30-day server-issued
  "lic": {
    "tier": "pro",
    "seats": 1,
    "features": ["ai_review","cloud_sync","pdf_ocr","nbbo","tlh"],
    "ai_credits_monthly_usd": 3.00,
    "device_id": "sha256:abc...",              // optional node-lock
    "grace_days": 14,
    "hard_offline_days": 30
  },
  "kid": "k1",                                 // for rotation
  "ver": 1
}
```

### Offline grace period — two-layer expiry

The pattern is **short server-issued tokens plus client-side grace**. The license server issues tokens with `exp = iat + 30 days`. While online, Zorivest silently refreshes the token every startup and every 24 hours. The cached token plus a "last successful refresh" timestamp sit inside the SQLCipher database.

On startup the client logic is:

1. Verify the cached token's signature with the embedded Ed25519 public key. If signature fails, treat as unlicensed.
2. If online, call `/v1/license/refresh` → replace token, reset `last_refresh_ts = now`.
3. If offline: if `now < exp`, run at full Pro. If `exp < now < exp + 14 days`, run with a visible "license is offline — reconnect to refresh" banner (full Pro features still work). If `exp + 14 < now < exp + 30`, cloud features degrade to read-only; local features still work. If `now > exp + 30`, refuse to unlock Pro features until the app can reach the license server.

```python
# license/verify.py
import jwt, time, keyring, sqlite3, hashlib
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from pathlib import Path

LICENSE_PUBKEY_PEM = Path(__file__).with_name("zorivest-license.pub.pem").read_bytes()
PUBKEY = load_pem_public_key(LICENSE_PUBKEY_PEM)
LEEWAY_SEC = 60
GRACE_SOFT_DAYS = 14
GRACE_HARD_DAYS = 30

class LicenseState: __slots__ = ("tier","features","mode","message")

def verify_cached(token: str, last_seen_monotonic: int) -> LicenseState:
    # Always pass algorithms explicitly — never omit.
    try:
        claims = jwt.decode(
            token, PUBKEY, algorithms=["EdDSA"],
            audience="zorivest-desktop",
            issuer="https://licenses.zorivest.com",
            leeway=LEEWAY_SEC,
            options={"require":["exp","iat","sub","jti","aud","iss"],
                     "verify_exp": False})   # we check exp manually for grace
    except jwt.InvalidTokenError as e:
        return _free_tier(f"Invalid license: {e}")

    now = int(time.time())
    # rollback-attack defense: if the system clock is earlier than the
    # highest iat we've ever seen or our monotonic marker, distrust it.
    if now < last_seen_monotonic - 86400:
        return _free_tier("Clock rollback detected — reconnect to verify")

    exp = claims["exp"]
    lic = claims["lic"]
    if now <= exp:
        return LicenseState(tier=lic["tier"], features=set(lic["features"]),
                            mode="online", message=None)
    days_expired = (now - exp) / 86400
    if days_expired <= GRACE_SOFT_DAYS:
        return LicenseState(tier=lic["tier"], features=set(lic["features"]),
                            mode="grace-soft",
                            message=f"Offline {int(days_expired)}d — reconnect within "
                                    f"{GRACE_SOFT_DAYS - int(days_expired)}d")
    if days_expired <= GRACE_HARD_DAYS:
        cloud = {"cloud_sync"}
        return LicenseState(tier=lic["tier"],
                            features=set(lic["features"]) - cloud,
                            mode="grace-hard-readonly",
                            message="Cloud features paused. Reconnect to restore.")
    return _free_tier("License expired offline — reconnect to refresh")
```

**Rollback-attack mitigations**. The classic desktop-license attack is setting the system clock backward. Defenses: (1) persist a monotonic `last_seen_ts` in three places (SQLCipher DB, OS keychain entry, HMAC'd hidden file) and treat the *maximum* as authoritative — deleting one doesn't reset; (2) update this value every 5 minutes the app is running; (3) reject any presented token whose `iat` is older than the highest `iat` previously seen (minus a 60-second NTP slack); (4) optionally read a TPM-backed monotonic counter where available. None of this stops a determined attacker with admin rights; it stops the overwhelming majority of casual clock rollback.

**Device binding**. For Pro, bind `device_id` on first activation as a hash of `machine-id + disk serial + CPU family + OS fingerprint`. The JWT's `lic.device_id` must match the client's computed fingerprint. Allow up to 2 active bindings per seat on Pro (home + laptop) with a "deactivate this device" flow in the customer portal — a friction point only once per device and universally expected by users of paid desktop software.

### Build vs buy — and the answer is buy

The honest build-vs-buy math for a solo developer: building a license server that handles JWT issuance, key rotation, revocation, offline grace, customer self-service, seat management, webhooks, and auditability is ~4–8 weeks of focused work you will maintain forever. Keygen does it for $49/mo. The labor cost dominates the license-tool cost by a factor of 10 at any realistic valuation of developer time.

| Scale (100/1k/10k users @ $15 MRR each) | Paddle-only | Paddle + Keygen | LemonSqueezy (built-in licenses) | Stripe direct + Keygen | Gumroad-only |
|---|---|---|---|---|---|
| **100 users — $18k ARR** | ~$1,632/yr (9.1%) | ~$2,220/yr (12.3%) | ~$1,632/yr (9.1%) | ~$1,560/yr + VAT labor | $2,400/yr (13.3%) |
| **1,000 users — $180k ARR** | ~$16,356/yr (9.1%) | ~$17,304/yr (9.6%) | ~$16,356/yr (9.1%) | ~$10,668/yr + $3–8k VAT filings | $24,000/yr (13.3%) |
| **10,000 users — $1.8M ARR** | ~$163,500/yr (9.1%) | ~$165,048/yr (9.2%) | ~$163,500/yr (9.1%) | ~$98,748/yr + $20k compliance | $240,000/yr (13.3%) |

The decision matrix:

- **At ≤1,000 paying users**: **Paddle (merchant of record) + Keygen Std 1 ($49/mo) for licensing** is the right combination. Paddle handles EU VAT, US sales tax, chargebacks, and refunds globally; Keygen handles cryptographic licenses, offline activation, seat management, and node-locking. Total effective take rate ~9.6% at 1k users in exchange for roughly zero compliance labor.
- **LemonSqueezy has native license keys and the same 5% + $0.50 rate**, but its acquisition by Stripe in July 2024 and the announced migration path to "Stripe Managed Payments" means starting new integrations on LS in 2026 risks a forced migration in 12–24 months. Use Paddle instead for new products targeting a 3+ year horizon.
- **Cryptlex** is the alternative to Keygen. Comparable features, cheaper trial-activation allowance, but activations-based pricing jumps aggressively (1k→10k doubles, 10k→100k doubles again) and support reviews are weaker. Keygen's SDK coverage (including an official Electron SDK) is meaningfully better for this stack.
- **Gumroad** at 10% + $0.50 is the wrong choice once MRR is material — worth it only if you want zero setup for the first 50 customers while validating demand.
- **Stripe direct + Keygen + self-managed VAT** becomes the cheaper path around **$30–50k MRR**, where saving 3–4 percentage points on fees is worth $20k/yr of compliance labor or tooling (Anrok, Quaderno, Taxually). Below that threshold, the labor cost eats the fee savings.

**The recommended path for Zorivest**: Paddle + Keygen from launch, with a planned migration to Stripe direct + Keygen around $30k MRR if and when the founder has the bandwidth for VAT administration. This keeps time-to-first-sale at a few days instead of a few weeks.

### Tamper resistance — what's worth it for a solo dev

Every desktop app can be cracked. The question is how much cracking cost you impose relative to your willingness to pay users. The diminishing-returns curve is steep after the first four items:

1. **Code-sign and notarize on both platforms**. $99/yr Apple Developer Program covers macOS notarization via `xcrun notarytool`; on Windows, **Azure Trusted Signing** (~$10/mo + per-signature if eligible — currently US/Canada businesses with 3+ years of history or US/Canada individuals as of late 2025) or **SSL.com eSigner** (~$250/yr OV with cloud HSM, no USB token needed) are the practical 2026 options. EV USB-dongle certs are largely obsolete for solo devs because Microsoft's March 2024 SmartScreen change removed EV's instant-reputation advantage for user-mode apps; only kernel drivers still require EV. Skip EV unless signing drivers.
2. **Enable ASAR integrity and hardened Electron fuses** (two lines of config; on-by-default since Electron 30). This stops script-kiddie patching of the ASAR bundle.
3. **Move the authoritative license check into Python** with Ed25519 verification against an embedded public key. The renderer gets a checked boolean over IPC — never makes the decision itself.
4. **Server-side gate the two features that matter most**: cloud sync and managed AI credits. A cracked client cannot fabricate an OpenAI response or a signed cloud-sync receipt.
5. Optionally, Nuitka-compile the Python license module. Not bulletproof — strings are still recoverable with Ghidra — but removes easy `grep`-ability for `verify_license`. Worth ~1 day of effort.

What is *not* worth the effort for a solo dev: PyArmor free tier (defeated in an afternoon with a memory dumper after runtime bootstrap), custom PyInstaller packers (trigger antivirus false positives that cost more in support tickets than they save in piracy), anti-debug `IsDebuggerPresent` tricks (trivially patched out of an unsigned binary; redundant on a signed one), string encryption of license constants (the decryption code sits right next to the constants), and JavaScript bundle obfuscation beyond standard minification. Time spent on these is better spent on server-side feature gating.

### Telemetry and what the server actually verifies

The split: **usage-limited features verify server-side; Pro-only features can verify client-side with a signed token**. AI reviews on the free tier require a server round-trip because the server is also the one incrementing the month's counter — that's intrinsic. But "does this user have PDF OCR enabled" can be answered locally from the JWT claims, because (a) faking it requires forging an Ed25519 signature, and (b) OCR runs entirely on the client so there's no server resource to protect. The rule of thumb: **if the feature consumes Zorivest server resources, the server must authorize every use; if the feature runs entirely on the client, a signed capability token is enough**.

Telemetry should be minimum-necessary. Phone home on: app start (license refresh), AI review request (server-gated for metered credits), cloud sync (server-gated), significant clock-rollback detection (security event). Do not phone home on: which trades the user imported, which persona was selected, which market they trade. GDPR Article 5(1)(c) data minimization is genuinely legal here; it is also good product practice in a privacy-sensitive vertical where retail traders will read your privacy policy.

### Grace, trial, and lapse UX

The 14-day trial (OpenWhispr uses 7 days; trade journaling warrants longer because traders evaluate tools across multiple market sessions) should be gated behind email signup but not credit card, matching Cryptlex/Keygen's "trial activations" model. When a subscription lapses, the right UX is:

- **Day 1–3 past due**: banner at the top of every view ("Your Pro subscription is past due. Update payment to avoid interruption."), but all features continue.
- **Day 4–14**: cloud sync is paused (no new sync; last synced state remains accessible); AI review credits pause; other Pro features continue.
- **Day 15+**: Pro features degrade to read-only. Critically, **all imported trade data remains fully accessible and exportable** — the user's own data is never held hostage. They can view, export to CSV, and PDF, but cannot run new AI reviews, connect new broker accounts, or sync. This is both an ethical obligation in financial software and a GDPR Article 20 requirement.

Full lockout ("your app won't start") is never the right choice for a financial tool. It both creates liability — a user who can't access their tax-relevant records during a tax deadline because a credit card expired will escalate — and signals disregard for the user's data sovereignty, which the retail trader audience is particularly sensitive to.

---

## 5. Referral and growth — handle with care

OpenWhispr's referral system is a textbook consumer-SaaS flywheel: unique codes, shareable links, email invites with sent/opened/converted tracking, a 2,000-word "completion" threshold so both parties earn, and a reward of one free Pro month each. For a transcription utility targeting casual prosumers with $15/mo price point, this works — the churn risk from referral abuse is bounded.

Financial software audiences are different. Traders are more privacy-conscious than average, more skeptical of viral mechanics (because they associate them with affiliate-pumped signals services and newsletter spam), and more likely to perceive referral pressure as a negative trust signal. The design must respect that.

**Zorivest's equivalent of "2,000 words" is "import ≥50 trades and generate ≥3 AI reviews"** — enough commitment that the referred user is demonstrably real, not enough to feel punitive. One free Pro month per side is the right reward; attempting to make referrals compound (5 referrals = lifetime Pro) is the exact pattern that breeds abuse in financial software.

**Fraud risks** specific to this category: sockpuppet accounts created with burner emails, VPN'd IPs, and fake trade imports (easy — any CSV with the right columns triggers "50 trades imported"); referral mills that farm free months to resell; credit-card chargebacks on referred-paying users that leave the referrer holding an earned month for a transaction Paddle reversed. Mitigations: (a) require the referred user to be on a *paid* plan for ≥30 days before the free month credits, not just hit the activity threshold — this is the anti-abuse pattern Dropbox converged on after early sockpuppet waves; (b) cap referral rewards at 12 months total per account; (c) cross-check device fingerprints between referrer and referee and decline obvious same-device signups; (d) deny referral credits on accounts that chargeback.

**Alternatives that fit the audience better**:

- **Affiliate program for finance content creators** (Substack authors, YouTube traders, Discord community owners) with a 25% recurring commission via Paddle's built-in affiliate system. Retail-trader discovery is dominated by personalities; a named creator's recommendation converts 10× better than a peer invite, and the fraud surface is vastly smaller because commissions go to tax-identified entities.
- **Community features**: a shared strategy library where Pro users can publish (anonymized, opt-in) strategy templates that free users can import. This drives word-of-mouth through *use value*, not incentive payouts.
- **Public "trade replay" sharing** — a Pro user generates a shareable read-only link to an AI review of a trade (with account numbers redacted). Free users who click through see a paywall after 3 replays/month. This is organic, high-conversion, and audience-appropriate.

Recommended path: **skip the peer-referral program at launch**, build affiliate + shareable-replay, revisit peer referrals after 12 months with the anti-abuse hardening above if the affiliate flywheel hasn't reached desired velocity.

---

## 6. Usage metering — the UX details that matter

### Unit of work

Zorivest has three candidate meters. Trades imported is the user's mental model and what TraderVue uses; AI reviews generated is the cost meter on Zorivest's managed-AI infrastructure; connected broker accounts is a natural tier divider because each account is ongoing sync burden. **Run two meters in parallel**: trades imported (50/month free) and AI reviews generated (10/month free). Showing both makes the upgrade pitch concrete: users who are hitting one but not the other see *which* feature is driving them toward Pro.

Avoid metering Monte Carlo simulations (they cost Zorivest nothing and feel punitive), chart views (wrong category), or data refreshes (StockCharts territory, wrong positioning).

### Window choice

**Calendar month with reset on the 1st.** Weekly windows like OpenWhispr's punish swing traders who have bursty weeks. Rolling 30-day windows are technically fairer but users hate them because they can't plan against "when does my limit reset?" — Anthropic's Claude rolling-window model is the most complained-about meter in consumer AI. A calendar month reset is universally understood and lets Zorivest show an "N days until reset" timer that reduces limit anxiety.

### The approach-to-limit UX

OpenWhispr's pattern is sound and directly transferable: color-coded progress bars at 80% (amber warning) and 100% (red block + upgrade dialog). The three-option upgrade dialog — **Upgrade / BYOK / Local** — is particularly well-designed because it gives the user an immediate non-payment path (local inference or your own key), which feels respectful rather than coercive.

For Zorivest, the approach UX:

- **At 60%**: subtle footer text "You've used 30 of 50 free trade imports this month."
- **At 80%**: amber bar + passive banner "Approaching your monthly limit. Pro removes all caps from $19/mo."
- **At 100% on trades**: block the import with a modal offering three paths: *Upgrade to Pro* (takes you to Paddle checkout), *Add a BYOK key* (only applicable for AI, not trade imports — so this option only shows on AI review blocks), or *Wait until reset* (shows countdown).
- **At 100% on AI reviews**: same modal, but BYOK is a real option because unlimited BYOK reviews are included on free tier as a deliberate pressure-valve.

Critically, **never show meters or progress bars to Pro users**. The second a user pays, every "limit" UI element disappears — they see "Unlimited" or, ideally, nothing at all. Showing a usage counter to a paying customer implies a cap they can hit, which is the single most common "why am I paying?" complaint in usage-based products. Pro users should see their AI credit balance *only* on the settings page and *only* if they opt in to transparency.

### Communicating limits without feeling stingy

Three language rules. Never say "you've exhausted your free tier" — say "you've hit this month's free limit; next reset is in 8 days." Never block a destructive action on a limit — block the *input* (the import button greys out) not the *output* (never delete data because a limit was hit). And always offer at least two paths forward — upgrade is one path, but BYOK, waiting for reset, or local-only are equally presented. The implicit message: Zorivest wants paying users, but doesn't *need* to coerce them.

---

## 7. What ties it all together

The architecture that emerges from this analysis is a system where **trust asymmetry is inverted from the OpenWhispr baseline**: instead of the client claiming "I'm Pro" and the server hopefully agreeing, Zorivest treats the client as untrusted and places cryptographic proof (Ed25519 JWT) and hard server-side gates (AI credits, cloud sync) at every Pro boundary. Keys never leave Python. Free features never phone home. Financial data never gets held hostage for lapsed subscriptions.

The regulatory perimeter is narrow precisely because Zorivest doesn't execute — the publisher's exclusion, the ESMA personal-recommendation test, the FINRA-membership requirement all bounce off a tool that merely analyzes the user's own imported history. The compliance stack collapses to GDPR (EU Representative, Privacy Policy, DPIA, Art. 30 ROPA, breach process) plus ordinary consumer law plus well-drafted disclaimers voluntarily modeled on FINRA Rule 2214's hypothetical-projections language. CCPA, NY DFS Cybersecurity Regulation, Reg BI, Reg S-P, AML/BSA, Circular 230 practitioner registration, and MiFID II investment-firm authorization all do not apply. Over-complying with rules written for broker-dealers is a genuine cost trap for solo devs in fintech; the rules that do apply are meaningfully narrower than the founder's first instinct will suggest.

The bootstrap-friendly build path: **Paddle + Keygen Std 1 for payments and licensing, Ed25519 JWTs with 30-day server tokens and 14-day offline grace, SQLCipher + OS keychain for local storage, FastAPI backend with `127.0.0.1` binding and per-launch auth tokens, BYOK via encrypted key vault with provider-validation round-trips, calendar-month 50-trades / 10-AI-reviews free tier, affiliate program before peer referrals, Pro at $19/mo, Lifetime at $349, and Team at $39/user/mo**. Code signing via Apple Developer ID + SSL.com eSigner on Windows ($350–450/year all-in). Skip PyArmor, skip anti-debug, skip EV certs, skip NY DFS compliance theater.

What remains is the hard product work: making the AI reviews actually better than the competition's, making the Monte Carlo simulations feel like revelation instead of noise, and making the trade-import flow work against every broker a retail user touches. The monetization architecture above is designed to get out of the way of that work — not to become a second product in itself.

---

## Conclusion — the five decisions that actually matter

Most of the machinery in this report is standard. Five decisions are load-bearing and worth re-stating. First, **put the license check in Python, not in localStorage** — this alone closes the gap between OpenWhispr's posture and Zorivest's threat model. Second, **treat BYOK as a permanent first-class feature, not a workaround** — it is unique differentiation in the trade-journal category and the only sustainable answer to heavy AI users. Third, **never lock data behind a lapsed subscription** — degrade Pro features to read-only but keep imports and exports open, both because it's ethically right and because the one lawsuit you don't want is a tax-season data-hostage story. Fourth, **pair Paddle with Keygen, not LemonSqueezy** — the acquisition uncertainty is not worth the marginally nicer license API on a 3+ year horizon. Fifth, **do not register as anything** — the publisher's exclusion, the absence of order execution, and the impersonal nature of the analysis keep Zorivest squarely outside broker-dealer, RIA, and MiFID II perimeters, and the correct legal posture is careful disclaimers rather than volunteered registration. These five decisions, made correctly and early, determine whether the next two years of Zorivest's development are spent building features or unwinding architectural mistakes.
