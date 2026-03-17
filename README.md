# Algo Trading Bot

# Algorithmic Trading System with Backtesting

A trading system that automatically finds trading opportunities using candlestick patterns. It uses Angel Broking's SmartApi to get real-time stock data and tests trading strategies on historical data.

## What This Project Does

This system watches over 50 Indian stocks and looks for specific candlestick patterns (Three White Soldiers and Three Black Crows). When it finds these patterns, it automatically:
- Opens buy or sell positions
- Sets profit targets and stop losses
- Closes trades when targets are hit
- Tracks all wins and losses

## Main Features

✅ **Gets Real Data** - Connects to Angel Broking to get 5-minute candle data  
✅ **Pattern Detection** - Finds Three White Soldiers (good to buy) and Three Black Crows (good to sell)  
✅ **Tests Strategy** - Backtests the strategy on historical data to see if it would have made money  
✅ **Multiple Stocks** - Analyzes 50+ stocks at the same time  
✅ **Risk Control** - Uses stop losses, profit targets, and position sizing to manage risk  
✅ **Shows Results** - Creates charts showing profits, losses, and account balance over time  
✅ **Saves Results** - Exports all trades to CSV files for further analysis  

## The Trading Strategy

### When to Buy (LONG)
- Three White Soldiers pattern appears
- Current price is above the 20-day average
- RSI is below 70 (not too high)

### When to Sell (SHORT)
- Three Black Crows pattern appears
- Current price is below the 20-day average
- RSI is above 30 (not too low)

### How Trades End
Trades close when ONE of these happens first:

| Exit Type | What It Means |
|-----------|-------------|
| **Profit Target** | Made enough profit (1.5 x ATR) |
| **Stop Loss** | Lost 1% - need to cut losses |
| **Trailing Stop** | Price going opposite direction by 1% |
| **Time Limit** | Trade has been open 30 minutes |

### Position Size

The system risks 1% of the account on each trade. It calculates how many shares to buy/sell based on:
- How much money is available
- How far away the stop loss is
- Maximum leverage allowed (5x)
- Maximum number of open trades (2)

## How to Use This

### Step 1: Set Up

```bash
# Install Python packages
pip install -r BACKTEST_REQUIREMENTS.txt
```

### Step 2: Add Your API Keys

Create a file named `key.txt` with your Angel Broking account details:

```
API_KEY REFRESH_TOKEN CLIENT_CODE PASSWORD TOTP_SECRET
```

Get these from Angel Broking when you set up your account.

### Step 3: Run the System

```bash
# Open Jupyter
jupyter notebook

# Find and open: Quantitative_Multi_Stock_Pattern_Trading_System.ipynb

# Run all cells from top to bottom
```


### Run the Real-Time Paper Trading Bot (new)

A standalone Python script is now available: `angel_one_realtime_paper_bot.py`.

Set credentials via environment variables (recommended):

```bash
export ANGEL_API_KEY="your_api_key"
export ANGEL_CLIENT_CODE="your_client_code"
export ANGEL_PIN="your_pin_or_password"
export ANGEL_TOTP_SECRET="your_totp_secret"
python angel_one_realtime_paper_bot.py
```

(Backward compatible fallback: `key.txt` is still supported.)


Rate-limit controls (recommended for AB1019):

```bash
export SYMBOLS_PER_CYCLE="8"
export SYMBOL_REQUEST_GAP_SECONDS="1.2"
export RATE_LIMIT_COOLDOWN_SECONDS="30"
```

The bot scans symbols in rotating batches instead of hitting all symbols every loop, which helps prevent SmartAPI historical-data throttling.

This script now follows official SmartAPI SDK flow (`SmartConnect`, `generateSession`, `getfeedToken`, `getProfile`) and runs the same pattern strategy in a live polling loop with retry + session refresh handling.

Logs:
- `paper_trades.csv`
- `paper_equity.csv`

### Step 4: Check the Results

The system will show:
- **Equity Chart** - How much money you had at each point in time
- **Drawdown Chart** - Biggest losses from peak
- **P&L Distribution** - Bar chart of all trades (wins and losses)
- **Open Trades Chart** - How many trades were open at each time

### Step 5: Save Results

Three CSV files are created:
- `backtest_trades.csv` - Details of every trade
- `backtest_equity.csv` - Account balance over time
- `backtest_concurrent.csv` - Number of open positions over time

## Settings You Can Change

Open the notebook and find Cell 6. You can change:

```python
CAPITAL = 300000        # Starting money in Rupees
LEVERAGE = 5            # How much you can borrow from broker
MAX_TRADES = 2          # Most trades open at the same time
VOLUME_FILTER = True    # Check if volume is increasing (for pattern confirmation)
TRADING_DAYS = 40       # How many days of old data to use
```

## The Files

```
algo_trading/
├── notebooks/
│   └── Quantitative_Multi_Stock_Pattern_Trading_System.ipynb
├── BACKTEST_README.md          # Full detailed explanation
├── BACKTEST_REQUIREMENTS.txt   # Python packages needed
├── README.md                   # This file
├── main.py                     # Main script
├── live.py                     # Live trading code
└── paper_trader.py             # Paper trading code
```

## Understanding the Results

### Important Numbers (Metrics)

- **Total Trades** - How many trades the system made
- **Win Rate** - What % of trades made money
- **Total P&L** - Total profit or loss in Rupees
- **Max Drawdown** - Biggest drop in account value
- **Sharpe Ratio** - How much profit per unit of risk (higher is better)

### CSV File Columns (backtest_trades.csv)

```
Stock          - Stock name (like INFY, TCS)
Direction      - BUY or SELL
Entry Time     - When trade opened
Exit Time      - When trade closed
Entry          - What price it opened at
Exit           - What price it closed at
Qty            - How many shares
Gross PnL      - Total profit/loss in Rupees
Win/Loss       - Did it make or lose money
Duration       - How long trade was open
Reason         - Why trade closed (profit target, stop loss, etc)
```

## What This Uses

- **Angel Broking SmartApi** - To get real-time stock data
- **Python Libraries** - pandas, numpy, matplotlib (for analysis and charts)
- **Jupyter Notebook** - For writing code and showing results

## Important Things to Know

⚠️ **This is NOT a live trading system yet** - It only tests strategies on old data

⚠️ **Past results don't mean future profits** - Just because it worked before doesn't mean it will work again

⚠️ **Real trading is different** - Real world has delays, fees, and prices might not fill at expected prices

⚠️ **You can lose money** - Trading always has risk. Only trade with money you can afford to lose.

⚠️ **API Limits** - Angel Broking limits how many requests you can make. This system waits 3 seconds between requests.

## How to Add New Stocks

Find Cell 10 in the notebook. Add your stock like this:

```python
tokens = {
    "RELIANCE": {"exchange": "NSE", "token": "1594"},
    "YOUR_STOCK": {"exchange": "NSE", "token": "XXXXX"},
}
```

Get the token number from Angel Broking's documentation.

## For More Details

Read [BACKTEST_README.md](BACKTEST_README.md) for a complete explanation of how the system works.

## Questions?

Check:
1. Angel Broking SmartApi documentation for API issues
2. Make sure your internet is working
3. Verify your key.txt file has correct information
4. Check market is open (9:15 AM - 3:30 PM IST)

---

**Made:** January 2026  
**For:** Learning and testing trading ideas  
**Status:** In development  
**Python:** Version 3.8 or newer required
