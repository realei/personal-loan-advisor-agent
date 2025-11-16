"""Unit tests for PersonalLoanAgent properties."""

import pytest
import os
from datetime import datetime

from src.agent import PersonalLoanAgent
from src.utils.memory import ConversationMemory


@pytest.mark.skipif(
    os.system("docker-compose ps | grep loan-advisor-mongodb | grep -q Up") != 0,
    reason="MongoDB not running - start with: docker-compose up -d"
)
class TestAgentProperties:
    """Test suite for Agent convenience properties."""

    @pytest.fixture
    def memory(self):
        """Create ConversationMemory instance."""
        mem = ConversationMemory(
            mongodb_uri="mongodb://admin:password123@localhost:27017/",
            database_name="loan_advisor_test",
            enable_evaluation=False  # Disable for faster tests
        )
        yield mem
        mem.close()

    def test_agent_without_memory(self):
        """Test that properties return None when no memory."""
        # Set dummy API key for initialization
        os.environ["OPENAI_API_KEY"] = "test-key"

        try:
            agent = PersonalLoanAgent(memory=None)

            assert agent.user_id is None
            assert agent.session_id is None
        finally:
            if os.environ.get("OPENAI_API_KEY") == "test-key":
                del os.environ["OPENAI_API_KEY"]

    def test_agent_with_memory_no_session(self, memory):
        """Test that properties return None when session not started."""
        agent = PersonalLoanAgent(memory=memory)

        assert agent.user_id is None
        assert agent.session_id is None

    def test_agent_with_active_session(self, memory):
        """Test that properties return correct values with active session."""
        user_id = f"test_user_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        session_id = memory.start_session(user_id)

        agent = PersonalLoanAgent(memory=memory)

        # Test properties
        assert agent.user_id == user_id
        assert agent.session_id == session_id
        assert agent.user_id is not None
        assert agent.session_id is not None

        # Cleanup
        memory.delete_session(session_id)

    def test_agent_properties_after_session_clear(self, memory):
        """Test that properties return None after session is cleared."""
        user_id = f"test_user_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        session_id = memory.start_session(user_id)

        agent = PersonalLoanAgent(memory=memory)

        # Before clear
        assert agent.user_id is not None
        assert agent.session_id is not None

        # Clear session
        memory.clear_session()

        # After clear
        assert agent.user_id is None
        assert agent.session_id is None

        # Cleanup
        memory.delete_session(session_id)

    def test_multiple_agents_same_memory(self, memory):
        """Test that multiple agents can share same memory."""
        user_id = f"test_user_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        session_id = memory.start_session(user_id)

        agent1 = PersonalLoanAgent(memory=memory)
        agent2 = PersonalLoanAgent(memory=memory)

        # Both should see same session
        assert agent1.user_id == user_id
        assert agent2.user_id == user_id
        assert agent1.session_id == session_id
        assert agent2.session_id == session_id

        # Cleanup
        memory.delete_session(session_id)

    def test_agent_session_resume(self, memory):
        """Test that agent properties work after resuming session."""
        user_id = f"test_user_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

        # Create and clear session
        session_id = memory.start_session(user_id)
        memory.add_message("user", "Hello")
        memory.clear_session()

        # Create agent with cleared memory
        agent = PersonalLoanAgent(memory=memory)
        assert agent.user_id is None
        assert agent.session_id is None

        # Resume session
        resumed = memory.resume_session(session_id)
        assert resumed is True

        # Now properties should return values
        assert agent.user_id == user_id
        assert agent.session_id == session_id

        # Cleanup
        memory.delete_session(session_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
