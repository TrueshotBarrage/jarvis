"""Tests for the Memory module."""

import os
import tempfile
from unittest.mock import patch

import pytest

from jarvis.memory import Memory


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    # Initialize the database schema
    import sqlite3

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_messages_created_at
        ON messages(created_at)
    """)
    conn.commit()
    conn.close()

    yield db_path

    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)


class TestMemoryInit:
    """Test suite for Memory initialization."""

    def test_default_db_path(self):
        """Test Memory uses default db path."""
        # Don't actually create the db
        with patch.object(Memory, "_ensure_db_exists"):
            memory = Memory()
            assert memory.db_path == "db/jarvis.db"

    def test_custom_db_path(self, temp_db):
        """Test Memory accepts custom db path."""
        memory = Memory(db_path=temp_db)
        assert memory.db_path == temp_db


class TestMemoryAddMessage:
    """Test suite for Memory.add_message method."""

    def test_add_user_message(self, temp_db):
        """Test adding a user message."""
        memory = Memory(db_path=temp_db)
        msg_id = memory.add_message("user", "Hello, Nova!")

        assert msg_id is not None
        assert msg_id > 0

    def test_add_assistant_message(self, temp_db):
        """Test adding an assistant message."""
        memory = Memory(db_path=temp_db)
        msg_id = memory.add_message("assistant", "Hello! How can I help?")

        assert msg_id is not None
        assert msg_id > 0

    def test_invalid_role_raises_error(self, temp_db):
        """Test that invalid role raises ValueError."""
        memory = Memory(db_path=temp_db)

        with pytest.raises(ValueError) as exc_info:
            memory.add_message("invalid", "Test message")

        assert "Invalid role" in str(exc_info.value)

    def test_message_ids_increment(self, temp_db):
        """Test that message IDs increment."""
        memory = Memory(db_path=temp_db)

        id1 = memory.add_message("user", "First")
        id2 = memory.add_message("assistant", "Second")
        id3 = memory.add_message("user", "Third")

        assert id2 > id1
        assert id3 > id2


class TestMemoryGetRecent:
    """Test suite for Memory.get_recent method."""

    def test_get_recent_empty(self, temp_db):
        """Test get_recent returns empty list when no messages."""
        memory = Memory(db_path=temp_db)
        messages = memory.get_recent()

        assert messages == []

    def test_get_recent_returns_messages(self, temp_db):
        """Test get_recent returns stored messages."""
        memory = Memory(db_path=temp_db)

        memory.add_message("user", "Hello")
        memory.add_message("assistant", "Hi there!")

        messages = memory.get_recent()

        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Hello"
        assert messages[1]["role"] == "assistant"
        assert messages[1]["content"] == "Hi there!"

    def test_get_recent_ordered_by_time(self, temp_db):
        """Test messages are ordered oldest to newest."""
        memory = Memory(db_path=temp_db)

        memory.add_message("user", "First")
        memory.add_message("user", "Second")
        memory.add_message("user", "Third")

        messages = memory.get_recent()

        assert messages[0]["content"] == "First"
        assert messages[1]["content"] == "Second"
        assert messages[2]["content"] == "Third"


class TestMemoryGetForContext:
    """Test suite for Memory.get_for_context method."""

    def test_returns_simplified_format(self, temp_db):
        """Test get_for_context returns only role and content."""
        memory = Memory(db_path=temp_db)

        memory.add_message("user", "Hello")
        memory.add_message("assistant", "Hi!")

        messages = memory.get_for_context()

        assert len(messages) == 2
        assert set(messages[0].keys()) == {"role", "content"}
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Hello"

    def test_respects_max_messages(self, temp_db):
        """Test get_for_context limits messages."""
        memory = Memory(db_path=temp_db)

        # Add 5 messages
        for i in range(5):
            memory.add_message("user", f"Message {i}")

        # Request only last 3
        messages = memory.get_for_context(max_messages=3)

        assert len(messages) == 3
        # Should get most recent 3
        assert messages[0]["content"] == "Message 2"
        assert messages[2]["content"] == "Message 4"


class TestMemoryClear:
    """Test suite for Memory.clear method."""

    def test_clear_removes_all_messages(self, temp_db):
        """Test clear removes all messages."""
        memory = Memory(db_path=temp_db)

        memory.add_message("user", "Hello")
        memory.add_message("assistant", "Hi!")

        deleted = memory.clear()

        assert deleted == 2
        assert memory.count() == 0

    def test_clear_returns_zero_when_empty(self, temp_db):
        """Test clear returns 0 when no messages."""
        memory = Memory(db_path=temp_db)

        deleted = memory.clear()

        assert deleted == 0


class TestMemoryCount:
    """Test suite for Memory.count method."""

    def test_count_empty(self, temp_db):
        """Test count returns 0 when empty."""
        memory = Memory(db_path=temp_db)
        assert memory.count() == 0

    def test_count_after_adding(self, temp_db):
        """Test count reflects added messages."""
        memory = Memory(db_path=temp_db)

        memory.add_message("user", "One")
        assert memory.count() == 1

        memory.add_message("assistant", "Two")
        assert memory.count() == 2
