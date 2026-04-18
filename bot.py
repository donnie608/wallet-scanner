import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from scanner import scan_wallet
from image_card import create_minimal_card, create_minimal_eth_card

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is live 🚀")


async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        wallet = context.args[0]
    except:
        await update.message.reply_text("Usage: /scan WALLET_ADDRESS")
        return

    await update.message.reply_text("Scanning... ⏳")

    try:
        chain = "eth" if wallet.startswith("0x") else "sol"
        result = scan_wallet(wallet, chain=chain)

        with open("position_card.png", "rb") as img:
            await update.message.reply_photo(photo=img)

        if chain == "eth":
            response = (
                f"🪙 {result['token_name']} (${result['token_symbol']})\n\n"
                f"📊 {result['buys']} Buys | {result['sells']} Sells\n"
                f"💰 Cost: ${result['total_usd_spent']}\n"
                f"💵 Value: ${result['value_usd']}\n"
                f"📈 Profit: ${result['current_profit_usd']}\n"
                f"🚀 ROI: {result['roi_multiple_usd']}x"
            )
        else:
            response = (
                f"🪙 {result['token_name']} (${result['token_symbol']})\n\n"
                f"📊 {result['buys']} Buys | {result['sells']} Sells\n"
                f"💰 Cost: {result['cost_sol']} SOL\n"
                f"💵 Value: {result['value_sol']} SOL\n"
                f"📈 Profit: {result['profit_sol']} SOL\n"
                f"🚀 ROI: {result['roi_multiple']}x"
            )

        await update.message.reply_text(response)

    except Exception as e:
        import traceback
        await update.message.reply_text(f"❌ Error: {str(e)}\n{traceback.format_exc()}")

async def share(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        wallet = context.args[0]
    except:
        await update.message.reply_text("Usage: /share WALLET_ADDRESS")
        return

    await update.message.reply_text("Generating card... ⏳")

    try:
        chain = "eth" if wallet.startswith("0x") else "sol"
        result = scan_wallet(wallet, chain=chain)

        if chain == "eth":
            create_minimal_eth_card(
                token_name=result["token_name"],
                profit_usd=result["current_profit_usd"],
                roi=result["roi_multiple_usd"],
                logo_path="temp_logo.png",
                token_symbol=result["token_symbol"],
            )
        else:
            create_minimal_card(
                token_name=result["token_name"],
                profit=result["profit_sol"],
                roi=result["roi_multiple"],
                logo_path=result.get("logo_path"),
                token_symbol=result["token_symbol"],
                sol_price_usd=result["sol_price_usd"],
            )

        with open("minimal_card.png", "rb") as img:
            await update.message.reply_photo(photo=img)

    except Exception as e:
        import traceback
        await update.message.reply_text(f"❌ Error: {str(e)}\n{traceback.format_exc()}")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan))
    app.add_handler(CommandHandler("share", share))

    print("Bot running...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
