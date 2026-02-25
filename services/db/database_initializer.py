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

    # Expanded channels table for the "pseudo-library" index
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_name TEXT NOT NULL,
            name TEXT NOT NULL,
            handle TEXT,
            channel_id TEXT,
            url TEXT,
            title TEXT,
            follower_count INTEGER,
            description TEXT,
            tags TEXT,
            thumbnails TEXT,
            UNIQUE(group_name, name),
            FOREIGN KEY(group_name) REFERENCES groups(name) ON DELETE CASCADE
        )
    """)

    # Video metadata table (UPDATED to include video_type and upload_date)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_name TEXT NOT NULL,
            video_id TEXT NOT NULL,
            title TEXT,
            url TEXT,
            view_count INTEGER,
            thumbnails TEXT,
            is_downloaded INTEGER DEFAULT 0,
            video_type TEXT,
            upload_date TEXT,
            FOREIGN KEY(channel_name) REFERENCES channels(name) ON DELETE CASCADE
        )
    """)

    # --- MIGRATION: Safely update existing databases ---
    cursor.execute("PRAGMA table_info(videos)")
    columns = [info[1] for info in cursor.fetchall()]

    if "video_type" not in columns:
        print("Migrating DB: Adding 'video_type' column...")
        cursor.execute("ALTER TABLE videos ADD COLUMN video_type TEXT")

    if "upload_date" not in columns:
        print("Migrating DB: Adding 'upload_date' column...")
        cursor.execute("ALTER TABLE videos ADD COLUMN upload_date TEXT")
    # ---------------------------------------------------

    conn.commit()
    conn.close()