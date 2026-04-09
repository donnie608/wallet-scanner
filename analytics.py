import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ANALYTICS_FILE = os.path.join(BASE_DIR, "analytics.json")


def load_analytics():
    if not os.path.exists(ANALYTICS_FILE):
        return {
            "total_scans": 0,
            "total_shares": 0,
            "unique_users": [],
            "wallets_scanned": []
        }

    try:
        with open(ANALYTICS_FILE, "r") as f:
            return json.load(f)
    except:
        return {
            "total_scans": 0,
            "total_shares": 0,
            "unique_users": [],
            "wallets_scanned": []
        }


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

    # Track unique users
    if user_id not in data["unique_users"]:
        data["unique_users"].append(user_id)

    # Track wallets
    if wallet not in data["wallets_scanned"]:
        data["wallets_scanned"].append(wallet)

    save_analytics(data)


def get_stats():
    data = load_analytics()

    return {
        "total_scans": data["total_scans"],
        "total_shares": data["total_shares"],
        "unique_users": len(data["unique_users"]),
        "wallets_scanned": len(data["wallets_scanned"])
    }
