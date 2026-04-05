from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from scanner import scan_wallet  # we will use your existing function

import os
BOT_TOKEN = os.getenv("BOT_TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is live 🚀")


async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        wallet = context.args[0]
    except:
        await update.message.reply_text("Usage: /scan WALLET")
        return

    await update.message.reply_text("Scanning... ⏳")

    try:
        result = scan_wallet(wallet)

        # Send image
        with open("position_card.png", "rb") as img:
            await update.message.reply_photo(photo=img)

        # Optional text (keep or remove later)
        response = f"""
ROI: {result['roi']}x
Profit: {result['profit_sol']} SOL
Value: {result['value_sol']} SOL
"""

        await update.message.reply_text(response)

    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan))

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()