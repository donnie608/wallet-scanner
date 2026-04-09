import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from scanner import scan_wallet
from image_card import create_card, create_minimal_card
from analytics import track_event, get_stats, get_top_wallets

BOT_TOKEN = os.getenv("BOT_TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to BOWS - Big Oinker's Wallet Scanner 🔍")


# =========================
# FULL SCAN
# =========================
async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("FULL TRIGGERED ✅")

    if not context.args:
        await update.message.reply_text("Usage: /scan WALLET")
        return

    wallet = context.args[0]
    user_id = update.message.from_user.id

    await update.message.reply_text("Scanning... ⏳")

    try:
        track_event("scan", user_id, wallet)

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


# =========================
# MINIMAL SHARE (UPDATED 🔥)
# =========================
async def share(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("MINIMAL TRIGGERED ✅")

    if not context.args:
        await update.message.reply_text("Usage: /share WALLET")
        return

    wallet = context.args[0]
    user_id = update.message.from_user.id

    await update.message.reply_text("Scanning... ⏳")

    try:
        track_event("share", user_id, wallet)

        result = scan_wallet(wallet)

        create_minimal_card(
            result.get("token_name"),
            result.get("profit_sol", 0),
            result.get("roi_multiple", 1),
            logo_path=result.get("logo_path"),
            token_symbol=result.get("token_symbol"),
            sol_price_usd=result.get("sol_price_usd", 0)
        )

        # ✅ Send minimal card
        with open("minimal_card.png", "rb") as img:
            await update.message.reply_photo(photo=img)

        # =========================
        # 🔥 ADD TRENDING WALLETS HERE
        # =========================
        top_wallets = get_top_wallets()

        if top_wallets:
            msg = "🔥 Trending Wallets\n\n"

            for i, (w, count) in enumerate(top_wallets, start=1):
                short = w[:6] + "..." + w[-4:]

                # Optional label for top wallet
                if i == 1:
                    label = " 🔥"
                else:
                    label = ""

                msg += f"{i}. {short} — {count} scans{label}\n"

            msg += "\n👉 Try scanning one of these wallets"

            await update.message.reply_text(msg)

    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")


# =========================
# STATS
# =========================
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
# TOP WALLETS
# =========================
async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top_wallets = get_top_wallets()

    if not top_wallets:
        await update.message.reply_text("No wallet data yet.")
        return

    msg = "🔥 Top Wallets\n\n"

    for i, (wallet, count) in enumerate(top_wallets, start=1):
        short = wallet[:6] + "..." + wallet[-4:]
        msg += f"{i}. {short} — {count} scans\n"

    await update.message.reply_text(msg)


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan))
    app.add_handler(CommandHandler("share", share))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("top", top))

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
