import sqlite3

DB_PATH = "analytics.db"


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
            wallet TEXT PRIMARY KEY,
            count INTEGER
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
# TRACK EVENT (FIXED)
# =========================
def track_event(command, user_id, wallet):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Track user
    c.execute(
        "INSERT OR IGNORE INTO users (user_id) VALUES (?)",
        (str(user_id),)
    )

    # Track scans / shares (NO nested calls)
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

    # Track wallet
    c.execute("SELECT count FROM wallets WHERE wallet = ?", (wallet,))
    row = c.fetchone()

    if row:
        c.execute(
            "UPDATE wallets SET count = count + 1 WHERE wallet = ?",
            (wallet,)
        )
    else:
        c.execute(
            "INSERT INTO wallets (wallet, count) VALUES (?, 1)",
            (wallet,)
        )

    conn.commit()
    conn.close()


# =========================
# GET STAT
# =========================
def get_stat(key):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT value FROM stats WHERE key = ?", (key,))
    row = c.fetchone()

    conn.close()
    return row[0] if row else 0


# =========================
# GET STATS
# =========================
def get_stats():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM users")
    users = c.fetchone()[0]

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
# INIT
# =========================
init_db()
