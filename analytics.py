import sqlite3
import time

DB_PATH = "analytics.db"

TREND_WINDOW = 7200  # 2 hours


# =========================
# INIT DATABASE
# =========================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS stats (
            key TEXT PRIMARY KEY,
            value INTEGER
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS wallets (
            wallet TEXT,
            timestamp INTEGER
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY
        )
    """)

    conn.commit()
    conn.close()


# =========================
# TRACK EVENT
# =========================
def track_event(command, user_id, wallet):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    now = int(time.time())

    # Track user
    c.execute(
        "INSERT OR IGNORE INTO users (user_id) VALUES (?)",
        (str(user_id),)
    )

    # Track stats
    if command == "scan":
        c.execute("""
            INSERT INTO stats (key, value)
            VALUES ('total_scans', 1)
            ON CONFLICT(key) DO UPDATE SET value = value + 1
        """)
    elif command == "share":
        c.execute("""
            INSERT INTO stats (key, value)
            VALUES ('total_shares', 1)
            ON CONFLICT(key) DO UPDATE SET value = value + 1
        """)

    # Track wallet with timestamp
    c.execute(
        "INSERT INTO wallets (wallet, timestamp) VALUES (?, ?)",
        (wallet, now)
    )

    conn.commit()
    conn.close()


# =========================
# GET STATS
# =========================
def get_stats():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM users")
    users = c.fetchone()[0]

    c.execute("SELECT COUNT(DISTINCT wallet) FROM wallets")
    wallets = c.fetchone()[0]

    c.execute("SELECT value FROM stats WHERE key = 'total_scans'")
    scans = c.fetchone()
    scans = scans[0] if scans else 0

    c.execute("SELECT value FROM stats WHERE key = 'total_shares'")
    shares = c.fetchone()
    shares = shares[0] if shares else 0

    conn.close()

    return {
        "unique_users": users,
        "total_scans": scans,
        "total_shares": shares,
        "wallets_scanned": wallets,
    }


# =========================
# LIVE TRENDING
# =========================
def get_top_wallets(limit=5):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    now = int(time.time())
    cutoff = now - TREND_WINDOW

    c.execute("""
        SELECT wallet, COUNT(*) as cnt
        FROM wallets
        WHERE timestamp >= ?
        GROUP BY wallet
        ORDER BY cnt DESC
        LIMIT ?
    """, (cutoff, limit))

    rows = c.fetchall()
    conn.close()

    return rows


# =========================
# INIT
# =========================
init_db()
