import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "database.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        full_name TEXT NOT NULL,
        account_number TEXT NOT NULL,
        balance REAL NOT NULL
    )
    """)
    
    # 2. Transactions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tx_id TEXT UNIQUE NOT NULL,
        timestamp TEXT NOT NULL,
        tx_type TEXT NOT NULL,
        recipient TEXT NOT NULL,
        account_dest TEXT NOT NULL,
        amount REAL NOT NULL,
        processing_time_ms REAL NOT NULL,
        network_status TEXT NOT NULL,
        status TEXT NOT NULL
    )
    """)
    
    # 3. Network Event Logs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS network_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        incoming_rate REAL,
        processing_rate REAL,
        queue_length INTEGER,
        congestion_level TEXT,
        event_text TEXT
    )
    """)
    
    # Seed default user if empty
    cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'student'")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO users (username, password, full_name, account_number, balance)
        VALUES ('student', '1234', 'Alex Student', 'XXXX XXXX 4821', 85450.00)
        """)
        
    # Seed fake transactions if table is empty
    cursor.execute("SELECT COUNT(*) FROM transactions")
    if cursor.fetchone()[0] == 0:
        seed_txs = [
            ("TXN-7192", "2026-09-28 14:22", "Transfer", "Dr. Rajesh Sharma", "HDFC0001248", 12500.00, 48.5, "NORMAL", "Completed"),
            ("TXN-6581", "2026-09-28 18:05", "Transfer", "Campus Bookstore", "SBI0004921", 2340.00, 142.0, "MODERATE", "Completed"),
            ("TXN-5902", "2026-09-29 01:12", "Salary Credit", "College Research Fellowship", "SELF-CREDIT", 45000.00, 38.0, "NORMAL", "Completed"),
            ("TXN-4811", "2026-09-29 03:45", "Transfer", "Priya Verma", "ICIC0009812", 4500.00, 420.0, "CONGESTED", "Delayed"),
            ("TXN-3914", "2026-09-29 05:10", "Utility Bill", "Campus Electricity Board", "UTIL-98124", 1850.00, 52.0, "NORMAL", "Completed"),
            ("TXN-2804", "2026-09-29 05:40", "Transfer", "Aditya Sen", "AXIS0003184", 8000.00, 610.0, "CONGESTED", "Completed")
        ]
        cursor.executemany("""
        INSERT INTO transactions (tx_id, timestamp, tx_type, recipient, account_dest, amount, processing_time_ms, network_status, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, seed_txs)
        
    conn.commit()
    conn.close()

def get_user_profile(username='student'):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return dict(user) if user else None

def get_recent_transactions(limit=15):
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM transactions ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def insert_transaction(tx_id, tx_type, recipient, account_dest, amount, processing_time_ms, network_status, status):
    conn = get_db_connection()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("""
    INSERT INTO transactions (tx_id, timestamp, tx_type, recipient, account_dest, amount, processing_time_ms, network_status, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (tx_id, timestamp, tx_type, recipient, account_dest, amount, processing_time_ms, network_status, status))
    
    # Update simulated user balance if completed or delayed
    if status in ("Completed", "Delayed", "Queued"):
        conn.execute("UPDATE users SET balance = balance - ? WHERE username = 'student'", (amount,))
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
