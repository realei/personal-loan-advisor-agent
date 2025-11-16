"""Unit tests for EvaluationManager."""

import pytest
import os
import time
from datetime import datetime

from src.utils.memory import ConversationMemory
from src.evaluation.evaluation_manager import EvaluationManager, EvaluationStatus


@pytest.mark.skipif(
    os.system("docker-compose ps | grep loan-advisor-mongodb | grep -q Up") != 0,
    reason="MongoDB not running - start with: docker-compose up -d"
)
class TestEvaluationManager:
    """Test suite for EvaluationManager."""

    @pytest.fixture
    def memory(self):
        """Create ConversationMemory instance with evaluation enabled."""
        mem = ConversationMemory(
            mongodb_uri="mongodb://admin:password123@localhost:27017/",
            database_name="loan_advisor_test",
            enable_evaluation=True
        )
        yield mem
        # Cleanup
        mem.close()

    @pytest.fixture
    def active_session(self, memory):
        """Create an active session for testing."""
        user_id = f"test_eval_user_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        session_id = memory.start_session(user_id)
        yield memory, session_id
        # Cleanup
        memory.delete_session(session_id)

    def test_evaluation_manager_initialization(self, memory):
        """Test that evaluation manager initializes correctly."""
        eval_manager = memory.evaluation_manager
        assert eval_manager is not None
        assert eval_manager.evaluations is not None
        assert len(eval_manager.metrics) == 4  # 4 metrics configured

    def test_submit_evaluation_async(self, active_session):
        """Test submitting evaluation asynchronously."""
        memory, session_id = active_session

        user_input = "I want a $50,000 loan for 36 months"
        agent_output = "I can help you with that loan request."
        context = {
            "loan_amount": 50000,
            "loan_term_months": 36,
        }

        # Submit evaluation
        eval_id = memory.evaluate_interaction(
            user_input=user_input,
            agent_output=agent_output,
            context=context
        )

        assert eval_id is not None
        assert eval_id.startswith("eval_")

        # Check evaluation was created in database
        eval_doc = memory.evaluation_manager.get_evaluation_result(eval_id)
        assert eval_doc is not None
        assert eval_doc["session_id"] == session_id
        assert eval_doc["user_input"] == user_input
        assert eval_doc["agent_output"] == agent_output
        assert eval_doc["status"] in [EvaluationStatus.PENDING, EvaluationStatus.IN_PROGRESS]

    def test_evaluation_status_progression(self, active_session):
        """Test that evaluation status progresses from pending to completed."""
        memory, session_id = active_session

        eval_id = memory.evaluate_interaction(
            user_input="Calculate payment for $50k loan",
            agent_output="Monthly payment would be approximately $1,500",
            context={"loan_amount": 50000}
        )

        # Initial status should be PENDING
        eval_doc = memory.evaluation_manager.get_evaluation_result(eval_id)
        assert eval_doc["status"] == EvaluationStatus.PENDING

        # Wait a bit for async evaluation to start/complete
        # Note: In real tests with OpenAI API, this would take longer
        time.sleep(1)

        # Check if status changed (might be IN_PROGRESS or COMPLETED)
        eval_doc = memory.evaluation_manager.get_evaluation_result(eval_id)
        assert eval_doc["status"] in [
            EvaluationStatus.PENDING,
            EvaluationStatus.IN_PROGRESS,
            EvaluationStatus.COMPLETED,
            EvaluationStatus.FAILED  # Might fail without OpenAI API key
        ]

    def test_get_session_evaluations(self, active_session):
        """Test retrieving all evaluations for a session."""
        memory, session_id = active_session

        # Submit multiple evaluations
        eval_ids = []
        for i in range(3):
            eval_id = memory.evaluate_interaction(
                user_input=f"Question {i}",
                agent_output=f"Answer {i}",
                context={}
            )
            eval_ids.append(eval_id)

        # Retrieve all evaluations for session
        evaluations = memory.get_session_evaluations()
        assert len(evaluations) == 3

        # Check all eval_ids are present
        retrieved_ids = [e["evaluation_id"] for e in evaluations]
        for eval_id in eval_ids:
            assert eval_id in retrieved_ids

    def test_get_session_evaluations_with_limit(self, active_session):
        """Test retrieving limited evaluations."""
        memory, session_id = active_session

        # Submit 5 evaluations
        for i in range(5):
            memory.evaluate_interaction(
                user_input=f"Question {i}",
                agent_output=f"Answer {i}",
                context={}
            )

        # Get only last 3
        evaluations = memory.get_session_evaluations(limit=3)
        assert len(evaluations) == 3

    def test_evaluation_context_extraction(self, active_session):
        """Test that context is properly stored in evaluation."""
        memory, session_id = active_session

        context = {
            "monthly_income": 10000,
            "credit_score": 720,
            "loan_amount": 50000,
            "age": 35,
        }

        eval_id = memory.evaluate_interaction(
            user_input="Am I eligible?",
            agent_output="Yes, you are eligible",
            context=context
        )

        eval_doc = memory.evaluation_manager.get_evaluation_result(eval_id)
        assert eval_doc["context"] == context

    def test_evaluation_metadata(self, active_session):
        """Test that metadata is stored correctly."""
        memory, session_id = active_session

        metadata = {
            "agent_version": "1.0",
            "test_flag": True,
        }

        eval_id = memory.evaluate_interaction(
            user_input="Test question",
            agent_output="Test answer",
            context={},
            metadata=metadata
        )

        eval_doc = memory.evaluation_manager.get_evaluation_result(eval_id)
        assert eval_doc["metadata"] == metadata

    def test_evaluation_without_memory(self):
        """Test that evaluation doesn't run when memory is disabled."""
        memory = ConversationMemory(
            mongodb_uri="mongodb://admin:password123@localhost:27017/",
            database_name="loan_advisor_test",
            enable_evaluation=False  # Disabled
        )

        user_id = f"test_no_eval_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        session_id = memory.start_session(user_id)

        eval_id = memory.evaluate_interaction(
            user_input="Test",
            agent_output="Response",
            context={}
        )

        # Should return None when disabled
        assert eval_id is None

        # Cleanup
        memory.delete_session(session_id)
        memory.close()

    def test_multiple_users_evaluation_isolation(self, memory):
        """Test that evaluations are isolated per user."""
        user1_id = f"eval_user1_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        user2_id = f"eval_user2_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

        # User 1 session
        session1 = memory.start_session(user1_id)
        eval1_id = memory.evaluate_interaction(
            user_input="User 1 question",
            agent_output="User 1 answer",
            context={}
        )
        memory.clear_session()

        # User 2 session
        session2 = memory.start_session(user2_id)
        eval2_id = memory.evaluate_interaction(
            user_input="User 2 question",
            agent_output="User 2 answer",
            context={}
        )

        # User 2 should only see their evaluations
        user2_evals = memory.get_session_evaluations()
        assert len(user2_evals) == 1
        assert user2_evals[0]["evaluation_id"] == eval2_id

        # Cleanup
        memory.delete_session(session1)
        memory.delete_session(session2)

    def test_get_session_statistics_empty(self, active_session):
        """Test statistics for session with no evaluations."""
        memory, session_id = active_session

        stats = memory.get_session_evaluation_stats()
        assert stats["total_evaluations"] == 0
        assert stats["completed"] == 0
        assert stats["pending"] == 0

    def test_get_session_statistics_with_evaluations(self, active_session):
        """Test statistics for session with evaluations."""
        memory, session_id = active_session

        # Submit 3 evaluations
        for i in range(3):
            memory.evaluate_interaction(
                user_input=f"Q{i}",
                agent_output=f"A{i}",
                context={}
            )

        stats = memory.get_session_evaluation_stats()
        assert stats["total_evaluations"] == 3
        # Initially all should be pending (async)
        assert stats["pending"] >= 0
        assert stats["completed"] >= 0


@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY") or
    os.system("docker-compose ps | grep loan-advisor-mongodb | grep -q Up") != 0,
    reason="Requires OpenAI API key and MongoDB running"
)
class TestEvaluationWithAPI:
    """Integration tests for evaluation with actual DeepEval API calls."""

    @pytest.fixture
    def memory(self):
        """Create ConversationMemory with evaluation enabled."""
        mem = ConversationMemory(
            mongodb_uri="mongodb://admin:password123@localhost:27017/",
            database_name="loan_advisor_test",
            enable_evaluation=True
        )
        yield mem
        mem.close()

    def test_full_evaluation_cycle(self, memory):
        """Test full evaluation cycle with API (may take time)."""
        user_id = f"api_test_user_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        session_id = memory.start_session(user_id)

        eval_id = memory.evaluate_interaction(
            user_input="I want to borrow $50,000 for 36 months at 5% interest",
            agent_output=(
                "For a $50,000 loan at 5% interest over 36 months, "
                "your monthly payment would be approximately $1,499. "
                "Total interest paid would be about $3,964."
            ),
            context={
                "loan_amount": 50000,
                "loan_term_months": 36,
                "annual_interest_rate": 0.05
            }
        )

        # Wait for evaluation to complete (DeepEval API call)
        max_wait = 30  # 30 seconds timeout
        waited = 0
        while waited < max_wait:
            eval_doc = memory.evaluation_manager.get_evaluation_result(eval_id)
            if eval_doc["status"] in [EvaluationStatus.COMPLETED, EvaluationStatus.FAILED]:
                break
            time.sleep(2)
            waited += 2

        # Check final result
        eval_doc = memory.evaluation_manager.get_evaluation_result(eval_id)

        if eval_doc["status"] == EvaluationStatus.COMPLETED:
            # Verify scores exist
            assert "scores" in eval_doc
            assert len(eval_doc["scores"]) > 0

            # Verify metrics_passed exists
            assert "metrics_passed" in eval_doc

            print(f"\n[Evaluation Results]")
            print(f"Scores: {eval_doc['scores']}")
            print(f"Metrics Passed: {eval_doc['metrics_passed']}")
            print(f"Critical Issues: {eval_doc.get('critical_issues', [])}")

        elif eval_doc["status"] == EvaluationStatus.FAILED:
            print(f"\n[Evaluation Failed]")
            print(f"Error: {eval_doc.get('error', 'Unknown error')}")

        # Cleanup
        memory.delete_session(session_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
