# 🚀 Crypto Analytics & Portfolio Engine

An asynchronous, feature-rich Python service designed for automated crypto portfolio tracking, hybrid market analysis, and risk management. It leverages NLP (FinBERT) for real-time news sentiment scoring and provides actionable alerts.

### 💼 Business Value
Manual portfolio tracking and emotional trading lead to significant capital loss. This engine automates risk calculation (strict 1% account risk parameters), performs objective technical/fundamental analysis 24/7, and generates automated alerts, allowing traders to make data-driven decisions instantly.

### 🛠 Key Features
* **Risk & Money Management:** Accurate position sizing (Long/Short), leverage recommendations, and automated Take-Profit (1:2, 1:3) / Stop-Loss generation.
* **AI News Sentiment Analysis:** Real-time Cointelegraph RSS parsing with headline evaluation (Positive/Negative/Neutral) using the ProsusAI/finbert Transformer model.
* **Hybrid Market Analytics:** Automated trading signal generation (Strong BUY, Weak SELL) based on RSI (14) and EMA (50/200).
* **Portfolio Tracker:** Real-time PnL calculation (%, $ USD) and overall valuation across multiple fiat currencies.
* **Background Scheduling:** Automated volatility alerts (±2% movements) and daily morning summaries.

### 🧰 Tech Stack
* **Core:** Python 3.10+, aiogram 3.x (Asyncio)
* **Data & AI:** pandas, ccxt, transformers, torch (FinBERT)
* **Infrastructure:** SQLite3, APScheduler

### ⚙️ Quick Start

1. Clone the repository:
   ```bash
   git clone [https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git](https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git)
   cd YOUR_REPOSITORY
Create and activate a virtual environment:

Bash
python -m venv venv
source venv/bin/activate  # On Linux/macOS
Install dependencies:

Bash
pip install -r requirements.txt
Create a .env file in the root directory:

BOT_TOKEN=your_telegram_bot_token_here
Run the service:

Bash
python main.py
