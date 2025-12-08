"""Database initialization script for Jarvis.

Run this script to create the SQLite database schema.
Usage: python db/init.py
"""

import sqlite3
from pathlib import Path


def init_database(db_path: str = "db/jarvis.db") -> None:
    """Initialize the Jarvis database with required tables.

    Args:
        db_path: Path to the SQLite database file.
    """
    # Ensure the db directory exists
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create messages table for conversation history
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create index for time-based queries
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_messages_created_at
        ON messages(created_at)
    """)

    conn.commit()
    conn.close()

    print(f"✅ Database initialized: {db_path}")


if __name__ == "__main__":
    init_database()
