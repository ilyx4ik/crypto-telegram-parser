# 🚀 Crypto Analytics & Portfolio Telegram Bot

A feature-rich **Python** Telegram bot built with `aiogram 3` for crypto portfolio tracking, hybrid technical & fundamental market analysis, risk management calculations, and automated news sentiment analysis using **FinBERT**.

---

## 🛠 Key Features

* 💼 **Portfolio Tracker:**
  * Track individual coin holdings with entry price and volume logging.
  * Real-time PnL calculation (%, $ USD) and overall portfolio valuation in **USD, UAH, EUR, and RUB**.
  * Flexible position management (delete single holdings or wipe the portfolio).

* 📊 **Hybrid Market Analytics:**
  * Technical Analysis indicators: **RSI (14)** and trend-following **EMA (50/200)**.
  * Automated trading signal generation (*Strong BUY, Weak SELL, Neutral*).

* 📰 **AI News Sentiment Analysis (FinBERT):**
  * Automated Cointelegraph RSS news feed parsing.
  * Headline sentiment evaluation (*Positive, Negative, Neutral*) leveraging the `ProsusAI/finbert` Transformer model.

* 🧮 **Risk & Money Management (Long/Short):**
  * Accurate position sizing based on a strict 1% account risk parameters.
  * Leverage recommendations and risk metrics calculation.
  * Automated **Take-Profit (1:2, 1:3)** and **Stop-Loss** level target generation.

* 🔔 **Automated Alerts & Background Scheduling:**
  * Volatility / Pump & Dump alerts (triggered on ±2% price movements).
  * Breaking news alerts with embedded sentiment scoring.
  * Scheduled daily morning summaries for monitored assets.

---

## 🧰 Tech Stack

* **Language:** Python 3.10+
* **Bot Framework:** `aiogram 3.x` (Asyncio)
* **Task Scheduler:** `APScheduler`
* **NLP / AI:** `transformers`, `torch` (ProsusAI/FinBERT)
* **Market Data APIs:** `ccxt`, `requests`, `pandas`
* **Database:** `SQLite3`

---

## ⚙️ Installation & Setup

### 1. Clone the repository
```bash
git clone [https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git](https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git)
cd YOUR_REPOSITORY


2. Create a virtual environment
Bash
python -m venv venv
source venv/bin/activate  # On Linux/macOS
# or
venv\Scripts\activate     # On Windows


3. Install dependencies
Bash
pip install -r requirements.txt
4. Configure environment variables
Create a .env file in the root directory:

BOT_TOKEN=your_telegram_bot_token_here
5. Run the bot
Bash
python main.py