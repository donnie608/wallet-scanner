import sqlite3
import os

DB_PATH = "analytics.db"


# =========================
# INIT DATABASE
# =========================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Stats table
    c.execute("""
        CREATE TABLE IF NOT EXISTS stats (
            key TEXT PRIMARY KEY,
            value INTEGER
        )
    """)

    # Wallet counts
    c.execute("""
        CREATE TABLE IF NOT EXISTS wallets (
            wallet TEXT PRIMARY KEY,
            count INTEGER
        )
    """)

    # Users
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY
        )
    """)

    conn.commit()
    conn.close()


# =========================
# HELPER: GET STAT
# =========================
def get_stat(key):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT value FROM stats WHERE key = ?", (key,))
    row = c.fetchone()

    conn.close()

    return row[0] if row else 0


# =========================
# HELPER: INCREMENT STAT
# =========================
def increment_stat(key):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT value FROM stats WHERE key = ?", (key,))
    row = c.fetchone()

    if row:
        c.execute("UPDATE stats SET value = value + 1 WHERE key = ?", (key,))
    else:
        c.execute("INSERT INTO stats (key, value) VALUES (?, 1)", (key,))

    conn.commit()
    conn.close()


# =========================
# TRACK EVENT
# =========================
def track_event(command, user_id, wallet):

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Track user
    c.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (str(user_id),))

    # Track scans / shares
    if command == "scan":
        increment_stat("total_scans")
    elif command == "share":
        increment_stat("total_shares")

    # Track wallet
    c.execute("SELECT count FROM wallets WHERE wallet = ?", (wallet,))
    row = c.fetchone()

    if row:
        c.execute("UPDATE wallets SET count = count + 1 WHERE wallet = ?", (wallet,))
    else:
        c.execute("INSERT INTO wallets (wallet, count) VALUES (?, 1)", (wallet,))

    conn.commit()
    conn.close()


# =========================
# GET STATS
# =========================
def get_stats():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Unique users
    c.execute("SELECT COUNT(*) FROM users")
    users = c.fetchone()[0]

    # Wallets scanned
    c.execute("SELECT COUNT(*) FROM wallets")
    wallets = c.fetchone()[0]

    conn.close()

    return {
        "unique_users": users,
        "total_scans": get_stat("total_scans"),
        "total_shares": get_stat("total_shares"),
        "wallets_scanned": wallets,
    }


# =========================
# TOP WALLETS
# =========================
def get_top_wallets(limit=5):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        SELECT wallet, count
        FROM wallets
        ORDER BY count DESC
        LIMIT ?
    """, (limit,))

    rows = c.fetchall()
    conn.close()

    return rows


# =========================
# INIT ON IMPORT
# =========================
init_db()
