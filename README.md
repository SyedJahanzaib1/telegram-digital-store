# 🛒 Automated Telegram Digital Store Bot

An end-to-end automated Telegram Digital Products Store Bot integrated with **AIVerseHub API** (or custom stock APIs). This bot allows customers to browse digital products (Spotify links, Netflix accounts, AI subscriptions, software keys), make purchases, and receive instant digital product delivery directly in Telegram DMs.

[![GitHub license](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-brightgreen.svg)](https://www.python.org/)

---

## 🌟 Features

- 📱 **Interactive Catalog:** Clean Telegram Inline Keyboards for easy product browsing.
- ⚡ **Instant Auto-Delivery:** Products (redeem links/credentials) delivered instantly upon purchase.
- 💰 **Profit Margin Configurator:** Set a custom profit markup percentage over wholesale API prices.
- 🔄 **Real-Time Stock Sync:** Automatically queries supplier API to check live stock & availability.
- 👤 **Account & Orders History:** Users can check their order history and balance anytime.
- 👑 **Admin Control Panel:** View total sales, wallet balance, and update store settings on the fly.

---

## 🏗️ Architecture & Business Flow

```text
[Customer / Telegram User]
           │
           │  1. /start -> Select Product
           ▼
┌─────────────────────────────────────────┐
│          Telegram Shop Bot              │
└─────────────────────────────────────────┘
           │
           │  2. Query Products & Stock
           ▼
┌─────────────────────────────────────────┐
│     AIVerseHub API (aiversehub.store)   │
└─────────────────────────────────────────┘
           │
           │  3. Execute Order (POST /api/v1/order)
           ▼
┌─────────────────────────────────────────┐
│       Product Delivery Engine           │
└─────────────────────────────────────────┘
           │
           │  4. Send Redeem Link/Credentials in DM
           ▼
[Customer Received Product Instantly 🎁]
```

Detailed architecture breakdown and sequence diagrams can be found in [ARCHITECTURE.md](./ARCHITECTURE.md).

---

## 🚀 Quick Setup Guide

### 1. Prerequisites
- Python 3.10 or higher
- A Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- An AIVerseHub API Key (from `aiversehub.store`)

### 2. Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/SyedJahanzaib1/telegram-digital-store.git
cd telegram-digital-store
pip install -r requirements.txt
```

### 3. Environment Configuration

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

Configure your environment variables in `.env`:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
AIVERSEHUB_API_KEY=AK_your_aiversehub_api_key
PROFIT_MARKUP_PERCENT=20  # Profit margin percentage added to wholesale price
ADMIN_CHAT_ID=your_telegram_user_id
```

### 4. Running the Bot

```bash
python bot.py
```

---

## 📁 Repository Structure

```text
telegram-digital-store/
├── README.md              # Project Overview & Setup Guide
├── ARCHITECTURE.md        # Technical Design & Business Flow
├── config.py              # Configuration & Environment Handler
├── aiverse_client.py      # Async AIVerseHub API Client
├── bot.py                 # Telegram Bot Handlers & UI logic
├── requirements.txt       # Dependencies
└── .env.example           # Example Environment Template
```

---

## 🔗 API Integration Details

The bot integrates with the AIVerseHub API endpoints:
- `GET /api/v1/me` — Fetches user info & wallet balance.
- `GET /api/v1/products` — Retrieves active products list and stock levels.
- `POST /api/v1/order` — Places an automated purchase order.
- `GET /api/v1/orders` — Retrieves historical orders.

---

## 🛡️ License

Distributed under the MIT License. See `LICENSE` for more information.
