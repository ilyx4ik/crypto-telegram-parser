import sqlite3

# Сохраняем твое исходное имя базы данных
conn = sqlite3.connect("crypto_bot.db", check_same_thread=False)


def init_db():
  cursor = conn.cursor()

  # 1. Таблица истории сигналов
  cursor.execute("""
    CREATE TABLE IF NOT EXISTS history(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        coin TEXT,
        price REAL,
        signal TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

  # 2. Таблица портфеля
  cursor.execute("""
    CREATE TABLE IF NOT EXISTS portfolio(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        coin TEXT,
        amount REAL,
        buy_price REAL
    )
    """)

  # 3. Таблица логов цен
  cursor.execute("""
    CREATE TABLE IF NOT EXISTS price_logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        coin TEXT,
        price REAL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

  # 4. Таблица пользователей (с добавлением колонки currency для фиата)
  cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        coin TEXT DEFAULT 'BTC/USDT',
        currency TEXT DEFAULT 'USD'
    )
    """)

  # Добавляем колонку currency, если база создавалась ранее без нее
  try:
    cursor.execute(
        "ALTER TABLE users ADD COLUMN currency TEXT DEFAULT 'USD'"
    )
  except sqlite3.OperationalError:
    pass  # Колонка уже существует

  # 5. Таблица отправленных новостей
  cursor.execute("""
    CREATE TABLE IF NOT EXISTS sent_news (
        url TEXT PRIMARY KEY
    )
    """)

  # 6. Избранные монеты
  cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_favorites (
        user_id INTEGER,
        coin TEXT,
        PRIMARY KEY (user_id, coin)
    )
    """)

  conn.commit()


# --- РАБОТА С ПОЛЬЗОВАТЕЛЯМИ И НАСТРОЙКАМИ ---
def set_user_coin(user_id: int, symbol: str):
  cursor = conn.cursor()
  cursor.execute(
      """
        INSERT INTO users (user_id, coin) VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET coin = ?
    """,
      (user_id, symbol, symbol),
  )
  conn.commit()


def get_user_coin(user_id: int) -> str:
  cursor = conn.cursor()
  cursor.execute("SELECT coin FROM users WHERE user_id = ?", (user_id,))
  row = cursor.fetchone()
  return row[0] if (row and row[0]) else "BTC/USDT"


def set_user_currency(user_id: int, currency: str):
  cursor = conn.cursor()
  cursor.execute(
      """
        INSERT INTO users (user_id, currency) VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET currency = ?
    """,
      (user_id, currency, currency),
  )
  conn.commit()


def get_user_currency(user_id: int) -> str:
  cursor = conn.cursor()
  cursor.execute("SELECT currency FROM users WHERE user_id = ?", (user_id,))
  row = cursor.fetchone()
  return row[0] if (row and row[0]) else "USD"


def get_all_users() -> list:
  cursor = conn.cursor()
  cursor.execute("SELECT user_id, coin FROM users")
  return cursor.fetchall()


# --- ЦЕНЫ И ЛОГИ ---
def log_price(coin: str, price: float):
  cursor = conn.cursor()
  cursor.execute(
      "INSERT INTO price_logs (coin, price) VALUES (?, ?)", (coin, price)
  )
  conn.commit()


def get_last_price(coin: str):
  cursor = conn.cursor()
  cursor.execute(
      "SELECT price FROM price_logs WHERE coin = ? ORDER BY id DESC LIMIT 1",
      (coin,),
  )
  row = cursor.fetchone()
  return row[0] if row else None


# --- НОВОСТИ ---
def is_news_sent(url: str) -> bool:
  cursor = conn.cursor()
  cursor.execute("SELECT url FROM sent_news WHERE url = ?", (url,))
  return cursor.fetchone() is not None


def log_sent_news(url: str):
  cursor = conn.cursor()
  cursor.execute("INSERT INTO sent_news(url) VALUES (?)", (url,))
  conn.commit()


# --- ПОРТФЕЛЬ ---
def add_to_portfolio(user_id: int, coin: str, amount: float, buy_price: float):
  cursor = conn.cursor()
  cursor.execute(
      "INSERT INTO portfolio(user_id, coin, amount, buy_price) VALUES (?, ?,"
      " ?, ?)",
      (user_id, coin, amount, buy_price),
  )
  conn.commit()


def get_user_portfolio(user_id: int):
  cursor = conn.cursor()
  cursor.execute(
      "SELECT coin, amount, buy_price FROM portfolio WHERE user_id = ?",
      (user_id,),
  )
  return cursor.fetchall()


def delete_portfolio_item(user_id: int, coin: str):
  cursor = conn.cursor()
  cursor.execute(
      "DELETE FROM portfolio WHERE user_id = ? AND coin = ?", (user_id, coin)
  )
  conn.commit()


def clear_portfolio(user_id: int):
  cursor = conn.cursor()
  cursor.execute("DELETE FROM portfolio WHERE user_id = ?", (user_id,))
  conn.commit()


# --- ИЗБРАННОЕ ---
def add_favorite_coin(user_id: int, coin: str):
  cursor = conn.cursor()
  cursor.execute(
      "INSERT OR IGNORE INTO user_favorites (user_id, coin) VALUES (?, ?)",
      (user_id, coin),
  )
  conn.commit()


def get_favorite_coins(user_id: int) -> list:
  cursor = conn.cursor()
  cursor.execute(
      "SELECT coin FROM user_favorites WHERE user_id = ?", (user_id,)
  )
  rows = cursor.fetchall()
  return [row[0] for row in rows]


def remove_favorite_coin(user_id: int, coin: str):
  conn = sqlite3.connect("bot_database.db")
  cursor = conn.cursor()
  cursor.execute(
      "DELETE FROM favorite_coins WHERE user_id = ? AND coin = ?",
      (user_id, coin),
  )
  conn.commit()
  conn.close()