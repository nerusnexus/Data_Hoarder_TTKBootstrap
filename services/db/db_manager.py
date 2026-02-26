import sqlite3
from config import DB_PATH

class DatabaseManager:
    @staticmethod
    def get_connection():
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        # Enable foreign keys automatically for every connection
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn