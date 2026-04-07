import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from scanner import scan_wallet
from image_card import create_card

from PIL import Image, ImageDraw, ImageFont, ImageFilter


def create_minimal_card(profit, roi, token_name, token_symbol, logo_path, sol_price_usd):
    from PIL import Image, ImageDraw, ImageFont
    import os

    width, height = 700, 400

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    font_path = os.path.join(BASE_DIR, "Inter.ttf")
    brand_logo_path = os.path.join(BASE_DIR, "logo.png")

    img = Image.new("RGBA", (width, height))
    draw = ImageDraw.Draw(img)

    # Gradient background
    for y in range(height):
        r = int(40 + (y / height) * 40)
        g = int(20 + (y / height) * 20)
        b = int(90 + (y / height) * 80)
        draw.line((0, y, width, y), fill=(r, g, b))

    # ===== ROI GLOW =====
    glow = Image.new("RGBA", (width + 100, height + 100), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)

    glow_color = (0, 255, 120) if roi > 1 else (255, 80, 80)

    glow_draw.ellipse(
        (250, 160, width - 250, height - 160),
        fill=(*glow_color, 120)
    )

    glow = glow.filter(ImageFilter.GaussianBlur(35))
    img.paste(glow, (-50, -50), glow)

    try:
        roi_font = ImageFont.truetype(font_path, 90)
        profit_font = ImageFont.truetype(font_path, 36)
        small_font = ImageFont.truetype(font_path, 22)
    except:
        roi_font = ImageFont.load_default()
        profit_font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    roi_color = (0, 255, 120) if roi > 1 else (255, 80, 80)
    profit_color = (0, 255, 120) if profit >= 0 else (255, 80, 80)

    # Header
    header_text = f"{token_name} (${token_symbol})"
    draw.text((30, 30), header_text, fill=(255, 255, 255), font=small_font)

    # Token logo
    try:
        if logo_path and os.path.exists(logo_path):
            token_logo = Image.open(logo_path).convert("RGBA")
            token_logo = token_logo.resize((80, 80))

            mask = Image.new("L", (80, 80), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, 80, 80), fill=255)
            token_logo.putalpha(mask)

            img.paste(token_logo, (width - 100, 20), token_logo)
    except:
        pass

    # ===== ROI (CENTERED HERO) =====
    roi_text = f"{roi:.2f}x"

    bbox = draw.textbbox((0, 0), roi_text, font=roi_font)
    text_w = bbox[2] - bbox[0]

    # Shadow
    draw.text(
        ((width - text_w) // 2 + 2, height // 2 - 88),
        roi_text,
        fill=(0, 0, 0),
        font=roi_font
    )

    draw.text(
        ((width - text_w) // 2, height // 2 - 90),
        roi_text,
        fill=roi_color,
        font=roi_font
    )

    # ===== PROFIT CENTERED =====
    profit_usd = profit * sol_price_usd
    profit_text = f"{'+' if profit >= 0 else ''}{profit:.2f} SOL (${profit_usd:.2f})"

    bbox = draw.textbbox((0, 0), profit_text, font=profit_font)
    text_w = bbox[2] - bbox[0]

    draw.text(
        ((width - text_w) // 2, height // 2 + 30),
        profit_text,
        fill=profit_color,
        font=profit_font
    )

    # Brand logo
    try:
        if os.path.exists(brand_logo_path):
            brand_logo = Image.open(brand_logo_path).convert("RGBA")
            brand_logo = brand_logo.resize((120, 120))
            img.paste(brand_logo, (width - 140, height - 140), brand_logo)
    except:
        pass

    img.save("position_card.png")


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

        print("DEBUG RESULT:", result)

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

        profit = result.get("profit_sol", 0)
        roi = result.get("roi_multiple", 1)

        create_minimal_card(
            profit,
            roi,
            result.get("token_name"),
            result.get("token_symbol"),
            result.get("logo_path"),
            result.get("sol_price_usd", 0)
        )

        with open("position_card.png", "rb") as img:
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
