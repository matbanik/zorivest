# WST Trade Logger — Logic & API Reference

> **Purpose**: Detailed technical documentation of the two core subsystems — the **Position Size Calculator** and the **Interactive Brokers TWS API integration** — with Python code examples that can be adapted to any language or project.

---

## Table of Contents

1. [Position Size Calculator](#1-position-size-calculator)
   - [1.1 Input Variables](#11-input-variables)
   - [1.2 Calculation Formulas](#12-calculation-formulas)
   - [1.3 Reactive Binding (Live Recalculation)](#13-reactive-binding-live-recalculation)
   - [1.4 Price Fetching from TradingView](#14-price-fetching-from-tradingview)
   - [1.5 Account Balance Population](#15-account-balance-population)
2. [TWS API Connection & Data Loading](#2-tws-api-connection--data-loading)
   - [2.1 Dependencies](#21-dependencies)
   - [2.2 Configuration Persistence](#22-configuration-persistence)
   - [2.3 The IBApp Class — API Wrapper](#23-the-ibapp-class--api-wrapper)
   - [2.4 Connection Flow](#24-connection-flow)
   - [2.5 Receiving Trade Executions](#25-receiving-trade-executions)
   - [2.6 Receiving Commission & P&L Reports](#26-receiving-commission--pl-reports)
   - [2.7 Receiving Account Data](#27-receiving-account-data)
   - [2.8 Auto-Refresh Mechanism](#28-auto-refresh-mechanism)
   - [2.9 Trade De-Duplication & Persistence](#29-trade-de-duplication--persistence)
   - [2.10 Balance History Logging](#210-balance-history-logging)
   - [2.11 Disconnect & Cleanup](#211-disconnect--cleanup)

---

## 1. Position Size Calculator

The Position Size Calculator helps a trader determine how many shares to buy based on their account equity, risk tolerance, and planned price levels.

### 1.1 Input Variables

| Variable | Type | Default | Source |
|---|---|---|---|
| `AccountBalance` | float | 0.0 | Auto-populated from TWS API when an account is selected. **Read-only** in the UI. |
| `RiskPrct` | float | 1.0 | User input — risk percentage (e.g., 1.0 means 1%). |
| `Entry` | float | 0.0 | User input or auto-filled by Fetch Price. The planned entry price per share. |
| `Stop` | float | 0.0 | User input or auto-filled. The planned stop-loss price per share. |
| `Target` | float | 0.0 | User input or auto-filled. The planned profit target price per share. |

### 1.2 Calculation Formulas

All 7 output values are derived from the 5 input variables above. Here is the exact logic:

```python
import math

def calculate_position_size(balance: float, risk_prct: float, entry: float, stop: float, target: float) -> dict:
    """
    Calculate all position sizing outputs.
    
    Args:
        balance:    Total account equity (e.g., 437903.03)
        risk_prct:  Risk percentage as entered by user (e.g., 1.0 means 1%)
        entry:      Planned entry price per share
        stop:       Planned stop-loss price per share
        target:     Planned profit target price per share
        
    Returns:
        Dictionary with all 7 calculated values.
    """
    
    # --- Step 1: Normalize risk percentage ---
    # Convert from "1.0" (user input meaning 1%) to 0.01 (decimal).
    # Clamp to valid range [0.01% .. 100%].
    risk_decimal = risk_prct / 100.0
    if not (0.0001 <= risk_decimal <= 1.0):
        risk_decimal = 0.01  # Default to 1% if out of range
    
    # --- Step 2: Account Risk (1R) ---
    # The dollar amount you are willing to lose on this trade.
    acc_1r = balance * risk_decimal
    # Example: $437,903.03 × 0.01 = $4,379.03
    
    # --- Step 3: Risk-per-Share ---
    # The price distance between your entry and your stop-loss.
    # This applies whether you are going long (entry > stop) or short (stop > entry).
    if entry > 0 and stop > 0:
        risk_per_share = abs(entry - stop)
    else:
        risk_per_share = 0
    # Example: |619.61 - 618.61| = $1.00
    
    # --- Step 4: Share Size to Buy ---
    # How many shares you can afford at your risk level.
    # Uses floor() to round DOWN — never risk more than your 1R.
    if risk_per_share > 0:
        share_size = math.floor(acc_1r / risk_per_share)
    else:
        share_size = 0
    # Example: floor($4,379.03 / $1.00) = 4,379 shares
    
    # --- Step 5: Position Size (total dollar cost) ---
    # Uses ceil() to round UP — gives worst-case cost estimate.
    position_size = math.ceil(entry * share_size)
    # Example: ceil(619.61 × 4,379) = $2,712,872
    
    # --- Step 6: Potential per Share ---
    # The price distance between entry and target.
    if target > 0:
        potential_per_share = abs(target - entry)
    else:
        potential_per_share = 0
    # Example: |620.61 - 619.61| = $1.00
    
    # --- Step 7: Reward/Risk Ratio ---
    # How much reward you get for each unit of risk.
    # Floored to 2 decimal places (truncated, not rounded).
    if risk_per_share > 0:
        reward_risk_ratio = potential_per_share / risk_per_share
    else:
        reward_risk_ratio = 0
    reward_risk_ratio = math.floor(reward_risk_ratio * 100) / 100
    # Example: $1.00 / $1.00 = 1.00
    
    # --- Step 8: Potential Profit ---
    # Total dollar profit if the target is reached.
    potential_profit = potential_per_share * share_size
    # Example: $1.00 × 4,379 = $4,379.00
    
    # --- Step 9: Position to Account (%) ---
    # What fraction of your account is used by this position.
    # Floored to 2 decimal places.
    if balance > 0:
        account_at_risk_prct = (position_size / balance) * 100
    else:
        account_at_risk_prct = 0
    account_at_risk_prct = math.floor(account_at_risk_prct * 100) / 100
    # Example: ($2,712,872 / $437,903.03) × 100 = 619.61%
    
    return {
        "account_risk_1r":       acc_1r,               # $4,379.03
        "risk_per_share":        risk_per_share,        # $1.00
        "share_size_to_buy":     share_size,            # 4,379
        "position_size":         position_size,         # $2,712,872
        "position_to_account":   account_at_risk_prct,  # 619.61%
        "reward_risk_ratio":     reward_risk_ratio,     # 1.00
        "potential_profit":      potential_profit,       # $4,379.00
    }
```

#### Formatting Rules for Display

```python
def format_outputs(results: dict) -> dict:
    """Format calculated values for display in the UI."""
    return {
        "Account Risk (1R)":       f"${results['account_risk_1r']:,.2f}",
        "Risk-per-Share":          f"${results['risk_per_share']:,.2f}",
        "Share Size to Buy":       f"{results['share_size_to_buy']:,}",
        "Position Size":           f"${results['position_size']:,.0f}",
        "Position to Account (%)": f"{results['position_to_account']:.2f} %",
        "Reward/Risk Ratio":       f"{results['reward_risk_ratio']:.2f}",
        "Potential Profit":        f"${results['potential_profit']:,.2f}",
    }
```

#### Edge Cases & Guards

| Condition | Behavior |
|---|---|
| Division by zero (risk_per_share = 0) | Share size, ratio, and potential all become 0 |
| Division by zero (balance = 0) | Position to Account becomes 0% |
| Risk % out of range (< 0.01% or > 100%) | Silently defaults to 1% |
| Entry or Stop is 0 or negative | Risk-per-share becomes 0, cascading to 0 shares |
| Target is 0 or not set | Potential per share and potential profit become 0 |
| Non-numeric input in any field | Entire calculation is silently skipped (no error) |
| `floor()` vs `round()` | Share size uses `floor()` (never buy more than you can risk). Reward/Risk and Position% use floor-to-2-decimals (truncate, don't round up). |
| `ceil()` vs `round()` | Position Size uses `ceil()` (worst-case cost). |

---

### 1.3 Reactive Binding (Live Recalculation)

The calculator recalculates **immediately** whenever any of the 5 numeric input variables change. This is achieved through variable-change callbacks (also known as "traces" or "watchers").

```python
import tkinter as tk

# --- Setup: Create traced variables ---
calc_vars = {
    'AccountBalance': tk.DoubleVar(),
    'RiskPrct':       tk.DoubleVar(value=1.0),
    'Entry':          tk.DoubleVar(),
    'Stop':           tk.DoubleVar(),
    'Target':         tk.DoubleVar(),
}

def on_any_input_change(*args):
    """Called automatically whenever any traced variable changes."""
    try:
        results = calculate_position_size(
            balance   = calc_vars['AccountBalance'].get(),
            risk_prct = calc_vars['RiskPrct'].get(),
            entry     = calc_vars['Entry'].get(),
            stop      = calc_vars['Stop'].get(),
            target    = calc_vars['Target'].get(),
        )
        # Update all 7 output labels with formatted values
        formatted = format_outputs(results)
        for key, value in formatted.items():
            result_labels[key].set(value)
    except (tk.TclError, ValueError):
        pass  # Silently ignore invalid intermediate states (e.g., empty field)

# --- Attach trace callbacks to all 5 inputs ---
for var_name in ['AccountBalance', 'RiskPrct', 'Entry', 'Stop', 'Target']:
    calc_vars[var_name].trace_add("write", on_any_input_change)
```

**Key concept**: The `trace_add("write", callback)` mechanism fires the callback **every time the variable's value changes** — whether from user typing, stepper buttons, or programmatic updates (like Fetch Price). This is the tkinter equivalent of a "reactive" or "observable" pattern.

**In other frameworks**, this could be implemented as:
- **JavaScript/React**: `useEffect` with dependency array, or `onChange` event handlers
- **C# / WPF**: `INotifyPropertyChanged` + data binding
- **Qt / C++**: Signals and slots on `QLineEdit::textChanged`
- **SwiftUI**: `@Published` properties with `Combine`

---

### 1.4 Price Fetching from TradingView

The "Fetch Price" button retrieves the latest closing price for a ticker symbol from TradingView's technical analysis API. This runs on a **background thread** to prevent freezing the UI.

#### Library Used

```bash
pip install tradingview_ta
```

#### Fetch Logic

```python
from tradingview_ta import TA_Handler, Interval
from threading import Thread

def fetch_ticker_price(ticker: str) -> float | None:
    """
    Attempt to fetch the latest closing price for a US stock ticker.
    Tries multiple exchanges in order until one returns a valid price.
    
    Args:
        ticker: Stock symbol, e.g., "SPY", "AAPL", "MSFT"
        
    Returns:
        The closing price as a float, or None if not found.
    """
    # Uppercase the ticker for consistency
    ticker = ticker.strip().upper()
    
    # Try these US exchanges in order of priority
    exchanges = ["NASDAQ", "NYSE", "AMEX", "ARCA"]
    
    for exchange in exchanges:
        try:
            handler = TA_Handler(
                symbol=ticker,
                screener="america",        # US market screener
                exchange=exchange,          # Exchange to query
                interval=Interval.INTERVAL_1_DAY  # Daily interval
            )
            analysis = handler.get_analysis()
            price = analysis.indicators["close"]
            
            if price is not None:
                return float(price)
                
        except Exception as e:
            # This exchange didn't have the symbol — try the next one
            print(f"TradingView fetch error for {ticker} on {exchange}: {e}")
            continue
    
    return None  # Not found on any exchange
```

#### Auto-Fill Behavior After Successful Fetch

```python
def on_price_fetched(price: float):
    """
    After a price is successfully fetched, auto-populate
    the Entry, Stop, and Target fields.
    """
    rounded_price = round(price, 2)
    
    # Set Entry to the fetched price
    calc_vars['Entry'].set(rounded_price)
    
    # Set Stop to $1.00 below entry (default risk per share)
    calc_vars['Stop'].set(round(rounded_price - 1.0, 2))
    
    # Set Target to $1.00 above entry (default reward per share)
    calc_vars['Target'].set(round(rounded_price + 1.0, 2))
    
    # These variable changes automatically trigger recalculation
    # via the trace callbacks (Section 1.3)
```

#### Threading Pattern

```python
def fetch_price_button_clicked():
    """
    Called when the user clicks [Fetch Price].
    Launches the fetch on a background thread so the UI stays responsive.
    """
    ticker = calc_vars['Ticker'].get().strip()
    
    if not ticker:
        messagebox.showwarning("Input Required", "Please enter a ticker symbol.")
        return
    
    status_bar.set(f"Fetching price for {ticker}...")
    
    def background_work():
        price = fetch_ticker_price(ticker)
        if price is not None:
            # Schedule UI update on the main thread
            # (GUI frameworks require UI updates from the main thread)
            root.after(0, lambda: on_price_fetched(price))
        else:
            root.after(0, lambda: messagebox.showerror(
                "Fetch Error",
                f"Could not fetch price for {ticker} on major US exchanges."
            ))
    
    Thread(target=background_work, daemon=True).start()
```

> **Cross-language note**: The `daemon=True` flag means the thread will be killed when the main application exits. The `root.after(0, callback)` pattern is how tkinter schedules work on the main/UI thread — equivalent to `Dispatcher.Invoke()` in WPF, `SwingUtilities.invokeLater()` in Java, or `requestAnimationFrame()` / `setState()` in JavaScript.

---

### 1.5 Account Balance Population

The Account Balance field is **not** user-editable. It is populated automatically from the TWS API when:

1. The application connects to TWS (auto-snapshot on connect).
2. The user clicks [Bal Snapshot].
3. The user selects a different account from the dropdown.

```python
def on_account_selected(event=None):
    """
    Called when the user picks a different account from the dropdown.
    Requests the Net Liquidation value from TWS for that account.
    """
    account = calc_vars['SelectedAccount'].get()
    if account and ib_app and ib_app.isConnected():
        req_id = ib_app.get_next_req_id()
        ib_app.reqAccountSummary(req_id, "All", "NetLiquidation")

def update_account_balance(account: str, value: str):
    """
    TWS API callback handler — called when account summary data arrives.
    Updates the calculator's Account Balance field if it matches
    the currently selected account.
    """
    if account == calc_vars['SelectedAccount'].get():
        calc_vars['AccountBalance'].set(float(value))
        # This triggers recalculation via trace callback (Section 1.3)
```

---

## 2. TWS API Connection & Data Loading

This section explains how the application connects to Interactive Brokers' Trader Workstation (TWS) and receives live trade data.

### 2.1 Dependencies

```bash
pip install ibapi
```

The `ibapi` package provides two base classes that the application extends:

| Class | Role |
|---|---|
| `EClient` | **Outbound** — methods to send requests to TWS (connect, request executions, request account data). |
| `EWrapper` | **Inbound** — callback methods that TWS calls when data arrives (executions, errors, account summaries). |

```python
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.execution import ExecutionFilter, Execution
from ibapi.commission_report import CommissionReport
```

### 2.2 Configuration Persistence

Connection settings are stored in a JSON file so they survive between application launches.

```python
import json
import os

CONFIG_FILE = "config.json"

def save_config(host: str, port: int, client_id: int,
                auto_refresh_enabled: bool, auto_refresh_seconds: int,
                auto_connect_enabled: bool) -> bool:
    """
    Save connection settings to config.json.
    Returns True on success, False on IO error.
    """
    config = {
        "host": host,                               # "127.0.0.1"
        "port": port,                               # 7497
        "clientId": client_id,                      # 1
        "auto_refresh_enabled": auto_refresh_enabled,  # True
        "auto_refresh_seconds": auto_refresh_seconds,  # 5
        "auto_connect_on_startup": auto_connect_enabled  # False
    }
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        return True
    except IOError as e:
        print(f"Error: Could not write to config file. Reason: {e}")
        return False

def load_config() -> tuple:
    """
    Load connection settings from config.json.
    Returns defaults if file is missing or corrupted.
    """
    defaults = ("127.0.0.1", 7497, 1, True, 5, False)
    
    if not os.path.exists(CONFIG_FILE):
        return defaults
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            return (
                config.get("host", "127.0.0.1"),
                config.get("port", 7497),
                config.get("clientId", 1),
                config.get("auto_refresh_enabled", True),
                config.get("auto_refresh_seconds", 5),
                config.get("auto_connect_on_startup", False),
            )
    except (json.JSONDecodeError, KeyError):
        return defaults
```

### 2.3 The IBApp Class — API Wrapper

The core of the TWS integration is a single class that inherits from **both** `EWrapper` (to receive data) and `EClient` (to send requests). This is the standard Interactive Brokers pattern.

```python
class IBApp(EWrapper, EClient):
    """
    Combined API client + callback handler for Interactive Brokers TWS.
    
    This class:
    - Inherits EClient to SEND requests (connect, reqExecutions, etc.)
    - Inherits EWrapper to RECEIVE callbacks (execDetails, error, etc.)
    - Holds a reference to the GUI so it can push data to the UI
    """
    
    def __init__(self, gui_reference):
        EClient.__init__(self, self)   # Initialize the client with self as wrapper
        self.gui = gui_reference       # Reference to update the GUI
        self.nextOrderId = None        # Set by TWS on connection
        self.next_req_id = 20000       # Starting request ID counter
    
    def get_next_req_id(self) -> int:
        """
        Generate a unique request ID for each API call.
        TWS requires each request to have a unique integer ID.
        """
        self.next_req_id += 1
        return self.next_req_id
```

### 2.4 Connection Flow

The connection process is a multi-step async operation:

```
User clicks [Login to TWS]
        │
        ▼
┌─────────────────────────────────────┐
│  1. Load config (host, port, ID)    │
│  2. Disable Login button            │
│  3. Create new IBApp instance       │
│  4. Call ib_app.connect(...)        │
│  5. Start ib_app.run() on a thread  │
│  6. Schedule status check in 3 sec  │
└─────────────────────────────────────┘
        │  (3 seconds later)
        ▼
┌─────────────────────────────────────┐
│  7. Check ib_app.isConnected()      │
│     ├─ True  → enable buttons,      │
│     │          start auto-refresh,  │
│     │          request accounts     │
│     └─ False → re-enable Login,     │
│                show error status    │
└─────────────────────────────────────┘
```

#### Python Implementation

```python
from threading import Thread

def connect_to_tws(is_auto_connect=False):
    """
    Initiate connection to TWS.
    
    Args:
        is_auto_connect: True if called automatically on startup
                         (suppresses "already connected" dialog).
    """
    # Guard: already connected
    if ib_app and ib_app.isConnected():
        if not is_auto_connect:
            messagebox.showinfo("Info", "Already connected to TWS.")
        return
    
    # Reload settings in case they changed
    host, port, client_id, *_ = load_config()
    
    # Update status bar
    update_status(f"Connecting to {host}:{port} with Client ID {client_id}...")
    login_button.config(state="disabled")
    
    # Create a fresh API instance
    ib_app = IBApp(gui_reference=self)
    
    # --- Step 1: Connect (non-blocking, establishes socket) ---
    ib_app.connect(host, port, clientId=client_id)
    
    # --- Step 2: Run the message loop on a daemon thread ---
    # .run() is a blocking loop that reads messages from TWS.
    # It MUST run on a separate thread to keep the GUI responsive.
    api_thread = Thread(target=ib_app.run, daemon=True)
    api_thread.start()
    
    # --- Step 3: Check connection status after 3 seconds ---
    # TWS needs a moment to complete the handshake.
    root.after(3000, lambda: check_connection_status(is_auto_connect))


def check_connection_status(is_auto_connect=False):
    """Called 3 seconds after connect() to verify the connection succeeded."""
    if ib_app and ib_app.isConnected():
        # SUCCESS
        update_status("Successfully connected to TWS. Awaiting trades...")
        login_button.config(text="Connected")
        refresh_button.config(state="normal")
        bal_snapshot_button.config(state="normal")
        start_auto_refresh()
    else:
        # FAILURE
        if is_auto_connect:
            update_status("Auto-connect failed. Please start TWS and connect manually.")
        else:
            update_status("Connection failed. Check TWS API settings and ensure it's running.")
        login_button.config(text="Login to TWS", state="normal")
        refresh_button.config(state="disabled")
        bal_snapshot_button.config(state="disabled")
```

#### What Happens Inside TWS After Connection

When `ib_app.connect()` succeeds and `.run()` starts, TWS automatically sends two initial callbacks:

```python
# --- Callback 1: nextValidId ---
# TWS sends this immediately after connection to confirm the session is alive.
def nextValidId(self, orderId: int):
    """
    Received at the start of EVERY new session.
    This is the signal that the connection is fully established.
    """
    super().nextValidId(orderId)
    self.nextOrderId = orderId
    
    # Immediately request all today's executions
    self.reqExecutions(10001, ExecutionFilter())
    
    # Also request the list of managed accounts
    self.reqManagedAccts()


# --- Callback 2: managedAccounts ---
# TWS sends the list of account IDs managed by this login.
def managedAccounts(self, accountsList: str):
    """
    Receives a comma-separated list of account IDs.
    Example: "DU3584717,DU3584718"
    """
    super().managedAccounts(accountsList)
    accounts = [acc for acc in accountsList.split(',') if acc]
    
    # Populate the Account dropdown in the calculator
    self.gui.set_managed_accounts(accounts)
    # set_managed_accounts also auto-triggers a balance snapshot
```

### 2.5 Receiving Trade Executions

Trade data arrives via the `execDetails` callback. Each execution represents one fill (a single buy or sell event).

```python
def execDetails(self, reqId: int, contract: Contract, execution: Execution):
    """
    Called by TWS for each execution/fill that matches the request filter.
    
    Args:
        reqId:     The request ID that initiated this data.
        contract:  Contains symbol, security type, currency, exchange.
        execution: Contains time, side (BOT/SLD), shares, price, account, execId.
    """
    super().execDetails(reqId, contract, execution)
    
    # Show temporary status while processing
    self.gui.update_status(f"Processing trade: {contract.symbol}...", is_temporary=True)
    
    # Build a trade data dictionary from the API objects
    trade_data = {
        "ExecId":       execution.execId,           # Unique execution ID (string)
        "Time":         execution.time,              # "20250702 13:25:21" (yyyyMMdd HH:mm:ss)
        "Instrument":   f"{contract.symbol} {contract.secType} ({contract.currency})",
                                                     # "SPY STK (USD)"
        "Action":       execution.side,              # "BOT" (bought) or "SLD" (sold)
        "Quantity":     execution.shares,             # 100.0 (float)
        "Price":        execution.price,              # 619.61 (float)
        "Account":      execution.acctNumber,         # "DU3584717"
        "Commission":   0.0,  # Placeholder — updated later via commissionReport
        "Realized P&L": 0.0,  # Placeholder — updated later via commissionReport
    }
    
    # Send to GUI for display and persistence
    self.gui.add_trade_to_table(trade_data)
```

#### Trade Data Object Diagram

```
┌────────────────────────────────┐
│         Contract               │
│  .symbol    = "SPY"            │
│  .secType   = "STK"           │
│  .currency  = "USD"           │
│  .exchange   = "SMART"         │
└────────────────────────────────┘

┌────────────────────────────────┐
│         Execution              │
│  .execId      = "0000e1c5..."  │
│  .time        = "20250702..."  │
│  .side        = "SLD"          │
│  .shares      = 100.0          │
│  .price       = 619.61         │
│  .acctNumber  = "DU3584717"    │
└────────────────────────────────┘
```

### 2.6 Receiving Commission & P&L Reports

Commission and realized P&L arrive **separately** from execution details, linked by the `execId`. They may arrive slightly after the execution.

```python
import sys

def commissionReport(self, commissionReport: CommissionReport):
    """
    Called by TWS with the commission and realized P&L for a specific execution.
    
    Args:
        commissionReport.execId:      Matches an execution's execId.
        commissionReport.commission:  Dollar amount of commission (e.g., 1.02).
        commissionReport.realizedPNL: Realized profit/loss in dollars.
                                      May be sys.float_info.max if no P&L applies.
    """
    super().commissionReport(commissionReport)
    
    self.gui.update_trade_financials(
        exec_id    = commissionReport.execId,
        commission = commissionReport.commission,
        pnl        = commissionReport.realizedPNL,
    )


def update_trade_financials(exec_id: str, commission: float, pnl: float):
    """
    GUI-side handler: update the commission and P&L for an existing trade row.
    """
    # Find the trade in our in-memory list
    trade = next((t for t in trades if t.get("ExecId") == exec_id), None)
    
    if trade:
        # Guard: TWS sends sys.float_info.max (1.7976931348623157e+308)
        # when there is no realized P&L. Treat it as 0.00.
        if pnl >= sys.float_info.max:
            pnl = 0.0
        
        trade["Commission"] = commission
        trade["Realized P&L"] = pnl
        
        # Save to disk and update the specific table row
        save_trades(trades)
        update_table_row(exec_id, trade)
```

> **Important edge case**: TWS uses `sys.float_info.max` (≈1.8×10³⁰⁸) as a sentinel value meaning "no realized P&L available." The application converts this to `0.00` before storing.

### 2.7 Receiving Account Data

Account data (specifically `NetLiquidation` — total account value) is requested and received via a request/callback pair.

#### Requesting Account Summary

```python
def take_balance_snapshot():
    """Request account NetLiquidation for all managed accounts."""
    if ib_app and ib_app.isConnected() and managed_accounts:
        for account in managed_accounts:
            req_id = ib_app.get_next_req_id()
            # "All" = all accounts, "NetLiquidation" = the specific tag we want
            ib_app.reqAccountSummary(req_id, "All", "NetLiquidation")
```

#### Receiving Account Summary

```python
def accountSummary(self, reqId: int, account: str, tag: str, value: str, currency: str):
    """
    TWS callback with account summary data.
    
    Args:
        reqId:    The request ID.
        account:  Account ID (e.g., "DU3584717").
        tag:      The data tag (we requested "NetLiquidation").
        value:    The value as a string (e.g., "437903.03").
        currency: Currency code (e.g., "USD").
    """
    super().accountSummary(reqId, account, tag, value, currency)
    
    if tag == "NetLiquidation":
        # Update the calculator's Account Balance field
        self.gui.update_account_balance(account, value)
        
        # Also log to balance history file
        self.gui.log_account_balance(account, value)


def accountSummaryEnd(self, reqId: int):
    """
    Called when all account summary data for reqId has been delivered.
    We cancel the subscription to avoid continuous updates.
    """
    super().accountSummaryEnd(reqId)
    self.cancelAccountSummary(reqId)
```

### 2.8 Auto-Refresh Mechanism

Auto-refresh periodically re-requests all executions from TWS to catch any new trades.

```python
def start_auto_refresh():
    """
    Begin the auto-refresh cycle. Only runs if:
    - Auto-refresh is enabled in settings
    - The app is connected to TWS
    """
    stop_auto_refresh()  # Cancel any existing timer
    
    if auto_refresh_enabled and ib_app and ib_app.isConnected():
        # Refresh immediately
        refresh_trades()
        
        # Schedule the next refresh after N seconds
        auto_refresh_job = root.after(
            auto_refresh_seconds * 1000,   # Convert seconds to milliseconds
            start_auto_refresh             # Recursive call — creates the loop
        )


def stop_auto_refresh():
    """Cancel the pending auto-refresh timer."""
    if auto_refresh_job:
        root.after_cancel(auto_refresh_job)
        auto_refresh_job = None


def refresh_trades():
    """Send a new execution request to TWS."""
    if ib_app and ib_app.isConnected():
        update_status("Refreshing trades...", is_temporary=True)
        # Use current timestamp as request ID for uniqueness
        ib_app.reqExecutions(int(time.time()), ExecutionFilter())
```

**Auto-refresh lifecycle:**

```
Connected to TWS
       │
       ▼
start_auto_refresh()
       │
       ├─► refresh_trades()     ← immediate first refresh
       │
       └─► schedule next call in {interval} seconds
                │
                ▼  (after interval)
           start_auto_refresh()     ← recursive loop
                │
                ├─► refresh_trades()
                └─► schedule next call ...
                         │
         ┌───────────────┤
         ▼               ▼
    Disconnected    Settings changed
         │               │
    stop_auto_refresh()  stop + restart with new interval
```

### 2.9 Trade De-Duplication & Persistence

Since auto-refresh re-requests all executions every cycle, the application must avoid adding duplicate trades. This is handled with a **set of known execution IDs**.

```python
TRADES_FILE = "trades.json"

def save_trades(trades: list):
    """Persist trades to disk."""
    with open(TRADES_FILE, 'w') as f:
        json.dump(trades, f, indent=4)

def load_trades() -> list:
    """Load trades from disk."""
    if not os.path.exists(TRADES_FILE):
        return []
    try:
        with open(TRADES_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []


# --- At application startup: ---
trades = load_trades()
# Build a set of known Execution IDs for fast O(1) dedup lookup
trade_exec_ids = {trade['ExecId'] for trade in trades if 'ExecId' in trade}


def add_trade_to_table(trade_data: dict):
    """
    Add a new trade to the table, but only if its ExecId is new.
    Called from the execDetails callback.
    """
    exec_id = trade_data.get("ExecId")
    
    # DEDUP CHECK: skip if we've already seen this execution
    if not exec_id or exec_id in trade_exec_ids:
        return
    
    # Mark as seen
    trade_exec_ids.add(exec_id)
    
    # Insert at the beginning of the list (newest first)
    trades.insert(0, trade_data)
    
    # Persist to disk immediately
    save_trades(trades)
    
    # Re-sort and re-render the table
    sort_and_repopulate_table()
```

### 2.10 Balance History Logging

Every time a new account balance is received, it is conditionally logged to the balance history file. A new record is only created if the balance has **actually changed** since the last recorded value for that account.

```python
BALANCE_HISTORY_FILE = "accountBalances.json"

def save_balance_history(history: list):
    with open(BALANCE_HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=4)

def load_balance_history() -> list:
    if not os.path.exists(BALANCE_HISTORY_FILE):
        return []
    try:
        with open(BALANCE_HISTORY_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []


def log_account_balance(account: str, balance_str: str):
    """
    Log balance to history ONLY if it changed since the last entry
    for this account. Prevents duplicate entries from repeated snapshots.
    """
    try:
        new_balance = float(balance_str)
        history = load_balance_history()
        
        # Find the most recent entry for this specific account
        latest_entry = None
        for record in reversed(history):
            if record.get("Account") == account:
                latest_entry = record
                break
        
        # Only log if this is the first entry OR the balance changed
        if latest_entry is None or float(latest_entry.get("Balance", 0.0)) != new_balance:
            new_record = {
                "Account":  account,
                "DateTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Balance":  new_balance,
            }
            history.append(new_record)
            save_balance_history(history)
            print(f"Logged new balance for {account}: {new_balance}")
            
    except ValueError:
        print(f"Could not log balance for {account}, invalid value: {balance_str}")
```

### 2.11 Disconnect & Cleanup

When the application window is closed:

```python
def on_closing():
    """
    Called when the user clicks the window's [✕] close button.
    Ensures graceful cleanup before exiting.
    """
    # 1. Stop the auto-refresh timer
    stop_auto_refresh()
    
    # 2. Disconnect from TWS if connected
    if ib_app and ib_app.isConnected():
        ib_app.disconnect()
    
    # 3. Destroy the window and exit
    root.destroy()
```

When TWS drops the connection unexpectedly:

```python
def connectionClosed(self):
    """
    TWS callback — called when the socket connection is lost.
    Resets the UI to the disconnected state.
    """
    self.gui.update_status("Disconnected from TWS.")
    self.gui.reset_login_button()
    # reset_login_button re-enables Login, disables Refresh/BalSnapshot,
    # stops auto-refresh
```

#### Error Handling

```python
def error(self, reqId, errorCode, errorString, advancedOrderReject=""):
    """
    TWS error callback. Handles informational and real errors.
    
    Error code ranges:
    - 2104, 2106, 2108, 2158: Informational (market data farm connected, etc.)
    - 162: Historical data limit
    - 321: Server validation errors
    - reqId == -1: System-level messages (not tied to a specific request)
    - reqId > 0: Request-specific errors
    """
    # System-level messages (not tied to a request)
    if reqId == -1 and errorCode not in [2104, 2158, 2106]:
        self.gui.update_status(f"TWS Info: {errorString}")
    
    # Request-specific errors (ignore informational codes)
    elif reqId > 0 and errorCode not in [2104, 2106, 2108, 162, 321]:
        print(f"Error. Id: {reqId}, Code: {errorCode}, Msg: {errorString}")
```

---

## Appendix: Complete Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          TWS / IB Gateway                                       │
│                     (Running on localhost:7497)                                  │
└──────────┬──────────────────────────────┬────────────────────────┬──────────────┘
           │                              │                        │
     nextValidId()               execDetails()              accountSummary()
     managedAccounts()           commissionReport()
           │                              │                        │
           ▼                              ▼                        ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                         IBApp (EWrapper + EClient)                                │
│                                                                                  │
│  SENDS:                           RECEIVES:                                      │
│  • connect(host, port, id)        • nextValidId() → triggers reqExecutions       │
│  • reqExecutions(id, filter)      • managedAccounts() → populates dropdown       │
│  • reqManagedAccts()              • execDetails() → builds trade_data dict       │
│  • reqAccountSummary(id,...)      • commissionReport() → updates commission/PnL  │
│  • cancelAccountSummary(id)       • accountSummary() → updates balance           │
│  • disconnect()                   • error() → updates status bar                 │
│                                   • connectionClosed() → resets UI               │
└──────────┬──────────────────────────────┬────────────────────────┬──────────────┘
           │                              │                        │
           ▼                              ▼                        ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                     TradeLoggerApp (GUI Layer)                                    │
│                                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌─────────────────────────────────────┐ │
│  │ Trades Table  │    │ Status Bar   │    │  Position Size Calculator           │ │
│  │              │    │              │    │                                     │ │
│  │ add_trade()  │    │ update_      │    │ AccountBalance ← accountSummary    │ │
│  │ update_      │    │   status()   │    │ Account list   ← managedAccounts   │ │
│  │  financials()│    │              │    │ Entry/Stop/Tgt ← Fetch Price (TV)  │ │
│  └──────┬───────┘    └──────────────┘    │ Outputs        ← auto-calculated  │ │
│         │                                └─────────────────────────────────────┘ │
│         ▼                                                                        │
│  ┌──────────────┐    ┌──────────────┐    ┌─────────────────────────────────────┐ │
│  │ trades.json   │    │ config.json  │    │  accountBalances.json               │ │
│  │ (persistence) │    │ (settings)   │    │  (balance history)                  │ │
│  └──────────────┘    └──────────────┘    └─────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix: TWS API Quick Reference

| Method | Direction | Purpose |
|---|---|---|
| `connect(host, port, clientId)` | App → TWS | Open socket connection |
| `run()` | App internal | Start message processing loop (blocking) |
| `disconnect()` | App → TWS | Close connection |
| `reqExecutions(reqId, filter)` | App → TWS | Request all matching trade executions |
| `reqManagedAccts()` | App → TWS | Request list of account IDs |
| `reqAccountSummary(reqId, group, tags)` | App → TWS | Request account data (e.g., NetLiquidation) |
| `cancelAccountSummary(reqId)` | App → TWS | Cancel a standing account summary subscription |
| `isConnected()` | App internal | Check if socket is still connected |
| `nextValidId(orderId)` | TWS → App | Session started, here's your first order ID |
| `managedAccounts(accountsList)` | TWS → App | Here are your account IDs |
| `execDetails(reqId, contract, execution)` | TWS → App | Here's one trade execution |
| `commissionReport(report)` | TWS → App | Here's commission + P&L for an execution |
| `accountSummary(reqId, account, tag, value, currency)` | TWS → App | Here's one account data point |
| `accountSummaryEnd(reqId)` | TWS → App | All account data for this request has been sent |
| `error(reqId, code, msg)` | TWS → App | Error or informational message |
| `connectionClosed()` | TWS → App | Connection was lost |
