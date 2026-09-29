import pandas as pd

import yfinance as yf


def calculate_rsi(prices, period=14):
    delta = prices.diff()

    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)

    average_gain = gains.rolling(period).mean()
    average_loss = losses.rolling(period).mean()

    rs = average_gain / average_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi


def get_market_data(symbol):
    data = yf.download(
        symbol,
        period="3mo",
        interval="1d",
        auto_adjust=True,
        progress=False,
    )

    close = data["Close"]

    if hasattr(close, "columns"):
        close = close.iloc[:, 0] 
    close = close.squeeze()
    data["SMA20"] = close.rolling(20).mean()

    data["SMA50"] = close.rolling(50).mean()

    data["RSI"] = calculate_rsi(close)

    latest = data.dropna().iloc[-1]

    return {
        "symbol": symbol,
        "price": float(latest["Close"].iloc[0]),
"sma20": float(latest["SMA20"].iloc[0]),
        "sma50": float(latest["SMA50"].iloc[0]),
        "rsi": float(latest["RSI"].iloc[0]),
    }


def generate_signal(data):
    long_score = 0
    short_score = 0

    # 1. Cena vs SMA20
    if data["price"] > data["sma20"]:
        long_score += 1
    else:
        short_score += 1

    # 2. Trend SMA20 vs SMA50
    if data["sma20"] > data["sma50"]:
        long_score += 1
    else:
        short_score += 1

    # 3. RSI
    if data["rsi"] < 50:
        long_score += 1
    else:
        short_score += 1

    if long_score >= 2:
        return "LONG"

    if short_score >= 2:
        return "SHORT"

    return "NO_TRADE"


    if data["rsi"] > 60 and data["price"] < data["sma20"]:
        return "SHORT"

    return "NO_TRADE"



def ai_analysis(data):
    price = data["price"]
    sma20 = data["sma20"]
    sma50 = data["sma50"]
    rsi = data["rsi"]

    if price > sma20 and sma20 > sma50:
        trend = "BULLISH"
    elif price < sma20 and sma20 < sma50:
        trend = "BEARISH"
    else:
        trend = "NEUTRAL"

    if rsi < 40:
        momentum = "OVERSOLD"
    elif rsi > 60:
        momentum = "OVERBOUGHT"
    else:
        momentum = "NEUTRAL"

    signal = generate_signal(data)

    if signal == "LONG":
        confidence = 70
    elif signal == "SHORT":
        confidence = 70
    else:
        confidence = 50

    return f"""
MARKET ANALYSIS
----------------
Price:      ${price:.2f}
RSI:        {rsi:.2f}
SMA20:      ${sma20:.2f}
SMA50:      ${sma50:.2f}

TREND:      {trend}
MOMENTUM:   {momentum}
SIGNAL:     {signal}
CONFIDENCE: {confidence}%

REASON:
Price relative to SMA20/SMA50 and RSI were used to determine the signal.
"""


    return reason


if __name__ == "__main__":
    market = get_market_data("SPY")
    signal = generate_signal(market)

    print()
    print("===== AI TRADER =====")
    print(f"Symbol: {market['symbol']}")
    print(f"Price:  ${market['price']:.2f}")
    print(f"SMA 20: ${market['sma20']:.2f}")
    print(f"SMA 50: ${market['sma50']:.2f}")
    print(f"RSI:    {market['rsi']:.2f}")
    print(f"Signal: {signal}")
    print(f"AI analýza: {ai_analysis(market)}")
    print("=====================")



def backtest(symbol="SPY", initial_cash=10000):
    data = yf.download(
        symbol,
        period="10y",
        interval="1d",
        auto_adjust=True,
        progress=False,
    )

    if isinstance(data.columns, pd.MultiIndex):
        data = data.xs(symbol, axis=1, level=1)

    close = data["Close"]

    data["SMA20"] = close.rolling(20).mean()
    data["SMA50"] = close.rolling(50).mean()
    data["RSI"] = calculate_rsi(close)

    data = data.dropna()

    # Rozdělení dat: 70 % trénink, 30 % nezávislý test
    split_index = int(len(data) * 0.7)
    train_data = data.iloc[:split_index]
    test_data = data.iloc[split_index:]

    print()
    print("===== DATA SPLIT =====")
    print(f"TRAIN: {train_data.index[0].date()} -> {train_data.index[-1].date()}")
    print(f"TEST:  {test_data.index[0].date()} -> {test_data.index[-1].date()}")
    print("======================")

    # Prozatím backtestujeme testovací část
    data = test_data

    cash = initial_cash
    shares = 0

    long_signals = 0
    short_signals = 0
    no_trade_signals = 0
    trades = []

    pending_signal = None

    for date, row in data.iterrows():

        market = {
            "symbol": symbol,
            "price": float(row["Close"]),
            "sma20": float(row["SMA20"]),
            "sma50": float(row["SMA50"]),
            "rsi": float(row["RSI"]),
        }

        # Provedeme včerejší signál za dnešní otevírací cenu
        signal = pending_signal if pending_signal else "NONE"
        pending_signal = generate_signal(market)
        market["price"] = float(row["Open"])

        if signal == "LONG":
            long_signals += 1

            if shares == 0:
                shares = cash / market["price"]
                cash = 0
                trades.append(("BUY", date, market["price"]))

        elif signal == "SHORT":
            short_signals += 1

            if shares > 0:
                cash = shares * market["price"]
                shares = 0
                trades.append(("SELL", date, market["price"]))

        else:
            no_trade_signals += 1

    # Zavření případné pozice na poslední ceně
    last_price = float(data.iloc[-1]["Close"])

    if shares > 0:
        cash = shares * last_price
        shares = 0

    final_value = cash
    profit = final_value - initial_cash

    # Srovnání: kdybych jen koupil a držel
    first_price = float(data.iloc[0]["Close"])
    bh_value = initial_cash * last_price / first_price
    bh_profit = bh_value - initial_cash

    # Statistiky jednotlivých obchodů
    completed_trades = []

    for i in range(0, len(trades) - 1, 2):
        buy = trades[i]
        sell = trades[i + 1]

        buy_price = buy[2]
        sell_price = sell[2]

        trade_profit = (sell_price - buy_price) / buy_price * 100
        completed_trades.append(trade_profit)

    winning_trades = [p for p in completed_trades if p > 0]
    losing_trades = [p for p in completed_trades if p <= 0]

    if completed_trades:
        win_rate = len(winning_trades) / len(completed_trades) * 100
        avg_profit = sum(completed_trades) / len(completed_trades)
        best_trade = max(completed_trades)
        worst_trade = min(completed_trades)
    else:
        win_rate = 0
        avg_profit = 0
        best_trade = 0
        worst_trade = 0

    print()
    print("===== BACKTEST =====")
    print(f"Symbol: {symbol}")
    print(f"Start:  ${initial_cash:,.2f}")
    print(f"End:    ${final_value:,.2f}")
    print(f"Profit: ${profit:,.2f}")
    print(f"Buy & hold: ${bh_profit:,.2f} ({bh_profit / initial_cash * 100:.2f}%)")
    print(f"Strategie:  ${profit:,.2f} ({profit / initial_cash * 100:.2f}%)")
    print()
    print("SIGNÁLY:")
    print(f"LONG:      {long_signals}")
    print(f"SHORT:     {short_signals}")
    print(f"NO_TRADE:  {no_trade_signals}")
    print()
    print(f"Trades: {len(trades)}")

    print()
    print("STATISTIKY OBCHODŮ:")
    print(f"Dokončené obchody: {len(completed_trades)}")
    print(f"Ziskové obchody:   {len(winning_trades)}")
    print(f"Ztrátové obchody:  {len(losing_trades)}")
    print(f"Win rate:          {win_rate:.1f}%")
    print(f"Průměr na obchod:  {avg_profit:.2f}%")
    print(f"Nejlepší obchod:   {best_trade:.2f}%")
    print(f"Nejhorší obchod:   {worst_trade:.2f}%")

    if trades:
        print()
        print("OBCHODY:")
        for action, date, price in trades:
            print(f"{action:4} {date.date()}  ${price:.2f}")

    print("====================")


if __name__ == "__main__":
    backtest("SPY")
