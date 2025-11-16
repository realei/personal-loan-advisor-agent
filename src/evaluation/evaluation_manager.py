"""Asynchronous evaluation manager using DeepEval.

This module provides 100% asynchronous evaluation of agent responses
with results stored in MongoDB.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

from deepeval.metrics import (
    AnswerRelevancyMetric,
    FaithfulnessMetric,
    HallucinationMetric,
    BiasMetric,
)
from deepeval.test_case import LLMTestCase
from deepeval import evaluate
from pymongo.collection import Collection

from src.utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)


class EvaluationStatus(str, Enum):
    """Evaluation status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class EvaluationManager:
    """Asynchronous evaluation manager for LLM responses."""

    def __init__(
        self,
        evaluations_collection: Collection,
        answer_relevancy_threshold: float = 0.7,
        faithfulness_threshold: float = 0.8,
        hallucination_threshold: float = 0.3,
        bias_threshold: float = 0.3,
        max_workers: int = 3,
    ):
        """Initialize evaluation manager.

        Args:
            evaluations_collection: MongoDB collection for storing evaluations
            answer_relevancy_threshold: Threshold for answer relevancy (0-1)
            faithfulness_threshold: Threshold for faithfulness (0-1)
            hallucination_threshold: Max acceptable hallucination score (0-1)
            bias_threshold: Max acceptable bias score (0-1)
            max_workers: Maximum number of concurrent evaluation workers
        """
        self.evaluations = evaluations_collection
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

        # Initialize DeepEval metrics
        self.metrics = {
            "answer_relevancy": AnswerRelevancyMetric(threshold=answer_relevancy_threshold),
            "faithfulness": FaithfulnessMetric(threshold=faithfulness_threshold),
            "hallucination": HallucinationMetric(threshold=hallucination_threshold),
            "bias": BiasMetric(threshold=bias_threshold),
        }

    def evaluate_async(
        self,
        session_id: str,
        user_id: str,
        user_input: str,
        agent_output: str,
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Submit evaluation task asynchronously (non-blocking).

        Args:
            session_id: Session ID this evaluation belongs to
            user_id: User ID
            user_input: User's input/query
            agent_output: Agent's response
            context: Context information (e.g., user profile, loan details)
            metadata: Additional metadata

        Returns:
            Evaluation ID for tracking
        """
        # Create evaluation record with pending status
        evaluation_id = f"eval_{session_id}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

        evaluation_doc = {
            "evaluation_id": evaluation_id,
            "session_id": session_id,
            "user_id": user_id,
            "status": EvaluationStatus.PENDING,
            "user_input": user_input,
            "agent_output": agent_output,
            "context": context or {},
            "metadata": metadata or {},
            "created_at": datetime.now(),
            "started_at": None,
            "completed_at": None,
            "scores": {},
            "metrics_passed": {},
            "critical_issues": [],
            "error": None,
        }

        self.evaluations.insert_one(evaluation_doc)

        # Submit to thread pool for async execution
        self.executor.submit(
            self._run_evaluation,
            evaluation_id,
            user_input,
            agent_output,
            context or {}
        )

        return evaluation_id

    def _run_evaluation(
        self,
        evaluation_id: str,
        user_input: str,
        agent_output: str,
        context: Dict[str, Any],
    ):
        """Run evaluation in background thread (internal method).

        Args:
            evaluation_id: Evaluation ID
            user_input: User input
            agent_output: Agent output
            context: Context information
        """
        try:
            logger.debug(f"Starting evaluation {evaluation_id}")

            # Update status to in_progress
            self.evaluations.update_one(
                {"evaluation_id": evaluation_id},
                {
                    "$set": {
                        "status": EvaluationStatus.IN_PROGRESS,
                        "started_at": datetime.now(),
                    }
                }
            )

            # Build retrieval context from user context
            retrieval_context = self._build_retrieval_context(context)

            # Create DeepEval test case
            test_case = LLMTestCase(
                input=user_input,
                actual_output=agent_output,
                retrieval_context=retrieval_context,
            )

            # Run evaluation with all metrics
            results = evaluate(
                test_cases=[test_case],
                metrics=list(self.metrics.values()),
            )

            # Extract scores
            scores = {}
            metrics_passed = {}

            # Parse results - DeepEval returns test results
            if hasattr(results, 'test_results') and results.test_results:
                test_result = results.test_results[0]

                for metric_name, metric in self.metrics.items():
                    # Find metric result
                    for metric_result in test_result.metrics_data:
                        if metric_result.name.lower().replace(" ", "_") == metric_name:
                            scores[metric_name] = metric_result.score
                            metrics_passed[metric_name] = metric_result.success
                            break

            # Identify critical issues
            critical_issues = self._identify_critical_issues(scores, metrics_passed)

            # Calculate overall pass/fail
            overall_passed = all(metrics_passed.values()) if metrics_passed else False

            logger.info(
                f"Evaluation {evaluation_id} completed - "
                f"Overall: {'PASSED' if overall_passed else 'FAILED'}, "
                f"Scores: {scores}"
            )

            # Update evaluation record with results
            self.evaluations.update_one(
                {"evaluation_id": evaluation_id},
                {
                    "$set": {
                        "status": EvaluationStatus.COMPLETED,
                        "completed_at": datetime.now(),
                        "scores": scores,
                        "metrics_passed": metrics_passed,
                        "overall_passed": overall_passed,
                        "critical_issues": critical_issues,
                    }
                }
            )

        except Exception as e:
            logger.error(f"Evaluation {evaluation_id} failed: {str(e)}", exc_info=True)

            # Update status
            self.evaluations.update_one(
                {"evaluation_id": evaluation_id},
                {
                    "$set": {
                        "status": EvaluationStatus.FAILED,
                        "completed_at": datetime.now(),
                        "error": str(e),
                    }
                }
            )

    def _build_retrieval_context(self, context: Dict[str, Any]) -> List[str]:
        """Build retrieval context from user context.

        Args:
            context: Context dictionary

        Returns:
            List of context strings
        """
        retrieval_context = []

        # Extract relevant information from context
        if "monthly_income" in context:
            retrieval_context.append(f"User monthly income: ${context['monthly_income']:,.2f}")

        if "credit_score" in context:
            retrieval_context.append(f"User credit score: {context['credit_score']}")

        if "loan_amount" in context:
            retrieval_context.append(f"Requested loan amount: ${context['loan_amount']:,.2f}")

        if "loan_term_months" in context:
            retrieval_context.append(f"Requested loan term: {context['loan_term_months']} months")

        if "age" in context:
            retrieval_context.append(f"User age: {context['age']}")

        if "employment_status" in context:
            retrieval_context.append(f"Employment status: {context['employment_status']}")

        return retrieval_context

    def _identify_critical_issues(
        self,
        scores: Dict[str, float],
        metrics_passed: Dict[str, bool]
    ) -> List[str]:
        """Identify critical issues from evaluation results.

        Args:
            scores: Metric scores
            metrics_passed: Whether each metric passed

        Returns:
            List of critical issue descriptions
        """
        issues = []

        # Check hallucination
        if "hallucination" in scores and not metrics_passed.get("hallucination", True):
            issues.append(
                f"HIGH: Hallucination detected (score: {scores['hallucination']:.2f})"
            )

        # Check bias - critical for financial services
        if "bias" in scores and not metrics_passed.get("bias", True):
            issues.append(
                f"CRITICAL: Bias detected (score: {scores['bias']:.2f}) - "
                "May violate fair lending regulations"
            )

        # Check answer relevancy
        if "answer_relevancy" in scores and not metrics_passed.get("answer_relevancy", True):
            issues.append(
                f"MEDIUM: Low answer relevancy (score: {scores['answer_relevancy']:.2f})"
            )

        # Check faithfulness
        if "faithfulness" in scores and not metrics_passed.get("faithfulness", True):
            issues.append(
                f"HIGH: Low faithfulness (score: {scores['faithfulness']:.2f}) - "
                "Response may not be grounded in context"
            )

        return issues

    def get_evaluation_result(self, evaluation_id: str) -> Optional[Dict[str, Any]]:
        """Get evaluation result by ID.

        Args:
            evaluation_id: Evaluation ID

        Returns:
            Evaluation result document or None
        """
        return self.evaluations.find_one({"evaluation_id": evaluation_id})

    def get_session_evaluations(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get all evaluations for a session.

        Args:
            session_id: Session ID
            limit: Maximum number of results

        Returns:
            List of evaluation documents
        """
        query = {"session_id": session_id}
        cursor = self.evaluations.find(query).sort("created_at", -1)

        if limit:
            cursor = cursor.limit(limit)

        return list(cursor)

    def get_session_statistics(self, session_id: str) -> Dict[str, Any]:
        """Get evaluation statistics for a session.

        Args:
            session_id: Session ID

        Returns:
            Statistics dictionary
        """
        evaluations = self.get_session_evaluations(session_id)

        if not evaluations:
            return {
                "total_evaluations": 0,
                "completed": 0,
                "pending": 0,
                "failed": 0,
                "average_scores": {},
                "pass_rate": 0.0,
                "critical_issues_count": 0,
            }

        total = len(evaluations)
        completed = sum(1 for e in evaluations if e["status"] == EvaluationStatus.COMPLETED)
        pending = sum(1 for e in evaluations if e["status"] == EvaluationStatus.PENDING)
        failed = sum(1 for e in evaluations if e["status"] == EvaluationStatus.FAILED)

        # Calculate average scores from completed evaluations
        completed_evals = [e for e in evaluations if e["status"] == EvaluationStatus.COMPLETED]

        average_scores = {}
        if completed_evals:
            all_scores = {}
            for eval_doc in completed_evals:
                for metric_name, score in eval_doc.get("scores", {}).items():
                    if metric_name not in all_scores:
                        all_scores[metric_name] = []
                    all_scores[metric_name].append(score)

            for metric_name, scores in all_scores.items():
                average_scores[metric_name] = sum(scores) / len(scores)

        # Calculate pass rate
        passed = sum(1 for e in completed_evals if e.get("overall_passed", False))
        pass_rate = (passed / completed) if completed > 0 else 0.0

        # Count critical issues
        critical_issues_count = sum(
            len(e.get("critical_issues", []))
            for e in completed_evals
        )

        return {
            "total_evaluations": total,
            "completed": completed,
            "pending": pending,
            "failed": failed,
            "average_scores": average_scores,
            "pass_rate": pass_rate,
            "critical_issues_count": critical_issues_count,
        }

    def get_user_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get evaluation statistics for a user across all sessions.

        Args:
            user_id: User ID

        Returns:
            Statistics dictionary
        """
        evaluations = list(self.evaluations.find({"user_id": user_id}))

        if not evaluations:
            return {
                "total_evaluations": 0,
                "sessions_count": 0,
                "average_scores": {},
                "pass_rate": 0.0,
            }

        completed_evals = [e for e in evaluations if e["status"] == EvaluationStatus.COMPLETED]

        # Calculate average scores
        average_scores = {}
        if completed_evals:
            all_scores = {}
            for eval_doc in completed_evals:
                for metric_name, score in eval_doc.get("scores", {}).items():
                    if metric_name not in all_scores:
                        all_scores[metric_name] = []
                    all_scores[metric_name].append(score)

            for metric_name, scores in all_scores.items():
                average_scores[metric_name] = sum(scores) / len(scores)

        # Calculate pass rate
        passed = sum(1 for e in completed_evals if e.get("overall_passed", False))
        pass_rate = (passed / len(completed_evals)) if completed_evals else 0.0

        # Count unique sessions
        unique_sessions = len(set(e["session_id"] for e in evaluations))

        return {
            "total_evaluations": len(evaluations),
            "sessions_count": unique_sessions,
            "average_scores": average_scores,
            "pass_rate": pass_rate,
        }

    def close(self):
        """Shutdown executor and cleanup."""
        self.executor.shutdown(wait=True)
