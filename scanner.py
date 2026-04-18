from image_card import create_card, create_eth_card
from dotenv import load_dotenv
import requests
import os
import json
import time
from image_card import create_card
from PIL import Image
from io import BytesIO

load_dotenv()

print("SCRIPT STARTED")

# =========================
# API KEYS FROM .env
# =========================
HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")
MORALIS_API_KEY = os.getenv("MORALIS_API_KEY")
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
ALPHAVANTAGE_API_KEY = os.getenv("ALPHAVANTAGE_API_KEY")

# =========================
# SOLANA CONFIG
# =========================
TARGET_TOKEN = "6LbSLaDwTTke2nmMzP2NKuEWVP7QWPGvmNMjD7QApump"
SOL_MINT = "So11111111111111111111111111111111111111112"
LAMPORTS_PER_SOL = 1_000_000_000

CACHE_FILE = "token_cache.json"
CACHE_TTL = 60  # seconds

# =========================
# ETH CONFIG
# =========================
ETH_TARGET_TOKEN = "0xc3f42ca0dcdfc9390a4ef881cb25116f5682def1"
CHAIN = "eth"
WETH_ADDRESS = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"

# =========================
# STARTUP CHECKS
# =========================
if not HELIUS_API_KEY:
    print("Warning: HELIUS_API_KEY not found in .env")

if not MORALIS_API_KEY:
    print("Warning: MORALIS_API_KEY not found in .env")

if not ETHERSCAN_API_KEY:
    print("Warning: ETHERSCAN_API_KEY not found in .env")

if not ALPHAVANTAGE_API_KEY:
    print("Warning: ALPHAVANTAGE_API_KEY not found in .env")

def safe_json(url, headers=None):
    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code != 200 or not res.text.strip():
            return {}
        return res.json()
    except Exception as e:
        print(f"Request error: {e}")
        return {}


# ==================================================
# DO NOT TOUCH THIS SOLANA CODE
# DO NOT REMOVE THIS SECTION
# PRESERVE EXACTLY AS-IS UNLESS I EXPLICITLY SAY SO
# MASTER BACKUP EXISTS IN solanascanner.py / GITHUB
# START SOLANA SECTION
# ==================================================

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

# =========================
# END SOLANA SECTION
# =========================


# =========================
# ETH SCANNER
# =========================
ETHERSCAN_CHAIN_ID = "1"


def safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def etherscan_get(url):
    try:
        res = requests.get(url, timeout=20)
        data = res.json()
        if str(data.get("status")) in {"1", "0"}:
            return data
        return {"status": "0", "message": "NOTOK", "result": []}
    except Exception:
        return {"status": "0", "message": "NOTOK", "result": []}


def get_eth_raw_transactions(wallet, max_pages=10):
    headers = {"X-API-Key": MORALIS_API_KEY}
    cursor = None
    all_results = []

    for _ in range(max_pages):
        url = f"https://deep-index.moralis.io/api/v2.2/{wallet}?chain={CHAIN}"
        if cursor:
            url += f"&cursor={cursor}"

        res = safe_json(url, headers)
        batch = res.get("result", []) if isinstance(res, dict) else []

        if not batch:
            break

        all_results.extend(batch)
        cursor = res.get("cursor")

        if not cursor:
            break

    return all_results


def get_eth_wallet_swaps(wallet, token_address, max_pages=10):
    headers = {"X-API-Key": MORALIS_API_KEY}
    cursor = None
    all_results = []

    for _ in range(max_pages):
        url = (
            f"https://deep-index.moralis.io/api/v2.2/wallets/{wallet}/swaps"
            f"?chain={CHAIN}&tokenAddress={token_address}"
        )
        if cursor:
            url += f"&cursor={cursor}"

        res = safe_json(url, headers)
        batch = res.get("result", []) if isinstance(res, dict) else []

        if not batch:
            break

        all_results.extend(batch)
        cursor = res.get("cursor")

        if not cursor:
            break

    return all_results


def get_etherscan_normal_txs(wallet, startblock=0, endblock=99999999, page_size=10000):
    if not ETHERSCAN_API_KEY:
        return []

    page = 1
    all_results = []

    while True:
        url = (
            "https://api.etherscan.io/v2/api"
            f"?chainid={ETHERSCAN_CHAIN_ID}"
            f"&module=account&action=txlist"
            f"&address={wallet}"
            f"&startblock={startblock}&endblock={endblock}"
            f"&page={page}&offset={page_size}&sort=asc"
            f"&apikey={ETHERSCAN_API_KEY}"
        )

        data = etherscan_get(url)
        batch = data.get("result", [])

        if not isinstance(batch, list) or not batch:
            break

        all_results.extend(batch)

        if len(batch) < page_size:
            break

        page += 1
        if page > 20:
            break

    return all_results


def get_etherscan_internal_by_hash(tx_hash):
    if not ETHERSCAN_API_KEY:
        return []

    url = (
        "https://api.etherscan.io/v2/api"
        f"?chainid={ETHERSCAN_CHAIN_ID}"
        f"&module=account&action=txlistinternal"
        f"&txhash={tx_hash}"
        f"&apikey={ETHERSCAN_API_KEY}"
    )

    data = etherscan_get(url)
    result = data.get("result", [])
    return result if isinstance(result, list) else []


def get_etherscan_tokentx(wallet, contract_address, startblock=0, endblock=99999999, page_size=10000):
    if not ETHERSCAN_API_KEY:
        return []

    page = 1
    all_results = []

    while True:
        url = (
            "https://api.etherscan.io/v2/api"
            f"?chainid={ETHERSCAN_CHAIN_ID}"
            f"&module=account&action=tokentx"
            f"&contractaddress={contract_address}"
            f"&address={wallet}"
            f"&startblock={startblock}&endblock={endblock}"
            f"&page={page}&offset={page_size}&sort=asc"
            f"&apikey={ETHERSCAN_API_KEY}"
        )

        data = etherscan_get(url)
        batch = data.get("result", [])

        if not isinstance(batch, list) or not batch:
            break

        all_results.extend(batch)

        if len(batch) < page_size:
            break

        page += 1
        if page > 20:
            break

    return all_results


def extract_unique_target_token_events(transfers, wallet):
    wallet_l = wallet.lower()
    events_by_hash = {}

    for tx in transfers:
        token = (tx.get("address") or "").lower()
        if token != ETH_TARGET_TOKEN.lower():
            continue

        tx_hash = (tx.get("transaction_hash") or "").lower()
        if not tx_hash:
            continue

        decimals = int(tx.get("decimals", 18))
        amount = int(tx.get("value", 0) or 0) / (10 ** decimals)

        from_addr = (tx.get("from_address") or "").lower()
        to_addr = (tx.get("to_address") or "").lower()

        if tx_hash not in events_by_hash:
            events_by_hash[tx_hash] = {
                "hash": tx_hash,
                "incoming_amount": 0.0,
                "outgoing_amount": 0.0,
            }

        if to_addr == wallet_l:
            events_by_hash[tx_hash]["incoming_amount"] += amount

        if from_addr == wallet_l:
            events_by_hash[tx_hash]["outgoing_amount"] += amount

    events = []
    for tx_hash, data in events_by_hash.items():
        incoming = data["incoming_amount"]
        outgoing = data["outgoing_amount"]

        if incoming > 0 and outgoing == 0:
            event_type = "incoming"
            amount = incoming
        elif outgoing > 0 and incoming == 0:
            event_type = "outgoing"
            amount = outgoing
        elif incoming > 0 and outgoing > 0:
            net = incoming - outgoing
            if net > 0:
                event_type = "incoming"
                amount = net
            elif net < 0:
                event_type = "outgoing"
                amount = abs(net)
            else:
                continue
        else:
            continue

        events.append({
            "type": event_type,
            "hash": tx_hash,
            "amount": amount,
        })

    return events


def get_weth_flows_by_hash(transfers, wallet):
    wallet_l = wallet.lower()
    weth_in_by_hash = {}
    weth_out_by_hash = {}

    for tx in transfers:
        token = (tx.get("address") or "").lower()
        if token != WETH_ADDRESS.lower():
            continue

        tx_hash = (tx.get("transaction_hash") or "").lower()
        if not tx_hash:
            continue

        decimals = int(tx.get("decimals", 18))
        amount = int(tx.get("value", 0) or 0) / (10 ** decimals)

        from_addr = (tx.get("from_address") or "").lower()
        to_addr = (tx.get("to_address") or "").lower()

        if from_addr == wallet_l:
            weth_out_by_hash[tx_hash] = weth_out_by_hash.get(tx_hash, 0.0) + amount
        if to_addr == wallet_l:
            weth_in_by_hash[tx_hash] = weth_in_by_hash.get(tx_hash, 0.0) + amount

    return weth_in_by_hash, weth_out_by_hash


def get_native_flow_summary(tx_obj, wallet):
    wallet_l = wallet.lower()

    native_out = 0.0
    native_in = 0.0

    try:
        value_wei = int(tx_obj.get("value", 0) or 0)
    except Exception:
        value_wei = 0

    from_addr = (tx_obj.get("from_address") or "").lower()
    to_addr = (tx_obj.get("to_address") or "").lower()

    if from_addr == wallet_l:
        native_out += value_wei / 1e18
    if to_addr == wallet_l:
        native_in += value_wei / 1e18

    for itx in tx_obj.get("internal_transactions", []) or []:
        try:
            ivalue = int(itx.get("value", 0) or 0) / 1e18
        except Exception:
            ivalue = 0.0

        if (itx.get("from") or "").lower() == wallet_l:
            native_out += ivalue
        if (itx.get("to") or "").lower() == wallet_l:
            native_in += ivalue

    return {
        "native_out": native_out,
        "native_in": native_in,
    }


def aggregate_sell_swaps_by_hash(swaps):
    sell_hashes = set()

    for swap in swaps:
        tx_hash = (swap.get("transactionHash") or "").lower()
        if not tx_hash:
            continue

        tx_type = (swap.get("transactionType") or "").lower()
        if tx_type != "sell":
            continue

        sold = swap.get("sold") or {}
        sold_address = (sold.get("address") or "").lower()
        if sold_address != ETH_TARGET_TOKEN.lower():
            continue

        sell_hashes.add(tx_hash)

    return sell_hashes

def get_eth_token_logo(token_address):
    try:
        url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
        res = safe_json(url)
        pairs = res.get("pairs", [])
        if not pairs:
            return None

        pair = pairs[0]
        logo_url = pair.get("info", {}).get("imageUrl")
        if not logo_url:
            return None

        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        logo_path = os.path.join(BASE_DIR, "temp_logo.png")

        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(logo_url, headers=headers, timeout=10)
        if response.status_code == 200 and response.content:
            img = Image.open(BytesIO(response.content)).convert("RGBA")
            img.save(logo_path, format="PNG")
            return logo_path

    except Exception:
        pass

    return None

def build_weth_receipts_by_hash_from_etherscan(wallet):
    weth_txs = get_etherscan_tokentx(wallet, WETH_ADDRESS)
    receipts = {}

    for tx in weth_txs:
        tx_hash = (tx.get("hash") or "").lower()
        if not tx_hash:
            continue

        to_addr = (tx.get("to") or "").lower()
        if to_addr != wallet.lower():
            continue

        try:
            decimals = int(tx.get("tokenDecimal", 18) or 18)
            value = int(tx.get("value", 0) or 0) / (10 ** decimals)
        except Exception:
            value = 0.0

        receipts[tx_hash] = receipts.get(tx_hash, 0.0) + value

    return receipts


def get_actual_eth_recovery_for_sell_hash(wallet, sell_hash, weth_receipts_by_hash):
    recovered_native = 0.0
    recovered_weth = 0.0

    internal_txs = get_etherscan_internal_by_hash(sell_hash)
    for itx in internal_txs:
        to_addr = (itx.get("to") or "").lower()
        is_error = str(itx.get("isError", "0"))
        if to_addr == wallet.lower() and is_error == "0":
            try:
                recovered_native += int(itx.get("value", 0) or 0) / 1e18
            except Exception:
                pass

    recovered_weth += weth_receipts_by_hash.get(sell_hash, 0.0)

    return {
        "native_eth": recovered_native,
        "weth": recovered_weth,
        "total": recovered_native + recovered_weth,
    }

def get_best_eth_timestamp(normal_tx=None, raw_tx=None):
    if normal_tx:
        try:
            ts = int(normal_tx.get("timeStamp", 0) or 0)
            if ts > 0:
                return ts
        except Exception:
            pass

    if raw_tx:
        raw_ts = raw_tx.get("block_timestamp") or raw_tx.get("blockTimestamp")
        if raw_ts:
            try:
                from datetime import datetime
                return int(datetime.fromisoformat(raw_ts.replace("Z", "+00:00")).timestamp())
            except Exception:
                pass

    return 0

ETH_PRICE_CACHE_FILE = "eth_price_cache.json"


def load_eth_price_cache_from_disk():
    if os.path.exists(ETH_PRICE_CACHE_FILE):
        try:
            with open(ETH_PRICE_CACHE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_eth_price_cache_to_disk(cache):
    try:
        with open(ETH_PRICE_CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=2)
    except Exception as e:
        print(f"Failed to save ETH price cache: {e}")
      
def preload_eth_usd_prices(date_keys, price_cache):
    valid_keys = [d for d in date_keys if d]
    if not valid_keys:
        return

    # Load from disk cache first
    disk_cache = load_eth_price_cache_from_disk()
    price_cache.update(disk_cache)

    # Only fetch dates not already cached
    missing_keys = [dk for dk in valid_keys if dk not in price_cache]
    if not missing_keys:
        return

    def date_key_to_ts(dk):
        return int(time.mktime(time.strptime(dk, "%d-%m-%Y")))

    timestamps = [date_key_to_ts(dk) for dk in missing_keys]
    ts_end = max(timestamps) + 86400
    ts_start = min(timestamps) - 86400
    days_needed = int((ts_end - ts_start) / 86400) + 2

    url = (
        "https://min-api.cryptocompare.com/data/v2/histoday"
        f"?fsym=ETH&tsym=USD&limit={days_needed}&toTs={ts_end}"
    )

    headers = {"User-Agent": "Mozilla/5.0"}

    for attempt in range(3):
        try:
            res = requests.get(url, headers=headers, timeout=20)
            data = res.json()

            if data.get("Response") != "Success":
                break

            price_points = data.get("Data", {}).get("Data", [])
            if not price_points:
                break

            range_prices = {}
            for point in price_points:
                dk = time.strftime("%d-%m-%Y", time.gmtime(point["time"]))
                range_prices[dk] = point["close"]

            for dk in missing_keys:
                price_cache[dk] = range_prices.get(dk, 0.0)

            # Save new prices to disk
            disk_cache.update({dk: price_cache[dk] for dk in missing_keys})
            save_eth_price_cache_to_disk(disk_cache)

            return

        except Exception as e:
            wait = 5 + attempt * 5
            time.sleep(wait)

    # All attempts failed
    for dk in missing_keys:
        price_cache[dk] = 0.0

def get_eth_date_key_from_timestamp(timestamp):
    if not timestamp:
        return None
    return time.strftime("%d-%m-%Y", time.gmtime(int(timestamp)))


def get_eth_usd_price_for_timestamp(timestamp, price_cache):
    date_key = get_eth_date_key_from_timestamp(timestamp)
    if not date_key:
        return 0.0
    return price_cache.get(date_key, 0.0)

def ethereum_scan(wallet):
    if not MORALIS_API_KEY:
        raise ValueError("MORALIS_API_KEY not found in .env")
    if not ETHERSCAN_API_KEY:
        raise ValueError("ETHERSCAN_API_KEY not found in .env")

    print("Scanning ETH wallet:", wallet)

    headers = {"X-API-Key": MORALIS_API_KEY}

    transfers_url = f"https://deep-index.moralis.io/api/v2/{wallet}/erc20/transfers?chain={CHAIN}"
    transfer_res = safe_json(transfers_url, headers)
    transfers = transfer_res.get("result", []) if isinstance(transfer_res, dict) else []

    raw_txs = get_eth_raw_transactions(wallet)
    swaps = get_eth_wallet_swaps(wallet, ETH_TARGET_TOKEN)
    normal_txs = get_etherscan_normal_txs(wallet)

    raw_by_hash = {}
    for tx in raw_txs:
        tx_hash = (tx.get("hash") or "").lower()
        if tx_hash and tx_hash not in raw_by_hash:
            raw_by_hash[tx_hash] = tx

    normal_by_hash = {}
    for tx in normal_txs:
        tx_hash = (tx.get("hash") or "").lower()
        if tx_hash and tx_hash not in normal_by_hash:
            normal_by_hash[tx_hash] = tx

    token_events = extract_unique_target_token_events(transfers, wallet)
    weth_in_by_hash, weth_out_by_hash = get_weth_flows_by_hash(transfers, wallet)
    sell_swap_hashes = aggregate_sell_swaps_by_hash(swaps)
    weth_receipts_by_hash = build_weth_receipts_by_hash_from_etherscan(wallet)

    buy_count = 0
    sell_count = 0
    transfer_out_count = 0
    received_transfer_count = 0

    total_bought = 0.0
    total_sold = 0.0
    total_transferred_out = 0.0
    total_received_transfer_in = 0.0

    native_spent_on_buys = 0.0
    weth_spent_on_buys = 0.0
    eth_recovered_on_sells = 0.0
    total_gas_fees = 0.0

    total_usd_spent = 0.0
    total_usd_recovered = 0.0
    price_cache = {}

    relevant_hashes = set()

    # Preload exact-date ETH/USD prices once per unique date
    needed_date_keys = set()

    for tx_hash, tx_obj in raw_by_hash.items():
        normal_tx = normal_by_hash.get(tx_hash)
        timestamp = get_best_eth_timestamp(normal_tx, tx_obj)
        date_key = get_eth_date_key_from_timestamp(timestamp)
        if date_key:
            needed_date_keys.add(date_key)

    preload_eth_usd_prices(needed_date_keys, price_cache)

    # Incoming actions: classify as buy or received transfer
    for event in token_events:
        if event["type"] != "incoming":
            continue

        tx_hash = event["hash"]
        relevant_hashes.add(tx_hash)

        tx_obj = raw_by_hash.get(tx_hash)
        normal_tx = normal_by_hash.get(tx_hash)

        weth_spent = weth_out_by_hash.get(tx_hash, 0.0)
        native_spent = 0.0
        timestamp = 0

        if tx_obj:
            flow = get_native_flow_summary(tx_obj, wallet)
            native_spent = max(flow["native_out"] - flow["native_in"], 0.0)

        timestamp = get_best_eth_timestamp(normal_tx, tx_obj)
        total_in_cost = weth_spent + native_spent

        if total_in_cost > 0:
            buy_count += 1
            total_bought += event["amount"]
            weth_spent_on_buys += weth_spent
            native_spent_on_buys += native_spent

            eth_usd = get_eth_usd_price_for_timestamp(timestamp, price_cache) if timestamp else 0.0
            total_usd_spent += total_in_cost * eth_usd
        else:
            received_transfer_count += 1
            total_received_transfer_in += event["amount"]

    # Outgoing actions: classify as sell or transfer out
    for event in token_events:
        if event["type"] != "outgoing":
            continue

        out_hash = event["hash"]
        relevant_hashes.add(out_hash)

        tx_obj = raw_by_hash.get(out_hash)
        normal_tx = normal_by_hash.get(out_hash)
        timestamp = get_best_eth_timestamp(normal_tx, tx_obj)

        if out_hash in sell_swap_hashes:
            sell_count += 1
            total_sold += event["amount"]

            recovery = get_actual_eth_recovery_for_sell_hash(wallet, out_hash, weth_receipts_by_hash)
            eth_recovered_on_sells += recovery["total"]

            eth_usd = get_eth_usd_price_for_timestamp(timestamp, price_cache) if timestamp else 0.0
            total_usd_recovered += recovery["total"] * eth_usd

        else:
            transfer_out_count += 1
            total_transferred_out += event["amount"]

    # Gas fees only for real buys and sells/transfers initiated by wallet
    for tx_hash in relevant_hashes:
        tx = normal_by_hash.get(tx_hash)
        if not tx:
            continue

        from_addr = (tx.get("from") or "").lower()
        if from_addr != wallet.lower():
            continue

        try:
            gas_used = int(tx.get("gasUsed", 0) or 0)
            gas_price = int(tx.get("gasPrice", 0) or 0)
            fee_eth = (gas_used * gas_price) / 1e18
            total_gas_fees += fee_eth

            raw_tx = raw_by_hash.get(tx_hash)
            timestamp = get_best_eth_timestamp(tx, raw_tx)
            eth_usd = get_eth_usd_price_for_timestamp(timestamp, price_cache) if timestamp else 0.0
            total_usd_spent += fee_eth * eth_usd
        except Exception:
            pass

    # Position includes bought tokens, received transfers, sells, and transfers out
    net_position = total_bought + total_received_transfer_in - total_sold - total_transferred_out

    total_eth_spent = native_spent_on_buys + weth_spent_on_buys + total_gas_fees
    total_eth_recovered = eth_recovered_on_sells

    average_cost_per_token = (
        total_eth_spent / total_bought
        if total_bought > 0 else 0.0
    )

    remaining_cost_basis_eth = net_position * average_cost_per_token
    break_even_remaining_usd = total_usd_spent - total_usd_recovered

    try:
        url = f"https://api.dexscreener.com/latest/dex/tokens/{ETH_TARGET_TOKEN}"
        res = safe_json(url)
        pairs = res.get("pairs", [])
        pair = pairs[0] if pairs else {}

        token_price_usd = float(pair.get("priceUsd", 0) or 0)
        token_name = pair.get("baseToken", {}).get("name", "Unknown Token")
        token_symbol = pair.get("baseToken", {}).get("symbol", "UNKNOWN")
        logo_url = pair.get("info", {}).get("imageUrl")
    except Exception:
        token_price_usd = 0.0
        token_name = "Unknown Token"
        token_symbol = "UNKNOWN"
        logo_url = None

    eth_logo_path = get_eth_token_logo(ETH_TARGET_TOKEN) if logo_url else None

    current_value_usd = net_position * token_price_usd
    current_profit_usd = current_value_usd - break_even_remaining_usd
    roi_multiple_usd = (current_profit_usd / break_even_remaining_usd) if break_even_remaining_usd > 0 else 0

    print("\n" + "=" * 50)
    print("ETH WALLET SUMMARY")
    print("=" * 50)

    print(f"Wallet: {wallet}")
    print(f"Token: {token_name} (${token_symbol})")

    print("\n--- ACTIVITY ---")
    print(
        f"{buy_count} Buys | {sell_count} Sells | "
        f"{transfer_out_count} Transfers Out | {received_transfer_count} Received Transfers"
    )

    print("\n--- POSITION ---")
    print(f"Net Position: {round(net_position, 2)} tokens")

    print("\n--- CAPITAL (USD) ---")
    print(f"Total USD Spent: ${total_usd_spent:.2f}")
    print(f"Total USD Recovered: ${total_usd_recovered:.2f}")
    print(f"Break-Even Remaining: ${break_even_remaining_usd:.2f}")
    print(f"Current Value: ${current_value_usd:.2f}")

    print("\n--- PERFORMANCE (USD) ---")
    print(f"Profit If Sold Now: ${current_profit_usd:.2f}")
    print(f"Return vs Break-Even Remaining: {round(roi_multiple_usd, 2)}x")

    print(f"\nToken Price: ${round(token_price_usd, 6)}")

    create_eth_card(
        token_name=token_name,
        wallet=wallet,
        tokens=round(net_position, 2),
        cost_usd=round(total_usd_spent, 2),
        value_usd=round(current_value_usd, 2),
        profit_usd=round(current_profit_usd, 2),
        roi=round(roi_multiple_usd, 2),
        logo_path=eth_logo_path,
        token_symbol=token_symbol,
        buy_count=buy_count,
        sell_count=sell_count,
    )

    return {
        "token_name": token_name,
        "token_symbol": token_symbol,
        "net_position": round(net_position, 2),
        "buys": buy_count,
        "sells": sell_count,
        "transfers_out": transfer_out_count,
        "received_transfers": received_transfer_count,
        "total_usd_spent": round(total_usd_spent, 2),
        "total_usd_recovered": round(total_usd_recovered, 2),
        "break_even_remaining_usd": round(break_even_remaining_usd, 2),
        "value_usd": round(current_value_usd, 2),
        "current_profit_usd": round(current_profit_usd, 2),
        "roi_multiple_usd": round(roi_multiple_usd, 2),
        "token_price_usd": round(token_price_usd, 6),

        # kept in return for internal use / future debugging
        "total_eth_spent": round(total_eth_spent, 12),
        "total_eth_recovered": round(total_eth_recovered, 12),
        "gas_fees_eth": round(total_gas_fees, 12),
        "remaining_cost_basis_eth": round(remaining_cost_basis_eth, 12),
    }

# =========================
# MAIN ROUTER
# =========================
def scan_wallet(wallet, chain="sol"):
    if chain == "sol":
        return solana_scan(wallet)
    elif chain == "eth":
        return ethereum_scan(wallet)
    else:
        raise ValueError("chain must be 'sol' or 'eth'")


if __name__ == "__main__":
    wallet = input("Enter wallet address: ").strip()
    if wallet.startswith("0x"):
        scan_wallet(wallet, chain="eth")
    else:
        scan_wallet(wallet, chain="sol")
    input("Press Enter to exit...")
