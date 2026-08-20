import pandas as pd
from crypto_api import get_coin_info, get_historical_klines
from news_api import get_latest_news
from sentiment import analyze_sentiment


def calculate_indicators(df: pd.DataFrame):
  df["ema_50"] = df["close"].ewm(span=50, adjust=False).mean()
  df["ema_200"] = df["close"].ewm(span=200, adjust=False).mean()

  delta = df["close"].diff()
  gain = delta.clip(lower=0)
  loss = -1 * delta.clip(upper=0)

  ema_gain = gain.ewm(span=14, adjust=False).mean()
  ema_loss = loss.ewm(span=14, adjust=False).mean()

  RS = ema_gain / ema_loss
  df["rsi"] = 100 - (100 / (1 + RS))

  latest = df.iloc[-1]

  return {
      "rsi": latest["rsi"],
      "ema_50": latest["ema_50"],
      "ema_200": latest["ema_200"],
  }


def get_hybrid_signal(coin: str, sentiment_score: int):
  df = get_historical_klines(coin, interval="1h", limit=250)

  if df is None or df.empty:
    return f"❌ Не удалось получить технические данные для {coin}."

  indicators = calculate_indicators(df)

  rsi = indicators["rsi"]
  ema_50 = indicators["ema_50"]
  ema_200 = indicators["ema_200"]

  trend = "Восходящий 📈" if ema_50 > ema_200 else "Нисходящий 📉"

  if rsi < 30 and sentiment_score >= 1:
    signal = "Strong BUY 🚀"
    reason = "RSI в зоне перепроданности (<30) + позитивный новостной фон."
  elif rsi > 70 and sentiment_score <= -1:
    signal = "Strong SELL 💥"
    reason = "RSI в зоне перекупленности (>70) + негативный новостной фон."
  elif rsi < 30:
    signal = "Weak BUY 🟢"
    reason = "Перепроданность по RSI, но нет подтверждения в новостях."
  elif rsi > 70:
    signal = "Weak SELL 🔴"
    reason = "Перекупленность по RSI, но нет подтверждения в новостях."
  else:
    signal = "Neutral 🟡"
    reason = "Рынок в консолидации, четких сигналов нет."

  return (
      f"📊 **Гибридный анализ {coin}:**\n"
      f"📈 **Тренд (EMA 50/200):** {trend}\n"
      f"📏 **RSI (14):** {rsi:.1f}\n"
      f"📰 **Сентимент-балл:** {sentiment_score}\n\n"
      f"🎯 **Итоговый сигнал:** {signal}\n"
      f"💡 *{reason}*"
  )


def get_market_summary(symbol="BTC/USDT"):
  score = 0

  data = get_coin_info(symbol)
  if not data:
    return "Не удалось получить данные о цене"

  price = data["price"]
  change_24h = data["change_24h"]

  if change_24h > 1.5:
    score += 1
  elif change_24h < -1.5:
    score -= 1

  news_list = get_latest_news()

  # 1. ИСПРАВЛЕНО: Проверка сентимента внутри цикла
  for item in news_list:
    sentiment = analyze_sentiment(item["title"])
    if "Positive 🚀" in sentiment:
      score += 1
    elif "Negative 📉" in sentiment:
      score -= 1

  if score >= 2:
    verdict = "🟢 Рынок настроен бычье (Bullish). Покупатели доминируют"
  elif score <= -2:
    verdict = "🔴 На рынке давление медведей (Bearish). Высокие риски."
  else:
    verdict = "🟡 Рынок в нейтральном / боковом состоянии (Neutral)."

  # 2. ИСПРАВЛЕНО: Вызываем гибридный сигнал
  hybrid_signal_text = get_hybrid_signal(symbol, score)

  summary = (
      f"📊 **Сводный анализ {symbol}:**\n"
      f"💵 Цена: ${price:,.2f} ({change_24h}%)\n"
      f"🧮 Балл настроения: {score}\n\n"
      f"**Итоговый вердикт:**\n{verdict}\n\n"
      f"-------------------\n\n"
      f"{hybrid_signal_text}"
  )

  return summary