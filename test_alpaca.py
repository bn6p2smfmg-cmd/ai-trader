import os
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient

load_dotenv()

api_key = os.getenv("ALPACA_API_KEY")
secret_key = os.getenv("ALPACA_SECRET_KEY")

if not api_key or not secret_key:
    print("CHYBA: API klíče nebyly načteny z .env")
    raise SystemExit(1)

client = TradingClient(
    api_key,
    secret_key,
    paper=True
)

account = client.get_account()

print("PRIPOJENI K ALPACA: OK")
print("Paper účet:", account.account_number)
print("Cash:", account.cash)
print("Buying power:", account.buying_power)

