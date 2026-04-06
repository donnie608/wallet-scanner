import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from scanner import scan_wallet
from image_card import create_card

BOT_TOKEN = os.getenv("BOT_TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is live 🚀")


async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /scan WALLET [minimal]")
        return

    wallet = context.args[0]
    mode = "minimal" if len(context.args) > 1 and context.args[1].lower() == "minimal" else "full"

    await update.message.reply_text("Scanning... ⏳")

    try:
        result = scan_wallet(wallet)

        create_card(
            result["token_name"],
            wallet,
            result["tokens"],
            result["cost_sol"],
            result["value_sol"],
            result["profit_sol"],
            result["roi"],
            logo_path=result.get("logo_path"),
            token_symbol=result.get("token_symbol"),
            buy_count=result.get("buy_count", 0),
            sell_count=result.get("sell_count", 0),
            sol_price_usd=result.get("sol_price_usd", 0),
            mode=mode
        )

        with open("position_card.png", "rb") as img:
            await update.message.reply_photo(photo=img)

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
