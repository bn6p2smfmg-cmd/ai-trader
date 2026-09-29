import os
from dotenv import load_dotenv
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime, timedelta
import pandas as pd

load_dotenv()

def load(symbol="SPY", period="10y"):
    client = StockHistoricalDataClient(
        os.getenv("ALPACA_API_KEY"),
        os.getenv("ALPACA_SECRET_KEY")
    )
    
    # Převod "10y" na počet dní
    days = 3650 if period == "10y" else (365 if period == "1y" else 180)
    start = datetime.now() - timedelta(days=days)
    
    request = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=TimeFrame.Day,
        start=start
    )
    
    bars = client.get_stock_bars(request)
    df = bars.df.reset_index()
    df = df[df["symbol"] == symbol].set_index("timestamp")
    return df["close"]

# Zachovat původní run() logiku beze změny
def run(symbol="SPY"):
    c = load(symbol)
    sma50 = c.rolling(50).mean()
    ret = c.pct_change()
    rules = {
        "Buy & hold": pd.Series(1, index=c.index),
        "Cena > SMA50": (c > sma50).astype(int),
    }
    valid = sma50.dropna().index
    split = int(len(valid) * 0.7)
    parts = {"TRAIN": valid[:split], "TEST": valid[split:]}

    for name, idx in parts.items():
        print()
        print(f"===== {name}: {idx[0].date()} -> {idx[-1].date()} =====")
        print(f"{'':16} {'výnos':>9} {'max. propad':>13}")
        for r, pos in rules.items():
            p = pos.shift(1).fillna(0)
            daily = (p * ret).loc[idx].fillna(0)
            eq = (1 + daily).cumprod()
            print(f"{r:16} {(eq.iloc[-1]-1)*100:8.1f} % {(eq/eq.cummax()-1).min()*100:11.1f} %")

    today = "V TRHU (cena nad SMA50)" if c.iloc[-1] > sma50.iloc[-1] else "MIMO TRH (cena pod SMA50)"
    print()
    print(f"DNES {c.index[-1].date()}: {symbol} ${c.iloc[-1]:.2f}, SMA50 ${sma50.iloc[-1]:.2f} -> {today}")


if __name__ == "__main__":
    run()
