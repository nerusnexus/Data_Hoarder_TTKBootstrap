import sqlite3
from pathlib import Path


def initialize_database(db_path: Path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create the groups table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """)

    # Create a unified channels table that supports both manual additions and yt-dlp metadata
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_name TEXT NOT NULL,
            name TEXT NOT NULL,
            handle TEXT,
            url TEXT,
            title TEXT,
            uploader_id TEXT,
            UNIQUE(group_name, name),
            FOREIGN KEY(group_name) REFERENCES groups(name) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()