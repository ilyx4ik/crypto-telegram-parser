from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="📊 Анализ рынка"),
            KeyboardButton(text="🧮 Калькулятор рисков"),
        ],
        [
            KeyboardButton(text="💼 Мой портфель"),
            KeyboardButton(text="➕Добавить в портфель"),
            KeyboardButton(text="🔔 Установить алерт")
        ],
        [KeyboardButton(text="📰 Новости"), KeyboardButton(text="⚙️ Настройки")],
    ],
    resize_keyboard=True,
)

settings_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🪙 Bitcoin (BTC/USDT)", callback_data="set_coin_BTC/USDT"
            )
        ],
        [
            InlineKeyboardButton(
                text="💎 Ethereum (ETH/USDT)", callback_data="set_coin_ETH/USDT"
            )
        ],
        [
            InlineKeyboardButton(
                text="🪙 Solana (SOL/USDT)", callback_data="set_coin_SOL/USDT"
            )
        ],
        [
            InlineKeyboardButton(
                text="✍️ Ввести свою монету", callback_data="custom_coin_input"
            )
        ],
        [
            InlineKeyboardButton(
                text="💱 Валюта отображения (USD/UAH/EUR/RUB)",
                callback_data="change_currency",
            )
        ],
        [InlineKeyboardButton(text="🗑 Удалить монету", callback_data="manage_fav_coins")]
    ]
)

currency_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="💵 Доллар ($ USD)", callback_data="curr_USD"),
            InlineKeyboardButton(
                text="₴ Гривна (₴ UAH)", callback_data="curr_UAH"
            ),
        ],
        [
            InlineKeyboardButton(text="💶 Евро (€ EUR)", callback_data="curr_EUR"),
            InlineKeyboardButton(text="₽ Рубль (₽ RUB)", callback_data="curr_RUB"),
        ],
    ]
)




def get_manage_favs_kb(favs: list) -> InlineKeyboardMarkup:
  keyboard = []
  for coin in favs:
    keyboard.append([
        InlineKeyboardButton(
            text=f"❌ {coin}", callback_data=f"del_fav_{coin}"
        )
    ])

  keyboard.append([
      InlineKeyboardButton(
          text="◀️ Назад в настройки", callback_data="back_to_settings"
      )
  ])
  return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_portfolio_manage_kb(portfolio_rows):
  buttons = []
  for item in portfolio_rows:
    coin = item[0]
    buttons.append([
        InlineKeyboardButton(
            text=f"❌ Удалить {coin}", callback_data=f"del_port_{coin}"
        )
    ])

  buttons.append([
      InlineKeyboardButton(
          text="🗑 Очистить весь портфель", callback_data="clear_full_portfolio"
      )
  ])
  return InlineKeyboardMarkup(inline_keyboard=buttons)