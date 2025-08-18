import sqlite3

class DatabaseHandler:
    def __init__(self, db_name="example.db"):
        self.db_name = db_name
        self._create_table()

    def _connect(self):
        return sqlite3.connect(self.db_name)

    def _create_table(self):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER
        )
        """)
        conn.commit()
        conn.close()

    def insert_user(self, name, age):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (name, age) VALUES (?, ?)", (name, age))
        conn.commit()
        conn.close()

    def get_users(self):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, age FROM users")
        rows = cursor.fetchall()
        conn.close()
        return rows

    def update_user(self, user_id, name, age):
        """Update a user's name and age by id. Returns number of rows updated."""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET name = ?, age = ? WHERE id = ?", (name, age, user_id))
        conn.commit()
        rows = cursor.rowcount
        conn.close()
        return rows

    def delete_user(self, user_id):
        """Delete a user by id. Returns number of rows deleted."""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        rows = cursor.rowcount
        conn.close()
        return rows
