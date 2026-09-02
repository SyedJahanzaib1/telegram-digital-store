# 📐 Technical Architecture & System Design

This document details the software architecture, payment & delivery flows, data models, and security principles behind the **Automated Telegram Digital Store Bot**.

---

## 🛠 System Overview

The system is designed as an asynchronous, event-driven Telegram Bot application communicating via HTTPS REST with the **AIVerseHub Wholesaler Gateway**.

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                             TELEGRAM ECOSYSTEM                              │
│                                                                             │
│   ┌──────────────────┐               ┌──────────────────────────────────┐   │
│   │  Customer User   │ ──(Bot UI)──► │ Telegram Bot (python-telegram-bot)  │
│   └──────────────────┘               └──────────────────────────────────┘   │
└────────────────────────────────────────────────────────┼────────────────────┘
                                                         │
                                               REST HTTPS (X-API-Key)
                                                         │
┌────────────────────────────────────────────────────────▼────────────────────┐
│                             AIVERSE HUB GATEWAY                             │
│                                                                             │
│   ┌──────────────────┐               ┌──────────────────────────────────┐   │
│   │  Wholesale Stock │ ◄──────────── │ Product & Fulfillment API        │   │
│   └──────────────────┘               └──────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Purchase & Auto-Delivery Sequence

```text
Customer                     Telegram Bot                  AIVerseHub API
   │                              │                              │
   │ ─── 1. /start or /products ─►│                              │
   │                              │ ─── 2. GET /api/v1/products ─►│
   │                              │ ◄── 3. Return Products Data ─│
   │ ◄── 4. Render Catalog Menu ──│                              │
   │                              │                              │
   │ ─── 5. Click "Buy Product" ──►│                              │
   │ ◄── 6. Confirm Purchase ─────│                              │
   │                              │                              │
   │ ─── 7. Confirm "YES" ───────►│                              │
   │                              │ ─── 8. POST /api/v1/order ──►│
   │                              │ ◄── 9. Return Order & Links ─│
   │                              │                              │
   │ ◄── 10. Deliver Credentials ─│                              │
   │       in Private DM          │                              │
```

---

## 📦 Data Schema & API Endpoints

### 1. Account Info (`GET /api/v1/me`)
```json
{
  "status": 200,
  "data": {
    "chat_id": 6042459817,
    "first_name": "Syed",
    "wallet_balance": 2.39
  }
}
```

### 2. Products List (`GET /api/v1/products`)
```json
{
  "status": 200,
  "data": {
    "services": [
      {
        "service_id": "service_1787461848",
        "name": "Spotify 3M Redeem Link",
        "price": 0.35,
        "stock": 648
      }
    ]
  }
}
```

### 3. Place Order (`POST /api/v1/order`)
Request:
```json
{
  "service": "service_1787461848",
  "quantity": 1
}
```
Response:
```json
{
  "success": true,
  "order_id": "TRXN1786005045BW4VVE",
  "delivered_products": [
    "https://serviceactivation.google.com/subscription/new/AQCpi..."
  ]
}
```

---

## 🔒 Security Best Practices

1. **API Key Isolation:** The `X-API-Key` is strictly stored in environment variables (`.env`) and never exposed to end-users or client-side code.
2. **Access Control / Admin Panel:** Administrative commands (`/admin`, `/balance`) are restricted to `ADMIN_CHAT_ID`.
3. **Idempotency & Race Conditions:** Checks stock levels before placing an order to prevent failed purchases.
4. **Secret Scrubbing:** Sensitive delivery links are sent via direct private messages with markdown formatting.
