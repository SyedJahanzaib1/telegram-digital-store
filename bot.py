import logging
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from config import config
from aiverse_client import AIVerseHubClient

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

client = AIVerseHubClient()

def get_main_menu_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("🛒 Buy Products", callback_data="menu_products"),
            InlineKeyboardButton("📦 My Orders", callback_data="menu_orders"),
        ],
        [
            InlineKeyboardButton("📖 How to Use", callback_data="menu_instructions"),
            InlineKeyboardButton("💳 Wallet", callback_data="menu_wallet"),
        ],
        [
            InlineKeyboardButton("👥 Refer & Earn", callback_data="menu_referral"),
            InlineKeyboardButton("💬 Support", callback_data="menu_support"),
        ],
        [
            InlineKeyboardButton("👤 Profile", callback_data="menu_profile"),
            InlineKeyboardButton("🔑 API Key", callback_data="menu_api"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message and main menu."""
    user = update.effective_user
    acc_info = client.get_account_info()
    balance = float(acc_info.get("wallet_balance", 0.0))

    welcome_text = (
        f"👋 *Welcome to Digital Jahan Store, {user.first_name}!*\n\n"
        f"💳 *Current Balance:* `${balance:.4f}`\n\n"
        f"Select a service from the menu below to purchase digital products, "
        f"check stock, or manage your wallet."
    )

    if update.message:
        await update.message.reply_text(
            welcome_text, parse_mode="Markdown", reply_markup=get_main_menu_keyboard()
        )
    elif update.callback_query:
        await update.callback_query.edit_message_text(
            welcome_text, parse_mode="Markdown", reply_markup=get_main_menu_keyboard()
        )

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle menu callbacks."""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "main_menu":
        await start(update, context)

    # 🛒 Buy Products Catalog
    elif data == "menu_products":
        products = client.get_products()
        if not products:
            await query.edit_message_text(
                "❌ *No products currently available.* Please check back later.",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")]]),
            )
            return

        keyboard = []
        for p in products:
            svc_id = p.get("service_id")
            name = p.get("name", "Product")
            price = p.get("retail_price", p.get("price", 0))
            stock = p.get("stock", 0)
            stock_status = f"(🟢 {stock} in stock)" if stock > 0 else "(🔴 Out of stock)"
            btn_text = f"{name} - ${price:.2f} {stock_status}"
            keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"prod_{svc_id}")])

        keyboard.append([InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")])

        await query.edit_message_text(
            "🛍️ *Select a Product to Purchase:*\n\nChoose an item below to view options and stock:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    # Product Details
    elif data.startswith("prod_"):
        svc_id = data.replace("prod_", "")
        products = client.get_products()
        product = next((p for p in products if p.get("service_id") == svc_id), None)

        if not product:
            await query.edit_message_text("❌ Product not found.", reply_markup=get_main_menu_keyboard())
            return

        name = product.get("name")
        price = product.get("retail_price", product.get("price", 0))
        stock = product.get("stock", 0)
        stock_icon = "🟢" if stock > 0 else "🔴"

        details_text = (
            f"📦 *Product Details*\n\n"
            f"• *Name:* `{name}`\n"
            f"• *Price:* `${price:.2f}`\n"
            f"• *Stock:* {stock_icon} `{stock}` available\n"
            f"• *Delivery:* Instant Automated DM\n\n"
            f"⚡ *Terms:* Instant activation link/credentials provided immediately after order."
        )

        keyboard = []
        if stock > 0:
            keyboard.append([InlineKeyboardButton("💳 Buy Product Now", callback_data=f"buy_{svc_id}")])
        else:
            details_text += "\n\n🔴 *Status:* Out of stock. Check back soon!"

        keyboard.append([InlineKeyboardButton("🔙 Back to Products", callback_data="menu_products")])
        await query.edit_message_text(details_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    # Buy Confirmation
    elif data.startswith("buy_"):
        svc_id = data.replace("buy_", "")
        products = client.get_products()
        product = next((p for p in products if p.get("service_id") == svc_id), None)

        if not product:
            await query.edit_message_text("❌ Product unavailable.", reply_markup=get_main_menu_keyboard())
            return

        name = product.get("name")
        price = product.get("retail_price", product.get("price", 0))

        confirm_text = (
            f"❓ *Confirm Purchase Order*\n\n"
            f"• *Item:* `{name}`\n"
            f"• *Total Amount:* `${price:.2f}`\n\n"
            f"Click *Confirm & Pay* to complete purchase and receive product."
        )
        keyboard = [
            [InlineKeyboardButton("✅ Confirm & Pay", callback_data=f"exec_{svc_id}")],
            [InlineKeyboardButton("❌ Cancel Order", callback_data="menu_products")],
        ]
        await query.edit_message_text(confirm_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    # Execute Order
    elif data.startswith("exec_"):
        svc_id = data.replace("exec_", "")
        await query.edit_message_text("⌛ *Processing your purchase... Please wait.*", parse_mode="Markdown")

        res = client.place_order(svc_id, quantity=1)

        if res.get("success"):
            order_id = res.get("order_id", "N/A")
            delivered = res.get("delivered_products", [])
            items_str = "\n".join([f"🔗 `{item}`" for item in delivered]) if delivered else "Link will be sent shortly."

            success_text = (
                f"🎉 *Order Completed Successfully!*\n\n"
                f"🆔 *Order ID:* `{order_id}`\n\n"
                f"🎁 *Delivered Product / Redeem Link:*\n{items_str}\n\n"
                f"⚠️ *Note:* Store link safely. No warranty available after link activation."
            )
            keyboard = [
                [InlineKeyboardButton("🔗 Recover Product Link", callback_data=f"recover_{order_id}")],
                [InlineKeyboardButton("🛍️ Browse More Products", callback_data="menu_products")],
            ]
            await query.edit_message_text(success_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            err_msg = res.get("error", "Insufficient balance or out of stock.")
            fail_text = f"❌ *Purchase Unsuccessful*\n\n*Reason:* {err_msg}\n\nPlease top up your wallet balance or contact support."
            keyboard = [
                [InlineKeyboardButton("💳 Top Up Wallet", callback_data="menu_wallet")],
                [InlineKeyboardButton("🔙 Back to Catalog", callback_data="menu_products")],
            ]
            await query.edit_message_text(fail_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    # 💳 Wallet Panel UI
    elif data == "menu_wallet":
        acc_info = client.get_account_info()
        balance = float(acc_info.get("wallet_balance", 0.0))

        wallet_text = (
            f"💰 *Wallet Information*\n\n"
            f"• *Current Balance:* `${balance:.4f}`\n\n"
            f"Add balance using Crypto, EasyPaisa, or UPI to purchase digital products directly."
        )
        keyboard = [
            [
                InlineKeyboardButton("➕ Top Up (Add Funds)", callback_data="wallet_topup"),
                InlineKeyboardButton("🎟️ Redeem Promo Code", callback_data="wallet_promo"),
            ],
            [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")],
        ]
        await query.edit_message_text(wallet_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    # ➕ Wallet Topup Options
    elif data == "wallet_topup":
        topup_text = (
            f"💳 *Deposit Funds to Wallet*\n\n"
            f"Choose your preferred payment method:\n\n"
            f"1️⃣ *EasyPaisa / JazzCash / Bank (Local)*\n"
            f"Send payment to Account & submit Transaction ID.\n\n"
            f"2️⃣ *Crypto / Binance Pay (Automatic)*\n"
            f"USDT / TRX instant auto credit.\n\n"
            f"Contact Admin for manual deposit: @SyedJahanzaib"
        )
        keyboard = [
            [InlineKeyboardButton("💬 Contact Support to Deposit", url="https://t.me/SyedJahanzaib")],
            [InlineKeyboardButton("🔙 Back to Wallet", callback_data="menu_wallet")],
        ]
        await query.edit_message_text(topup_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "wallet_promo":
        promo_text = "🎟️ *Redeem Promo Code*\n\nPlease send your promo code in chat or contact @SyedJahanzaib for voucher redemption."
        keyboard = [[InlineKeyboardButton("🔙 Back to Wallet", callback_data="menu_wallet")]]
        await query.edit_message_text(promo_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    # 📦 My Orders UI
    elif data == "menu_orders":
        orders_data = client.get_orders()
        orders_list = orders_data.get("orders", [])

        if not orders_list:
            text = "📦 *Your Recent Orders*\n\nYou haven't placed any orders yet."
            keyboard = [[InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]]
        else:
            text = "📦 *Your Recent Orders*\n\n"
            keyboard = []
            for idx, o in enumerate(orders_list[:5], 1):
                oid = o.get("order_id")
                amount = o.get("amount")
                status = o.get("status", "unknown")
                status_icon = "✅" if status == "success" else "❌"
                text += (
                    f"{idx}. *Order ID:* `{oid}`\n"
                    f"   • Amount: `${amount}` | Status: {status_icon} `{status}`\n\n"
                )
                if status == "success":
                    keyboard.append([InlineKeyboardButton(f"🔗 Recover Link ({oid[:8]}...)", callback_data=f"recover_{oid}")])

            keyboard.append([InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")])

        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    # 🔗 Recover Link / Order Details
    elif data.startswith("recover_"):
        oid = data.replace("recover_", "")
        orders_data = client.get_orders()
        orders_list = orders_data.get("orders", [])
        order = next((o for o in orders_list if o.get("order_id") == oid), None)

        if not order:
            await query.edit_message_text("❌ Order not found.", reply_markup=get_main_menu_keyboard())
            return

        delivered = order.get("delivered_products", [])
        items_str = "\n".join([f"🔗 `{item}`" for item in delivered]) if delivered else "No link found."

        text = (
            f"📦 *Order Details & Delivered Item*\n\n"
            f"• *Order ID:* `{oid}`\n"
            f"• *Amount:* `${order.get('amount')}`\n"
            f"• *Status:* `{order.get('status')}`\n\n"
            f"🎁 *Delivered Links:*\n{items_str}"
        )
        keyboard = [[InlineKeyboardButton("🔙 Back to Orders", callback_data="menu_orders")]]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    # 👤 Profile UI
    elif data == "menu_profile":
        user = update.effective_user
        acc_info = client.get_account_info()
        balance = float(acc_info.get("wallet_balance", 0.0))
        joined_date = "2026-08-30"

        profile_text = (
            f"👤 *User Profile*\n\n"
            f"• *Name:* `{user.first_name}`\n"
            f"• *ID:* `{user.id}`\n"
            f"• *Joined Date:* `{joined_date}`\n"
            f"• *Wallet Balance:* `${balance:.4f} USDT`\n"
            f"• *Total Spent:* `$0.6000`"
        )
        keyboard = [
            [InlineKeyboardButton("➕ Top Up Balance", callback_data="wallet_topup")],
            [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")],
        ]
        await query.edit_message_text(profile_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    # 📖 How to Use / Instructions UI
    elif data == "menu_instructions":
        products = client.get_products()
        text = (
            "📖 *Product Instructions & Activation Guide*\n\n"
            "Select a service below for step-by-step activation guide:"
        )
        keyboard = []
        for p in products[:5]:
            keyboard.append([InlineKeyboardButton(f"📘 {p.get('name')}", callback_data="guide_info")])
        keyboard.append([InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")])

        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "guide_info":
        guide_text = (
            "📘 *Activation Guide*\n\n"
            "1. Open the delivered activation link in your web browser.\n"
            "2. Log in with your account credentials.\n"
            "3. Follow the on-screen prompt to redeem your subscription.\n\n"
            "For assistance, contact @SyedJahanzaib"
        )
        keyboard = [[InlineKeyboardButton("🔙 How to Use", callback_data="menu_instructions")]]
        await query.edit_message_text(guide_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    # 👥 Refer & Earn UI
    elif data == "menu_referral":
        user_id = update.effective_user.id
        ref_link = f"https://t.me/DigitalJahan_bot?start=ref_{user_id}"
        text = (
            f"👥 *Referral Program*\n\n"
            f"Share your referral link with friends and earn 5% bonus balance on every purchase they make!\n\n"
            f"🔗 *Your Referral Link:*\n`{ref_link}`"
        )
        keyboard = [[InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    # 🔑 API UI
    elif data == "menu_api":
        key = config.aiverse_api_key
        text = (
            f"🔑 *Developer API Gateway*\n\n"
            f"Integrate Digital Jahan store API directly into your apps and bots.\n\n"
            f"• *API Key:* `{key[:8]}...{key[-4:]}`\n"
            f"• *Base URL:* `https://aiversehub.store`\n\n"
            f"Header format: `X-API-Key: <your_key>`"
        )
        keyboard = [[InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    # 💬 Support UI
    elif data == "menu_support":
        text = (
            "💬 *Customer Support Center*\n\n"
            "Need help with an order, balance deposit, or product link?\n"
            "Our support team is available 24/7."
        )
        keyboard = [
            [InlineKeyboardButton("📲 Contact Owner (@SyedJahanzaib)", url="https://t.me/SyedJahanzaib")],
            [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")],
        ]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin dashboard command."""
    user_id = str(update.effective_user.id)
    if user_id != config.admin_chat_id:
        await update.message.reply_text("⛔ Unauthorized access.")
        return

    acc_info = client.get_account_info()
    products = client.get_products()
    orders_data = client.get_orders()

    total_stock = sum(p.get("stock", 0) for p in products)
    total_orders = orders_data.get("total_orders", 0)

    admin_text = (
        f"👑 *Admin Control Panel*\n\n"
        f"💰 *Supplier Wallet:* `${acc_info.get('wallet_balance', 0.0):.4f}`\n"
        f"📦 *Active Products:* `{len(products)}`\n"
        f"📊 *Total Stock Items:* `{total_stock}`\n"
        f"🧾 *Total Lifetime Orders:* `{total_orders}`\n"
        f"📈 *Configured Profit Markup:* `{config.profit_markup_percent}%`"
    )
    await update.message.reply_text(admin_text, parse_mode="Markdown")

def main():
    token = config.telegram_token
    if not token:
        print("TELEGRAM_BOT_TOKEN environment variable is missing. Set it in .env file.")
        return

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_cmd))
    app.add_handler(CallbackQueryHandler(menu_handler))

    print("🚀 Digital Jahan Store Bot UI is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
