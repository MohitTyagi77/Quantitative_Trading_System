# Quantitative Multi-Stock Pattern Trading System

This is a system that automatically tests trading strategies on historical stock data. It uses Angel Broking's SmartApi to get real-time stock prices and finds patterns to buy and sell stocks.

## What is This?

Think of it like a robot that:
1. Watches the prices of 50+ stocks
2. Looks for specific candlestick patterns
3. Automatically buys or sells when it finds these patterns
4. Closes trades when it makes enough profit or loses enough money
5. Keeps track of how much money it made or lost

This is a **backtest** system, which means it tests the strategy on old data to see if it would have worked. It's like running a time machine to see if your idea would have made money in the past.

## The Trading Strategy - Simple Version

### What Are Three White Soldiers?
A pattern where the price goes UP for 3 days in a row. This usually means the price will keep going up.
- Signal: **BUY**

### What Are Three Black Crows?
A pattern where the price goes DOWN for 3 days in a row. This usually means the price will keep going down.
- Signal: **SELL**

### Entry Rules (When to Start a Trade)

**To BUY (LONG):**
- Three White Soldiers pattern shows up
- Price is above the 20-day average price
- RSI (a speed/momentum number) is less than 70

**To SELL (SHORT):**
- Three Black Crows pattern shows up
- Price is below the 20-day average price
- RSI is greater than 30

### Exit Rules (When to End a Trade)

A trade closes when the FIRST of these happens:

| Exit Type | Meaning |
|-----------|---------|
| **Profit Target** | Made 1.5 times the volatility (ATR) in profit |
| **Stop Loss** | Lost 1% from entry price |
| **Trailing Stop** | Price went opposite direction by 1% from highest/lowest point |
| **Time Exit** | Trade has been open for 30 minutes (6 five-minute candles) |

### How Much Money to Risk

The system automatically decides how many shares to buy/sell:
- Risk: 1% of account per trade
- How many shares: Based on the distance to stop loss
- Max leverage: 5x (can borrow up to 5 times your money)
- Max open trades at once: 2

## Technical Indicators Used

1. **MA20** - Average price for last 20 candles (shows trend direction)
2. **ATR** - How much price moves on average (used for profit targets and stops)
3. **RSI** - Momentum number 0-100 (used to check if price is too high or low)

## How to Run This

### Get Ready

```bash
# Install everything you need
pip install -r BACKTEST_REQUIREMENTS.txt
```

### Add Your Broker Info

Create a file called `key.txt` with:

```
API_KEY REFRESH_TOKEN CLIENT_CODE PASSWORD TOTP_SECRET
```

Get these from Angel Broking's website.

### Run It

```bash
# Start Jupyter
jupyter notebook

# Open: Quantitative_Multi_Stock_Pattern_Trading_System.ipynb

# Run all cells (or press Ctrl+A then Ctrl+Enter)
```

Wait 3-5 minutes while it:
- Downloads stock data from Angel Broking
- Finds the patterns
- Tests the strategy
- Makes charts and numbers

### Look at Results

Four charts appear:
1. **Equity Curve** - Shows how much money you had over time
2. **Drawdown** - Shows biggest loss from peak
3. **P&L Distribution** - Bar chart of all wins and losses
4. **Concurrent Trades** - Shows how many open trades at each time

Three CSV files are saved:
- `backtest_trades.csv` - Every single trade
- `backtest_equity.csv` - Account balance over time
- `backtest_concurrent.csv` - Open positions count over time

## What the Numbers Mean

After running, you see:

| Number | What It Means |
|--------|---------------|
| **Total Trades** | How many trades were made |
| **Long Trades** | Buys |
| **Short Trades** | Sells |
| **Total P&L** | Total money made or lost (₹) |
| **Win Rate (%)** | What % of trades made money |
| **Max Drawdown (%)** | Biggest % drop in account value |
| **Sharpe Ratio** | Profit per unit of risk (higher is better) |

## You Can Change Things

In Cell 6 of the notebook:

```python
CAPITAL = 300000        # Starting money
LEVERAGE = 5            # How much you can borrow
MAX_TRADES = 2          # Most trades open at once
VOLUME_FILTER = True    # Check if trading volume is increasing
TRADING_DAYS = 40       # How many days of old data to use
```

Change these and run again to test different ideas.

## Add Different Stocks

In Cell 10, you can add more stocks:

```python
tokens = {
    "INFY": {"exchange": "NSE", "token": "1594"},
    "YOURSTOCK": {"exchange": "NSE", "token": "XXXXX"},
}
```

Find stock tokens on Angel Broking's website.

## What the CSV Files Show

### backtest_trades.csv columns:

```
Stock          - Stock name (INFY, TCS, etc)
Direction      - LONG (buy) or SHORT (sell)
Entry Time     - When trade started
Exit Time      - When trade ended
Entry          - Price at entry
Exit           - Price at exit
Qty            - Number of shares
Net PnL        - Money made or lost
Reason         - Why it closed (TP=profit, SL=stop loss, etc)
Trade Duration - How long trade was open in minutes
```

## Important Things to Remember

⚠️ **This is a TEST, not real trading**
- It uses old data
- Real world is different (fees, delays, price changes)

⚠️ **Past success ≠ Future success**
- Just because it worked before doesn't mean it will work again
- Markets change, patterns change

⚠️ **Trading has risk**
- You can lose money
- Only trade with money you can afford to lose
- This system didn't account for commissions or taxes

⚠️ **Angel Broking Limits**
- API has request limits
- System waits 3 seconds between requests
- Takes 3-5 minutes to run with 50+ stocks

⚠️ **Market Hours Matter**
- Best to run during/after market hours (9:15 AM - 3:30 PM IST)
- Won't get data if market is closed

## Troubleshooting

**"No data for XYZ stock"**
- Stock might not exist or token is wrong
- Market might be closed
- API limit reached

**"Login failed"**
- Check key.txt has correct information
- Check internet connection
- Contact Angel Broking support

**Code doesn't run**
- Make sure all packages installed: `pip install -r BACKTEST_REQUIREMENTS.txt`
- Use Python 3.8+
- Restart Jupyter if needed

## What Uses What

- **Angel Broking SmartApi** - Gets stock data
- **Pandas/NumPy** - Does math and analysis
- **Matplotlib** - Makes charts
- **Jupyter** - Lets you write and run code

## Next Steps

1. Change the stocks list to ones you care about
2. Change the settings and see how results change
3. Add your own indicators if you want
4. Think about how to make the strategy better

---

**Created:** January 2026  
**What For:** Learning algorithmic trading  
**Status:** Works great for testing ideas  
**Needs:** Python 3.8+, Angel Broking account

## 📋 Overview

This backtesting system implements a multi-stock, pattern-based trading strategy using technical analysis. It detects **Three White Soldiers** (bullish) and **Three Black Crows** (bearish) candlestick patterns across 50+ Indian stocks and simulates portfolio performance.

### Key Features

✅ **Real-time Data Integration** - Fetches 5-minute candlestick data directly from Angel Broking broker API  
✅ **Pattern Recognition** - Detects Three White Soldiers and Three Black Crows candlestick patterns  
✅ **Multi-Stock Strategy** - Simultaneously analyzes 50+ stocks across NSE  
✅ **Advanced Risk Management** - Implements stop-loss, profit targets, trailing stops, and position sizing  
✅ **Leverage Support** - Accounts for broker leverage (5x) in position calculations  
✅ **Comprehensive Metrics** - Calculates win rates, max drawdown, Sharpe ratio, and more  
✅ **Performance Visualization** - Generates equity curves, drawdown charts, and trade analysis plots  
✅ **CSV Export** - Saves all results for further analysis  

## 🎯 Trading Strategy

### Entry Rules

**LONG Signals:**
- Three White Soldiers pattern detected
- Close price > 20-period Moving Average (MA20)
- RSI (14) < 70 (not overbought)

**SHORT Signals:**
- Three Black Crows pattern detected
- Close price < 20-period Moving Average (MA20)
- RSI (14) > 30 (not oversold)

### Exit Rules

Each position exits on **first occurrence** of:

| Exit Type | Condition |
|-----------|-----------|
| **Profit Target** | Entry + (1.5 × ATR) for long / Entry - (1.5 × ATR) for short |
| **Stop Loss** | Entry × 0.99 (1% loss) |
| **Trailing Stop** | 1% below highest price (long) / 1% above lowest price (short) |
| **Time Exit** | After 6 candles (30 minutes) |

### Position Sizing

```
Risk per Trade = 1% of Account Capital
Stop Distance = 1% from Entry Price
Quantity = min(Risk-based Qty, Leverage Constraint, Valid Lot Size)
Max Concurrent Positions = 2 (configurable)
Account Leverage = 5x
```

## 📊 Technical Indicators

1. **Moving Average (MA20)** - 20-period simple moving average for trend direction
2. **ATR (14)** - Average True Range for volatility-based profit targets and stops
3. **RSI (14)** - Relative Strength Index for momentum confirmation

## 🔧 Configuration Parameters

Edit these values in **Cell 6** to customize the strategy:

```python
CAPITAL = 300000        # Starting capital in INR
LEVERAGE = 5            # Broker leverage multiplier
MAX_TRADES = 2          # Maximum concurrent open positions
VOLUME_FILTER = True    # Require volume confirmation for patterns
TRADING_DAYS = 40       # Historical data lookback period
```

## 📁 Project Structure

```
Quantitative_Multi_Stock_Pattern_Trading_System.ipynb
├── Cell 1: Environment Test
├── Cell 2: Core Library Imports
├── Cell 3: Extended Library Imports
├── Cell 4: Load API Credentials
├── Cell 5: Broker Authentication
├── Cell 6: Configuration Parameters
├── Cell 7: Technical Indicators & Data Fetching
├── Cell 8: Pattern Detection Functions
├── Cell 9: Backtest Engine
├── Cell 10: Stock Universe Definition
├── Cell 11: Data Fetching & Pattern Detection
├── Cell 12: Backtest Execution & Analysis
└── Cell 13: Results Export
```

## 🚀 Quick Start

### 1. Prerequisites

```bash
# Python 3.8+
python --version

# Install dependencies
pip install -r requirements.txt
```

### 2. Setup Broker Credentials

Create a `key.txt` file in the project root with Angel Broking API credentials:

```
API_KEY REFRESH_TOKEN CLIENT_CODE PASSWORD TOTP_SECRET
```

Format: Space-separated values on a single line

### 3. Run the System

```bash
# Launch Jupyter notebook
jupyter notebook

# Open Quantitative_Multi_Stock_Pattern_Trading_System.ipynb
# Run all cells in order (Ctrl+A then Ctrl+Enter)
# Or run cells individually for step-by-step analysis
```

### 4. View Results

- **Equity Curve** - Shows portfolio value progression
- **Drawdown Chart** - Visualizes peak-to-trough declines
- **P&L Distribution** - Histogram of trade outcomes
- **Concurrent Trades** - Open position count over time

### 5. Export Results

Three CSV files are generated:
- `backtest_trades.csv` - Individual trade details
- `backtest_equity.csv` - Equity values over time
- `backtest_concurrent.csv` - Open position counts over time

## 📈 Understanding the Output

### Trade Metrics

| Metric | Description |
|--------|-------------|
| **Total Trades** | Number of completed trades |
| **Long/Short Trades** | Breakdown by direction |
| **Total P&L** | Sum of all trade profits/losses |
| **Win Rate (%)** | Percentage of profitable trades |
| **Max Drawdown (%)** | Largest peak-to-trough decline |
| **Sharpe Ratio** | Risk-adjusted return metric |

### CSV Columns (backtest_trades.csv)

```
Stock           - Stock symbol (NSE ticker)
Direction       - Trade direction (long/short)
Entry Time      - Trade entry timestamp
Exit Time       - Trade exit timestamp
Entry           - Entry price
Exit            - Exit price
Qty             - Quantity traded
Gross PnL       - Total profit/loss in INR
Net PnL         - Net P&L after fees
Trade Duration  - Duration in minutes
Reason          - Exit reason (TP/SL/TS/Timeout)
```

## 🔄 API Rate Limiting

The script includes 3-second delays between API calls to respect broker rate limits:
- Total runtime: ~50-60 stocks × 3 seconds = 3-5 minutes
- Handles rate limiting gracefully with try-catch blocks

## ⚠️ Limitations & Disclaimers

⚡ **Backtest vs Live Performance**
- Past performance ≠ future results
- Backtest assumes perfect fill at bar close prices
- Slippage, commissions, and taxes not included
- Market gaps and circuit breakers not modeled

⚡ **Stock Universe**
- Limited to 50+ NSE stocks
- Add/remove stocks by modifying Cell 10
- Ensure instrument tokens are current

⚡ **Data Freshness**
- Uses up to 40 days of historical data
- Works best with post-market hours execution
- Real-time data requires active market hours

## 🛠️ Customization

### Add New Stocks

Edit the `tokens` dictionary in **Cell 10** of the system:

```python
tokens = {
    "NEW_STOCK": {"exchange": "NSE", "token": "XXXXX"},
    ...
}
```

### Modify Trading Parameters

Edit **Cell 6** of the system:

```python
CAPITAL = 500000        # Increase starting capital
MAX_TRADES = 3          # Allow more concurrent positions
VOLUME_FILTER = False   # Disable volume confirmation
```

### Change Indicators

Edit **Cell 7** (RSI period, MA20 period, ATR period):

```python
df["MA50"] = df["close"].rolling(window=50).mean()
df["RSI"] = compute_rsi(df["close"], 21)  # Change period
```

## 📦 Dependencies

All dependencies are listed in `requirements.txt`:

- `pandas` - Data manipulation and analysis
- `numpy` - Numerical computing
- `matplotlib` - Data visualization
- `smartapi-python` - Angel Broking API client
- `pyotp` - TOTP authentication
- `python-dateutil` - Date utilities

## 🤝 Contributing

To improve the strategy:

1. Modify pattern detection logic in **Cell 8**
2. Add new technical indicators in **Cell 7**
3. Adjust risk management in **Cell 9**
4. Test with different time periods and parameter combinations
5. Export and analyze results in CSV files

## 📞 Support

For issues:
- Check broker API documentation (Angel Broking)
- Verify `key.txt` credentials format
- Ensure market hours (9:15 AM - 3:30 PM IST)
- Check network connectivity and API rate limits

## 📄 License

This project is provided as-is for educational and research purposes.

## ⚖️ Disclaimer

**NOT FINANCIAL ADVICE**

This backtesting system is for educational purposes only. The strategy has not been tested in live trading conditions. Past performance does not guarantee future results. Do not use real money without extensive live testing and proper risk management. All trading involves risk of loss.

---

**Last Updated:** January 2026  
**Author:** Algorithmic Trading Team  
**Version:** 1.0
