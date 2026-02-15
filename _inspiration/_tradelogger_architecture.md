# WST Trade Logger — GUI Architecture & Feature Specification

> **Purpose**: This document is a complete, code-free blueprint of the WST Trade Logger desktop application.
> It is intended for a developer working in **any** language/framework who needs to recreate the entire GUI with all features, behaviors, and layouts described below.

---

## Table of Contents

1. [Application Overview](#1-application-overview)
2. [Main Window](#2-main-window)
3. [Toolbar — Action Buttons](#3-toolbar--action-buttons)
4. [Trades Table](#4-trades-table)
5. [Position Size Calculator Panel](#5-position-size-calculator-panel)
6. [Status Bar](#6-status-bar)
7. [Settings Dialog Window](#7-settings-dialog-window)
8. [Account Balance History Window](#8-account-balance-history-window)
9. [Data Persistence & Files](#9-data-persistence--files)
10. [Startup Behavior](#10-startup-behavior)
11. [Connection Lifecycle](#11-connection-lifecycle)
12. [Color Scheme & Styling](#12-color-scheme--styling)

---

## 1. Application Overview

| Property | Value |
|---|---|
| **Window Title** | `WST Trade Logger` |
| **Default Size** | 1600 × 600 pixels |
| **Resizable** | Yes |
| **Theme** | "Clam" style (modern flat look) |
| **External APIs** | Interactive Brokers TWS API, TradingView TA (for price fetching) |

The application is a **single-window** desktop tool with **two child dialog windows** that can be opened on demand (Settings and Balance History). The main window is split horizontally into two resizable panes:

- **Left pane** (≈75% width): Toolbar + Trades Table
- **Right pane** (≈25% width): Position Size Calculator

---

## 2. Main Window

### 2.1. Overall Layout (ASCII)

```
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│  WST Trade Logger                                                              [─] [□] [✕]  │
├──────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                              │
│  ┌───────────────────────────────────────────────────────┬──────────────────────────────────┐ │
│  │                LEFT PANE (weight=3)                   │    RIGHT PANE (weight=1)         │ │
│  │                                                       │                                  │ │
│  │  ┌─────────────────────────────────────────────────┐  │  ┌────────────────────────────┐  │ │
│  │  │                 TOOLBAR                         │  │  │  Position Size Calculator  │  │ │
│  │  │  [Login to TWS] [Refresh] [Bal Snapshot]        │  │  │                            │  │ │
│  │  │  [Show Bal] [Export Trades] [Export Bal]         │  │  │  Ticker: [____] [Fetch]    │  │ │
│  │  │  [Settings]                                     │  │  │  Account: [dropdown ▼]     │  │ │
│  │  └─────────────────────────────────────────────────┘  │  │  Account Balance: [____]   │  │ │
│  │                                                       │  │  Risk (%): [__] [-][+]     │  │ │
│  │  ┌─────────────────────────────────────────────────┐  │  │  Entry:    [__] [-][+]     │  │ │
│  │  │              TRADES TABLE                       │  │  │  Stop:     [__] [-][+]     │  │ │
│  │  │                                                 │  │  │  Target:   [__] [-][+]     │  │ │
│  │  │  Time | Instrument | Action | Qty | Price |...  │  │  │  ─────────────────────     │  │ │
│  │  │  ─────────────────────────────────────────────  │  │  │  Account Risk (1R): $0.00  │  │ │
│  │  │  20250702 13:25:21 | SPY STK (USD) | SLD |...  │  │  │  Risk-per-Share:    $0.00  │  │ │
│  │  │  20250702 13:25:19 | SPY STK (USD) | SLD |...  │  │  │  Share Size to Buy: 0      │  │ │
│  │  │  20250702 12:42:31 | SPY STK (USD) | BOT |...  │  │  │  Position Size:     $0     │  │ │
│  │  │  ...                                            │  │  │  Position to Acct:  0.00 % │  │ │
│  │  │                                                 │  │  │  Reward/Risk Ratio: 0.00   │  │ │
│  │  │                                                 │  │  │  Potential Profit:  $0.00  │  │ │
│  │  └─────────────────────────────────────────────────┘  │  └────────────────────────────┘  │ │
│  └───────────────────────────────────────────────────────┴──────────────────────────────────┘ │
│                                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────────────────────────┐ │
│  │ STATUS BAR:  Ready. Please login to TWS.                                                │ │
│  └──────────────────────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2. Layout Details

| Layout Element | Type | Behavior |
|---|---|---|
| **Main Container** | Horizontal Split Pane (PanedWindow) | Divides the window into left and right panes with a draggable divider. Padded 10px all sides. |
| **Left Pane** | Frame, weight 3 | Contains the toolbar at the top, then the trades table filling the remaining space. Padding 10px. |
| **Right Pane** | Frame, weight 1 | Contains the Position Size Calculator panel. |
| **Status Bar** | Label at bottom | Spans full window width below the split pane. Sunken relief, left-aligned, 5px padding. |

---

## 3. Toolbar — Action Buttons

### 3.1. Toolbar Layout (ASCII)

```
┌───────────────────────────────────────────────────────────────────────────────────┐
│ [Login to TWS] [Refresh] [Bal Snapshot] [Show Bal] [Export Trades] [Export Bal]   │
│ [Settings]                                                                       │
└───────────────────────────────────────────────────────────────────────────────────┘
```

All buttons are arranged horizontally in a row, flowing left-to-right, with 5px horizontal spacing between each button.

### 3.2. Button Specifications

#### Button 1: Login to TWS

| Property | Value |
|---|---|
| **Label** | `Login to TWS` |
| **Initial State** | Enabled |
| **Click Action** | Initiates a connection to Interactive Brokers TWS. |

**Behavior on click:**
1. If already connected, shows an info dialog: *"Already connected to TWS."*
2. If not connected, disables the button and updates the status bar: *"Connecting to {host}:{port} with Client ID {clientId}..."*
3. Creates a new API connection instance using the host, port, and client ID from saved settings.
4. Starts the API connection on a background thread.
5. After a 3-second delay, checks whether the connection succeeded:
   - **Success**: Changes button text to `Connected`, enables the [Refresh] and [Bal Snapshot] buttons, starts the auto-refresh timer, and updates status to *"Successfully connected to TWS. Awaiting trades..."*
   - **Failure**: Re-enables the button with original text `Login to TWS`, disables [Refresh] and [Bal Snapshot], and updates status to *"Connection failed. Check TWS API settings and ensure it's running."*

**State changes on disconnect (connection lost):**
- Button text reverts to `Login to TWS`, state becomes Enabled.
- [Refresh] and [Bal Snapshot] buttons become Disabled.
- Auto-refresh timer stops.
- Status bar shows: *"Disconnected from TWS."*

---

#### Button 2: Refresh

| Property | Value |
|---|---|
| **Label** | `Refresh` |
| **Initial State** | **Disabled** |
| **Enabled When** | Successfully connected to TWS |
| **Click Action** | Re-fetches all execution (trade) data from TWS API for the current session. |

**Behavior on click:**
1. If connected, sends a request to TWS API for all executions with a fresh request ID.
2. Status bar temporarily shows: *"Refreshing trades..."* (reverts after 4 seconds).
3. If not connected and auto-connect is off, shows a warning dialog: *"Please connect to TWS before refreshing."*

---

#### Button 3: Bal Snapshot

| Property | Value |
|---|---|
| **Label** | `Bal Snapshot` |
| **Initial State** | **Disabled** |
| **Enabled When** | Successfully connected to TWS |
| **Click Action** | Requests a fresh account balance snapshot from TWS for all managed accounts. |

**Behavior on click:**
1. If connected and accounts are available, it requests the `NetLiquidation` value for each managed account.
2. Status bar temporarily shows: *"Requesting balance snapshot..."*
3. The received balance is:
   - Updated in the Position Size Calculator's Account Balance field (if the account matches the selected one).
   - Logged into the balance history file **only if the balance has changed** since the last recorded value for that account.
4. If not connected, shows a warning dialog: *"Please connect to TWS to take a balance snapshot."*

> **Note**: A balance snapshot is also taken **automatically** each time the application successfully connects to TWS.

---

#### Button 4: Show Bal

| Property | Value |
|---|---|
| **Label** | `Show Bal` |
| **Initial State** | **Enabled** (always) |
| **Click Action** | Opens the [Account Balance History window](#8-account-balance-history-window). |

**Behavior on click:**
- Opens a modal dialog displaying the full account balance history from the persisted file.
- This button works even when disconnected from TWS, because it reads from local storage.

---

#### Button 5: Export Trades

| Property | Value |
|---|---|
| **Label** | `Export Trades` |
| **Initial State** | **Enabled** (always) |
| **Click Action** | Exports all current trade data to a CSV file. |

**Behavior on click:**
1. If no trades exist, shows an info dialog: *"There are no trades to export."*
2. If trades exist, writes all trade records to `trades_export.csv` in the application directory.
3. On success, shows: *"Trades successfully exported to {full path}"*
4. On error, shows: *"Could not write to file trades_export.csv. Reason: {error details}"*

**CSV columns**: All fields from the trade data (ExecId, Time, Instrument, Action, Quantity, Price, Account, Commission, Realized P&L).

---

#### Button 6: Export Bal

| Property | Value |
|---|---|
| **Label** | `Export Bal` |
| **Initial State** | **Enabled** (always) |
| **Click Action** | Exports the full balance history to a CSV file. |

**Behavior on click:**
1. If no history exists, shows: *"There is no balance history to export."*
2. If history exists, writes to `balances_export.csv` in the application directory.
3. On success, shows: *"Balance history successfully exported to {full path}"*
4. On error, shows the error details.

**CSV columns**: Account, DateTime, Balance.

---

#### Button 7: Settings

| Property | Value |
|---|---|
| **Label** | `Settings` |
| **Initial State** | **Enabled** (always) |
| **Click Action** | Opens the [Settings dialog window](#7-settings-dialog-window). |

---

## 4. Trades Table

### 4.1. Table Layout (ASCII)

```
┌──────────────────┬──────────────────┬────────┬──────────┬──────────┬────────────┬────────────┬──────────────┐
│ Time             │ Instrument       │ Action │ Quantity │ Price    │ Account    │ Commission │ Realized P&L │
├──────────────────┼──────────────────┼────────┼──────────┼──────────┼────────────┼────────────┼──────────────┤
│ 20250702 13:25:21│ SPY STK (USD)    │  SLD   │    100.0 │   619.61│ DU3584717  │       0.02 │        20.17 │
│ 20250702 13:25:19│ SPY STK (USD)    │  SLD   │    100.0 │   619.61│ DU3584717  │       1.02 │        19.17 │
│ 20250702 12:42:31│ SPY STK (USD)    │  BOT   │    100.0 │   619.56│ DU3584717  │       1.00 │         0.00 │
│ ...              │ ...              │  ...   │      ... │      ...│ ...        │        ... │          ... │
└──────────────────┴──────────────────┴────────┴──────────┴──────────┴────────────┴────────────┴──────────────┘
```

### 4.2. Column Specifications

| # | Column Name | Width (px) | Alignment | Data Type | Sort Type |
|---|---|---|---|---|---|
| 1 | **Time** | 140 | Left | String (yyyyMMdd HH:mm:ss) | Alphabetical |
| 2 | **Instrument** | 220 | Left | String (e.g., "SPY STK (USD)") | Alphabetical |
| 3 | **Action** | 80 | Center | String ("BOT" or "SLD") | Alphabetical |
| 4 | **Quantity** | 80 | Right | Numeric (float) | Numeric |
| 5 | **Price** | 100 | Right | Numeric (float) | Numeric |
| 6 | **Account** | 120 | Center | String (e.g., "DU3584717") | Alphabetical |
| 7 | **Commission** | 100 | Right | Numeric (float, 2 decimals) | Numeric |
| 8 | **Realized P&L** | 120 | Right | Numeric (float, 2 decimals) | Numeric |

### 4.3. Table Behaviors

| Behavior | Description |
|---|---|
| **Column Header Click → Sort** | Clicking any column header sorts the entire table by that column. Clicking the same header again toggles between ascending and descending order. The default sort is by **Time**, descending (newest first). |
| **Row Height** | 25 pixels per row. |
| **Background** | Subtle off-white (`#fdfdfd`). |
| **Header Style** | Bold font, light gray background (`#e0e0e0`), flat relief. On hover: groove relief. On press: sunken relief. |
| **New Trade Arrival** | When a new execution is received from TWS, it is inserted at position 0 (top) in the data, saved to disk, and then the table is re-sorted by the current sort column. Duplicate execution IDs are ignored (de-duplication by ExecId). |
| **Financial Updates** | Commission and Realized P&L values arrive separately from execution details. When they arrive, only the matching row is updated in-place (no full table re-sort). A max-float sentinel value for P&L is treated as `0.00`. |
| **Fills Remaining Space** | The table expands to fill all available vertical and horizontal space in the left pane. |

---

## 5. Position Size Calculator Panel

### 5.1. Panel Layout (ASCII)

```
┌────────────────────────────────────────┐
│  Position Size Calculator              │
│                                        │
│  Ticker:    [__________] [Fetch Price] │
│                                        │
│  Account:   [▼ dropdown_____________]  │
│                                        │
│  Account Balance: [______] (read-only) │
│                                        │
│  Risk (%):  [_1.0_] [-][+]            │
│                                        │
│  Entry:     [_0.0_] [-][+]            │
│                                        │
│  Stop:      [_0.0_] [-][+]            │
│                                        │
│  Target:    [_0.0_] [-][+]            │
│                                        │
│  ──────────────────────────────────    │
│                                        │
│  Account Risk (1R):       $0.00        │
│  Risk-per-Share:          $0.00        │
│  Share Size to Buy:       0            │
│  Position Size:           $0           │
│  Position to Account (%): 0.00 %       │
│  Reward/Risk Ratio:       0.00         │
│  Potential Profit:        $0.00        │
└────────────────────────────────────────┘
```

### 5.2. Input Fields

#### Row 0: Ticker

```
┌───────────────────────────────────────────┐
│ Ticker:  [___text_input___] [Fetch Price] │
└───────────────────────────────────────────┘
```

| Element | Type | Description |
|---|---|---|
| **Label** | Static text | "Ticker:" |
| **Text Input** | Text entry field | User types a stock ticker symbol (e.g., "SPY", "AAPL"). Expands to fill available width. |
| **Fetch Price Button** | Button | Labeled "Fetch Price". Placed to the right of the text input. |

**Fetch Price Behavior:**
1. If the ticker field is empty, shows a warning dialog: *"Please enter a ticker symbol."*
2. If a ticker is entered, the status bar temporarily shows: *"Fetching price for {TICKER}..."*
3. The fetch runs on a **background thread** to prevent UI freezing.
4. It attempts to look up the closing price from TradingView on the following US exchanges in order: NASDAQ → NYSE → AMEX → ARCA.
5. On the **first successful** match:
   - **Entry** field is set to the fetched closing price (rounded to 2 decimals).
   - **Stop** field is set to `Entry - 1.00`.
   - **Target** field is set to `Entry + 1.00`.
   - Status bar temporarily shows: *"Price updated successfully."*
6. If no exchange returns a price, shows an error dialog: *"Could not fetch price for {TICKER} on major US exchanges. Please check the symbol."*

---

#### Row 1: Account

```
┌──────────────────────────────────────┐
│ Account:  [▼ DU3584717            ]  │
└──────────────────────────────────────┘
```

| Element | Type | Description |
|---|---|---|
| **Label** | Static text | "Account:" |
| **Dropdown** | Dropdown / combobox (read-only) | Populated with accounts received from TWS after connection. Initially empty. |

**Behavior:**
- When the application connects to TWS, the account list is populated automatically.
- The first account is auto-selected if nothing is already selected.
- When the user selects a different account, a request is sent to TWS for that account's `NetLiquidation` (total balance), which then updates the Account Balance field.

---

#### Row 2: Account Balance

```
┌──────────────────────────────────────┐
│ Account Balance:  [437,903.03     ]  │
└──────────────────────────────────────┘
```

| Element | Type | Description |
|---|---|---|
| **Label** | Static text | "Account Balance:" |
| **Entry** | Text entry (**read-only**) | Displays the Net Liquidation value for the selected account. Updated via TWS API callbacks. Not user-editable. |

---

#### Rows 3–6: Risk, Entry, Stop, Target (with Steppers)

Each of these rows follows an identical pattern:

```
┌──────────────────────────────────────────────┐
│ {Label}:  [__numeric_value__]  [-] [+]       │
└──────────────────────────────────────────────┘
```

| Row | Label | Default Value | Stepper Increment | Description |
|---|---|---|---|---|
| 3 | **Risk (%):** | 1.0 | ±0.25 | The percentage of account equity the user is willing to risk. |
| 4 | **Entry:** | 0.0 | ±1.0 | The planned entry price per share. |
| 5 | **Stop:** | 0.0 | ±1.0 | The planned stop-loss price per share. |
| 6 | **Target:** | 0.0 | ±1.0 | The planned profit-target price per share. |

**Stepper Buttons Detail:**

```
             Text input              Steppers
         ┌────────────────┐         ┌───┬───┐
         │     1.0        │         │ - │ + │
         └────────────────┘         └───┴───┘
```

| Element | Description |
|---|---|
| **[-] Button** | Decreases the field value by the stepper increment. |
| **[+] Button** | Increases the field value by the stepper increment. |
| **Font** | Smaller than main buttons (8pt vs 10pt). |
| **Width** | Very narrow (2 characters wide). |

**Stepper Behavior:**
- Clicking [-] subtracts the increment, clicking [+] adds the increment.
- Values are rounded to 2 decimal places after each adjustment.
- If the current value is invalid or empty, pressing a stepper sets the value to the increment amount (positive or negative).
- The text input is also directly editable by typing.

---

### 5.3. Separator

A horizontal line (separator) divides the input fields from the calculated output fields.

```
══════════════════════════════════════
```

---

### 5.4. Calculated Output Fields (Read-Only Labels)

These 7 output values are **automatically recalculated** whenever any of the 5 numeric input variables change (Account Balance, Risk %, Entry, Stop, Target).

```
┌─────────────────────────────────────────────┐
│  Account Risk (1R):         $4,379.03       │
│  Risk-per-Share:            $1.00           │
│  Share Size to Buy:         4,379           │
│  Position Size:             $2,712,877      │
│  Position to Account (%):   619.61 %        │
│  Reward/Risk Ratio:         1.00            │
│  Potential Profit:          $4,379.00        │
└─────────────────────────────────────────────┘
```

| # | Output Label | Format | Calculation Logic |
|---|---|---|---|
| 1 | **Account Risk (1R)** | `$X,XXX.XX` | `AccountBalance × (Risk% / 100)` — the dollar amount of risk per trade. |
| 2 | **Risk-per-Share** | `$X.XX` | `|Entry − Stop|` — the price distance between entry and stop-loss. |
| 3 | **Share Size to Buy** | `X,XXX` (integer) | `floor(Account Risk (1R) / Risk-per-Share)` — how many shares you can buy at the given risk. |
| 4 | **Position Size** | `$X,XXX` (integer) | `ceil(Entry × Share Size to Buy)` — total dollar cost of the position. |
| 5 | **Position to Account (%)** | `XX.XX %` | `(Position Size / Account Balance) × 100` — what percentage of the account is allocated. Floored to 2 decimals. |
| 6 | **Reward/Risk Ratio** | `X.XX` | `|Target − Entry| / |Entry − Stop|` — the ratio of potential reward to risk. Floored to 2 decimals. |
| 7 | **Potential Profit** | `$X,XXX.XX` | `|Target − Entry| × Share Size to Buy` — the profit if the target is reached. |

**Calculation Behavior:**
- All outputs update **live** as inputs change (reactive binding via variable trace callbacks).
- If Risk % is outside 0.01%–100%, it defaults to 1%.
- If Entry or Stop is 0 or invalid, Risk-per-Share is 0 and Share Size to Buy is 0.
- If any calculation would cause a division by zero, the affected output shows 0.
- Any invalid or non-numeric input is silently ignored (no error dialogs).

---

## 6. Status Bar

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│  Ready. Please login to TWS.                                                    │
└──────────────────────────────────────────────────────────────────────────────────┘
```

| Property | Description |
|---|---|
| **Position** | Docked to the very bottom of the window, spanning full width. |
| **Relief** | Sunken (inset border). |
| **Alignment** | Left-aligned. |
| **Padding** | 5px. |
| **Default Text** | "Ready. Please login to TWS." |

### 6.1. Message Types

| Type | Behavior |
|---|---|
| **Permanent Message** | Replaces the current status text and remains until another permanent message is set. |
| **Temporary Message** | Displays for 4 seconds, then automatically reverts to the last permanent message. |

### 6.2. Status Message Examples

| Trigger | Message | Type |
|---|---|---|
| App startup | "Ready. Please login to TWS." | Permanent |
| Connecting | "Connecting to 127.0.0.1:7497 with Client ID 1..." | Permanent |
| Connected | "Successfully connected to TWS. Awaiting trades..." | Permanent |
| Disconnected | "Disconnected from TWS." | Permanent |
| Auto-connect failed | "Auto-connect failed. Please start TWS and connect manually." | Permanent |
| Connection failed | "Connection failed. Check TWS API settings and ensure it's running." | Permanent |
| Trade arriving | "Processing trade: SPY..." | Temporary (4s) |
| Refresh | "Refreshing trades..." | Temporary (4s) |
| Fetching price | "Fetching price for SPY..." | Temporary (4s) |
| Price fetched | "Price updated successfully." | Temporary (4s) |
| Balance request | "Requesting balance snapshot..." | Temporary (4s) |

---

## 7. Settings Dialog Window

### 7.1. Window Properties

| Property | Value |
|---|---|
| **Title** | `Settings` |
| **Size** | 400 × 340 pixels |
| **Type** | Modal dialog (blocks interaction with parent until closed) |
| **Transient** | Child of main window (stays on top of it) |

### 7.2. Layout (ASCII)

```
┌─────────────────────────────────────────────┐
│  Settings                              [✕]  │
├─────────────────────────────────────────────┤
│                                             │
│  ┌─ Connection ──────────────────────────┐  │
│  │                                       │  │
│  │  TWS Host: [_127.0.0.1_____________]  │  │
│  │                                       │  │
│  │  Port:     [_7497___________________]  │  │
│  │                                       │  │
│  │  Client ID:[_1______________________]  │  │
│  │                                       │  │
│  └───────────────────────────────────────┘  │
│                                             │
│  ┌─ Application ─────────────────────────┐  │
│  │                                       │  │
│  │  [✓] Enable Auto-Refresh             │  │
│  │                                       │  │
│  │  Refresh Interval (sec): [_4_]        │  │
│  │                                       │  │
│  │  [✓] Auto-connect on startup          │  │
│  │                                       │  │
│  └───────────────────────────────────────┘  │
│                                             │
│       [   OK   ]  [ Cancel ]  [  Apply  ]   │
│                                             │
└─────────────────────────────────────────────┘
```

### 7.3. Section: Connection

| Field | Type | Default | Description |
|---|---|---|---|
| **TWS Host** | Text entry | `127.0.0.1` | The IP address or hostname of the TWS/IB Gateway instance. |
| **Port** | Text entry | `7497` | The socket port. TWS default is 7497, IB Gateway default is 4001. |
| **Client ID** | Text entry | `1` | The unique client ID for the API connection. Must be integer. |

### 7.4. Section: Application

| Field | Type | Default | Description |
|---|---|---|---|
| **Enable Auto-Refresh** | Checkbox | ✓ Checked | When enabled, the app periodically re-fetches trade data from TWS at the specified interval. |
| **Refresh Interval (sec)** | Text entry (narrow, 10-char width) | `5` | Interval in whole seconds between auto-refresh cycles. Must be ≥ 1. |
| **Auto-connect on startup** | Checkbox | ☐ Unchecked | When enabled, the app automatically attempts to connect to TWS 500ms after launching. |

### 7.5. Dialog Buttons

```
┌──────────────────────────────────────┐
│     [   OK   ] [ Cancel ] [ Apply ] │
└──────────────────────────────────────┘
```

| Button | Action |
|---|---|
| **OK** | Validates and saves all settings, then closes the dialog. If validation fails, the dialog stays open. |
| **Cancel** | Closes the dialog **without** saving any changes. |
| **Apply** | Validates and saves all settings **without** closing the dialog. Immediately applies changes to the running app (e.g., restarts auto-refresh with new interval). |

### 7.6. Validation Rules

All three buttons that save (OK and Apply) perform validation:

| Rule | Error Handling |
|---|---|
| Port must be a valid positive integer | Shows error dialog: *"Port, Client ID, and Interval must be valid positive numbers."* |
| Client ID must be a valid positive integer | Same as above |
| Refresh Interval must be a valid integer ≥ 1 | Same as above |
| File write must succeed | Shows error dialog: *"Could not save settings to config.json. Please check file permissions."* |

### 7.7. Settings Persistence

All settings are persisted to `config.json`. When the dialog opens, it reads from this file. When saved, the main application reloads its internal copy of the settings and restarts the auto-refresh timer if applicable.

---

## 8. Account Balance History Window

### 8.1. Window Properties

| Property | Value |
|---|---|
| **Title** | `Account Balance History` |
| **Size** | 600 × 400 pixels |
| **Type** | Modal dialog (blocks parent) |
| **Transient** | Child of main window |

### 8.2. Layout (ASCII)

```
┌──────────────────────────────────────────────────────────────┐
│  Account Balance History                                [✕]  │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────┬─────────────────────────┬──────────────┐ │
│  │ Account        │ DateTime                │      Balance │ │
│  ├────────────────┼─────────────────────────┼──────────────┤ │
│  │ DU3584717      │ 2025-07-02 13:22:31     │ $437,903.03  │ │
│  │ DU3584717      │ 2025-07-02 13:24:46     │ $437,967.03  │ │
│  │ DU3584717      │ 2025-07-02 13:36:36     │ $437,997.99  │ │
│  │ DU3584717      │ 2025-09-19 19:38:16     │ $441,492.97  │ │
│  │                │                         │              │ │
│  │                │                         │              │ │
│  │                │                         │              │ │
│  └────────────────┴─────────────────────────┴──────────────┘ │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 8.3. Column Specifications

| Column | Width (px) | Alignment | Sort Type |
|---|---|---|---|
| **Account** | 120 | Left | Alphabetical |
| **DateTime** | 150 | Left | Alphabetical (works because format is ISO-like) |
| **Balance** | 120 | Right | Numeric |

### 8.4. Behaviors

| Behavior | Description |
|---|---|
| **Data Source** | Reads from `accountBalances.json` on disk when the window opens. |
| **Default Sort** | Sorted by **DateTime**, descending (newest first). |
| **Column Sort** | Clicking any header sorts by that column. Clicking the same header toggles asc/desc. |
| **Balance Formatting** | Displayed as `$XXX,XXX.XX` (currency-formatted with dollar sign). |
| **Fills Window** | The table expands to fill all available space with 10px padding. |

---

## 9. Data Persistence & Files

All data is persisted to JSON files in the **same directory as the application executable**.

| File | Content | Structure |
|---|---|---|
| **`config.json`** | Connection and application settings | `{ "host": str, "port": int, "clientId": int, "auto_refresh_enabled": bool, "auto_refresh_seconds": int, "auto_connect_on_startup": bool }` |
| **`trades.json`** | Array of all recorded trade executions | `[ { "ExecId": str, "Time": str, "Instrument": str, "Action": str, "Quantity": float, "Price": float, "Account": str, "Commission": float, "Realized P&L": float }, ... ]` |
| **`accountBalances.json`** | Array of balance snapshots over time | `[ { "Account": str, "DateTime": "YYYY-MM-DD HH:MM:SS", "Balance": float }, ... ]` |

### Export Files

| File | Format | Generated By |
|---|---|---|
| **`trades_export.csv`** | CSV with header row | [Export Trades] button |
| **`balances_export.csv`** | CSV with header row | [Export Bal] button |

### Defaults When Files Missing

| File | Default Values |
|---|---|
| `config.json` not found | host=127.0.0.1, port=7497, clientId=1, autoRefresh=true, interval=5s, autoConnect=false |
| `trades.json` not found | Empty array `[]` |
| `accountBalances.json` not found | Empty array `[]` |
| Any file has malformed JSON | Treated as if file does not exist (defaults used) |

---

## 10. Startup Behavior

```
Application Launch
       │
       ├─► Load config.json (or use defaults)
       ├─► Load trades.json (or use empty list)
       ├─► Build a set of known ExecIds for de-duplication
       ├─► Set default sort: Time column, descending
       ├─► Apply visual styles/theme
       ├─► Build all UI elements
       ├─► Populate trades table from loaded data
       │
       └─► Is "Auto-connect on startup" enabled?
               │
               ├─ YES → Wait 500ms, then auto-connect to TWS
               │          (same as clicking [Login to TWS])
               │
               └─ NO  → Status: "Ready. Please login to TWS."
                          User must click [Login to TWS] manually
```

---

## 11. Connection Lifecycle

```
            ┌──────────────────┐
            │    DISCONNECTED  │
            │  Login btn: ON   │
            │  Refresh: OFF    │
            │  BalSnap: OFF    │
            └────────┬─────────┘
                     │  [Login to TWS] clicked
                     │  or auto-connect on startup
                     ▼
            ┌──────────────────┐
            │   CONNECTING...  │
            │  Login btn: OFF  │
            │  3-second wait   │
            └────────┬─────────┘
                     │
           ┌─────────┴──────────┐
           ▼                    ▼
  ┌────────────────┐   ┌────────────────┐
  │   CONNECTED    │   │  FAILED        │
  │  Login: "Conn" │   │  Back to       │
  │  Refresh: ON   │   │  DISCONNECTED  │
  │  BalSnap: ON   │   └────────────────┘
  │  Auto-refresh  │
  │    starts      │
  └───────┬────────┘
          │
          │  TWS connection drops
          ▼
  ┌────────────────┐
  │  DISCONNECTED  │
  │  All reverted  │
  └────────────────┘
```

### Auto-Refresh Cycle

```
Connected + Auto-Refresh Enabled?
       │
       ├─ YES → Immediately refresh trades
       │         ├─► Schedule next refresh after {interval} seconds
       │         └─► Repeat indefinitely until disconnected
       │              or auto-refresh disabled
       │
       └─ NO  → No automatic refreshes; user uses [Refresh] manually
```

---

## 12. Color Scheme & Styling

### 12.1. Theme

The application uses the **"Clam"** theme (a modern flat UI toolkit theme).

### 12.2. Color Reference

| Element | Property | Value |
|---|---|---|
| **Buttons** | Background | `#007bff` (Bootstrap blue) |
| **Buttons** | Text color | `#ffffff` (white) |
| **Buttons (hover)** | Background | `#0056b3` (darker blue) |
| **Buttons (disabled)** | Background | `#c0c0c0` (gray) |
| **Main frames** | Background | `#f0f0f0` (light gray) |
| **Table rows** | Background | `#fdfdfd` (near-white) |
| **Table headings** | Background | `#e0e0e0` (medium gray) |
| **Calculator panel** | Background | `#f8f9fa` (off-white) |
| **Status bar text (Disconnected)** | Color | Red (based on status) |

### 12.3. Typography

| Element | Font | Size | Weight |
|---|---|---|---|
| **Buttons** | Calibri | 10pt | Normal |
| **Table rows** | Calibri | 10pt | Normal |
| **Table headings** | Calibri | 10pt | **Bold** |
| **Calculator result labels** | Calibri | 10pt | **Bold** |
| **Calculator input labels** | Calibri | 10pt | Normal |
| **Stepper buttons** | Calibri | 8pt | Normal |

---

## Appendix A: Complete Element Inventory

### Main Window Elements

| # | Element | Type | Parent | Initial State |
|---|---|---|---|---|
| 1 | Login to TWS | Button | Toolbar | Enabled |
| 2 | Refresh | Button | Toolbar | Disabled |
| 3 | Bal Snapshot | Button | Toolbar | Disabled |
| 4 | Show Bal | Button | Toolbar | Enabled |
| 5 | Export Trades | Button | Toolbar | Enabled |
| 6 | Export Bal | Button | Toolbar | Enabled |
| 7 | Settings | Button | Toolbar | Enabled |
| 8 | Trades Table | Treeview (8 cols) | Left Pane | Populated from file |
| 9 | Ticker input | Text entry | Calculator | Empty |
| 10 | Fetch Price | Button | Calculator | Enabled |
| 11 | Account dropdown | Combobox (read-only) | Calculator | Empty |
| 12 | Account Balance | Entry (read-only) | Calculator | 0.0 |
| 13 | Risk (%) input | Entry + Stepper (±0.25) | Calculator | 1.0 |
| 14 | Entry input | Entry + Stepper (±1.0) | Calculator | 0.0 |
| 15 | Stop input | Entry + Stepper (±1.0) | Calculator | 0.0 |
| 16 | Target input | Entry + Stepper (±1.0) | Calculator | 0.0 |
| 17 | Horizontal Separator | Separator | Calculator | — |
| 18 | Account Risk (1R) | Label (output) | Calculator | $0.00 |
| 19 | Risk-per-Share | Label (output) | Calculator | $0.00 |
| 20 | Share Size to Buy | Label (output) | Calculator | 0 |
| 21 | Position Size | Label (output) | Calculator | $0 |
| 22 | Position to Account (%) | Label (output) | Calculator | 0.00 % |
| 23 | Reward/Risk Ratio | Label (output) | Calculator | 0.00 |
| 24 | Potential Profit | Label (output) | Calculator | $0.00 |
| 25 | Status Bar | Label (sunken) | Window bottom | "Ready. Please login to TWS." |

### Settings Dialog Elements

| # | Element | Type | Parent | Default |
|---|---|---|---|---|
| 1 | TWS Host | Text entry | Connection group | 127.0.0.1 |
| 2 | Port | Text entry | Connection group | 7497 |
| 3 | Client ID | Text entry | Connection group | 1 |
| 4 | Enable Auto-Refresh | Checkbox | Application group | Checked |
| 5 | Refresh Interval | Text entry (10 chars) | Application group | 5 |
| 6 | Auto-connect on startup | Checkbox | Application group | Unchecked |
| 7 | OK | Button | Button bar | Enabled |
| 8 | Cancel | Button | Button bar | Enabled |
| 9 | Apply | Button | Button bar | Enabled |

### Balance History Window Elements

| # | Element | Type | Parent | Notes |
|---|---|---|---|---|
| 1 | Balance History Table | Treeview (3 cols) | Window | Sortable by click |

---

## Appendix B: Dialog / Message Box Inventory

| Trigger | Type | Title | Message |
|---|---|---|---|
| Already connected and [Login] clicked | Info | "Info" | "Already connected to TWS." |
| [Refresh] clicked while disconnected | Warning | "Not Connected" | "Please connect to TWS before refreshing." |
| [Bal Snapshot] while disconnected | Warning | "Not Connected" | "Please connect to TWS to take a balance snapshot." |
| [Export Trades] with no trades | Info | "Export Info" | "There are no trades to export." |
| [Export Trades] success | Info | "Export Success" | "Trades successfully exported to {path}" |
| [Export Trades] write error | Error | "Export Error" | "Could not write to file. Reason: {error}" |
| [Export Bal] with no history | Info | "Export Info" | "There is no balance history to export." |
| [Export Bal] success | Info | "Export Success" | "Balance history successfully exported to {path}" |
| [Export Bal] write error | Error | "Export Error" | "Could not write to file. Reason: {error}" |
| [Fetch Price] with empty ticker | Warning | "Input Required" | "Please enter a ticker symbol." |
| [Fetch Price] no result found | Error | "Fetch Error" | "Could not fetch price for {TICKER}..." |
| Settings: invalid Port/ClientID/Interval | Error | "Input Error" | "Port, Client ID, and Interval must be valid positive numbers." |
| Settings: file write failure | Error | "Save Error" | "Could not save settings to config.json..." |
| App start: missing dependencies | Error | "Dependency Error" | "The following packages are not installed: ..." |

---

## Appendix C: Window Close Behavior

When the main window's close button [✕] is clicked:

1. The auto-refresh timer is stopped.
2. If connected to TWS, the connection is gracefully disconnected.
3. The application window is destroyed and the process exits.

> **Note**: There is no "are you sure?" confirmation dialog before closing.
