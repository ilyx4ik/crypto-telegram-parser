import asyncio
from aiogram import Bot
from analytics import get_market_summary
from crypto_api import get_coin_info
from database import (
    get_all_users,
    get_last_price,
    is_news_sent,
    log_price,
    log_sent_news,
)
from news_api import get_latest_news
from sentiment import analyze_sentiment


async def check_price_alerts(bot: Bot):
  users = await asyncio.to_thread(get_all_users)
  if not users:
    return

  unique_coins = set(coin for user_id, coin in users)

  for coin in unique_coins:
    data = await asyncio.to_thread(get_coin_info, coin)
    if not data:
      continue
    current_price = data["price"]

    last_price = await asyncio.to_thread(get_last_price, coin)

    if last_price:
      percent_change = ((current_price - last_price) / last_price) * 100

      if abs(percent_change) >= 2.0:
        text = (
            f"🚨 PUMP/DUMP Alert: {coin} изменился на {percent_change:.2f}%!"
        )
        for user_id, user_coin in users:
          if user_coin == coin:
            try:
              await bot.send_message(user_id, text)
            except Exception as e:
              print(f"❌ Ошибка отправки аларта пользователю {user_id}: {e}")

    await asyncio.to_thread(log_price, coin, current_price)


async def check_news_alerts(bot: Bot):
  try:
    news_items = await asyncio.to_thread(get_latest_news)
    if not news_items:
      return

    all_users = await asyncio.to_thread(get_all_users)
    unique_user_ids = set(user[0] for user in all_users)

    for item in news_items:
      url = item.get("url")
      if not url:
        continue

      if await asyncio.to_thread(is_news_sent, url):
        continue

      await asyncio.to_thread(log_sent_news, url)

      title = item.get("title", "")
      sentiment = await asyncio.to_thread(analyze_sentiment, title)

      text = (
          "⚡ **СРОЧНЫЙ НОВОСТНОЙ АЛАРТ**\n\n"
          f"📰 **{title}**\n\n"
          f"📊 **Анализ настроения (FinBERT):** {sentiment}\n\n"
          f"🔗 [Читать источник полностью]({url})"
      )

      for user_id in unique_user_ids:
        try:
          await bot.send_message(
              user_id,
              text,
              parse_mode="Markdown",
              disable_web_page_preview=False,
          )
        except Exception as e:
          print(f"❌ Ошибка отправки новости пользователю {user_id}: {e}")

  except Exception as e:
    print(f"❌ Ошибка в check_news_alerts: {e}")


async def send_daily_digest(bot: Bot):
  users = await asyncio.to_thread(get_all_users)
  if not users:
    return

  for user_id, coin in users:
    try:
      summary = await asyncio.to_thread(get_market_summary, coin)
      text = f"☀️ **Утренний дайджест по {coin}**\n\n{summary}"
      await bot.send_message(user_id, text, parse_mode="Markdown")
    except Exception as e:
      print(f"❌ Ошибка отправки дайджеста для user_id {user_id}: {e}")