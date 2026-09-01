"""Data layer for Spendly — Step 1: Database Setup.

Raw sqlite3 by design: there is no ORM in this project. Every query the app runs
lives in this module so route handlers never open a cursor of their own.
"""

import sqlite3
from datetime import date
from pathlib import Path

from werkzeug.security import generate_password_hash

DB_PATH = Path(__file__).resolve().parent.parent / "expense_tracker.db"

# The fixed category vocabulary. Expense features in later steps read from here
# rather than redefining their own list.
CATEGORIES = [
    "Food",
    "Transport",
    "Bills",
    "Health",
    "Entertainment",
    "Shopping",
    "Other",
]

# Dev seed data as (day_of_month, amount, category, description). Days stay in
# 1..28 so every entry is valid in any month.
SEED_EXPENSES = [
    (2, 480.0, "Food", "Groceries for the week"),
    (4, 60.0, "Transport", "Metro card top-up"),
    (7, 1850.0, "Bills", "Electricity bill"),
    (9, 350.0, "Health", "Pharmacy — vitamins"),
    (12, 299.0, "Entertainment", "Movie tickets"),
    (15, 1299.0, "Shopping", "Running shoes"),
    (18, 200.0, "Other", "Gift wrap and card"),
    (21, 260.0, "Food", "Dinner with friends"),
]


# ------------------------------------------------------------------ #
# Connection                                                          #
# ------------------------------------------------------------------ #

def get_db():
    """Open a connection with dict-style rows and foreign keys enforced.

    DB_PATH is read at call time so tests can repoint it at a temp file.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ------------------------------------------------------------------ #
# Schema                                                              #
# ------------------------------------------------------------------ #

def init_db():
    """Create both tables. Safe to call on every startup."""
    conn = get_db()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                name          TEXT NOT NULL,
                email         TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at    TEXT DEFAULT (datetime('now'))
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS expenses (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL REFERENCES users(id),
                amount      REAL NOT NULL,
                category    TEXT NOT NULL,
                date        TEXT NOT NULL,
                description TEXT,
                created_at  TEXT DEFAULT (datetime('now'))
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def seed_db():
    """Insert one demo user and eight sample expenses, once."""
    conn = get_db()
    try:
        if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] > 0:
            return

        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Demo User", "demo@spendly.com", generate_password_hash("demo123")),
        )
        user_id = cursor.lastrowid

        month_start = date.today().replace(day=1)
        conn.executemany(
            """
            INSERT INTO expenses (user_id, amount, category, date, description)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (
                    user_id,
                    amount,
                    category,
                    month_start.replace(day=day).isoformat(),
                    description,
                )
                for day, amount, category, description in SEED_EXPENSES
            ],
        )
        conn.commit()
    finally:
        conn.close()


# ------------------------------------------------------------------ #
# Users                                                               #
# ------------------------------------------------------------------ #

def get_user_by_email(email):
    """Return the matching row, or None. Step 3's login reuses this."""
    conn = get_db()
    try:
        return conn.execute(
            "SELECT id, name, email, password_hash, created_at"
            " FROM users WHERE email = ?",
            (email,),
        ).fetchone()
    finally:
        conn.close()


def create_user(name, email, password_hash):
    """Insert a user and return the new id. created_at uses the column DEFAULT."""
    conn = get_db()
    try:
        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, password_hash),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()
