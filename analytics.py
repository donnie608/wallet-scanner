import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ANALYTICS_FILE = os.path.join(BASE_DIR, "analytics.json")


def default_data():
    return {
        "total_scans": 0,
        "total_shares": 0,
        "unique_users": [],
        "wallets_scanned": [],
        "wallet_counts": {}  # 🔥 NEW
    }


def load_analytics():
    if not os.path.exists(ANALYTICS_FILE):
        return default_data()

    try:
        with open(ANALYTICS_FILE, "r") as f:
            data = json.load(f)

        # 🔧 Ensure new field exists (safe upgrade)
        if "wallet_counts" not in data:
            data["wallet_counts"] = {}

        return data

    except:
        return default_data()


def save_analytics(data):
    with open(ANALYTICS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def track_event(command, user_id, wallet):
    data = load_analytics()

    # Count commands
    if command == "scan":
        data["total_scans"] += 1
    elif command == "share":
        data["total_shares"] += 1

    # Unique users
    if user_id not in data["unique_users"]:
        data["unique_users"].append(user_id)

    # Unique wallets
    if wallet not in data["wallets_scanned"]:
        data["wallets_scanned"].append(wallet)

    # 🔥 Wallet frequency tracking
    if wallet not in data["wallet_counts"]:
        data["wallet_counts"][wallet] = 0

    data["wallet_counts"][wallet] += 1

    save_analytics(data)


def get_stats():
    data = load_analytics()

    return {
        "total_scans": data["total_scans"],
        "total_shares": data["total_shares"],
        "unique_users": len(data["unique_users"]),
        "wallets_scanned": len(data["wallets_scanned"])
    }


def get_top_wallets(limit=5):
    data = load_analytics()
    wallet_counts = data.get("wallet_counts", {})

    # Sort by usage
    sorted_wallets = sorted(wallet_counts.items(), key=lambda x: x[1], reverse=True)

    return sorted_wallets[:limit]
