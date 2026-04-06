import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from scanner import scan_wallet
from image_card import create_card, create_minimal_card

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

        # SAFE KEY HANDLING
        token_name = result.get("token_name") or result.get("name") or "Token"
        token_symbol = result.get("token_symbol") or result.get("symbol")

        # 🔥 MODE SWITCH (CORRECT WAY)
        if mode == "minimal":
            create_minimal_card(
                result.get("profit_sol", 0),
                result.get("roi", 1)
            )
        else:
            create_card(
                token_name,
                wallet,
                result.get("tokens", 0),
                result.get("cost_sol", 0),
                result.get("value_sol", 0),
                result.get("profit_sol", 0),
                result.get("roi", 1),
                logo_path=result.get("logo_path"),
                token_symbol=token_symbol,
                buy_count=result.get("buy_count", 0),
                sell_count=result.get("sell_count", 0),
                sol_price_usd=result.get("sol_price_usd", 0)
            )

        # SEND IMAGE
        with open("position_card.png", "rb") as img:
            await update.message.reply_photo(photo=img)

        # TEXT RESPONSE
        response = f"""
ROI: {result.get('roi', 0)}x
Profit: {result.get('profit_sol', 0)} SOL
Value: {result.get('value_sol', 0)} SOL
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
