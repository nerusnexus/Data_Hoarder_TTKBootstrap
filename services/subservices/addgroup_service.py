import sqlite3
from services.db.db_manager import DatabaseManager

class AddGroupService:
    @staticmethod
    def add_group(name: str):
        if not name:
            raise ValueError("Group name cannot be empty")

        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("INSERT INTO groups (name) VALUES (?)", (name,))
        except sqlite3.IntegrityError:
            conn.close()
            raise ValueError(f"The group '{name}' already exists in your database.")

        conn.commit()
        conn.close()

        return name

    @staticmethod
    def get_all_groups():
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM groups")
        groups = cursor.fetchall()

        conn.close()
        return [g[0] for g in groups]

    @staticmethod
    def delete_group(name: str):
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM groups WHERE name = ?", (name,))
        cursor.execute("DELETE FROM channels WHERE group_name = ?", (name,))

        conn.commit()
        conn.close()