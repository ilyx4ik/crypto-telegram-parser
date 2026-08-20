import asyncio
import os
from alerts import check_news_alerts, check_price_alerts, send_daily_digest
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from analytics import get_market_summary
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from crypto_api import get_coin_info
from database import (
    add_favorite_coin,
    add_to_portfolio,
    clear_portfolio,
    delete_portfolio_item,
    get_favorite_coins,
    get_user_coin,
    get_user_currency,
    get_user_portfolio,
    init_db,
    remove_favorite_coin,
    set_user_currency,
)
from dotenv import load_dotenv
from keyboards import (
    currency_kb,
    get_manage_favs_kb,
    get_portfolio_manage_kb,
    main_kb,
    settings_kb,
)
from news_api import get_latest_news
from sentiment import analyze_sentiment

load_dotenv()

token = os.getenv("BOT_TOKEN")
bot = Bot(token=token)
dp = Dispatcher()
scheduler = AsyncIOScheduler()

FIAT_RATES = {"USD": 1.0, "UAH": 41.5, "EUR": 0.92, "RUB": 90.0}
FIAT_SYMBOLS = {"USD": "$", "UAH": "₴", "EUR": "€", "RUB": "₽"}


class RiskCalc(StatesGroup):
  deposit = State()
  entry_price = State()
  stop_loss = State()


class PortfolioAdd(StatesGroup):
  coin = State()
  amount = State()
  buy_price = State()


class PriceAlertState(StatesGroup):
  coin = State()
  target_price = State()


class SettingsState(StatesGroup):
  waiting_for_coin = State()


@dp.message(CommandStart())
async def cmd_start(message: types.Message):
  await message.answer(
      "👋 Приветствую! Бот настроен и полностью готов к работе.",
      reply_markup=main_kb,
  )


@dp.message(F.text == "📊 Анализ рынка")
async def market_analysis(message: types.Message):
  user_id = message.from_user.id
  favorites = (await asyncio.to_thread(get_favorite_coins, user_id)) or [
      "BTC/USDT"
  ]
  portfolio = await asyncio.to_thread(get_user_portfolio, user_id)

  coins_to_analyze = list(favorites)
  if portfolio:
    for item in portfolio:
      if item[0] not in coins_to_analyze:
        coins_to_analyze.append(item[0])

  await message.answer(
      f"⏳ Собираем данные и анализируем рынок для:"
      f" {', '.join(coins_to_analyze)}..."
  )

  for coin in coins_to_analyze:
    try:
      summary = await asyncio.to_thread(get_market_summary, coin)
      await message.answer(summary, parse_mode="Markdown")
    except Exception as e:
      print(f"❌ Ошибка в market_analysis для {coin}: {e}")
      await message.answer(
          f"⚠️ Не удалось собрать данные по рынку для {coin}."
      )


@dp.message(F.text == "🧮 Калькулятор рисков")
async def risk_handlers(message: types.Message, state: FSMContext):
  await message.answer("Введите ваш общий депозит в $ (например: 1000):")
  await state.set_state(RiskCalc.deposit)


@dp.message(RiskCalc.deposit)
async def risk_process_deposit(message: types.Message, state: FSMContext):
  await state.update_data(deposit=message.text)
  await message.answer("Введите цену входа:")
  await state.set_state(RiskCalc.entry_price)


@dp.message(RiskCalc.entry_price)
async def risk_process_entry(message: types.Message, state: FSMContext):
  await state.update_data(entry=message.text)
  await message.answer("Введите цену стоп-лосса:")
  await state.set_state(RiskCalc.stop_loss)


@dp.message(RiskCalc.stop_loss)
async def final_risk_handlers(message: types.Message, state: FSMContext):
  coin = (await asyncio.to_thread(get_user_coin, message.from_user.id)) or "Crypto"
  await state.update_data(stop=message.text)
  data = await state.get_data()

  try:
    deposit = float(str(data["deposit"]).replace(",", "."))
    entry = float(str(data["entry"]).replace(",", "."))
    stop = float(message.text.replace(",", "."))
  except ValueError:
    await message.answer(
        "❌ **Ошибка:** Вводите только числа (например: 1000 или 64500.50)."
    )
    await state.clear()
    return

  price_risk = abs(entry - stop)
  if price_risk == 0:
    await message.answer("❌ Цена входа и цена стоп-лосса не могут совпадать!")
    await state.clear()
    return

  risk_usd = deposit * 0.01
  position_size = risk_usd / price_risk
  position_usd = position_size * entry
  leverage = position_usd / deposit

  if entry > stop:
    direction = "Long 📈 (Покупка на рост)"
    tp1 = entry + (price_risk * 2)
    tp2 = entry + (price_risk * 3)
  else:
    direction = "Short 📉 (Продажа на падение)"
    tp1 = entry - (price_risk * 2)
    tp2 = entry - (price_risk * 3)

  leverage_text = (
      f"{leverage:.1f}x" if position_usd > deposit else "1x (Без плеча)"
  )

  result_text = (
      f"📊 **Расчет риск-менеджмента для {coin} ({direction})**\n\n"
      f"💵 **Депозит:** ${deposit:,.2f}\n"
      f"🛡 **Допустимый риск (1%):** ${risk_usd:,.2f}\n\n"
      f"📦 **Размер позиции:** {position_size:.4f} монет (${position_usd:,.2f})\n"
      f"⚙️ **Рекомендуемое плечо:** {leverage_text}\n\n"
      f"🎯 **Цели Take-Profit:**\n"
      f"• **TP1 (1:2):** ${tp1:,.2f}\n"
      f"• **TP2 (1:3):** ${tp2:,.2f}\n\n"
      f"🛑 **Stop-Loss:** ${stop:,.2f}"
  )

  await message.answer(result_text, parse_mode="Markdown")
  await state.clear()


@dp.message(F.text == "➕Добавить в портфель")
async def cmd_portfolio_add(message: types.Message, state: FSMContext):
  await message.answer(
      "Введите монету (например: `ETH`, `BTC`, `TRUMP` или `DOGE`):"
  )
  await state.set_state(PortfolioAdd.coin)


@dp.message(PortfolioAdd.coin)
async def process_portfolio_coin(message: types.Message, state: FSMContext):
  coin_input = message.text.upper().strip()

  if "/" not in coin_input:
    coin_input = f"{coin_input}/USDT"
  elif not coin_input.endswith("/USDT"):
    base_coin = coin_input.split("/")[0]
    coin_input = f"{base_coin}/USDT"

  await state.update_data(coin=coin_input)
  await message.answer(
      f"Принято: **{coin_input}**.\nВведите количество монет (например: `0.05`"
      " или `500`):",
      parse_mode="Markdown",
  )
  await state.set_state(PortfolioAdd.amount)


@dp.message(PortfolioAdd.amount)
async def process_portfolio_amount(
    message: types.Message, state: FSMContext
):
  await state.update_data(amount=message.text.replace(",", "."))
  await message.answer(
      "Введите цену покупки 1 монеты в $ USD (например: `2500` или `0.12`):"
  )
  await state.set_state(PortfolioAdd.buy_price)


@dp.message(PortfolioAdd.buy_price)
async def final_portfolio_add(message: types.Message, state: FSMContext):
  data = await state.get_data()

  try:
    amount = float(str(data["amount"]).replace(",", "."))
    buy_price = float(message.text.replace(",", "."))
  except ValueError:
    await message.answer("❌ **Ошибка:** Вводите только числа.")
    await state.clear()
    return

  coin = data.get("coin", "BTC/USDT")
  user_id = message.from_user.id

  await asyncio.to_thread(add_to_portfolio, user_id, coin, amount, buy_price)
  await asyncio.to_thread(add_favorite_coin, user_id, coin)
  await state.clear()

  formatted_amount = f"{amount:.8f}".rstrip("0").rstrip(".")
  await message.answer(
      f"✅ Позиция **{coin}** ({formatted_amount} шт. по ${buy_price:,.2f})"
      " добавлена в портфель!",
      parse_mode="Markdown",
  )


@dp.message(F.text == "💼 Мой портфель")
async def my_portfolio(message: types.Message):
  user_id = message.from_user.id
  rows = await asyncio.to_thread(get_user_portfolio, user_id)

  if not rows:
    await message.answer("Ваш портфель пуст.")
    return

  curr = await asyncio.to_thread(get_user_currency, user_id)
  rate = FIAT_RATES.get(curr, 1.0)
  sym = FIAT_SYMBOLS.get(curr, "$")

  total_invested_usd = 0
  total_current_usd = 0
  items_list_text = ""

  for coin, amount, buy_price_usd in rows:
    data = await asyncio.to_thread(get_coin_info, coin)
    current_price_usd = data["price"] if data else buy_price_usd

    spent_usd = amount * buy_price_usd
    current_val_usd = amount * current_price_usd
    pnl_usd = current_val_usd - spent_usd
    pnl_perc = (
        ((current_price_usd - buy_price_usd) / buy_price_usd) * 100
        if buy_price_usd > 0
        else 0
    )

    total_invested_usd += spent_usd
    total_current_usd += current_val_usd

    buy_price_fiat = buy_price_usd * rate
    curr_price_fiat = current_price_usd * rate
    pnl_fiat = pnl_usd * rate

    coin_emoji = "🟢" if pnl_usd >= 0 else "🔴"
    formatted_amount = f"{amount:.8f}".rstrip("0").rstrip(".")

    items_list_text += (
        f"{coin_emoji} **{coin}**\n"
        f"├ Кол-во: `{formatted_amount}`\n"
        f"├ Вход: `{sym}{buy_price_fiat:,.2f}` ➔ Сейчас:"
        f" `{sym}{curr_price_fiat:,.2f}`\n"
        f"└ PnL: **{pnl_fiat:+.2f}{sym}** (`{pnl_perc:+.2f}%`)\n\n"
    )

  total_pnl_usd = total_current_usd - total_invested_usd
  total_pnl_fiat = total_pnl_usd * rate
  total_pnl_perc = (
      ((total_current_usd - total_invested_usd) / total_invested_usd) * 100
      if total_invested_usd > 0
      else 0
  )
  total_emoji = "🚀" if total_pnl_usd >= 0 else "💥"

  summary_text = (
      f"💼 **Твой Портфель ({curr})**\n\n"
      f"{items_list_text}"
      f"───────────────────\n"
      f"💵 **Инвестировано:** `{sym}{total_invested_usd * rate:,.2f}`\n"
      f"💎 **Текущая стоимость:** `{sym}{total_current_usd * rate:,.2f}`\n"
      f"{total_emoji} **Общий PnL:** **{total_pnl_fiat:+.2f}{sym}**"
      f" (`{total_pnl_perc:+.2f}%`)\n\n"
      f"👇 *Управление позициями:*"
  )

  await message.answer(
      summary_text,
      reply_markup=get_portfolio_manage_kb(rows),
      parse_mode="Markdown",
  )


@dp.callback_query(F.data.startswith("del_port_"))
async def process_delete_portfolio_item(callback: types.CallbackQuery):
  coin_to_delete = callback.data.replace("del_port_", "")
  await asyncio.to_thread(delete_portfolio_item, callback.from_user.id, coin_to_delete)
  await callback.answer(f"Позиция {coin_to_delete} удалена!")
  await callback.message.edit_text(
      f"❌ Позиция **{coin_to_delete}** удалена из портфеля.",
      parse_mode="Markdown",
  )


@dp.callback_query(F.data == "clear_full_portfolio")
async def process_clear_portfolio(callback: types.CallbackQuery):
  await asyncio.to_thread(clear_portfolio, callback.from_user.id)
  await callback.answer("Портфель очищен!")
  await callback.message.edit_text("🗑 Ваш портфель полностью очищен.")


@dp.message(F.text == "⚙️ Настройки")
async def settings_handlers(message: types.Message):
  favs = (await asyncio.to_thread(get_favorite_coins, message.from_user.id)) or ["BTC/USDT"]
  curr = await asyncio.to_thread(get_user_currency, message.from_user.id)
  text = (
      f"⚙️ **Настройки бота**\n\n"
      f"📌 **Отслеживаемые монеты:** `{', '.join(favs)}`\n"
      f"💱 **Валюта отображения:** `{curr}`\n\n"
      f"Выберите действие ниже:"
  )
  await message.answer(text, reply_markup=settings_kb, parse_mode="Markdown")


@dp.callback_query(F.data == "change_currency")
async def change_currency_start(callback: types.CallbackQuery):
  await callback.message.edit_text(
      "💱 Выберите основную валюту для отображения портфеля и цен:",
      reply_markup=currency_kb,
  )


@dp.callback_query(F.data.startswith("curr_"))
async def set_currency_handler(callback: types.CallbackQuery):
  selected_curr = callback.data.replace("curr_", "")
  await asyncio.to_thread(set_user_currency, callback.from_user.id, selected_curr)
  await callback.answer(f"Валюта изменена на {selected_curr}!")
  await callback.message.edit_text(
      f"✅ Валюта отображения успешно изменена на **{selected_curr}**!",
      parse_mode="Markdown",
  )


@dp.callback_query(F.data.startswith("set_coin_"))
async def set_coin_handler(callback: types.CallbackQuery):
  new_coin = callback.data.replace("set_coin_", "")
  await asyncio.to_thread(add_favorite_coin, callback.from_user.id, new_coin)
  await callback.answer(f"Добавлена монета {new_coin}!")
  await callback.message.answer(
      f"✅ Монета **{new_coin}** добавлена в список!", parse_mode="Markdown"
  )


@dp.callback_query(F.data == "manage_fav_coins")
async def manage_fav_coins_handler(callback: types.CallbackQuery):
  favs = (await asyncio.to_thread(get_favorite_coins, callback.from_user.id)) or []
  if not favs:
    await callback.answer("У вас нет отслеживаемых монет.", show_alert=True)
    return

  await callback.message.edit_text(
      "🗑 **Выберите монету для удаления из отслеживаемых:**",
      reply_markup=get_manage_favs_kb(favs),
      parse_mode="Markdown",
  )


@dp.callback_query(F.data.startswith("del_fav_"))
async def delete_fav_coin_handler(callback: types.CallbackQuery):
  coin_to_remove = callback.data.replace("del_fav_", "")
  user_id = callback.from_user.id

  await asyncio.to_thread(remove_favorite_coin, user_id, coin_to_remove)
  await callback.answer(f"Монета {coin_to_remove} удалена!")

  favs = (await asyncio.to_thread(get_favorite_coins, user_id)) or []
  if favs:
    await callback.message.edit_text(
        "🗑 **Выберите монету для удаления из отслеживаемых:**",
        reply_markup=get_manage_favs_kb(favs),
        parse_mode="Markdown",
    )
  else:
    await callback.message.edit_text(
        "✅ Список отслеживаемых монет теперь пуст!"
    )


@dp.callback_query(F.data == "back_to_settings")
async def back_to_settings_handler(callback: types.CallbackQuery):
  favs = (await asyncio.to_thread(get_favorite_coins, callback.from_user.id)) or ["BTC/USDT"]
  curr = await asyncio.to_thread(get_user_currency, callback.from_user.id)
  text = (
      f"⚙️ **Настройки бота**\n\n"
      f"📌 **Отслеживаемые монеты:** `{', '.join(favs)}`\n"
      f"💱 **Валюта отображения:** `{curr}`\n\n"
      f"Выберите действие ниже:"
  )
  await callback.message.edit_text(
      text, reply_markup=settings_kb, parse_mode="Markdown"
  )


@dp.callback_query(F.data == "custom_coin_input")
async def custom_coin_start(callback: types.CallbackQuery, state: FSMContext):
  await callback.message.answer("✍️ Введите тикер монеты (например: `TRUMP`):")
  await state.set_state(SettingsState.waiting_for_coin)
  await callback.answer()


@dp.message(SettingsState.waiting_for_coin)
async def process_custom_coin(message: types.Message, state: FSMContext):
  new_coin = message.text.upper().strip()
  if "/" not in new_coin:
    new_coin = f"{new_coin}/USDT"

  await asyncio.to_thread(add_favorite_coin, message.from_user.id, new_coin)
  await state.clear()
  await message.answer(
      f"✅ Монета **{new_coin}** добавлена в отслеживаемые!",
      parse_mode="Markdown",
  )


@dp.message(F.text == "📰 Новости")
async def news_handlers(message: types.Message):
  try:
    news_item = await asyncio.to_thread(get_latest_news)
    if not news_item:
      await message.answer("❌ Не удалось получить новости.")
      return

    text = "<b>📰 Последние новости рынка:</b>\n\n"
    for item in news_item:
      title = item["title"]
      url = item["url"]
      sentiment = await asyncio.to_thread(analyze_sentiment, title)
      text += (
          f"🔹 <b>{title}</b>\n"
          f"Анализ: {sentiment}\n"
          f"🔗 <a href='{url}'>Читать далее</a>\n\n"
      )

    await message.answer(text, parse_mode="HTML", disable_web_page_preview=True)
  except Exception as e:
    print(f"❌ Ошибка в news_handlers: {e}")
    await message.answer("⚠️ Не удалось загрузить новости.")


@dp.message(F.text == "🔔 Установить алерт")
async def cmd_add_alert(message: types.Message, state: FSMContext):
  await message.answer(
      "Введите монету для алерта (например: `SOL`, `BTC` или `TON`):"
  )
  await state.set_state(PriceAlertState.coin)


@dp.message(PriceAlertState.coin)
async def process_alert_coin(message: types.Message, state: FSMContext):
  coin = message.text.upper().strip()
  if "/" not in coin:
    coin = f"{coin}/USDT"
  await state.update_data(coin=coin)
  await message.answer(
      f"Принято: **{coin}**.\nВведите целевую цену в $ USD (например: `85` или"
      " `100`):",
      parse_mode="Markdown",
  )
  await state.set_state(PriceAlertState.target_price)


@dp.message(PriceAlertState.target_price)
async def process_alert_price(message: types.Message, state: FSMContext):
  try:
    target_price = float(message.text.replace(",", "."))
  except ValueError:
    await message.answer("❌ Вводите только число (например: 85 или 92.5).")
    await state.clear()
    return

  data = await state.get_data()
  coin = data["coin"]

  await message.answer(
      f"🔔 Алерт установлен! Бот напишет, когда **{coin}** достигнет"
      f" **${target_price:,.2f}**.",
      parse_mode="Markdown",
  )
  await state.clear()


@dp.message()
async def fallback_handler(message: types.Message):
  await message.answer("🤖 Выберите команду в меню 👇", reply_markup=main_kb)


async def main():
  init_db()
  # Добавлен misfire_grace_time=120, чтобы предотвратить ошибки просрочки задач
  scheduler.add_job(
      check_news_alerts,
      "interval",
      minutes=15,
      args=[bot],
      misfire_grace_time=120,
  )
  scheduler.add_job(
      check_price_alerts,
      "interval",
      minutes=5,
      args=[bot],
      misfire_grace_time=120,
  )
  scheduler.add_job(
      send_daily_digest,
      "cron",
      hour=12,
      minute=0,
      args=[bot],
      misfire_grace_time=120,
  )
  scheduler.start()

  print("🚀 Бот полностью собран и запущен!")
  await dp.start_polling(bot)


if __name__ == "__main__":
  asyncio.run(main())