async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /scan WALLET [minimal]")
        return

    wallet = context.args[0]
    mode = "minimal" if len(context.args) > 1 and context.args[1].lower() == "minimal" else "full"

    await update.message.reply_text("Scanning... ⏳")

    try:
        result = scan_wallet(wallet)

        # ✅ FIXED KEY MAPPING
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

        if mode == "minimal":
            create_minimal_card(profit, roi)
        else:
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

        await update.message.reply_text(
            f"ROI: {roi}x\n"
            f"Profit: {profit} SOL\n"
            f"Value: {value} SOL"
        )

    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")
