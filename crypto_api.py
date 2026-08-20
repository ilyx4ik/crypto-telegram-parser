import ccxt
import pandas as pd
import requests

exchange = ccxt.binance({"timeout": 10000})


def get_coin_info(symbol: str):
  try:
    ticker = exchange.fetch_ticker(symbol)
    price = round(ticker["last"], 2)
    change_24h = round(ticker["percentage"], 2)
    return {"price": price, "change_24h": change_24h}
  except Exception as e:
    print(f"Ошибка при получении цены: {e}")
    return None


def get_historical_klines(coin: str, interval="1h", limit=250):
  symbol = coin.replace("/", "")
  url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"

  try:
    response = requests.get(url, timeout=10)
    data = response.json()

    df = pd.DataFrame(
        data,
        columns=[
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "close_time",
            "qav",
            "num_trades",
            "taker_base_vol",
            "taker_quote_vol",
            "ignore",
        ],
    )

    df["close"] = df["close"].astype(float)
    return df
  except Exception as e:
    print(f"Ошибка получения свечей для {coin}: {e}")
    return None