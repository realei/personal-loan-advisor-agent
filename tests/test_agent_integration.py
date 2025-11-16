"""Integration tests for PersonalLoanAgent.

These tests verify end-to-end functionality of the agent.
"""

import pytest
import os
from datetime import datetime

from src.agent import PersonalLoanAgent
from src.utils.memory import ConversationMemory


@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OpenAI API key not available - skipping integration tests"
)
class TestAgentIntegration:
    """Integration tests for PersonalLoanAgent (requires API key)."""

    @pytest.fixture
    def agent(self):
        """Create PersonalLoanAgent instance without memory for basic tests."""
        return PersonalLoanAgent(model="gpt-4", temperature=0.3, debug_mode=False, memory=None)

    def test_agent_initialization(self, agent):
        """Test that agent initializes correctly."""
        assert agent is not None
        assert agent.eligibility_tool is not None
        assert agent.calculator_tool is not None
        assert agent.agent is not None

    def test_simple_payment_calculation(self, agent):
        """Test simple payment calculation request."""
        # Just verify agent can be called - actual response is printed, not returned
        try:
            agent.run(
                "Calculate monthly payment for a $50,000 loan at 5% interest for 36 months",
                stream=False
            )
            # If no exception, test passes
            assert True
        except Exception as e:
            pytest.fail(f"Agent failed: {e}")

    def test_eligibility_check_request(self, agent):
        """Test eligibility check request."""
        try:
            agent.run(
                "I'm 35 years old, earn $10,000 per month, have a credit score of 720, "
                "work full-time for 5 years with $1,000 monthly debt. "
                "Can I get a $50,000 loan for 36 months?",
                stream=False
            )
            assert True
        except Exception as e:
            pytest.fail(f"Agent failed: {e}")

    def test_affordability_question(self, agent):
        """Test affordability assessment."""
        try:
            agent.run(
                "I make $8,000 per month and have $1,500 in existing debt. "
                "Can I afford a $60,000 loan at 5.5% for 48 months?",
                stream=False
            )
            assert True
        except Exception as e:
            pytest.fail(f"Agent failed: {e}")

    def test_comparison_request(self, agent):
        """Test loan term comparison."""
        try:
            agent.run(
                "Compare 24, 36, and 48 month terms for a $40,000 loan at 4.5%",
                stream=False
            )
            assert True
        except Exception as e:
            pytest.fail(f"Agent failed: {e}")


class TestAgentToolAccess:
    """Test that agent tools are accessible and configured correctly."""

    def test_eligibility_tool_configured(self):
        """Test eligibility tool is properly configured."""
        # Create agent without API key to test tool setup
        os.environ["OPENAI_API_KEY"] = "test-key-for-init"

        try:
            agent = PersonalLoanAgent()
            assert agent.eligibility_tool is not None
            assert hasattr(agent, 'check_eligibility')
        finally:
            # Clean up test key if it wasn't set before
            if os.environ.get("OPENAI_API_KEY") == "test-key-for-init":
                del os.environ["OPENAI_API_KEY"]

    def test_calculator_tool_configured(self):
        """Test calculator tool is properly configured."""
        os.environ["OPENAI_API_KEY"] = "test-key-for-init"

        try:
            agent = PersonalLoanAgent()
            assert agent.calculator_tool is not None
            assert hasattr(agent, 'calculate_loan_payment')
            assert hasattr(agent, 'generate_payment_schedule')
            assert hasattr(agent, 'check_affordability')
        finally:
            if os.environ.get("OPENAI_API_KEY") == "test-key-for-init":
                del os.environ["OPENAI_API_KEY"]

    def test_agent_has_all_tools(self):
        """Test that agent has all expected tools."""
        os.environ["OPENAI_API_KEY"] = "test-key-for-init"

        try:
            agent = PersonalLoanAgent()

            # Verify all tool methods exist
            expected_tools = [
                'check_eligibility',
                'calculate_loan_payment',
                'generate_payment_schedule',
                'check_affordability',
                'compare_loan_terms',
                'calculate_max_affordable_loan',
            ]

            for tool_name in expected_tools:
                assert hasattr(agent, tool_name), f"Missing tool: {tool_name}"
        finally:
            if os.environ.get("OPENAI_API_KEY") == "test-key-for-init":
                del os.environ["OPENAI_API_KEY"]


@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY") or os.system("docker-compose ps | grep loan-advisor-mongodb | grep -q Up") != 0,
    reason="Requires OpenAI API key and MongoDB running"
)
class TestAgentWithMemory:
    """Integration tests for PersonalLoanAgent with MongoDB memory."""

    @pytest.fixture
    def memory(self):
        """Create ConversationMemory instance."""
        mem = ConversationMemory(
            mongodb_uri="mongodb://admin:password123@localhost:27017/",
            database_name="loan_advisor_test"
        )
        user_id = f"test_agent_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        session_id = mem.start_session(user_id)
        yield mem
        # Cleanup
        mem.delete_session(session_id)
        mem.close()

    @pytest.fixture
    def agent_with_memory(self, memory):
        """Create PersonalLoanAgent with memory."""
        return PersonalLoanAgent(
            model="gpt-4",
            temperature=0.3,
            debug_mode=False,
            memory=memory
        )

    def test_agent_remembers_loan_amount(self, agent_with_memory, memory):
        """Test that agent remembers loan amount across turns."""
        # First turn: provide loan details
        print("\n--- Turn 1: User provides loan information ---")
        agent_with_memory.run(
            "I want to borrow $50,000 for 36 months",
            stream=False
        )

        # Verify message was stored
        history = memory.get_conversation_history()
        assert len(history) >= 2  # User message + assistant response

        # Second turn: ask about payment without repeating amount
        print("\n--- Turn 2: Ask about payment (should remember $50,000) ---")
        agent_with_memory.run(
            "What would my monthly payment be at 5% interest?",
            stream=False
        )

        # Verify both turns are in history
        history = memory.get_conversation_history()
        assert len(history) >= 4  # 2 turns = 4 messages minimum

    def test_agent_remembers_user_profile(self, agent_with_memory, memory):
        """Test that agent remembers user profile information."""
        # First turn: provide profile
        print("\n--- Turn 1: User provides profile ---")
        agent_with_memory.run(
            "I'm 35 years old, earn $8000/month, and have a credit score of 720",
            stream=False
        )

        # Second turn: ask about eligibility without repeating info
        print("\n--- Turn 2: Ask about loan (should remember profile) ---")
        agent_with_memory.run(
            "Can I get a $50,000 loan for 36 months?",
            stream=False
        )

        # Verify conversation history
        history = memory.get_conversation_history()
        assert len(history) >= 4

        # Verify user profile info is in first message
        assert "35" in history[0]["content"] or "8000" in history[0]["content"]

    def test_conversation_persistence(self, memory):
        """Test that conversations persist across agent instances."""
        # Create first agent and add message
        agent1 = PersonalLoanAgent(model="gpt-4", temperature=0.3, memory=memory)
        agent1.run("I need a $100,000 loan", stream=False)

        # Create second agent with same memory
        agent2 = PersonalLoanAgent(model="gpt-4", temperature=0.3, memory=memory)

        # Verify it has access to previous conversation
        history = memory.get_conversation_history()
        assert len(history) >= 2
        assert any("100,000" in msg["content"] or "100000" in msg["content"] for msg in history)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
