"""Data-access layer: every SQL statement in the app lives in this file.
All transaction / goal queries are scoped to a user_id."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "finance.db"

DEFAULT_CATEGORIES = {
    "Expense": ["Food", "Transport", "Rent", "Education", "Entertainment",
                "Shopping", "Health", "Bills", "Other"],
    "Income": ["Pocket Money", "Salary", "Scholarship", "Freelance", "Other"],
}


class Database:
    def __init__(self, path=DB_PATH):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._create_tables()
        self._migrate()
        self._seed_categories()

    # ---------------------------------------------------------- setup
    def _create_tables(self):
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT NOT NULL UNIQUE COLLATE NOCASE,
            password_hash TEXT NOT NULL,
            created_at    TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS categories (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            name  TEXT NOT NULL,
            type  TEXT NOT NULL CHECK (type IN ('Income', 'Expense')),
            UNIQUE (name, type)
        );
        CREATE TABLE IF NOT EXISTS transactions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER REFERENCES users(id) ON DELETE CASCADE,
            type        TEXT NOT NULL CHECK (type IN ('Income', 'Expense')),
            amount      REAL NOT NULL CHECK (amount > 0),
            category_id INTEGER NOT NULL REFERENCES categories(id),
            description TEXT DEFAULT '',
            date        TEXT NOT NULL,              -- ISO format YYYY-MM-DD
            created_at  TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS goals (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id  INTEGER REFERENCES users(id) ON DELETE CASCADE,
            name     TEXT NOT NULL,
            target   REAL NOT NULL CHECK (target > 0),
            saved    REAL NOT NULL DEFAULT 0,
            deadline TEXT DEFAULT ''
        );
        """)
        self.conn.commit()

    def _migrate(self):
        """Upgrade databases created before the login feature existed."""
        for table in ("transactions", "goals"):
            cols = [r["name"] for r in self.conn.execute(f"PRAGMA table_info({table})")]
            if "user_id" not in cols:
                self.conn.execute(
                    f"ALTER TABLE {table} ADD COLUMN user_id INTEGER REFERENCES users(id)")
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_tx_user_date ON transactions(user_id, date)")
        self.conn.commit()

    def _seed_categories(self):
        for tx_type, names in DEFAULT_CATEGORIES.items():
            for name in names:
                self.conn.execute(
                    "INSERT OR IGNORE INTO categories (name, type) VALUES (?, ?)",
                    (name, tx_type))
        self.conn.commit()

    def close(self):
        self.conn.close()

    # -------------------------------------------------------------- users
    def create_user(self, username, password_hash):
        """Insert a user. Raises sqlite3.IntegrityError if the name is taken."""
        cur = self.conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash))
        user_id = cur.lastrowid
        # The very first account adopts any rows saved before logins existed.
        if self.conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 1:
            for table in ("transactions", "goals"):
                self.conn.execute(
                    f"UPDATE {table} SET user_id = ? WHERE user_id IS NULL", (user_id,))
        self.conn.commit()
        return user_id

    def get_user(self, username):
        row = self.conn.execute(
            "SELECT id, username, password_hash FROM users WHERE username = ?",
            (username,)).fetchone()
        return dict(row) if row else None

    # ----------------------------------------------------- categories
    def get_categories(self, tx_type):
        rows = self.conn.execute(
            "SELECT name FROM categories WHERE type = ? ORDER BY name", (tx_type,))
        return [r["name"] for r in rows]

    def _category_id(self, name, tx_type):
        """Return the id of a category, creating it if it does not exist yet."""
        self.conn.execute(
            "INSERT OR IGNORE INTO categories (name, type) VALUES (?, ?)",
            (name, tx_type))
        row = self.conn.execute(
            "SELECT id FROM categories WHERE name = ? AND type = ?",
            (name, tx_type)).fetchone()
        return row["id"]

    # ---------------------------------------------------- transactions
    def insert_transaction(self, uid, tx_type, amount, category, description, date):
        cat_id = self._category_id(category, tx_type)
        cur = self.conn.execute(
            "INSERT INTO transactions (user_id, type, amount, category_id, description, date) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (uid, tx_type, amount, cat_id, description, date))
        self.conn.commit()
        return cur.lastrowid

    def update_transaction(self, uid, tx_id, tx_type, amount, category, description, date):
        cat_id = self._category_id(category, tx_type)
        self.conn.execute(
            "UPDATE transactions SET type=?, amount=?, category_id=?, "
            "description=?, date=? WHERE id=? AND user_id=?",
            (tx_type, amount, cat_id, description, date, tx_id, uid))
        self.conn.commit()

    def delete_transaction(self, uid, tx_id):
        self.conn.execute(
            "DELETE FROM transactions WHERE id = ? AND user_id = ?", (tx_id, uid))
        self.conn.commit()

    def fetch_transactions(self, uid, month=None, tx_type=None, search=None):
        sql = ("SELECT t.id, t.date, t.type, c.name AS category, "
               "t.description, t.amount "
               "FROM transactions t JOIN categories c ON c.id = t.category_id "
               "WHERE t.user_id = ?")
        params = [uid]
        if month:
            sql += " AND substr(t.date, 1, 7) = ?"
            params.append(month)
        if tx_type:
            sql += " AND t.type = ?"
            params.append(tx_type)
        if search:
            sql += " AND (t.description LIKE ? OR c.name LIKE ?)"
            params += [f"%{search}%", f"%{search}%"]
        sql += " ORDER BY t.date DESC, t.id DESC"
        return [dict(r) for r in self.conn.execute(sql, params)]

    # -------------------------------------------------------- analytics
    def totals(self, uid, month=None):
        sql = ("SELECT type, COALESCE(SUM(amount), 0) AS total "
               "FROM transactions WHERE user_id = ?")
        params = [uid]
        if month:
            sql += " AND substr(date, 1, 7) = ?"
            params.append(month)
        sql += " GROUP BY type"
        result = {"Income": 0.0, "Expense": 0.0}
        for r in self.conn.execute(sql, params):
            result[r["type"]] = r["total"]
        return result

    def category_breakdown(self, uid, tx_type, month=None):
        sql = ("SELECT c.name AS category, SUM(t.amount) AS total "
               "FROM transactions t JOIN categories c ON c.id = t.category_id "
               "WHERE t.user_id = ? AND t.type = ?")
        params = [uid, tx_type]
        if month:
            sql += " AND substr(t.date, 1, 7) = ?"
            params.append(month)
        sql += " GROUP BY c.name ORDER BY total DESC"
        return [(r["category"], r["total"]) for r in self.conn.execute(sql, params)]

    def monthly_totals(self, uid, year):
        """Return {1..12: {'Income': x, 'Expense': y}} for the given year."""
        data = {m: {"Income": 0.0, "Expense": 0.0} for m in range(1, 13)}
        rows = self.conn.execute(
            "SELECT CAST(substr(date, 6, 2) AS INTEGER) AS m, type, SUM(amount) AS total "
            "FROM transactions WHERE user_id = ? AND substr(date, 1, 4) = ? "
            "GROUP BY m, type", (uid, str(year)))
        for r in rows:
            data[r["m"]][r["type"]] = r["total"]
        return data

    def months_available(self, uid):
        rows = self.conn.execute(
            "SELECT DISTINCT substr(date, 1, 7) AS m FROM transactions "
            "WHERE user_id = ? ORDER BY m DESC", (uid,))
        return [r["m"] for r in rows]

    # ------------------------------------------------------------ goals
    def insert_goal(self, uid, name, target, deadline):
        self.conn.execute(
            "INSERT INTO goals (user_id, name, target, deadline) VALUES (?, ?, ?, ?)",
            (uid, name, target, deadline))
        self.conn.commit()

    def fetch_goals(self, uid):
        return [dict(r) for r in self.conn.execute(
            "SELECT id, name, target, saved, deadline FROM goals "
            "WHERE user_id = ? ORDER BY id DESC", (uid,))]

    def add_to_goal(self, uid, goal_id, amount):
        self.conn.execute(
            "UPDATE goals SET saved = MAX(saved + ?, 0) WHERE id = ? AND user_id = ?",
            (amount, goal_id, uid))
        self.conn.commit()

    def delete_goal(self, uid, goal_id):
        self.conn.execute(
            "DELETE FROM goals WHERE id = ? AND user_id = ?", (goal_id, uid))
        self.conn.commit()
