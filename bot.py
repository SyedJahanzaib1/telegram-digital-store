import logging
import asyncio
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
        [InlineKeyboardButton("🛒 Browse Products", callback_data="menu_products")],
        [
            InlineKeyboardButton("👤 My Balance / Info", callback_data="menu_account"),
            InlineKeyboardButton("📜 Order History", callback_data="menu_history"),
        ],
        [InlineKeyboardButton("💬 Support & Help", callback_data="menu_support")],
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message and main menu."""
    user = update.effective_user
    welcome_text = (
        f"👋 *Welcome to Digital Store, {user.first_name}!*\n\n"
        "⚡ *Instant Automated Delivery 24/7*\n"
        "Browse our premium digital products below and receive your links/keys instantly upon order.\n\n"
        "Select an option from the menu below:"
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

    elif data == "menu_products":
        products = client.get_products()
        if not products:
            await query.edit_message_text(
                "❌ *No products currently available.* Please try again later.",
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
            "🛍️ *Available Digital Products:*\n\nSelect a product to view details and buy:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

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
            f"📦 *Product:* `{name}`\n"
            f"💰 *Price:* `${price:.2f}`\n"
            f"📊 *Stock Available:* {stock_icon} `{stock}` units\n"
            f"⚡ *Delivery:* Instant Digital Link/Key\n\n"
        )

        keyboard = []
        if stock > 0:
            keyboard.append([InlineKeyboardButton("💳 Buy Now", callback_data=f"buy_{svc_id}")])
        else:
            details_text += "🔴 *Status:* Out of stock currently. Check back soon!"

        keyboard.append([InlineKeyboardButton("🔙 Back to Products", callback_data="menu_products")])
        await query.edit_message_text(details_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

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
            f"❓ *Confirm Purchase*\n\n"
            f"Are you sure you want to buy 1x *{name}* for *${price:.2f}*?\n\n"
            f"Click *Confirm Purchase* below to complete order."
        )
        keyboard = [
            [InlineKeyboardButton("✅ Confirm Purchase", callback_data=f"exec_{svc_id}")],
            [InlineKeyboardButton("❌ Cancel", callback_data="menu_products")],
        ]
        await query.edit_message_text(confirm_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("exec_"):
        svc_id = data.replace("exec_", "")
        await query.edit_message_text("⌛ *Processing your order... Please wait.*", parse_mode="Markdown")

        res = client.place_order(svc_id, quantity=1)

        if res.get("success"):
            order_id = res.get("order_id", "N/A")
            delivered = res.get("delivered_products", [])
            items_str = "\n".join([f"🔗 `{item}`" for item in delivered]) if delivered else "Link will be sent shortly."

            success_text = (
                f"🎉 *Order Successful!*\n\n"
                f"🆔 *Order ID:* `{order_id}`\n"
                f"📦 *Delivered Product:* \n{items_str}\n\n"
                f"Thank you for your purchase! Enjoy your product."
            )
            keyboard = [[InlineKeyboardButton("🛍️ Buy Another Product", callback_data="menu_products")]]
            await query.edit_message_text(success_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            err_msg = res.get("error", "Failed to process order.")
            fail_text = f"❌ *Purchase Failed*\n\n*Reason:* {err_msg}\n\nPlease check API balance or contact support."
            keyboard = [[InlineKeyboardButton("🔙 Back to Catalog", callback_data="menu_products")]]
            await query.edit_message_text(fail_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "menu_account":
        acc_info = client.get_account_info()
        balance = acc_info.get("wallet_balance", 0.0)
        user_name = acc_info.get("first_name", update.effective_user.first_name)

        text = (
            f"👤 *Account Details*\n\n"
            f"• *User:* `{user_name}`\n"
            f"• *Wholesale Wallet Balance:* `${balance:.2f}`\n\n"
            f"Keep your balance topped up to ensure automated fulfillment!"
        )
        keyboard = [[InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "menu_history":
        orders_data = client.get_orders()
        orders_list = orders_data.get("orders", [])

        if not orders_list:
            text = "📜 *Order History*\n\nYou haven't placed any orders yet."
        else:
            text = "📜 *Recent Orders History:*\n\n"
            for o in orders_list[:5]:
                oid = o.get("order_id")
                amount = o.get("amount")
                status = o.get("status")
                text += f"• `{oid}` | Status: *{status}* | `${amount}`\n"

        keyboard = [[InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "menu_support":
        text = (
            "💬 *Customer Support*\n\n"
            "Need help with an order or account top-up?\n"
            "Contact our support team directly:\n"
            "👉 @SyedJahanzaib"
        )
        keyboard = [[InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin dashboard command."""
    user_id = str(update.effective_user.id)
    if user_id != config.admin_chat_id:
        await update.message.reply_text("⛔ Unauthorized.")
        return

    acc_info = client.get_account_info()
    products = client.get_products()
    orders_data = client.get_orders()

    total_stock = sum(p.get("stock", 0) for p in products)
    total_orders = orders_data.get("total_orders", 0)

    admin_text = (
        f"👑 *Admin Dashboard*\n\n"
        f"💰 *Supplier Wallet Balance:* `${acc_info.get('wallet_balance', 0.0):.2f}`\n"
        f"📦 *Total Products Active:* `{len(products)}`\n"
        f"📊 *Total Stock Items:* `{total_stock}`\n"
        f"🧾 *Total Lifetime Orders:* `{total_orders}`\n"
        f"📈 *Configured Markup:* `{config.profit_markup_percent}%`"
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

    print("🚀 Telegram Digital Store Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
