import os
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime, timedelta

st.set_page_config(page_title="AI Trader Paper", layout="wide")
st.title("🤖 AI Trader — Paper Trading")

# Načtení klíčů z Secrets (nejprve zkusit Streamlit secrets, jinak z .env)
def get_secret(key):
    try:
        return st.secrets[key]
    except Exception:
        return os.getenv(key)

load_dotenv()

ALPACA_API_KEY = get_secret("ALPACA_API_KEY")
ALPACA_SECRET_KEY = get_secret("ALPACA_SECRET_KEY")

if not ALPACA_API_KEY or not ALPACA_SECRET_KEY:
    st.error("Chybí ALPACA_API_KEY nebo ALPACA_SECRET_KEY")
    st.stop()

client = TradingClient(ALPACA_API_KEY, ALPACA_SECRET_KEY, paper=True)
data_client = StockHistoricalDataClient(ALPACA_API_KEY, ALPACA_SECRET_KEY)

# Zobrazení účtu
account = client.get_account()
col1, col2, col3 = st.columns(3)
col1.metric("Equity", f"${float(account.equity):,.2f}")
col2.metric("Cash", f"${float(account.cash):,.2f}")
col3.metric("Buying Power", f"${float(account.buying_power):,.2f}")

st.divider()

# Zobrazení pozic
st.subheader("📊 Pozice")
positions = client.get_all_positions()
if positions:
    rows = []
    for p in positions:
        rows.append({
            "Symbol": p.symbol,
            "Qty": float(p.qty),
            "Avg Entry": f"${float(p.avg_entry_price):.2f}",
            "Current": f"${float(p.current_price):.2f}",
            "P/L": f"${float(p.unrealized_pl):,.2f}",
            "P/L %": f"{float(p.unrealized_plpc)*100:.2f}%"
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True)
else:
    st.info("Žádné otevřené pozice")

st.divider()

# Výběr symbolu a zobrazení grafu
st.subheader("📈 Graf a signál")
symbol = st.selectbox("Symbol", ["SPY", "QQQ", "IWM", "GLD", "TLT"])

request = StockBarsRequest(
    symbol_or_symbols=symbol,
    timeframe=TimeFrame.Day,
    start=datetime.now() - timedelta(days=365)
)
bars = data_client.get_stock_bars(request)
df = bars.df.reset_index()
df = df[df["symbol"] == symbol].set_index("timestamp")
df["SMA50"] = df["close"].rolling(50).mean()

st.line_chart(df[["close", "SMA50"]])

price = float(df["close"].iloc[-1])
sma = float(df["SMA50"].iloc[-1])
signal = "V TRHU" if price > sma else "MIMO TRH"

st.metric(f"{symbol} cena", f"${price:.2f}", delta=f"SMA50 ${sma:.2f}")
st.metric("Signál", signal)
