import sqlite3
from pathlib import Path


class AddGroupService:
    def __init__(self, db_path: Path):
        self.db_path = db_path

    def add_group(self, name: str):
        if not name:
            raise ValueError("Group name cannot be empty")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("INSERT INTO groups (name) VALUES (?)", (name,))
        except sqlite3.IntegrityError:
            conn.close()
            raise Exception("Group already exists")

        conn.commit()
        conn.close()

        return name

    def get_all_groups(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM groups")
        groups = cursor.fetchall()

        conn.close()
        return [g[0] for g in groups]

    def delete_group(self, name: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM groups WHERE name = ?", (name,))
        cursor.execute("DELETE FROM channels WHERE group_name = ?", (name,))

        conn.commit()
        conn.close()