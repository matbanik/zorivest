# packages/core/src/zorivest_core/domain/enums.py

from enum import StrEnum


class AccountType(StrEnum):
    BROKER = "broker"           # Brokerage account (Interactive Brokers, etc.)
    BANK = "bank"               # Checking/savings
    REVOLVING = "revolving"     # Credit cards, lines of credit
    INSTALLMENT = "installment" # Loans (mortgage, auto, student)
    IRA = "ira"                 # Individual Retirement Account
    K401 = "401k"               # Employer-sponsored retirement


class TradeAction(StrEnum):
    BOT = "BOT"  # Bought
    SLD = "SLD"  # Sold


class ConvictionLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    MAX = "max"


class PlanStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    EXECUTED = "executed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class ImageOwnerType(StrEnum):
    TRADE = "trade"
    REPORT = "report"
    PLAN = "plan"


class DisplayModeFlag(StrEnum):
    """GUI display privacy toggles — stored in user settings."""
    HIDE_DOLLARS = "hide_dollars"            # Privacy mode — hide all $ amounts
    HIDE_PERCENTAGES = "hide_percentages"    # Privacy mode — hide all % values
    PERCENT_MODE = "percent_mode"            # Show % of total portfolio alongside $


# ── Build Plan Expansion enums ──────────────────────────────────────────


class RoundTripStatus(StrEnum):  # §3
    OPEN = "open"
    CLOSED = "closed"
    PARTIAL = "partial"


class IdentifierType(StrEnum):  # §5
    CUSIP = "cusip"
    ISIN = "isin"
    SEDOL = "sedol"
    FIGI = "figi"


class FeeType(StrEnum):  # §9
    COMMISSION = "commission"
    EXCHANGE = "exchange"
    REGULATORY = "regulatory"
    ECN = "ecn"
    CLEARING = "clearing"
    PLATFORM = "platform"
    OTHER = "other"


class StrategyType(StrEnum):  # §8
    VERTICAL = "vertical"
    IRON_CONDOR = "iron_condor"
    BUTTERFLY = "butterfly"
    CALENDAR = "calendar"
    STRADDLE = "straddle"
    STRANGLE = "strangle"
    CUSTOM = "custom"


class MistakeCategory(StrEnum):  # §17
    EARLY_EXIT = "early_exit"
    LATE_EXIT = "late_exit"
    OVERSIZED = "oversized"
    NO_STOP = "no_stop"
    REVENGE_TRADE = "revenge_trade"
    FOMO_ENTRY = "fomo_entry"
    IGNORED_PLAN = "ignored_plan"
    OVERTRADING = "overtrading"
    CHASING = "chasing"
    OTHER = "other"


class RoutingType(StrEnum):  # §23
    PFOF = "pfof"
    DMA = "dma"
    HYBRID = "hybrid"


class TransactionCategory(StrEnum):  # §26
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"
    FEE = "fee"
    INTEREST = "interest"
    DIVIDEND = "dividend"
    ACH_DEBIT = "ach_debit"
    ACH_CREDIT = "ach_credit"
    WIRE_IN = "wire_in"
    WIRE_OUT = "wire_out"
    CHECK = "check"
    CARD_PURCHASE = "card_purchase"
    REFUND = "refund"
    ATM = "atm"
    OTHER = "other"


class BalanceSource(StrEnum):  # §26
    MANUAL = "manual"
    CSV_IMPORT = "csv_import"
    OFX_IMPORT = "ofx_import"
    QIF_IMPORT = "qif_import"
    PDF_IMPORT = "pdf_import"
    AGENT_SUBMIT = "agent_submit"


class AuthMethod(StrEnum):
    """How the API key is passed to the market data provider."""

    QUERY_PARAM = "query_param"
    BEARER_HEADER = "bearer_header"
    CUSTOM_HEADER = "custom_header"
    RAW_HEADER = "raw_header"
