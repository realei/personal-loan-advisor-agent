"""
Personal Loan Advisor Agent Evaluation using DeepEval.

This test evaluates the loan_advisor_agent by:
1. Running predefined test cases through the agent
2. Evaluating with both reference-based and reference-free metrics
3. Checking expected tools, arguments, and outputs

Following DeepEval best practices with SOLID principles.
"""

import pytest
from typing import List, Dict, Any

from deepeval import evaluate, assert_test
from deepeval.dataset import EvaluationDataset, Golden
from deepeval.metrics import (
    AnswerRelevancyMetric,
    FaithfulnessMetric,
    HallucinationMetric,
)
from deepeval.test_case import LLMTestCase

from src.agent.loan_advisor_agent import loan_advisor_agent


# ============================================================================
# Test Cases Definition
# ============================================================================

TEST_CASES = [
    {
        "id": "loan_calculation_basic",
        "input": "Calculate my monthly payment for a $50,000 loan "
                 "at 5% annual interest rate for 36 months.",
        "expected_output_contains": ["1,498", "1498", "monthly payment"],
    },
    {
        "id": "eligibility_check",
        "input": "Check my loan eligibility: I'm 25 years old, "
                 "monthly income $6000, credit score 680, "
                 "requesting $30,000 loan for 36 months. "
                 "I work full-time and have been employed for 3 years.",
        "expected_output_contains": ["eligible", "qualify", "approved", "congratulations"],
    },
]


# ============================================================================
# Agent Runner
# ============================================================================

class AgentRunner:
    """Runs test cases through the loan_advisor_agent."""

    def __init__(self, agent):
        self.agent = agent

    def run_test_case(self, test_input: str) -> Dict[str, Any]:
        """
        Run a test case through the agent.

        Returns:
            Dict with:
            - actual_output: Agent's response
            - tools_called: List of tool names called
            - tool_calls_with_args: List of dicts with tool names and arguments
            - retrieval_context: List of tool results (re-executed)
            - context: Extracted context (user intent + tool results)
        """
        # Create a unique session for this test
        import uuid
        import json
        session_id = f"test_{uuid.uuid4().hex[:8]}"

        # Run agent
        response = self.agent.run(
            input=test_input,
            session_id=session_id,
            stream=False,
        )

        # Extract response content
        actual_output = response.content if hasattr(response, 'content') else str(response)

        # Extract tools called and arguments from messages
        tools_called = []
        tool_calls_with_args = []

        if hasattr(response, 'messages'):
            for msg in response.messages:
                # Extract tool calls (they are dicts)
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    for tc in msg.tool_calls:
                        if isinstance(tc, dict) and 'function' in tc:
                            function_name = tc['function'].get('name')
                            if function_name:
                                tools_called.append(function_name)

                                # Extract arguments
                                arguments_str = tc['function'].get('arguments', '{}')
                                try:
                                    arguments = json.loads(arguments_str)
                                except json.JSONDecodeError:
                                    arguments = {}

                                tool_calls_with_args.append({
                                    'name': function_name,
                                    'arguments': arguments
                                })

        # ✨ Re-execute tool calls to get retrieval context
        # This is what Faithfulness/Hallucination metrics need
        retrieval_context = self._reconstruct_context(tool_calls_with_args)

        return {
            "actual_output": actual_output,
            "tools_called": tools_called,
            "tool_calls_with_args": tool_calls_with_args,
            "retrieval_context": retrieval_context,
        }

    def _reconstruct_context(self, tool_calls_with_args: list) -> list:
        """
        Reconstruct retrieval_context by re-executing tool calls.

        This provides accurate retrieval_context for Faithfulness/Hallucination metrics.
        Re-executes tools with the same arguments the agent used.
        """
        import json
        from dataclasses import asdict, is_dataclass
        retrieval_context = []

        # Import the underlying tool classes (not the decorated functions)
        from src.tools.loan_eligibility import LoanEligibilityTool, ApplicantInfo, EmploymentStatus
        from src.tools.loan_calculator import LoanCalculatorTool, LoanRequest
        from src.utils.config import config

        # Initialize tool instances
        eligibility_checker = LoanEligibilityTool(
            min_age=config.loan.min_age,
            max_age=config.loan.max_age,
            min_monthly_income=config.loan.min_income,
            min_credit_score=config.loan.min_credit_score,
            max_dti_ratio=config.loan.max_dti_ratio,
            min_employment_length=1.0,
            max_loan_amount=config.loan.max_loan_amount,
        )
        loan_calculator = LoanCalculatorTool(max_dti_ratio=config.loan.max_dti_ratio)

        def serialize_result(result):
            """Serialize tool result to JSON string, handling both Pydantic models and dataclasses."""
            if hasattr(result, 'model_dump'):
                # Pydantic model
                return json.dumps(result.model_dump())
            elif is_dataclass(result):
                # Dataclass
                result_dict = asdict(result)
                # Handle pandas DataFrame in AmortizationSchedule
                if 'schedule' in result_dict and hasattr(result_dict['schedule'], 'to_dict'):
                    result_dict['schedule'] = result_dict['schedule'].to_dict(orient='records')
                return json.dumps(result_dict, default=str)
            else:
                # Fallback
                return json.dumps(str(result))

        for tool_call in tool_calls_with_args:
            tool_name = tool_call['name']
            arguments = tool_call['arguments']

            try:
                # Re-execute the tool based on tool name
                if tool_name == 'check_loan_eligibility':
                    applicant = ApplicantInfo(
                        age=arguments['age'],
                        monthly_income=arguments['monthly_income'],
                        credit_score=arguments['credit_score'],
                        employment_status=EmploymentStatus(arguments['employment_status']),
                        employment_length_years=arguments['employment_length_years'],
                        monthly_debt_obligations=arguments.get('monthly_debt_obligations', 0.0),
                        has_existing_loans=arguments.get('has_existing_loans', False),
                        previous_defaults=arguments.get('previous_defaults', False),
                    )
                    result = eligibility_checker.check_eligibility(
                        applicant=applicant,
                        requested_loan_amount=arguments['requested_loan_amount'],
                        loan_term_months=arguments['loan_term_months'],
                    )
                    retrieval_context.append(serialize_result(result))

                elif tool_name == 'calculate_loan_payment':
                    loan_request = LoanRequest(
                        loan_amount=arguments['loan_amount'],
                        annual_interest_rate=arguments['annual_interest_rate'],
                        loan_term_months=arguments['loan_term_months'],
                    )
                    result = loan_calculator.calculate_monthly_payment(loan_request)
                    retrieval_context.append(serialize_result(result))

                elif tool_name == 'check_loan_affordability':
                    loan_request = LoanRequest(
                        loan_amount=arguments.get('loan_amount', 0),
                        annual_interest_rate=arguments.get('annual_interest_rate', 0),
                        loan_term_months=arguments.get('loan_term_months', 1),
                    )
                    result = loan_calculator.check_affordability(
                        loan_request=loan_request,
                        monthly_income=arguments['monthly_income'],
                        monthly_debt_obligations=arguments['monthly_debt_obligations'],
                        proposed_monthly_payment=arguments.get('proposed_monthly_payment'),
                    )
                    retrieval_context.append(serialize_result(result))

                elif tool_name == 'compare_loan_terms':
                    loan_request = LoanRequest(
                        loan_amount=arguments['loan_amount'],
                        annual_interest_rate=arguments['annual_interest_rate'],
                        loan_term_months=arguments['loan_term_months'],
                    )
                    result = loan_calculator.compare_loan_options(
                        loan_request=loan_request,
                        alternative_terms=arguments.get('alternative_terms', [48, 60]),
                    )
                    retrieval_context.append(serialize_result(result))

                elif tool_name == 'calculate_max_affordable_loan':
                    result = loan_calculator.calculate_max_loan_amount(
                        monthly_income=arguments['monthly_income'],
                        monthly_debt_obligations=arguments['monthly_debt_obligations'],
                        annual_interest_rate=arguments['annual_interest_rate'],
                        loan_term_months=arguments['loan_term_months'],
                    )
                    retrieval_context.append(serialize_result(result))

                elif tool_name == 'generate_payment_schedule':
                    loan_request = LoanRequest(
                        loan_amount=arguments['loan_amount'],
                        annual_interest_rate=arguments['annual_interest_rate'],
                        loan_term_months=arguments['loan_term_months'],
                    )
                    result = loan_calculator.generate_amortization_schedule(loan_request)
                    retrieval_context.append(serialize_result(result))

            except Exception as e:
                # If tool execution fails, add error message
                error_msg = f"Tool {tool_name} failed: {str(e)}"
                retrieval_context.append(error_msg)

        return retrieval_context


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def agent_runner():
    """Provide AgentRunner instance."""
    return AgentRunner(loan_advisor_agent)


@pytest.fixture(scope="session")
def evaluation_dataset(agent_runner) -> EvaluationDataset:
    """
    Create EvaluationDataset by running test cases through agent.

    This follows DeepEval's pattern:
    - Define test cases with expected outputs
    - Run through agent to get actual outputs
    - Create Goldens for evaluation
    """
    goldens = []

    for tc in TEST_CASES:
        print(f"\n🤖 Running test case: {tc['id']}")

        # Run through agent
        result = agent_runner.run_test_case(tc["input"])

        # Create Golden with both expected and actual outputs
        golden = Golden(
            input=tc["input"],
            actual_output=result["actual_output"],
            expected_output=" ".join(tc.get("expected_output_contains", [])),
            # retrieval_context: for Faithfulness/Hallucination metrics
            retrieval_context=result["retrieval_context"],
            additional_metadata={
                "test_id": tc["id"],
                "expected_output_contains": tc.get("expected_output_contains", []),
                # Extract from agent response
                "actual_tools_called": result["tools_called"],
                "actual_tool_calls_with_args": result["tool_calls_with_args"],
            }
        )
        goldens.append(golden)

    return EvaluationDataset(goldens=goldens)


@pytest.fixture(scope="session")
def reference_free_metrics():
    """Metrics that don't require expected_output."""
    return [
        AnswerRelevancyMetric(threshold=0.7),
        FaithfulnessMetric(threshold=0.7),
        HallucinationMetric(threshold=0.5),
    ]


# ============================================================================
# Test Functions
# ============================================================================

def test_agent_with_reference_free_metrics(
    evaluation_dataset: EvaluationDataset,
    reference_free_metrics
):
    """
    Test agent with reference-free metrics.

    These metrics don't require expected_output:
    - AnswerRelevancy: Is the answer relevant to the question?
    - Faithfulness: Is the answer based on the context?
    - Hallucination: Does the answer contain hallucinated information?
    """
    test_cases = [
        LLMTestCase(
            input=g.input,
            actual_output=g.actual_output,
            # context: for HallucinationMetric
            context=g.retrieval_context,
            # retrieval_context: for FaithfulnessMetric
            retrieval_context=g.retrieval_context,
        )
        for g in evaluation_dataset.goldens
    ]

    # Evaluate
    evaluate(test_cases=test_cases, metrics=reference_free_metrics)

    print("\n" + "="*80)
    print("✅ Reference-Free Metrics Evaluation Complete")
    print("="*80)


def test_tool_calls_info(evaluation_dataset: EvaluationDataset):
    """
    Display information about tools called and their arguments.

    This test shows what tools were called and with what arguments,
    extracted automatically from the agent's response.
    """
    print("\n" + "="*80)
    print("🔧 Tool Calls Information")
    print("="*80)

    for golden in evaluation_dataset.goldens:
        metadata = golden.additional_metadata
        test_id = metadata["test_id"]
        actual_tools = metadata["actual_tools_called"]
        tool_calls_with_args = metadata["actual_tool_calls_with_args"]

        print(f"\n📋 Test Case: {test_id}")
        print(f"  Tools Called: {actual_tools}")

        for tool_call in tool_calls_with_args:
            print(f"\n  🔧 Tool: {tool_call['name']}")
            print(f"     Arguments:")
            for arg_name, arg_value in tool_call['arguments'].items():
                print(f"       - {arg_name}: {arg_value}")

    print("\n" + "="*80)
    print("✅ Tool call information extracted successfully")
    print("="*80)


def test_expected_output_keywords(evaluation_dataset: EvaluationDataset):
    """
    Test that the agent's output contains expected keywords.

    This checks if the response mentions the important information.
    """
    print("\n" + "="*80)
    print("🔍 Output Keyword Validation")
    print("="*80)

    for idx, golden in enumerate(evaluation_dataset.goldens):
        metadata = golden.additional_metadata
        test_id = metadata["test_id"]
        expected_keywords = metadata.get("expected_output_contains", [])
        output = golden.actual_output.lower()

        print(f"\n📋 Test Case: {test_id}")
        print(f"  Expected keywords: {expected_keywords}")

        if not expected_keywords:
            print(f"  ⚠️  No expected keywords defined")
            continue

        # Check if at least one expected keyword is present
        found_keywords = [
            keyword for keyword in expected_keywords
            if keyword.lower() in output
        ]

        assert len(found_keywords) > 0, (
            f"None of the expected keywords found in output for test '{test_id}'. "
            f"Expected: {expected_keywords}, "
            f"Got: {output[:200]}..."
        )

        print(f"  ✅ Found keywords: {found_keywords}")

    print("\n" + "="*80)
    print("✅ All outputs contain expected keywords")
    print("="*80)


def test_individual_case_example(agent_runner, reference_free_metrics):
    """
    Example: Test a single case individually.

    This shows how to test one specific case if needed.
    """
    # Pick one test case
    test_case = TEST_CASES[0]

    print(f"\n🎯 Testing individual case: {test_case['id']}")

    # Run through agent
    result = agent_runner.run_test_case(test_case["input"])

    # Create test case
    llm_test_case = LLMTestCase(
        input=test_case["input"],
        actual_output=result["actual_output"],
        # context: for HallucinationMetric
        context=result["retrieval_context"],
        # retrieval_context: for FaithfulnessMetric
        retrieval_context=result["retrieval_context"],
    )

    # Evaluate with each metric
    for metric in reference_free_metrics:
        metric.measure(llm_test_case)
        print(f"  {metric.__class__.__name__}: {metric.score:.2f} "
              f"(threshold: {metric.threshold}) "
              f"{'✅ PASS' if metric.is_successful() else '❌ FAIL'}")

    # Use DeepEval's assert_test for assertions
    for metric in reference_free_metrics:
        assert_test(llm_test_case, [metric])


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    """
    Run evaluations directly without pytest.

    Usage:
        python tests/test_loan_advisor_agent.py
    """
    print("="*80)
    print("🚀 Running Loan Advisor Agent Evaluation")
    print("="*80)

    # Create runner
    runner = AgentRunner(loan_advisor_agent)

    # Run test cases and create dataset
    goldens = []
    for tc in TEST_CASES:
        print(f"\n🤖 Running: {tc['id']}")
        result = runner.run_test_case(tc["input"])

        golden = Golden(
            input=tc["input"],
            actual_output=result["actual_output"],
            expected_output=" ".join(tc["expected_output_contains"]),
            retrieval_context=result["retrieval_context"],
        )
        goldens.append(golden)

    # Create dataset
    dataset = EvaluationDataset(goldens=goldens)

    # Define metrics
    metrics = [
        AnswerRelevancyMetric(threshold=0.7),
        FaithfulnessMetric(threshold=0.7),
    ]

    # Evaluate
    test_cases_list = [
        LLMTestCase(
            input=g.input,
            actual_output=g.actual_output,
            # context: for HallucinationMetric
            context=g.retrieval_context,
            # retrieval_context: for FaithfulnessMetric
            retrieval_context=g.retrieval_context,
        )
        for g in dataset.goldens
    ]

    print("\n" + "="*80)
    print("📊 Running Evaluation")
    print("="*80)

    evaluate(test_cases=test_cases_list, metrics=metrics)

    print("\n" + "="*80)
    print("✅ Evaluation Complete")
    print("="*80)
