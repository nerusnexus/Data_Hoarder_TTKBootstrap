import sqlite3
from services.db.db_manager import DatabaseManager

class AddGroupService:
    @staticmethod
    def add_group(name: str):
        if not name:
            raise ValueError("Group name cannot be empty")

        # Using 'with' automatically handles commit() and close()
        with DatabaseManager.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO groups (name) VALUES (?)", (name,))
            except sqlite3.IntegrityError:
                raise ValueError(f"The group '{name}' already exists in your database.")

        return name

    @staticmethod
    def get_all_groups():
        with DatabaseManager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM groups")
            groups = cursor.fetchall()
            return [g[0] for g in groups]

    @staticmethod
    def delete_group(name: str):
        with DatabaseManager.get_connection() as conn:
            cursor = conn.cursor()
            # Deleting a group also triggers cascades if foreign keys are ON
            cursor.execute("DELETE FROM groups WHERE name = ?", (name,))
            cursor.execute("DELETE FROM channels WHERE group_name = ?", (name,))