import sqlite3
from config import DB_PATH

def initialize_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_name TEXT NOT NULL,
            name TEXT UNIQUE NOT NULL,
            handle TEXT,
            channel_id TEXT,
            url TEXT,
            title TEXT,
            follower_count INTEGER,
            description TEXT,
            tags TEXT,
            thumbnails TEXT,
            creation_date TEXT,
            country TEXT,
            view_count INTEGER,
            links TEXT,
            is_lost_media INTEGER DEFAULT 2,
            last_fetch_date TEXT DEFAULT NULL,
            FOREIGN KEY(group_name) REFERENCES groups(name) ON DELETE CASCADE
        )
    """)

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
            is_metadata_downloaded INTEGER DEFAULT 0,
            video_type TEXT,
            upload_date TEXT,
            duration INTEGER,
            description TEXT,
            tags TEXT,
            like_count INTEGER,
            comment_count INTEGER,
            filepath TEXT,
            thumb_filepath TEXT,
            is_lost_media INTEGER DEFAULT NULL,
            last_metadata_fetch_date TEXT DEFAULT NULL,
            FOREIGN KEY(channel_name) REFERENCES channels(name) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS playlists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_name TEXT NOT NULL,
            playlist_id TEXT UNIQUE NOT NULL,
            title TEXT,
            url TEXT,
            last_updated TEXT,
            FOREIGN KEY(channel_name) REFERENCES channels(name) ON DELETE CASCADE
        )
    """)

    # --- NEW: INSTAGRAM TABLES (Strictly Separate) ---
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS ig_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                full_name TEXT,
                user_id TEXT,
                biography TEXT,
                followers INTEGER,
                following INTEGER,
                profile_pic_path TEXT,
                is_private INTEGER,
                last_sync_date TEXT
            )
        """)

    cursor.execute("""
            CREATE TABLE IF NOT EXISTS ig_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                shortcode TEXT UNIQUE NOT NULL,
                type TEXT,
                text TEXT,
                timestamp TEXT,
                likes INTEGER,
                comments INTEGER,
                is_downloaded INTEGER DEFAULT 0,
                FOREIGN KEY(account_id) REFERENCES ig_accounts(id) ON DELETE CASCADE
            )
        """)

    conn.commit()
    conn.close()