import os
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from compare import load

load_dotenv()

TRADING_CLIENT = TradingClient(
    os.getenv("ALPACA_API_KEY"),
    os.getenv("ALPACA_SECRET_KEY"),
    paper=True  # Klíčové: simulované obchodování
)

def get_position(symbol):
    try:
        return TRADING_CLIENT.get_open_position(symbol)
    except Exception:
        return None

def main(symbol="GLD"):
    c = load(symbol, period="6mo")
    sma50 = c.rolling(50).mean()
    price = float(c.iloc[-1])
    sma = float(sma50.iloc[-1])
    signal = "IN" if price > sma else "OUT"

    position = get_position(symbol)

    if signal == "IN" and position is None:
        order = MarketOrderRequest(
            symbol=symbol,
            notional=1000,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY
        )
        TRADING_CLIENT.submit_order(order)
        print(f"KOUPENO: {symbol} @ ${price:.2f}")

    elif signal == "OUT" and position is not None:
        TRADING_CLIENT.close_position(symbol)
        print(f"PRODÁNO: {symbol} @ ${price:.2f}")

    else:
        state = "drží pozici" if position else "bez pozice"
        print(f"BEZ AKCE: {signal}, {state}")

if __name__ == "__main__":
    main()
