import sqlite3

class DatabaseHandler:
    def __init__(self, db_name="example.db"):
        self.db_name = db_name
        self._create_table()
        # ensure blink tables exist
        self._create_blink_tables()

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

    def _create_blink_tables(self):
        """Create tables for blink events and aggregates."""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS blink_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_id TEXT,
            event_ts TEXT NOT NULL,
            event_epoch_ms INTEGER NOT NULL,
            duration_ms INTEGER,
            event_type TEXT,
            ear REAL,
            source TEXT,
            metadata TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS blink_aggregates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            day TEXT NOT NULL,
            blink_count INTEGER NOT NULL DEFAULT 0,
            avg_duration_ms REAL,
            median_ear REAL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(user_id, day),
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_blink_user_ts ON blink_events(user_id, event_epoch_ms)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_blink_event_ts ON blink_events(event_epoch_ms)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_aggregates_user_day ON blink_aggregates(user_id, day)")
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

    # --- Blink event helpers ---
    def insert_blink_event(self, user_id, session_id, event_ts, event_epoch_ms, duration_ms=None, event_type=None, ear=None, source=None, metadata=None):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO blink_events (user_id, session_id, event_ts, event_epoch_ms, duration_ms, event_type, ear, source, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, session_id, event_ts, event_epoch_ms, duration_ms, event_type, ear, source, metadata)
        )
        conn.commit()
        last_id = cursor.lastrowid
        conn.close()
        return last_id

    def get_blink_events(self, user_id=None, start_epoch_ms=None, end_epoch_ms=None, limit=1000):
        conn = self._connect()
        cursor = conn.cursor()
        sql = "SELECT id, user_id, session_id, event_ts, event_epoch_ms, duration_ms, event_type, ear, source, metadata FROM blink_events"
        params = []
        where = []
        if user_id is not None:
            where.append("user_id = ?")
            params.append(user_id)
        if start_epoch_ms is not None:
            where.append("event_epoch_ms >= ?")
            params.append(start_epoch_ms)
        if end_epoch_ms is not None:
            where.append("event_epoch_ms <= ?")
            params.append(end_epoch_ms)
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY event_epoch_ms DESC LIMIT ?"
        params.append(limit)
        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall()
        conn.close()
        return rows

    def upsert_blink_aggregate(self, user_id, day, blink_count, avg_duration_ms=None, median_ear=None):
        """Insert or update daily aggregate for a user."""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO blink_aggregates (user_id, day, blink_count, avg_duration_ms, median_ear)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, day) DO UPDATE SET
                blink_count = excluded.blink_count,
                avg_duration_ms = excluded.avg_duration_ms,
                median_ear = excluded.median_ear,
                created_at = datetime('now')
            """,
            (user_id, day, blink_count, avg_duration_ms, median_ear)
        )
        conn.commit()
        conn.close()

    def get_aggregates(self, user_id, start_day=None, end_day=None):
        conn = self._connect()
        cursor = conn.cursor()
        sql = "SELECT user_id, day, blink_count, avg_duration_ms, median_ear FROM blink_aggregates WHERE user_id = ?"
        params = [user_id]
        if start_day is not None:
            sql += " AND day >= ?"
            params.append(start_day)
        if end_day is not None:
            sql += " AND day <= ?"
            params.append(end_day)
        sql += " ORDER BY day DESC"
        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall()
        conn.close()
        return rows
