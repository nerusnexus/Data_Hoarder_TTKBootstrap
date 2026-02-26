import sqlite3
from config import DB_PATH

def initialize_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create the groups table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """)

    # Expanded channels table
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

    # Video metadata table (now includes duration, description, tags, etc.)
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
            duration INTEGER,
            description TEXT,
            tags TEXT,
            like_count INTEGER,
            comment_count INTEGER,
            filepath TEXT,
            FOREIGN KEY(channel_name) REFERENCES channels(name) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()