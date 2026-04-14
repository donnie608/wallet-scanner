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
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
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
        except Exception:
            pass

    try:
        url = f"https://api.dexscreener.com/latest/dex/tokens/{TARGET_TOKEN}"
        res = requests.get(url, timeout=10).json()

        pairs = res.get("pairs", [])
        sol_pairs = [
            p for p in pairs
            if p.get("quoteToken", {}).get("address") == SOL_MINT
        ]

        if not sol_pairs:
            return 0, 0, 0, "Unknown Token", "UNKNOWN", []

        best_pair = max(sol_pairs, key=lambda p: float(p.get("volume", {}).get("h24", 0) or 0))

        raw_logo = best_pair.get("info", {}).get("imageUrl")
        token_price_usd = float(best_pair.get("priceUsd", 0) or 0)
        token_name = best_pair.get("baseToken", {}).get("name", "Unknown Token")
        token_symbol = best_pair.get("baseToken", {}).get("symbol", "UNKNOWN")

        logo_candidates = []
        if raw_logo:
            logo_candidates.append(raw_logo)

        sol_url = f"https://api.dexscreener.com/latest/dex/tokens/{SOL_MINT}"
        sol_res = requests.get(sol_url, timeout=10).json()

        sol_pairs = sol_res.get("pairs", [])
        best_sol = max(sol_pairs, key=lambda p: float(p.get("volume", {}).get("h24", 0) or 0))

        sol_price_usd = float(best_sol.get("priceUsd", 0) or 0)
        token_price_sol = token_price_usd / sol_price_usd if sol_price_usd else 0

        try:
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "timestamp": time.time(),
                    "price_usd": token_price_usd,
                    "price_sol": token_price_sol,
                    "sol_price_usd": sol_price_usd,
                    "token_name": token_name,
                    "token_symbol": token_symbol,
                    "logo_candidates": logo_candidates
                }, f)
        except Exception:
            pass

        return token_price_usd, token_price_sol, sol_price_usd, token_name, token_symbol, logo_candidates

    except Exception:
        return 0, 0, 0, "Unknown Token", "UNKNOWN", []


def download_logo(logo_candidates):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    logo_path = os.path.join(base_dir, "temp_logo.png")

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
        except Exception:
            continue

    return None

def get_wallet_token_balance(wallet, token_mint):
    try:
        url = f"https://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}"
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTokenAccountsByOwner",
            "params": [
                wallet,
                {"mint": token_mint},
                {"encoding": "jsonParsed"}
            ]
        }
        res = requests.post(url, json=payload, timeout=15).json()
        accounts = res.get("result", {}).get("value", [])
        total = 0.0
        for acc in accounts:
            amount = acc.get("account", {}).get("data", {}).get("parsed", {}).get("info", {}).get("tokenAmount", {}).get("uiAmount", 0) or 0
            total += float(amount)
        return total
    except Exception as e:
        print("RPC BALANCE ERROR:", e)
        return 0.0

def get_wallet_token_account(wallet, token_mint):
    try:
        url = f"https://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}"
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTokenAccountsByOwner",
            "params": [
                wallet,
                {"mint": token_mint},
                {"encoding": "jsonParsed"}
            ]
        }

        res = requests.post(url, json=payload, timeout=15).json()
        accounts = res.get("result", {}).get("value", [])

        if not accounts:
            return None

        return accounts[0].get("pubkey")

    except Exception as e:
        print("RPC TOKEN ACCOUNT ERROR:", e)
        return None

def get_signatures_for_address(address, limit=1000):
    try:
        url = f"https://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}"
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getSignaturesForAddress",
            "params": [
                address,
                {"limit": limit}
            ]
        }

        res = requests.post(url, json=payload, timeout=20).json()
        results = res.get("result", [])

        signatures = []
        for item in results:
            sig = item.get("signature")
            if sig:
                signatures.append(sig)

        return signatures

    except Exception as e:
        print("RPC SIGNATURE ERROR:", e)
        return []

def solana_scan(wallet):
    if not HELIUS_API_KEY:
        raise ValueError("HELIUS_API_KEY not found in .env")

    print("Scanning SOL wallet:", wallet)

    token_account = get_wallet_token_account(wallet, TARGET_TOKEN)
   
    all_transactions = []
    max_tx = 1000

    # 1) Fetch wallet-address transactions (your current source)
    before = None
    while True:
        url = f"https://api.helius.xyz/v0/addresses/{wallet}/transactions?api-key={HELIUS_API_KEY}"
        if before:
            url += f"&before={before}"

        response = requests.get(url, timeout=20)
        batch = response.json()

        if not batch:
            break

        all_transactions.extend(batch)

        if len(all_transactions) >= max_tx:
            break

        before = batch[-1]["signature"]

    # 2) Fetch token-account transactions for missing transfer coverage
    extra_transactions = []
    seen_wallet_sigs = {tx.get("signature") for tx in all_transactions if tx.get("signature")}

    token_account_sigs = get_signatures_for_address(token_account, limit=100)
    missing_token_sigs = [sig for sig in token_account_sigs if sig not in seen_wallet_sigs]

    for sig in missing_token_sigs:
        url = f"https://api.helius.xyz/v0/transactions/?api-key={HELIUS_API_KEY}"
        payload = {"transactions": [sig]}

        try:
            response = requests.post(url, json=payload, timeout=20)
            batch = response.json()

            if isinstance(batch, list) and batch:
                extra_transactions.extend(batch)
        except Exception:
            pass

    all_transactions.extend(extra_transactions)

    total_bought = 0.0
    total_sold = 0.0
    sol_spent = 0.0
    sol_received = 0.0

    buy_count = 0
    sell_count = 0
    transfer_in_count = 0
    transfer_out_count = 0

    buy_signatures = set()
    sell_signatures = set()
    transfer_in_signatures = set()
    transfer_out_signatures = set()

    SOL_TRADE_THRESHOLD = 0.01

    for tx in all_transactions:
        sig = tx.get("signature", "")
        sol_change = 0.0

        for acc in tx.get("accountData", []):
            if acc.get("account") == wallet:
                sol_change = acc.get("nativeBalanceChange", 0) / LAMPORTS_PER_SOL
                break

        incoming_amount = 0.0
        outgoing_amount = 0.0

        for transfer in tx.get("tokenTransfers", []):
            if transfer.get("mint") != TARGET_TOKEN:
                continue

            token_amount = transfer.get("tokenAmount", 0)
            if isinstance(token_amount, dict):
                amount = float(token_amount.get("uiAmount", 0) or 0)
            elif token_amount is not None:
                try:
                    amount = float(token_amount)
                except Exception:
                    amount = 0.0
            else:
                amount = 0.0

            sender = transfer.get("fromUserAccount")
            receiver = transfer.get("toUserAccount")

            if receiver == wallet and amount > 0:
                incoming_amount += amount
            elif sender == wallet and amount > 0:
                outgoing_amount += amount

        if incoming_amount > 0 and outgoing_amount == 0:
            if sol_change < -SOL_TRADE_THRESHOLD and sig not in buy_signatures:
                buy_signatures.add(sig)
                total_bought += incoming_amount
                sol_spent += abs(sol_change)
                buy_count += 1
            elif sig not in transfer_in_signatures:
                transfer_in_signatures.add(sig)
                transfer_in_count += 1

        elif outgoing_amount > 0 and incoming_amount == 0:
            if sol_change > SOL_TRADE_THRESHOLD and sig not in sell_signatures:
                sell_signatures.add(sig)
                total_sold += outgoing_amount
                sol_received += abs(sol_change)
                sell_count += 1
            elif sig not in transfer_out_signatures:
                transfer_out_signatures.add(sig)
                transfer_out_count += 1

        elif incoming_amount > 0 and outgoing_amount > 0:
            net_amount = incoming_amount - outgoing_amount

            if net_amount > 0:
                if sol_change < -SOL_TRADE_THRESHOLD and sig not in buy_signatures:
                    buy_signatures.add(sig)
                    total_bought += net_amount
                    sol_spent += abs(sol_change)
                    buy_count += 1
                elif sig not in transfer_in_signatures:
                    transfer_in_signatures.add(sig)
                    transfer_in_count += 1

            elif net_amount < 0:
                if sol_change > SOL_TRADE_THRESHOLD and sig not in sell_signatures:
                    sell_signatures.add(sig)
                    total_sold += abs(net_amount)
                    sol_received += abs(sol_change)
                    sell_count += 1
                elif sig not in transfer_out_signatures:
                    transfer_out_signatures.add(sig)
                    transfer_out_count += 1
    net_position = get_wallet_token_balance(wallet, TARGET_TOKEN)
    net_cost = sol_spent - sol_received

    price_usd, price_sol, sol_price_usd, token_name, token_symbol, logo_candidates = get_token_data()
    logo_path = download_logo(logo_candidates)

    current_value_sol = net_position * price_sol
    unrealized_profit = current_value_sol - net_cost

    if net_cost > 0:
        roi_multiple = unrealized_profit / net_cost
    elif sol_spent > 0:
        roi_multiple = (sol_received - sol_spent) / sol_spent
    else:
        roi_multiple = 0

    print("\n" + "=" * 50)
    print("SOL WALLET SUMMARY")
    print("=" * 50)

    print(f"Wallet: {wallet}")
    print(f"Token: {token_name} (${token_symbol})")

    print("\n--- ACTIVITY ---")
    print(f"{buy_count} Buys | {sell_count} Sells | {transfer_in_count} Transfers In | {transfer_out_count} Transfers Out")

    print("\n--- POSITION ---")
    print(f"Net Position: {round(net_position, 2)} tokens")

    print("\n--- CAPITAL ---")
    print(f"SOL Spent: {round(sol_spent, 4)}")
    print(f"SOL Recovered: {round(sol_received, 4)}")
    print(f"Net Cost: {round(net_cost, 4)}")
    print(f"Current Value: {round(current_value_sol, 4)}")

    print("\n--- PERFORMANCE ---")
    print(f"PnL: {round(unrealized_profit, 4)} SOL")
    print(f"ROI: {round(roi_multiple, 2)}x")

    print(f"\nSOL Price: ${round(sol_price_usd, 2)}")

    create_card(
        token_name=token_name,
        wallet=wallet,
        tokens=round(net_position, 2),
        cost=round(net_cost, 4),
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
        "cost_sol": round(net_cost, 4),
        "value_sol": round(current_value_sol, 4),
        "profit_sol": round(unrealized_profit, 4),
        "roi_multiple": round(roi_multiple, 2),
        "buys": buy_count,
        "sells": sell_count,
        "transfers_in": transfer_in_count,
        "transfers_out": transfer_out_count,
        "sol_price_usd": sol_price_usd,
        "logo_path": logo_path
    }

def scan_wallet(wallet):
    return solana_scan(wallet)
