"""Seed one realistic random Indian user into the Spendly users table.

Standalone by design: database/db.py is still the Step 1 stub, so this script
reproduces its documented connection contract (sqlite3.Row row factory +
foreign keys ON) instead of importing from it.

    venv/Scripts/python.exe scripts/seed_user.py
"""

import random
import sqlite3
from datetime import datetime
from pathlib import Path

from werkzeug.security import generate_password_hash

DB_PATH = Path(__file__).resolve().parent.parent / "expense_tracker.db"
DEFAULT_PASSWORD = "password123"


# ------------------------------------------------------------------ #
# Name pools — grouped by region so first/last pairings stay coherent #
# ------------------------------------------------------------------ #

NAME_POOLS = [
    # North India
    (
        ["Rahul", "Priya", "Amit", "Neha", "Vikram", "Anjali", "Rohit",
         "Kavita", "Arjun", "Pooja", "Ankit", "Shivani"],
        ["Sharma", "Verma", "Gupta", "Malhotra", "Chopra", "Bhatia",
         "Agarwal", "Sinha", "Kapoor", "Saxena"],
    ),
    # South India
    (
        ["Karthik", "Divya", "Suresh", "Lakshmi", "Venkatesh", "Meena",
         "Arun", "Deepa", "Praveen", "Shruti", "Vignesh", "Aishwarya"],
        ["Iyer", "Nair", "Reddy", "Menon", "Rao", "Krishnan",
         "Subramaniam", "Pillai", "Naidu", "Raman"],
    ),
    # Maharashtra & Gujarat
    (
        ["Sanket", "Aditi", "Nikhil", "Snehal", "Omkar", "Rutuja",
         "Harsh", "Krutika", "Siddharth", "Manasi"],
        ["Patil", "Deshmukh", "Joshi", "Kulkarni", "Shah", "Patel",
         "Desai", "Mehta", "Jadhav", "Gaikwad"],
    ),
    # Bengal & Odisha
    (
        ["Soumya", "Ananya", "Abhijit", "Rituparna", "Debashish", "Payel",
         "Sourav", "Moumita", "Indranil", "Sohini"],
        ["Banerjee", "Chatterjee", "Mukherjee", "Das", "Ghosh", "Bose",
         "Sen", "Dutta", "Mishra", "Panda"],
    ),
    # Punjab
    (
        ["Harpreet", "Simran", "Gurpreet", "Manpreet", "Jaspreet",
         "Navneet", "Amarjeet", "Rupinder"],
        ["Singh", "Gill", "Dhillon", "Sandhu", "Grewal", "Bajwa"],
    ),
]

# ------------------------------------------------------------------ #
# Connection helper — mirrors the get_db() contract in database/db.py #
# ------------------------------------------------------------------ #

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def ensure_users_table(conn):
    """Create the users table only, using the exact Step 1 spec schema so a
    later init_db() call is a harmless no-op for this table."""
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
    conn.commit()


# ------------------------------------------------------------------ #
# Generation                                                          #
# ------------------------------------------------------------------ #

def random_name():
    first_names, last_names = random.choice(NAME_POOLS)
    return f"{random.choice(first_names)} {random.choice(last_names)}"


def email_for(name):
    first, last = name.lower().split()
    return f"{first}.{last}{random.randint(10, 999)}@gmail.com"


def email_exists(conn, email):
    row = conn.execute(
        "SELECT 1 FROM users WHERE email = ?", (email,)
    ).fetchone()
    return row is not None


def unique_user(conn, max_attempts=500):
    """Regenerate until the derived email is unused in the users table."""
    for _ in range(max_attempts):
        name = random_name()
        email = email_for(name)
        if not email_exists(conn, email):
            return name, email
    raise RuntimeError(
        f"could not find an unused email in {max_attempts} attempts"
    )

# ------------------------------------------------------------------ #
# Entry point                                                         #
# ------------------------------------------------------------------ #

def main():
    conn = get_db()
    try:
        ensure_users_table(conn)
        name, email = unique_user(conn)
        cursor = conn.execute(
            """
            INSERT INTO users (name, email, password_hash, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                name,
                email,
                generate_password_hash(DEFAULT_PASSWORD),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )
        conn.commit()

        print("Seeded user")
        print(f"  id       : {cursor.lastrowid}")
        print(f"  name     : {name}")
        print(f"  email    : {email}")
        print(f"  password : {DEFAULT_PASSWORD}  (stored as a hash)")
    finally:
        conn.close()


if __name__ == "__main__":
    main()


