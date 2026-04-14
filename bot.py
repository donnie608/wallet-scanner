import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from scanner import scan_wallet

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

        with open("position_card.png", "rb") as img:
            await update.message.reply_photo(photo=img)

        response = f"""
SOL WALLET SUMMARY

Token: {result['token_name']} (${result['token_symbol']})
Wallet: {wallet}

ACTIVITY
{result['buys']} Buys | {result['sells']} Sells | {result['transfers_in']} Transfers In | {result['transfers_out']} Transfers Out

POSITION
Net Position: {result['net_position']} tokens

CAPITAL
Net Cost: {result['cost_sol']} SOL
Current Value: {result['value_sol']} SOL

PERFORMANCE
PnL: {result['profit_sol']} SOL
ROI: {result['roi_multiple']}x

SOL Price: ${round(result['sol_price_usd'], 2)}
"""
        await update.message.reply_text(response)


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan))

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
