import sqlite3

from src.core.settings import DB_PATH


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()


def get_db_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)
