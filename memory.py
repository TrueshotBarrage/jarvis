"""Memory module for persistent conversation storage.

This module provides SQLite-based conversation history storage
with time-based retrieval for multi-turn AI conversations.
"""

from __future__ import annotations

import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


class Memory:
    """Persistent conversation memory using SQLite.

    Stores conversation history with timestamps and provides
    time-based retrieval for building AI context.

    Attributes:
        db_path: Path to the SQLite database file.
        logger: Module logger instance.
    """

    DEFAULT_DB_PATH = "db/jarvis.db"

    def __init__(self, db_path: str | None = None) -> None:
        """Initialize the memory storage.

        Args:
            db_path: Path to SQLite database. Defaults to db/jarvis.db.
        """
        self.db_path = db_path or self.DEFAULT_DB_PATH
        self.logger = logging.getLogger(__name__)
        self._ensure_db_exists()

    def _ensure_db_exists(self) -> None:
        """Ensure the database and tables exist."""
        db_file = Path(self.db_path)

        if not db_file.exists():
            self.logger.info(f"Initializing database: {self.db_path}")
            # Import and run init script
            from db.init import init_database

            init_database(self.db_path)

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def add_message(self, role: str, content: str) -> int:
        """Store a message in the conversation history.

        Args:
            role: Either 'user' or 'assistant'.
            content: The message content.

        Returns:
            The ID of the inserted message.

        Raises:
            ValueError: If role is not 'user' or 'assistant'.
        """
        if role not in ("user", "assistant"):
            raise ValueError(f"Invalid role: {role}. Must be 'user' or 'assistant'.")

        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO messages (role, content) VALUES (?, ?)",
            (role, content),
        )
        message_id = cursor.lastrowid

        conn.commit()
        conn.close()

        self.logger.debug(f"Stored {role} message (id={message_id})")
        return message_id

    def get_recent(self, hours: float = 4.0) -> list[dict[str, Any]]:
        """Get messages from the last N hours.

        Args:
            hours: Number of hours to look back. Defaults to 4.

        Returns:
            List of message dicts with keys: id, role, content, created_at.
            Messages are ordered oldest to newest.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cutoff = datetime.now() - timedelta(hours=hours)
        cutoff_str = cutoff.strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute(
            """
            SELECT id, role, content, created_at
            FROM messages
            WHERE created_at >= ?
            ORDER BY created_at ASC
            """,
            (cutoff_str,),
        )

        messages = [dict(row) for row in cursor.fetchall()]
        conn.close()

        self.logger.debug(f"Retrieved {len(messages)} messages from last {hours} hours")
        return messages

    def get_for_context(self, hours: float = 4.0, max_messages: int = 50) -> list[dict[str, str]]:
        """Get messages formatted for AI context.

        Args:
            hours: Number of hours to look back.
            max_messages: Maximum number of messages to return.

        Returns:
            List of dicts with 'role' and 'content' keys only,
            suitable for passing to the AI model.
        """
        messages = self.get_recent(hours)

        # Take most recent messages if over limit
        if len(messages) > max_messages:
            messages = messages[-max_messages:]

        return [{"role": msg["role"], "content": msg["content"]} for msg in messages]

    def clear(self) -> int:
        """Clear all conversation history.

        Returns:
            Number of messages deleted.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM messages")
        count = cursor.fetchone()[0]

        cursor.execute("DELETE FROM messages")
        conn.commit()
        conn.close()

        self.logger.info(f"Cleared {count} messages from memory")
        return count

    def count(self) -> int:
        """Get the total number of stored messages.

        Returns:
            Total message count.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM messages")
        count = cursor.fetchone()[0]

        conn.close()
        return count
