import sqlite3
from pathlib import Path


def init_db(db_path: Path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS groups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS channels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id INTEGER NOT NULL,
        handle TEXT NOT NULL,
        url TEXT NOT NULL,
        title TEXT,
        uploader_id TEXT,
        FOREIGN KEY(group_id) REFERENCES groups(id)
    )
    """)

    conn.commit()
    conn.close()
