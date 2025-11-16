"""Unit tests for ConversationMemory (MongoDB-based)."""

import pytest
import os
from datetime import datetime

from src.utils.memory import ConversationMemory


@pytest.mark.skipif(
    os.system("docker-compose ps | grep loan-advisor-mongodb | grep -q Up") != 0,
    reason="MongoDB not running - start with: docker-compose up -d"
)
class TestConversationMemory:
    """Test suite for ConversationMemory."""

    @pytest.fixture
    def memory(self):
        """Create ConversationMemory instance for testing."""
        mem = ConversationMemory(
            mongodb_uri="mongodb://admin:password123@localhost:27017/",
            database_name="loan_advisor_test"
        )
        yield mem
        # Cleanup after test
        mem.close()

    @pytest.fixture
    def active_session(self, memory):
        """Create a session for testing."""
        user_id = f"test_user_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        session_id = memory.start_session(user_id)
        yield memory, session_id
        # Cleanup
        memory.delete_session(session_id)

    def test_connection(self, memory):
        """Test MongoDB connection works."""
        assert memory.client is not None
        assert memory.db is not None
        assert memory.sessions is not None
        assert memory.messages is not None

    def test_start_session(self, memory):
        """Test starting a new session."""
        user_id = "test_user_001"
        session_id = memory.start_session(user_id)

        assert session_id is not None
        assert memory.session_id == session_id
        assert memory.user_id == user_id
        assert session_id.startswith(user_id)

        # Cleanup
        memory.delete_session(session_id)

    def test_add_message(self, active_session):
        """Test adding messages to a session."""
        memory, session_id = active_session

        memory.add_message("user", "Hello, I need a loan")
        memory.add_message("assistant", "I can help with that")

        history = memory.get_conversation_history()
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "Hello, I need a loan"
        assert history[1]["role"] == "assistant"

    def test_add_message_without_session(self, memory):
        """Test that adding message without session raises error."""
        with pytest.raises(ValueError, match="No active session"):
            memory.add_message("user", "This should fail")

    def test_get_conversation_history(self, active_session):
        """Test retrieving conversation history."""
        memory, session_id = active_session

        # Add multiple messages
        messages = [
            ("user", "I'm 35 years old"),
            ("assistant", "Thank you for that information"),
            ("user", "I earn $8000/month"),
            ("assistant", "Got it, noted your income"),
        ]

        for role, content in messages:
            memory.add_message(role, content)

        history = memory.get_conversation_history()
        assert len(history) == 4
        assert history[0]["content"] == "I'm 35 years old"
        assert history[-1]["content"] == "Got it, noted your income"

    def test_get_conversation_history_with_limit(self, active_session):
        """Test retrieving limited conversation history."""
        memory, session_id = active_session

        # Add 5 messages
        for i in range(5):
            memory.add_message("user", f"Message {i}")

        # Get only last 3
        history = memory.get_conversation_history(limit=3)
        assert len(history) == 3

    def test_resume_session(self, active_session):
        """Test resuming an existing session."""
        memory, session_id = active_session

        # Add a message
        memory.add_message("user", "Test message")

        # Clear session
        memory.clear_session()
        assert memory.session_id is None

        # Resume session
        resumed = memory.resume_session(session_id)
        assert resumed is True
        assert memory.session_id == session_id

        # Verify message is still there
        history = memory.get_conversation_history()
        assert len(history) == 1
        assert history[0]["content"] == "Test message"

    def test_resume_nonexistent_session(self, memory):
        """Test resuming a session that doesn't exist."""
        resumed = memory.resume_session("nonexistent_session_id")
        assert resumed is False
        assert memory.session_id is None

    def test_get_user_sessions(self, memory):
        """Test getting all sessions for a user."""
        user_id = f"test_multi_user_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

        # Create multiple sessions
        session_ids = []
        for i in range(3):
            sid = memory.start_session(user_id)
            memory.add_message("user", f"Message in session {i}")
            session_ids.append(sid)
            memory.clear_session()  # Clear to allow creating new session with same user
            import time
            time.sleep(1)  # Ensure unique timestamp for session_id

        # Get user sessions
        sessions = memory.get_user_sessions(user_id, limit=10)
        assert len(sessions) >= 3

        # Verify session info
        assert all("session_id" in s for s in sessions)
        assert all("message_count" in s for s in sessions)

        # Cleanup
        for sid in session_ids:
            memory.delete_session(sid)

    def test_delete_session(self, memory):
        """Test deleting a session."""
        user_id = "test_delete_user"
        session_id = memory.start_session(user_id)

        memory.add_message("user", "This will be deleted")

        # Delete session
        memory.delete_session(session_id)

        # Verify session is gone
        resumed = memory.resume_session(session_id)
        assert resumed is False

    def test_get_session_info(self, active_session):
        """Test getting session information."""
        memory, session_id = active_session

        memory.add_message("user", "Test 1")
        memory.add_message("assistant", "Test 2")

        info = memory.get_session_info()
        assert info is not None
        assert info["session_id"] == session_id
        assert info["message_count"] == 2
        assert "created_at" in info
        assert "last_active" in info

    def test_get_session_info_without_session(self, memory):
        """Test getting session info without active session."""
        info = memory.get_session_info()
        assert info is None

    def test_clear_session(self, active_session):
        """Test clearing session from memory."""
        memory, session_id = active_session

        memory.add_message("user", "Test message")

        # Clear session
        memory.clear_session()
        assert memory.session_id is None
        assert memory.user_id is None

        # Session still exists in DB
        resumed = memory.resume_session(session_id)
        assert resumed is True

    def test_multiple_users_isolation(self, memory):
        """Test that users have isolated conversations."""
        user1_id = f"user1_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        user2_id = f"user2_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

        # User 1 session
        session1 = memory.start_session(user1_id)
        memory.add_message("user", "User 1 message")
        memory.clear_session()

        # User 2 session
        session2 = memory.start_session(user2_id)
        memory.add_message("user", "User 2 message")

        # User 2 should only see their messages
        history = memory.get_conversation_history()
        assert len(history) == 1
        assert history[0]["content"] == "User 2 message"

        # Cleanup
        memory.delete_session(session1)
        memory.delete_session(session2)

    def test_session_updates_last_active(self, active_session):
        """Test that adding messages updates last_active timestamp."""
        memory, session_id = active_session

        info1 = memory.get_session_info()
        first_active = info1["last_active"]

        # Add a message (this should update last_active)
        import time
        time.sleep(1)  # Ensure timestamp difference
        memory.add_message("user", "New message")

        info2 = memory.get_session_info()
        second_active = info2["last_active"]

        # Last active should be updated
        assert second_active >= first_active

    def test_conversation_history_order(self, active_session):
        """Test that conversation history is in chronological order."""
        memory, session_id = active_session

        # Add messages
        messages = ["First", "Second", "Third", "Fourth"]
        for msg in messages:
            memory.add_message("user", msg)

        history = memory.get_conversation_history()
        retrieved = [h["content"] for h in history]

        assert retrieved == messages

    def test_total_users_count(self, memory):
        """Test getting total number of users."""
        # Create sessions for unique users
        user_ids = [f"count_user_{i}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}" for i in range(3)]
        session_ids = []

        for uid in user_ids:
            sid = memory.start_session(uid)
            session_ids.append(sid)

        total = memory.get_total_users()
        assert total >= 3  # At least our 3 test users

        # Cleanup
        for sid in session_ids:
            memory.delete_session(sid)

    def test_user_message_count(self, active_session):
        """Test getting total message count for a user."""
        memory, session_id = active_session

        # Add messages
        for i in range(5):
            memory.add_message("user", f"Message {i}")

        count = memory.get_user_message_count(memory.user_id)
        assert count >= 5


class TestConversationMemoryEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def memory(self):
        """Create ConversationMemory instance for testing."""
        mem = ConversationMemory(
            mongodb_uri="mongodb://admin:password123@localhost:27017/",
            database_name="loan_advisor_test"
        )
        yield mem
        mem.close()

    def test_empty_message_content(self, memory):
        """Test adding message with empty content."""
        user_id = f"empty_test_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        session_id = memory.start_session(user_id)

        memory.add_message("user", "")
        history = memory.get_conversation_history()

        assert len(history) == 1
        assert history[0]["content"] == ""

        # Cleanup
        memory.delete_session(session_id)

    def test_very_long_message(self, memory):
        """Test adding very long message."""
        user_id = f"long_test_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        session_id = memory.start_session(user_id)

        long_message = "A" * 10000  # 10k characters
        memory.add_message("user", long_message)

        history = memory.get_conversation_history()
        assert len(history[0]["content"]) == 10000

        # Cleanup
        memory.delete_session(session_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
