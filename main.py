import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from scanner import scan_wallet
from image_card import create_card, create_minimal_card
from analytics import track_event, get_stats, get_top_wallets

BOT_TOKEN = os.getenv("BOT_TOKEN")


# =========================
# KEYBOARD
# =========================
def get_keyboard():
    return ReplyKeyboardMarkup(
        [
            ["🔍 Scan Wallet", "📤 Share Card"],
            ["🔥 Trending", "📊 Stats"],
        ],
        resize_keyboard=True,
    )


# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to BOWS 🐷\n\nChoose an option:",
        reply_markup=get_keyboard(),
    )


# =========================
# COMMAND: /scan
# =========================
async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # Case 1: wallet provided directly
    if context.args:
        wallet = context.args[0]
        user_id = update.message.from_user.id

        await update.message.reply_text("Full Scan Triggered ⏳")

        try:
            track_event("scan", user_id, wallet)
            result = scan_wallet(wallet)

            create_card(
                result.get("token_name"),
                wallet,
                result.get("net_position", 0),
                result.get("cost_sol", 0),
                result.get("value_sol", 0),
                result.get("profit_sol", 0),
                result.get("roi_multiple", 1),
                logo_path=result.get("logo_path"),
                token_symbol=result.get("token_symbol"),
                buy_count=result.get("buys", 0),
                sell_count=result.get("sells", 0),
                sol_price_usd=result.get("sol_price_usd", 0),
            )

            with open("position_card.png", "rb") as img:
                await update.message.reply_photo(photo=img)

        except Exception as e:
            await update.message.reply_text(f"Error: {str(e)}")

    else:
        # Case 2: group or missing wallet → wait for next message
        context.user_data["mode"] = "scan"
        await update.message.reply_text("Send wallet address to scan ⏳")


# =========================
# COMMAND: /share
# =========================
async def share(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if context.args:
        wallet = context.args[0]
        user_id = update.message.from_user.id

        await update.message.reply_text("Share Scan Triggered ⏳")

        try:
            track_event("share", user_id, wallet)
            result = scan_wallet(wallet)

            create_minimal_card(
                result.get("token_name"),
                result.get("profit_sol", 0),
                result.get("roi_multiple", 1),
                logo_path=result.get("logo_path"),
                token_symbol=result.get("token_symbol"),
                sol_price_usd=result.get("sol_price_usd", 0),
            )

            with open("minimal_card.png", "rb") as img:
                await update.message.reply_photo(photo=img)

            await send_trending(update)

        except Exception as e:
            await update.message.reply_text(f"Error: {str(e)}")

    else:
        context.user_data["mode"] = "share"
        await update.message.reply_text("Send wallet address to generate share card ⏳")


# =========================
# HANDLE BUTTONS + WALLET INPUT
# =========================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    # BUTTONS
    if text == "🔍 Scan Wallet":
        context.user_data["mode"] = "scan"
        await update.message.reply_text("Send wallet address to scan ⏳")

    elif text == "📤 Share Card":
        context.user_data["mode"] = "share"
        await update.message.reply_text("Send wallet address to generate share card ⏳")

    elif text == "🔥 Trending":
        await send_trending(update)

    elif text == "📊 Stats":
        await send_stats(update)

    else:
        # Assume wallet input
        mode = context.user_data.get("mode")

        if not mode:
            await update.message.reply_text("Please choose an option first.")
            return

        wallet = text
        user_id = update.message.from_user.id

        if mode == "scan":
            await update.message.reply_text("Full Scan Triggered ⏳")

            try:
                track_event("scan", user_id, wallet)
                result = scan_wallet(wallet)

                create_card(
                    result.get("token_name"),
                    wallet,
                    result.get("net_position", 0),
                    result.get("cost_sol", 0),
                    result.get("value_sol", 0),
                    result.get("profit_sol", 0),
                    result.get("roi_multiple", 1),
                    logo_path=result.get("logo_path"),
                    token_symbol=result.get("token_symbol"),
                    buy_count=result.get("buys", 0),
                    sell_count=result.get("sells", 0),
                    sol_price_usd=result.get("sol_price_usd", 0),
                )

                with open("position_card.png", "rb") as img:
                    await update.message.reply_photo(photo=img)

            except Exception as e:
                await update.message.reply_text(f"Error: {str(e)}")

        elif mode == "share":
            await update.message.reply_text("Share Scan Triggered ⏳")

            try:
                track_event("share", user_id, wallet)
                result = scan_wallet(wallet)

                create_minimal_card(
                    result.get("token_name"),
                    result.get("profit_sol", 0),
                    result.get("roi_multiple", 1),
                    logo_path=result.get("logo_path"),
                    token_symbol=result.get("token_symbol"),
                    sol_price_usd=result.get("sol_price_usd", 0),
                )

                with open("minimal_card.png", "rb") as img:
                    await update.message.reply_photo(photo=img)

                await send_trending(update)

            except Exception as e:
                await update.message.reply_text(f"Error: {str(e)}")


# =========================
# STATS
# =========================
async def send_stats(update: Update):
    data = get_stats()

    msg = (
        f"📊 Analytics\n\n"
        f"👥 Users: {data['unique_users']}\n"
        f"🔍 Scans: {data['total_scans']}\n"
        f"📤 Shares: {data['total_shares']}\n"
        f"💼 Wallets: {data['wallets_scanned']}"
    )

    await update.message.reply_text(msg)


# =========================
# TRENDING
# =========================
async def send_trending(update: Update):
    top_wallets = get_top_wallets()

    if not top_wallets:
        await update.message.reply_text("No wallet data yet.")
        return

    msg = "🔥 Trending Wallets\n\n"

    for i, (wallet, count) in enumerate(top_wallets, start=1):
        short = wallet[:6] + "..." + wallet[-4:]
        label = " 🔥" if i == 1 else ""
        msg += f"{i}. {short} — Active{label}\n"

    msg += "\n👉 Try scanning one of these wallets"

    await update.message.reply_text(msg)


# =========================
# MAIN
# =========================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan))
    app.add_handler(CommandHandler("share", share))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
