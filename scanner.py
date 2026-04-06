import requests
import os
import json
import time
from image_card import create_card
from PIL import Image
from io import BytesIO

print("SCRIPT STARTED")

import os
API_KEY = os.getenv("HELIUS_API_KEY")

TARGET_TOKEN = "6LbSLaDwTTke2nmMzP2NKuEWVP7QWPGvmNMjD7QApump"
SOL_MINT = "So11111111111111111111111111111111111111112"

LAMPORTS_PER_SOL = 1_000_000_000

CACHE_FILE = "token_cache.json"
CACHE_TTL = 60  # seconds


# ===== TOKEN DATA WITH CACHING =====
def get_token_data():

    # Try cache first
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                cache = json.load(f)

            if time.time() - cache["timestamp"] < CACHE_TTL:
                return (
                    cache["price_usd"],
                    cache["price_sol"],
                    cache["sol_price_usd"],
                    cache["token_name"],
                    cache["token_symbol"],
                    cache["logo_candidates"]
                )
        except:
            pass

    # Fetch fresh
    try:
        url = f"https://api.dexscreener.com/latest/dex/tokens/{TARGET_TOKEN}"
        res = requests.get(url, timeout=10).json()

        pairs = res.get("pairs", [])
        sol_pairs = [p for p in pairs if p.get("quoteToken", {}).get("address") == SOL_MINT]

        if not sol_pairs:
            return 0, 0, 0, "Unknown Token", "UNKNOWN", []

        best_pair = max(sol_pairs, key=lambda p: float(p.get("volume", {}).get("h24", 0)))

        raw_logo = best_pair.get("info", {}).get("imageUrl")

        token_price_usd = float(best_pair.get("priceUsd", 0))
        token_name = best_pair.get("baseToken", {}).get("name", "Unknown Token")
        token_symbol = best_pair.get("baseToken", {}).get("symbol", "UNKNOWN")

        logo_candidates = []
        if raw_logo:
            logo_candidates.append(raw_logo)

        # SOL price
        sol_url = f"https://api.dexscreener.com/latest/dex/tokens/{SOL_MINT}"
        sol_res = requests.get(sol_url, timeout=10).json()

        sol_pairs = sol_res.get("pairs", [])
        best_sol = max(sol_pairs, key=lambda p: float(p.get("volume", {}).get("h24", 0)))

        sol_price_usd = float(best_sol.get("priceUsd", 0))

        token_price_sol = token_price_usd / sol_price_usd if sol_price_usd else 0

        # Save cache
        try:
            with open(CACHE_FILE, "w") as f:
                json.dump({
                    "timestamp": time.time(),
                    "price_usd": token_price_usd,
                    "price_sol": token_price_sol,
                    "sol_price_usd": sol_price_usd,
                    "token_name": token_name,
                    "token_symbol": token_symbol,
                    "logo_candidates": logo_candidates
                }, f)
        except:
            pass

        return token_price_usd, token_price_sol, sol_price_usd, token_name, token_symbol, logo_candidates

    except:
        return 0, 0, 0, "Unknown Token", "UNKNOWN", []


def download_logo(logo_candidates):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    logo_path = os.path.join(BASE_DIR, "temp_logo.png")

    for url in logo_candidates:
        try:
            if not url:
                continue

            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200 and response.content:
                img = Image.open(BytesIO(response.content)).convert("RGBA")
                img.save(logo_path, format="PNG")
                return logo_path

        except:
            continue

    return None


def scan_wallet(wallet,):
    print("Scanning wallet:", wallet)

    all_transactions = []
    before = None
    MAX_TX = 1000

    while True:
        url = f"https://api.helius.xyz/v0/addresses/{wallet}/transactions?api-key={API_KEY}"
        if before:
            url += f"&before={before}"

        response = requests.get(url)
        batch = response.json()

        if not batch:
            break

        all_transactions.extend(batch)

        if len(all_transactions) >= MAX_TX:
            break

        before = batch[-1]["signature"]

    total_bought = 0
    total_sold = 0
    sol_spent = 0

    buy_count = 0
    sell_count = 0

    for tx in all_transactions:
        sol_change = 0

        for acc in tx.get("accountData", []):
            if acc.get("account") == wallet:
                sol_change = acc.get("nativeBalanceChange", 0) / LAMPORTS_PER_SOL

        for transfer in tx.get("tokenTransfers", []):
            if transfer.get("mint") != TARGET_TOKEN:
                continue

            token_amount = transfer.get("tokenAmount", 0)

            if isinstance(token_amount, dict):
                amount = token_amount.get("uiAmount", 0)
            else:
                amount = token_amount

            sender = transfer.get("fromUserAccount")
            receiver = transfer.get("toUserAccount")

            if receiver == wallet:
                total_bought += amount
                sol_spent += abs(sol_change)
                buy_count += 1

            elif sender == wallet:
                total_sold += amount
                sell_count += 1

    net_position = total_bought - total_sold

    price_usd, price_sol, sol_price_usd, token_name, token_symbol, logo_candidates = get_token_data()
    logo_path = download_logo(logo_candidates)

    current_value_sol = net_position * price_sol
    unrealized_profit = current_value_sol - sol_spent
    roi_multiple = current_value_sol / sol_spent if sol_spent > 0 else 0

    # ===== DASHBOARD =====
    print("\n" + "="*50)
    print("WALLET SUMMARY")
    print("="*50)

    print(f"Wallet: {wallet}")
    print(f"Token: {token_name} (${token_symbol})")

    print("\n--- ACTIVITY ---")
    print(f"{buy_count} Buys | {sell_count} Sells")

    print("\n--- POSITION ---")
    print(f"Net Position: {round(net_position, 2)} tokens")

    print("\n--- CAPITAL ---")
    print(f"SOL Spent: {round(sol_spent, 4)}")
    print(f"Current Value: {round(current_value_sol, 4)}")

    print("\n--- PERFORMANCE ---")
    print(f"PnL: {round(unrealized_profit, 4)} SOL")
    print(f"ROI: {round(roi_multiple, 2)}x")

    print(f"\nSOL Price: ${round(sol_price_usd, 2)}")

    create_card(
        token_name=token_name,
        wallet=wallet,
        tokens=round(net_position, 2),
        cost=round(sol_spent, 4),
        value=round(current_value_sol, 4),
        profit=round(unrealized_profit, 4),
        roi=round(roi_multiple, 2),
        logo_path=logo_path,
        token_symbol=token_symbol,
        buy_count=buy_count,
        sell_count=sell_count,
        sol_price_usd=sol_price_usd
    )

    print("\n--- CARD GENERATED ---")
    print("Saved as position_card.png\n")

      return {
        "token_name": token_name,
        "token_symbol": token_symbol,
        "net_position": round(net_position, 2),
        "cost_sol": round(sol_spent, 4),
        "value_sol": round(current_value_sol, 4),
        "profit_sol": round(unrealized_profit, 4),
        "roi_multiple": round(roi_multiple, 2),
        "buys": buy_count,
        "sells": sell_count,
        "sol_price_usd": sol_price_usd,
        "logo_path": logo_path
    }

