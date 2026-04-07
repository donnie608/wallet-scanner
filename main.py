import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from scanner import scan_wallet
from image_card import create_card, create_minimal_card  # ✅ IMPORT BOTH

BOT_TOKEN = os.getenv("BOT_TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to BOWS - Big Oinker's Wallet Scanner 🔍")


async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("FULL TRIGGERED ✅")

    if not context.args:
        await update.message.reply_text("Usage: /scan WALLET")
        return

    wallet = context.args[0]
    await update.message.reply_text("Scanning... ⏳")

    try:
        result = scan_wallet(wallet)

        token_name = result.get("token_name", "Token")
        token_symbol = result.get("token_symbol")

        create_card(
            token_name,
            wallet,
            result.get("net_position", 0),
            result.get("cost_sol", 0),
            result.get("value_sol", 0),
            result.get("profit_sol", 0),
            result.get("roi_multiple", 1),
            logo_path=result.get("logo_path"),
            token_symbol=token_symbol,
            buy_count=result.get("buys", 0),
            sell_count=result.get("sells", 0),
            sol_price_usd=result.get("sol_price_usd", 0)
        )

        with open("position_card.png", "rb") as img:
            await update.message.reply_photo(photo=img)

    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")


async def share(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("MINIMAL TRIGGERED ✅")

    if not context.args:
        await update.message.reply_text("Usage: /share WALLET")
        return

    wallet = context.args[0]
    await update.message.reply_text("Scanning... ⏳")

    try:
        result = scan_wallet(wallet)

        create_minimal_card(
            result.get("token_name"),
            result.get("profit_sol", 0),
            result.get("roi_multiple", 1),
            logo_path=result.get("logo_path"),
            token_symbol=result.get("token_symbol"),
            sol_price_usd=result.get("sol_price_usd", 0)
        )

        with open("minimal_card.png", "rb") as img:  # ✅ CORRECT FILE
            await update.message.reply_photo(photo=img)

    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan))
    app.add_handler(CommandHandler("share", share))

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
