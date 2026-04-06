import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from scanner import scan_wallet
from image_card import create_card

from PIL import Image, ImageDraw, ImageFont


def create_minimal_card(profit, roi):
    img = Image.new("RGB", (600, 300), (20, 20, 40))
    draw = ImageDraw.Draw(img)

    try:
        font_big = ImageFont.truetype("Inter.ttf", 110)
        font_small = ImageFont.truetype("Inter.ttf", 40)
    except:
        font_big = ImageFont.load_default()
        font_small = ImageFont.load_default()

    roi_color = (0, 255, 120) if roi > 1 else (255, 80, 80)
    profit_color = (0, 255, 120) if profit >= 0 else (255, 80, 80)

    draw.text((120, 60), f"{roi:.2f}x", fill=roi_color, font=font_big)
    draw.text((140, 200), f"{'+' if profit >= 0 else ''}{profit:.2f} SOL",
              fill=profit_color, font=font_small)

    img.save("position_card.png")


BOT_TOKEN = os.getenv("BOT_TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is live 🚀")


# ✅ FULL CARD
async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /scan WALLET")
        return

    wallet = context.args[0]
    await update.message.reply_text("Scanning... ⏳")

    try:
        result = scan_wallet(wallet)

        token_name = result.get("token_name") or result.get("name") or "Token"
        token_symbol = result.get("token_symbol") or result.get("symbol")

        tokens = result.get("net_position", 0)
        cost = result.get("cost_sol", 0)
        value = result.get("value_sol", 0)
        profit = result.get("profit_sol", 0)
        roi = result.get("roi_multiple", 1)

        buy_count = result.get("buys", 0)
        sell_count = result.get("sells", 0)

        sol_price = result.get("sol_price_usd", 0)

        create_card(
            token_name,
            wallet,
            tokens,
            cost,
            value,
            profit,
            roi,
            logo_path=result.get("logo_path"),
            token_symbol=token_symbol,
            buy_count=buy_count,
            sell_count=sell_count,
            sol_price_usd=sol_price
        )

        with open("position_card.png", "rb") as img:
            await update.message.reply_photo(photo=img)

    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")


# ✅ MINIMAL CARD (NEW COMMAND)
async def scanminimal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /scanminimal WALLET")
        return

    wallet = context.args[0]
    await update.message.reply_text("Scanning... ⏳")

    try:
        result = scan_wallet(wallet)

        profit = result.get("profit_sol", 0)
        roi = result.get("roi_multiple", 1)

        create_minimal_card(profit, roi)

        with open("position_card.png", "rb") as img:
            await update.message.reply_photo(photo=img)

    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan))
    app.add_handler(CommandHandler("scanminimal", scanminimal))  # ✅ NEW

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
