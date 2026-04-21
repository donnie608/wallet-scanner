import os
import time
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    CallbackQueryHandler,
    filters,
)

from scanner import scan_wallet
from image_card import create_card, create_minimal_card, create_eth_card, create_minimal_eth_card
from analytics import track_event, get_stats, get_top_wallets

BOT_TOKEN = os.getenv("BOT_TOKEN")


# =========================
# KEYBOARD
# =========================
def get_keyboard():
    return ReplyKeyboardMarkup(
        [
            ["🔍 Scan Wallet", "📤 Create Shareable Card"],
            ["🔥 Trending", "📊 Stats"],
        ],
        resize_keyboard=True,
    )


# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to BOWS 🐷 - Big Oinker's Wallet Scanner\n\n"
        "Scan any SOL or ETH wallet instantly.\n\n"
        "How to use:\n"
        "• 🔍 Scan Wallet — paste an address to see your full position, cost, value, profit & ROI\n"
        "• 📤 Create Shareable Card — generate a minimal image card to share your ROI\n"
        "• 🔥 Trending — see the most scanned wallets in the past 2 hours\n"
        "• 📊 Stats — view bot usage analytics\n\n"
        "You can also type /scan or /share followed by a wallet address.\n\n"
        "SOL wallets start with a letter or number\n"
        "ETH wallets start with 0x\n\n"
        "How to read your results:\n"
        "• Cost — total SOL/USD you spent buying (USD uses historical prices per transaction)\n"
        "• Value — what your tokens are worth right now\n"
        "• Break-Even — how much you still need to recover (negative = you're already in profit from sells)\n"
        "• Profit — value + sells minus cost\n"
        "• ROI — your total return if you sold everything now (2x = doubled your money, 0.5x = lost half)",
        reply_markup=get_keyboard(),
    )


# =========================
# HELPER: build card for either chain
# =========================
def build_card_for_result(result, wallet, chain):
    if chain == "eth":
        create_eth_card(
            token_name=result.get("token_name"),
            wallet=wallet,
            tokens=result.get("net_position", 0),
            cost_usd=result.get("total_usd_spent", 0),
            value_usd=result.get("value_usd", 0),
            profit_usd=result.get("current_profit_usd", 0),
            roi=result.get("roi_multiple_usd", 0),
            logo_path="temp_logo.png",
            token_symbol=result.get("token_symbol"),
            buy_count=result.get("buys", 0),
            sell_count=result.get("sells", 0),
        )
    else:
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
            cost_usd_historical=result.get("total_usd_spent"),
        )


def build_minimal_card_for_result(result, chain):
    if chain == "eth":
        create_minimal_eth_card(
            token_name=result.get("token_name"),
            profit_usd=result.get("current_profit_usd", 0),
            roi=result.get("roi_multiple_usd", 0),
            logo_path="temp_logo.png",
            token_symbol=result.get("token_symbol"),
            avg_buy_price=result.get("avg_buy_price_usd", 0),
            current_price=result.get("token_price_usd", 0),
        )
    else:
        create_minimal_card(
            result.get("token_name"),
            result.get("profit_sol", 0),
            result.get("roi_multiple", 1),
            logo_path=result.get("logo_path"),
            token_symbol=result.get("token_symbol"),
            sol_price_usd=result.get("sol_price_usd", 0),
        )


# =========================
# /scan
# =========================
async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        wallet = context.args[0]
        user_id = update.message.from_user.id

        await update.message.reply_text("Full Scan Triggered ⏳")

        try:
            track_event("scan", user_id, wallet)
            chain = "eth" if wallet.startswith("0x") else "sol"
            start_time = time.time()
            result = scan_wallet(wallet, chain=chain)

            if result.get("buys", 0) == 0 and result.get("sells", 0) == 0 and result.get("net_position", 0) == 0:
                await update.message.reply_text(
                    "⚠️ No activity found for this wallet.\n\n"
                    "• Double check the wallet address\n"
                    "• Make sure it has traded the target token"
                )
                return

            build_card_for_result(result, wallet, chain)

            with open("position_card.png", "rb") as img:
                await update.message.reply_photo(photo=img)

            await update.message.reply_text(build_scan_report(result, wallet, chain))
            elapsed = round(time.time() - start_time, 1)
            await update.message.reply_text(f"✅ Scan completed in {elapsed}s")

        except Exception as e:
            print(f"Scan error: {e}")
            await update.message.reply_text(
                "❌ Scan failed. Please check:\n\n"
                "• Is the wallet address correct?\n"
                "• SOL wallets start with a letter or number\n"
                "• ETH wallets start with 0x\n\n"
                "If the address is correct, try again in a minute — the server may be busy."
            )

    else:
        context.user_data["mode"] = "scan"
        await update.message.reply_text("Send wallet address to scan ⏳")


# =========================
# /share
# =========================
async def share(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        wallet = context.args[0]
        user_id = update.message.from_user.id

        await update.message.reply_text("Share Scan Triggered ⏳")

        try:
            track_event("share", user_id, wallet)
            chain = "eth" if wallet.startswith("0x") else "sol"
            start_time = time.time()
            result = scan_wallet(wallet, chain=chain)

            if result.get("buys", 0) == 0 and result.get("sells", 0) == 0 and result.get("net_position", 0) == 0:
                await update.message.reply_text(
                    "⚠️ No activity found for this wallet.\n\n"
                    "• Double check the wallet address\n"
                    "• Make sure it has traded the target token"
                )
                return

            build_minimal_card_for_result(result, chain)

            with open("minimal_card.png", "rb") as img:
                await update.message.reply_photo(photo=img)

            elapsed = round(time.time() - start_time, 1)
            await update.message.reply_text(f"✅ Card generated in {elapsed}s")
            await send_trending(update)

        except Exception as e:
            print(f"Share error: {e}")
            await update.message.reply_text(
                "❌ Card generation failed. Please check:\n\n"
                "• Is the wallet address correct?\n"
                "• SOL wallets start with a letter or number\n"
                "• ETH wallets start with 0x\n\n"
                "If the address is correct, try again in a minute — the server may be busy."
            )

    else:
        context.user_data["mode"] = "share"
        await update.message.reply_text("Send wallet address to generate share card ⏳")


def build_scan_report(result, wallet, chain="sol"):
    if chain == "eth":
        return f"""
ETH WALLET SUMMARY

Token: {result.get('token_name')} (${result.get('token_symbol')})
Wallet: {wallet}

ACTIVITY
{result.get('buys', 0)} Buys | {result.get('sells', 0)} Sells | {result.get('received_transfers', 0)} Transfers In | {result.get('transfers_out', 0)} Transfers Out

POSITION
Net Position: {result.get('net_position', 0)} tokens

CAPITAL (USD)
Cost: ${result.get('total_usd_spent', 0)}
Value: ${result.get('value_usd', 0)}
Break-Even Remaining: ${result.get('break_even_remaining_usd', 0)}

PERFORMANCE
Profit: ${result.get('current_profit_usd', 0)}
ROI: {result.get('roi_multiple_usd', 0)}x

Avg Buy Price: ${result.get('avg_buy_price_usd', 0)}
Token Price: ${result.get('token_price_usd', 0)}
"""
    else:
        return f"""
SOL WALLET SUMMARY

Token: {result.get('token_name')} (${result.get('token_symbol')})
Wallet: {wallet}

ACTIVITY
{result.get('buys', 0)} Buys | {result.get('sells', 0)} Sells | {result.get('transfers_in', 0)} Transfers In | {result.get('transfers_out', 0)} Transfers Out

POSITION
Net Position: {result.get('net_position', 0)} tokens

CAPITAL
Net Cost: {result.get('cost_sol', 0)} SOL
Historical USD Cost: ${result.get('total_usd_spent', 0)}
Current Value: {result.get('value_sol', 0)} SOL

PERFORMANCE
PnL: {result.get('profit_sol', 0)} SOL
ROI: {result.get('roi_multiple', 0)}x

SOL Price: ${round(result.get('sol_price_usd', 0), 2)}
"""


# =========================
# /stats
# =========================
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_stats(update)


# =========================
# /top
# =========================
async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_trending(update)


# =========================
# HANDLE BUTTONS + WALLET INPUT
# =========================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "🔍 Scan Wallet":
        context.user_data["mode"] = "scan"
        await update.message.reply_text("Send wallet address to scan ⏳")

    elif text == "📤 Create Shareable Card":
        context.user_data["mode"] = "share"
        await update.message.reply_text("Send wallet address to generate share card ⏳")

    elif text == "🔥 Trending":
        await send_trending(update)

    elif text == "📊 Stats":
        await send_stats(update)

    else:
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
                chain = "eth" if wallet.startswith("0x") else "sol"
                start_time = time.time()
                result = scan_wallet(wallet, chain=chain)

                if result.get("buys", 0) == 0 and result.get("sells", 0) == 0 and result.get("net_position", 0) == 0:
                    await update.message.reply_text(
                        "⚠️ No activity found for this wallet.\n\n"
                        "• Double check the wallet address\n"
                        "• Make sure it has traded the target token"
                    )
                    return

                build_card_for_result(result, wallet, chain)

                with open("position_card.png", "rb") as img:
                    await update.message.reply_photo(photo=img)
                await update.message.reply_text(build_scan_report(result, wallet, chain))
                elapsed = round(time.time() - start_time, 1)
                await update.message.reply_text(f"✅ Scan completed in {elapsed}s")

            except Exception as e:
                print(f"Scan error: {e}")
                await update.message.reply_text(
                    "❌ Scan failed. Please check:\n\n"
                    "• Is the wallet address correct?\n"
                    "• SOL wallets start with a letter or number\n"
                    "• ETH wallets start with 0x\n\n"
                    "If the address is correct, try again in a minute — the server may be busy."
                )

        elif mode == "share":
            await update.message.reply_text("Share Scan Triggered ⏳")

            try:
                track_event("share", user_id, wallet)
                chain = "eth" if wallet.startswith("0x") else "sol"
                start_time = time.time()
                result = scan_wallet(wallet, chain=chain)

                if result.get("buys", 0) == 0 and result.get("sells", 0) == 0 and result.get("net_position", 0) == 0:
                    await update.message.reply_text(
                        "⚠️ No activity found for this wallet.\n\n"
                        "• Double check the wallet address\n"
                        "• Make sure it has traded the target token"
                    )
                    return

                build_minimal_card_for_result(result, chain)

                with open("minimal_card.png", "rb") as img:
                    await update.message.reply_photo(photo=img)

                elapsed = round(time.time() - start_time, 1)
                await update.message.reply_text(f"✅ Card generated in {elapsed}s")
                await send_trending(update)

            except Exception as e:
                print(f"Scan error: {e}")
                await update.message.reply_text(
                    "❌ Scan failed. Please check:\n\n"
                    "• Is the wallet address correct?\n"
                    "• SOL wallets start with a letter or number\n"
                    "• ETH wallets start with 0x\n\n"
                    "If the address is correct, try again in a minute — the server may be busy."
                )

# =========================
# CALLBACK HANDLER
# =========================
async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data.startswith("scan_"):
        wallet = data.replace("scan_", "")
        user_id = query.from_user.id

        await query.message.reply_text("Full Scan Triggered ⏳")

        try:
            track_event("scan", user_id, wallet)
            chain = "eth" if wallet.startswith("0x") else "sol"
            start_time = time.time()
            result = scan_wallet(wallet, chain=chain)

            if result.get("buys", 0) == 0 and result.get("sells", 0) == 0 and result.get("net_position", 0) == 0:
                await query.message.reply_text(
                    "⚠️ No activity found for this wallet.\n\n"
                    "• Double check the wallet address\n"
                    "• Make sure it has traded the target token"
                )
                return

            build_card_for_result(result, wallet, chain)

            with open("position_card.png", "rb") as img:
                await query.message.reply_photo(photo=img)

            await query.message.reply_text(build_scan_report(result, wallet, chain))
            elapsed = round(time.time() - start_time, 1)
            await query.message.reply_text(f"✅ Scan completed in {elapsed}s")

        except Exception as e:
            print(f"Scan error: {e}")
            await query.message.reply_text(
                "❌ Scan failed. Please check:\n\n"
                "• Is the wallet address correct?\n"
                "• SOL wallets start with a letter or number\n"
                "• ETH wallets start with 0x\n\n"
                "If the address is correct, try again in a minute — the server may be busy."
            )


# =========================
# STATS LOGIC
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
# TRENDING LOGIC
# =========================
async def send_trending(update: Update):
    top_wallets = get_top_wallets()

    if not top_wallets:
        await update.message.reply_text("No wallet data yet.")
        return

    msg = "🔥 Trending Wallets\n\n"
    keyboard = []

    for i, (wallet, count) in enumerate(top_wallets, start=1):
        short = wallet[:6] + "..." + wallet[-4:]
        label = " 🔥" if i == 1 else ""

        msg += f"{i}. {short} — Active{label}\n"

        keyboard.append([
            InlineKeyboardButton(
                text=f"🔍 Scan {short}",
                callback_data=f"scan_{wallet}"
            )
        ])

    msg += "\n👇 Tap to scan instantly"

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(msg, reply_markup=reply_markup)


# =========================
# MAIN
# =========================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # COMMANDS
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan))
    app.add_handler(CommandHandler("share", share))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("top", top))

    # CALLBACK BUTTONS
    app.add_handler(CallbackQueryHandler(handle_button))

    # MESSAGE HANDLER LAST
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot running...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
