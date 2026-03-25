# Platform Feature Matrix

| **Feature**              | **TradingView**                                                                   | **TC2000**                                                                 | **Thinkorswim (TOS)**                                                       | **Webull**                                                             | **IBKR (TWS)**                                                                                       |
|--------------------------|-----------------------------------------------------------------------------------|----------------------------------------------------------------------------|-----------------------------------------------------------------------------|------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------|
| **Default Columns**      | *Symbol*, Last Price, Net Change, % Change, Volume, *(extended-hours Δ)*【1†L63-L69】【8†L55-L63】. (Table view adds Day High/Low, Bid, Ask, Time)【16†L70-L78】. | *Symbol*, Last, Net Change, % Change, Volume (likely defaults). (All columns are user-defined; “Default View” can be reset)【55†L684-L693】【58†L35-L43】.   | *Symbol*, Last, Net Change, % Change, Bid, Ask (plus Time/Date). (Users can select from hundreds of fields like Mark, P/L, etc.)【34†L23-L30】. | *Symbol*, Last Price, (small sparkline chart), Net Change (%)【81†L186-L189】. Minimal by default; other fields accessed on tap.    | *Instrument*, Last Price, Net Change, % Change【55†L684-L693】. (By default, just these; others can be added.)                                             |
| **Optional Columns**     | High, Low, Bid, Ask, Time, Session Volume, Fundamentals (PE, Market Cap), custom “heatmap” fields【16†L70-L78】【1†L103-L112】. Customizable via “Columns” menu. | Any technical or fundamental metric. Supports *Value* columns (e.g. RSI, P/E), *True/False* condition columns, *Tag* (flag) columns【19†L23-L30】, custom PCF formulas. “Most Watched” and “Trending” popularity scores【30†L24-L33】 can be added. | Any built-in or user-scripted field. Includes Mark, Mark Change, P/L, Greeks, open/high/low, RSI, etc.【34†L23-L30】. Custom thinkScript columns (with full color/conditional formatting) are a hallmark. | Webull has few column options. Desktop lets you add fields like Last, Change, %Chg, Volume, Bid/Ask, VWAP, etc., but mobile is fixed. (The mobile watchlist itself shows mostly price and %.)  | Anything TWS offers: bid/ask, day’s high/low, 52-week range, volume, open interest, Greeks, P/E, Beta, etc. Users can save custom *Views* with any combination【58†L35-L43】.              |
| **Real-Time Data**       | Streaming via WebSockets for live quotes and chart updates. Watchlist values update continuously when connected【1†L103-L112】. | Supports real-time (Streaming) data feeds (with Premium service) or auto-refresh polling. True/False columns update as conditions become true.【19†L23-L30】 | Streaming quotes when logged in (with real-time data subscription). No explicit freshness indicator (values color-change instantly, as in heatmap).       | Streaming quotes (real-time data feed). Mobile view shows live % changes in color. No explicit “age” label; prices auto-update.                                           | Streaming quotes via IB’s data feeds. The watchlist shows time-stamps and uses color (green/red) for changes【55†L684-L693】. The data is real-time (no manual refresh needed).       |
| **Unique UX Patterns**   | “Advanced” table mode with detachable ticker details (news, fundamentals) below or to the side【1†L103-L112】. Users can *add notes* to symbols and group by sector or custom section. Custom watchlists support hotlists and alerts integration. | Conditional coloring of columns (user sets positive/negative colors)【27†L132-L139】, ability to highlight “True/False” conditions with checkmarks, and *Tag* columns for watchlist membership. “Most Watched/Trending” columns show server-side popularity scores【30†L24-L33】. Column Sets let traders save and switch presets. | *Linking*: color-coded cursors sync watchlist with other gadgets【32†L46-L50】. Fully scriptable columns (thinkScript) with color-coding and icon support. Public pre-built watchlists (e.g. “Top Losers/Volume”) accessible. Deep integration with chart and scanner. | Mini-sparkline chart in each row (in mobile app) plus after-hours % label【81†L186-L189】. Mobile-first UI: taps reveal more details (chart, fundamentals, order entry). Simple default view (symbol+price+%Δ). | Market Scanners generate dynamic watchlists (e.g. “Top Gainers”). Users can save multiple watchlist tabs, group symbols, and create “Custom Views” of columns【58†L35-L43】. Color highlights (green/red) on moves【55†L692-L700】. Anchored to the “Monitor” panel with tabbed portfolio/watchlists.

*Sources:* TradingView Watchlists documentation【1†L63-L69】【16†L70-L78】; TC2000 Help (adding columns)【19†L23-L30】【30†L24-L33】; Thinkorswim manual【32†L46-L50】【34†L23-L30】; Webull app screenshot【81†L186-L189】; IBKR Campus guide【55†L684-L693】【58†L35-L43】.

# Recommended Column Set for Zorivest

For active US equity traders, the most critical watchlist columns (beyond the ticker and note) are price, change, and volume, with some context on range and liquidity. A suggested priority list:

1. **Last Price** – Current bid or trade price (from real-time quote).  
2. **Change (Net)** – Price change vs previous close (numeric).  
3. **Change (%)** – Percent change vs previous close. These first three allow instant assessment of movers【1†L63-L69】【16†L70-L78】.  
4. **Volume** – Today’s volume, indicating activity. Helps spot unusual volume spikes.  
5. **Day Range (High/Low)** – Provides quick visual of intraday volatility【16†L70-L78】.  
6. **Bid / Ask** – Bid and ask quotes (or sizes), useful for liquidity insight.  
7. **VWAP (or Open)** – The volume-weighted average price (or simply “Open” price) to gauge intraday trend.  
8. **52-Week High / Low** – Contextual resistance/support levels (if available).  
9. **Mini-Chart (Sparkline)** – A small in-row chart of recent price trend (e.g. 1-day or 1-week sparkline) for at-a-glance trend. (Webull’s watchlist uses these【81†L186-L189】.)  
10. **Fundamental Indicators (optional)** – e.g. P/E ratio, if relevant to strategy.  
11. **Custom Notes/Alerts** – User’s own tags or notes on the ticker (Zorivest already has “notes”).

All numeric fields should be right-aligned and color-formatted (red vs green)【27†L132-L139】【55†L692-L700】. The REST `GET /quote?ticker=` provides price, change, %change, volume, etc., so most columns map directly to that. Static fields like 52-week range might come from a separate fundamentals API or an extended quote endpoint. A sparkline could be drawn from a small intraday series (fetched via existing time-series API), or generated on the fly if real-time ticks come in.

# React Implementation Guide

For the watchlist table in a React/Electron UI, use a high-performance data grid with virtual scrolling and efficient updates:

- **TanStack Table (React Table)** – Lightweight and headless, allowing full control over rendering and virtualization (e.g. via `react-virtual` or `react-window`). Can handle dynamic data updates by updating row data in state. (One community solution for keyboard navigation involves setting `tabIndex` on `<tr>` and handling arrow keys【89†L330-L339】.)  
- **AG Grid** – Popular enterprise grid. Supports streaming data via *async transactions* to batch updates【61†L293-L302】, enabling high-frequency quote updates without full re-renders. It also has built-in column filtering/sorting. (AG Grid’s client-side mode can handle thousands of rows and frequent updates efficiently.)  
- **MUI DataGrid / XGrid** – React DataGrid (Material UI) has a Pro version that supports live updates and virtual scrolling. It also offers a built-in Sparkline column type with the `@mui/x-charts` SparkLineChart component【66†L78-L86】, which can render mini-charts in cells.  
- **Other Options** – `react-data-grid` (adazzle), `Tabulator`, or `DevExtreme React Grid` are also capable of live updates. Many use canvas or WebGL for speed.

For number formatting, use a library like `numbro` or `Intl.NumberFormat` to color positive values green and negative red (or use CSS classes). Right-align numeric columns. To minimize re-renders, only update cell values that change (key by ticker). Consider splitting into multiple components (e.g. fixed symbol column vs dynamic price columns).

**Sparkline libraries:** For 20–50 mini-charts, use a very lightweight chart renderer. Options include:
- **MUI SparkLineChart** (uses lightweight SVG canvas)【66†L78-L86】.
- **react-sparklines** (SVG-based, simple API).
- **TradingView Lightweight Charts** (canvas; very performant for time series, though setup is heavier).
- **Chart.js or ApexCharts** – can draw small line charts, but may be overkill.
- **Custom Canvas drawing** – for maximum performance, draw lines directly on HTML5 canvas for each row.
Choose a library that can update points incrementally. Avoid full re-rendering of all sparklines on each tick.

Example snippet (using TanStack Table + MUI Sparkline):

```jsx
import { useTable } from '@tanstack/react-table';
import { SparkLineChart } from '@mui/x-charts';

// Define columns with custom sparkline cell:
const columns = [
  { header: 'Ticker', accessor: 'symbol' },
  { header: 'Last', accessor: 'last', cell: props => Number(props.value).toFixed(2) },
  { header: '% Change', accessor: 'pctChange', cell: props => (
      <span className={props.value >= 0 ? 'text-green' : 'text-red'}>
        {props.value.toFixed(2)}%
      </span>
    ) },
  // ... other columns ...
  { header: 'Trend', accessor: 'sparkData', cell: props => (
      <SparkLineChart
         data={props.value}
         height={30}
         color={props.row.original.pctChange >= 0 ? 'rgba(0,200,0,0.7)' : 'rgba(200,0,0,0.7)'}
      />
    ) },
];
const table = useTable({ data: watchlistData, columns });
```

All components should support efficient re-rendering on prop/data changes. Use React Query (TanStack Query) or SWR to fetch and cache quotes, with a short refresh interval.  

# Data Fetching Strategy

To handle rate limits and keep data fresh:

- **Stale-While-Revalidate Caching:** Use React Query’s staleTime/keepPreviousData features so that a watchlist still shows recent data while background refreshes run. This avoids flicker and limits API calls. For example, mark data stale after e.g. 10 seconds, then re-fetch.  
- **Batch Requests:** Whenever possible, use a batch-quote API. For example, Alpha Vantage’s *REALTIME_BULK_QUOTES* lets you fetch up to 100 tickers at once【70†L15-L23】. IEX Cloud’s batch endpoint (e.g. `stock/market/batch?symbols=AAPL,MSFT&types=quote`) returns multiple quotes in one call【72†L159-L168】. If using such provider, query 20–50 tickers in one request instead of 50 separate calls.  
- **Priority Queues:** Implement a queue that prioritizes visible/watchlist tickers and “favorite” lists first, delaying background updates for scrolled-off-screen items. For example, first fetch all quotes in the top 20 rows, then the next 20, etc. This can use incremental loading: as the user scrolls a virtualized table, trigger fetches for new visible symbols.  
- **Rate Limit Handling:** If provider limits calls/minute, enforce a throttle on request rate (using tokens or setTimeout), and catch rate-limit errors to retry later. You can fallback to less-frequent polling (e.g. every 15–30s) if data is not too stale.  
- **Data Freshness Indicators:** Show a small timestamp or status icon on each row indicating last update. For example, a tooltip on price like “Updated 30s ago”, or a faded text color for stale (>30s) data. UI cues (blinking “Loading…” icon, or dimming) help users know when data isn’t live.  
- **Incremental Columns:** Load essential columns (price, change) first, then secondary (extended-hours change, fundamentals) as separate queries. Use React Query dependent queries or trigger after initial render.

Example strategy: On mounting the watchlist view, use one batch request to get all last prices and % changes. Display these immediately. Then, for each ticker, asynchronously fetch bid/ask or 52wk range (maybe from a different API). Use optimistic updates so values fill in when ready.

# Design Specification (Dark Theme)

- **Color Palette:** On dark backgrounds (#121212 or #1E1E1E), use high-contrast text (#E0E0E0 or white) for readability. Lines or grid boundaries can be a subtle gray (#333 or #444). Use a bright color for positive (e.g. green #18C75E) and negative (e.g. red #E65A7C) values. For colorblind-friendliness, consider blue (#3399FF) for up and orange (#FFA500) for down instead of red/green【27†L132-L139】. Always also use arrows (▲/▼) or +/- signs to encode direction.  
- **Font & Sizing:** Use a clear, legible sans-serif (e.g. Roboto, Open Sans) at ~12px–14px for data cells. Header font can be slightly larger or bold. Ensure sufficient row height (~24–28px) to avoid cramped text.  
- **Spacing & Layout:** Align numeric columns right, text columns left. Use padding (8px) around cells to separate content. Freeze the ticker column so it’s always visible when horizontally scrolling. Use zebra striping or hover highlight (slightly lighter background on hover) to help row scanning.  
- **Visual Cues:** Alternate row shading subtly (e.g. #1A1A1A vs #121212) to delineate rows. Highlight selected row (or on focus) with a tinted overlay. For dark mode, avoid pure black (reduces eye strain) and pure white (for text). Aim for balanced contrast (WCAG AA standards).  
- **Color-Coding:** As noted, avoid red/green combos alone. Many traders are colorblind: Bloomberg uses yellow/blue for up/down, many charts let users customize. Provide an option or use blue/orange default. Also include a small up/down triangle icon or text in addition to color.  
- **Keyboard Navigation:** Make the table focusable. Support arrow keys: up/down moves selection, left/right (if grouping) navigates columns. Hitting a letter could jump to the first symbol starting with that letter (a common desktop pattern). Ensure all buttons and the search input are keyboard-accessible (tab order). Use proper ARIA roles for the grid (`role="table"`, `role="row"`, `role="gridcell"`). For example, with TanStack Table you can add `tabIndex="0"` to each `<tr>` and handle `onKeyDown` to focus the next/previous row【89†L330-L339】.  

# Quick Wins

- **Display Basic Columns:** Immediately implement Symbol, Last Price, Net Change, % Change, and Volume columns using the existing quote API. These require minimal new code and use already-fetched data. Highlight changes with color (green/red) by comparing to previous close.  
- **Sorting and Grouping:** Enable click-to-sort on columns (built-in in most React table libraries). Add the ability to group symbols by section (like TradingView’s custom sections). We already have a “notes” field – make it appear in the row.  
- **Search & Add Ticker:** Integrate the `GET /market-data/search?query=` to allow searching tickers by name or symbol and adding them to the watchlist. (Webull shows a simple add-button; mimic that.)  
- **Visual Highlight for Stale Data:** Implement a simple “updated at” timestamp in the corner of the watchlist pane. Shade rows in light gray if the last update was >30s ago. (No infrastructure change needed.)  
- **Dark Theme Styling:** Apply dark theme colors (text, background, gridlines) to the current list, verifying contrast. Traders often prefer dark mode by default, so this aligns with the existing app style.  

# Strategic Features

- **Real-Time Feeds:** Integrate a WebSocket or streaming API for quotes. This requires backend support or a long-lived connection to a data vendor. With streaming, remove the need for frequent polling and reduce API calls.  
- **Batch Quote Endpoint:** Build or acquire a backend feature that accepts multiple tickers and returns all quotes in one API call (e.g. proxy to Alpha V or IEX bulk endpoints). This allows efficient refresh of 50-ticker lists.  
- **Alerts & Conditional Formatting:** Add true/false “alert” columns or flags. For example, allow user to set “Price > X” and highlight rows when triggered. These need a rule engine (server or client-side) to evaluate conditions continuously.  
- **Order Entry / Trading Integration:** Eventually enable quick trade actions from the watchlist (e.g. right-click “Buy/Sell”). This involves more complex integration but is a common pro feature (seen in TOS, IBKR).  
- **Portfolio Linkage:** Add a “Star” or tag to mark symbols as favorites. Prioritize fetching for favorites. Also, allow grouping tickers by user-defined lists (like Webull’s multiple watchlists).  
- **Customization & Persistence:** Save column layouts and sorts per user. Enable drag/drop to reorder columns, and save these preferences (like IBKR’s Custom Views【58†L35-L43】).  

Each of these strategic features may need additional infrastructure (e.g. WebSocket service, condition evaluator, order APIs), but will greatly enhance the watchlist’s power and appeal.
