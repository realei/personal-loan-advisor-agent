"""
DeepEval configuration file
Centralized management of all evaluation-related configurations
"""

from typing import Dict, List, Any
import os


# ============= DeepEval Configuration =============

# Model used for DeepEval evaluation
# Can be configured in .env via DEEPEVAL_MODEL, defaults to gpt-4o-mini
EVAL_MODEL = os.getenv("DEEPEVAL_MODEL", "gpt-4o-mini")

# API key (if needed)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Model used by Agent (for conversation and tool calls)
# Can be configured in .env via AGENT_MODEL, defaults to gpt-4o-mini
AGENT_MODEL = os.getenv("AGENT_MODEL", "gpt-4o-mini")

# Evaluation thresholds - can be configured via environment variables, uses defaults if not set
METRIC_THRESHOLDS = {
    "answer_relevancy": float(os.getenv("EVAL_THRESHOLD_ANSWER_RELEVANCY", "0.7")),
    "faithfulness": float(os.getenv("EVAL_THRESHOLD_FAITHFULNESS", "0.75")),
    "hallucination": float(os.getenv("EVAL_THRESHOLD_HALLUCINATION", "0.3")),
    "bias": float(os.getenv("EVAL_THRESHOLD_BIAS", "0.3")),
    "toxicity": float(os.getenv("EVAL_THRESHOLD_TOXICITY", "0.2")),
    "contextual_relevancy": float(os.getenv("EVAL_THRESHOLD_CONTEXTUAL_RELEVANCY", "0.7")),
    "contextual_precision": float(os.getenv("EVAL_THRESHOLD_CONTEXTUAL_PRECISION", "0.7")),
    "contextual_recall": float(os.getenv("EVAL_THRESHOLD_CONTEXTUAL_RECALL", "0.7")),
}

# Custom metric thresholds - can be configured via environment variables
CUSTOM_THRESHOLDS = {
    "tool_accuracy": float(os.getenv("EVAL_THRESHOLD_TOOL_ACCURACY", "0.8")),
    "parameter_correctness": float(os.getenv("EVAL_THRESHOLD_PARAMETER_CORRECTNESS", "0.9")),
    "response_time": float(os.getenv("EVAL_THRESHOLD_RESPONSE_TIME", "15.0")),
    "token_limit": int(os.getenv("EVAL_THRESHOLD_TOKEN_LIMIT", "5000")),
    "tool_chain_logic": float(os.getenv("EVAL_THRESHOLD_TOOL_CHAIN_LOGIC", "0.85")),
}

# Expected tool mapping
EXPECTED_TOOLS_MAP = {
    # Payment calculation keywords
    "calculate monthly payment": ["calculate_loan_payment"],
    "calculate repayment": ["calculate_loan_payment"],
    "how much monthly payment": ["calculate_loan_payment"],
    "monthly repayment": ["calculate_loan_payment"],
    "calculate payment": ["calculate_loan_payment"],
    "monthly payment": ["calculate_loan_payment"],
    "what's the monthly payment": ["calculate_loan_payment"],
    "how much per month": ["calculate_loan_payment"],

    # Eligibility check keywords
    "check eligibility": ["check_loan_eligibility"],
    "am I qualified": ["check_loan_eligibility"],
    "can I get loan": ["check_loan_eligibility"],
    "loan qualification": ["check_loan_eligibility"],
    "loan eligibility": ["check_loan_eligibility"],
    "do I qualify": ["check_loan_eligibility"],
    "eligible for loan": ["check_loan_eligibility"],

    # Affordability keywords
    "can afford": ["check_loan_affordability"],
    "is it affordable": ["check_loan_affordability"],
    "affordability capacity": ["check_loan_affordability"],
    "affordability": ["check_loan_affordability"],
    "can I afford": ["check_loan_affordability"],
    "within budget": ["check_loan_affordability"],

    # Loan comparison keywords
    "compare loans": ["compare_loan_terms"],
    "compare terms": ["compare_loan_terms"],
    "which is better": ["compare_loan_terms"],
    "which option": ["compare_loan_terms"],
    "loan comparison": ["compare_loan_terms"],

    # Payment schedule keywords
    "payment schedule": ["generate_payment_schedule"],
    "payment details": ["generate_payment_schedule"],
    "installment schedule": ["generate_payment_schedule"],
    "amortization schedule": ["generate_payment_schedule"],
    "payment breakdown": ["generate_payment_schedule"],

    # Maximum loan keywords
    "maximum loan": ["calculate_max_affordable_loan"],
    "maximum can borrow": ["calculate_max_affordable_loan"],
    "loan limit": ["calculate_max_affordable_loan"],
    "max loan amount": ["calculate_max_affordable_loan"],
    "how much can I borrow": ["calculate_max_affordable_loan"],

    # Composite scenarios
    "check eligibility and calculate": ["check_loan_eligibility", "calculate_loan_payment"],
    "calculate and evaluate": ["calculate_loan_payment", "check_loan_affordability"],
    "comprehensive analysis": ["check_loan_eligibility", "calculate_loan_payment", "check_loan_affordability"],
    "full evaluation": ["check_loan_eligibility", "calculate_loan_payment", "check_loan_affordability"],
}

# Parameter validation rules
PARAMETER_VALIDATION_RULES = {
    "calculate_loan_payment": {
        "loan_amount": {
            "type": "number",
            "min": 1000,
            "max": 10000000,
            "required": True
        },
        "annual_interest_rate": {
            "type": "number",
            "min": 0.001,
            "max": 0.5,  # Must be decimal form, not percentage
            "required": True,
            "format": "decimal"  # Special marker: must be decimal
        },
        "loan_term_months": {
            "type": "integer",
            "min": 1,
            "max": 360,
            "required": True
        }
    },
    "check_loan_eligibility": {
        "age": {
            "type": "integer",
            "min": 18,
            "max": 100,
            "required": True
        },
        "monthly_income": {
            "type": "number",
            "min": 0,
            "required": True
        },
        "credit_score": {
            "type": "integer",
            "min": 300,
            "max": 850,
            "required": True
        },
        "requested_loan_amount": {
            "type": "number",
            "min": 1000,
            "required": True
        },
        "employment_status": {
            "type": "string",
            "enum": ["full_time", "part_time", "self_employed", "unemployed", "retired"],
            "required": True
        }
    },
    "check_loan_affordability": {
        "loan_amount": {
            "type": "number",
            "min": 1000,
            "required": True
        },
        "annual_interest_rate": {
            "type": "number",
            "min": 0.001,
            "max": 0.5,
            "required": True,
            "format": "decimal"
        },
        "loan_term_months": {
            "type": "integer",
            "min": 1,
            "max": 360,
            "required": True
        },
        "monthly_income": {
            "type": "number",
            "min": 0,
            "required": True
        },
        "existing_monthly_debt": {
            "type": "number",
            "min": 0,
            "required": False,
            "default": 0
        }
    }
}

# Performance benchmarks (based on actual agent performance)
PERFORMANCE_BENCHMARKS = {
    "response_time": {
        "excellent": 5.0,    # seconds
        "good": 8.0,         # Based on actual data: average 8.64 seconds
        "acceptable": 15.0,  # Threshold set to 15 seconds
        "poor": 30.0         # Over 30 seconds is too slow
    },
    "token_usage": {
        "excellent": 2000,
        "good": 3500,        # Based on actual data: average 3512 tokens
        "acceptable": 5000,  # Threshold set to 5000
        "poor": 8000
    },
    "tool_calls": {
        "simple_query": 1,      # Simple query should only call 1 tool
        "moderate_query": 2,    # Moderate query 2 tools
        "complex_query": 3,     # Complex query 3 tools
        "max_allowed": 5        # Maximum of 5 tools
    }
}

# Test data filter criteria
TEST_DATA_FILTERS = {
    "recent": {
        "hours": 24,
        "limit": 20
    },
    "performance": {
        "hours": 168,  # One week
        "limit": 100
    },
    "quality": {
        "hours": 48,
        "limit": 30
    }
}

# Report configuration
REPORT_CONFIG = {
    "include_details": True,
    "include_metrics": True,
    "include_tools": True,
    "include_performance": True,
    "output_format": "markdown",  # Options: markdown, json, html
    "save_to_file": False,
    "file_path": "evaluation_report.md"
}

# Test suite definitions
TEST_SUITES = {
    "basic_quality": {
        "name": "Basic Quality Test",
        "metrics": ["answer_relevancy", "faithfulness"],
        "required": True
    },
    "advanced_quality": {
        "name": "Advanced Quality Test",
        "metrics": ["hallucination", "bias", "toxicity"],
        "required": False
    },
    "context_evaluation": {
        "name": "Context Evaluation",
        "metrics": ["contextual_relevancy", "contextual_precision"],
        "required": False
    },
    "tool_evaluation": {
        "name": "Tool Evaluation",
        "metrics": ["tool_accuracy", "parameter_correctness"],
        "required": True
    },
    "performance": {
        "name": "Performance Evaluation",
        "metrics": ["response_time", "token_usage"],
        "required": True
    }
}

# CI/CD configuration
CI_CONFIG = {
    "fail_on_threshold_breach": True,  # Fail when below threshold
    "parallel_execution": True,        # Execute tests in parallel
    "max_workers": 4,                  # Maximum parallel workers
    "retry_failed": True,              # Retry failed tests
    "max_retries": 2,                  # Maximum retry attempts
    "generate_report": True,           # Generate test report
    "upload_results": False            # Upload results to external service
}


# ============= Helper Functions =============

def get_threshold(metric_name: str) -> float:
    """Get metric threshold"""
    if metric_name in METRIC_THRESHOLDS:
        return METRIC_THRESHOLDS[metric_name]
    elif metric_name in CUSTOM_THRESHOLDS:
        return CUSTOM_THRESHOLDS[metric_name]
    else:
        return 0.7  # Default threshold


def get_expected_tools(input_text: str) -> List[str]:
    """Get expected tools based on input text"""
    expected_tools = []
    input_lower = input_text.lower()

    for pattern, tools in EXPECTED_TOOLS_MAP.items():
        if pattern.lower() in input_lower:
            expected_tools.extend(tools)

    # Deduplicate and return
    return list(set(expected_tools))


def validate_parameter(func_name: str, param_name: str, param_value: Any) -> bool:
    """Validate a single parameter"""
    if func_name not in PARAMETER_VALIDATION_RULES:
        return True  # Functions without defined rules pass by default

    rules = PARAMETER_VALIDATION_RULES[func_name].get(param_name, {})

    if not rules:
        return True  # Parameters without defined rules pass by default

    # Type checking
    param_type = rules.get("type")
    if param_type == "number":
        if not isinstance(param_value, (int, float)):
            return False
    elif param_type == "integer":
        if not isinstance(param_value, int):
            return False
    elif param_type == "string":
        if not isinstance(param_value, str):
            return False

    # Range checking
    if "min" in rules and param_value < rules["min"]:
        return False
    if "max" in rules and param_value > rules["max"]:
        return False

    # Enum checking
    if "enum" in rules and param_value not in rules["enum"]:
        return False

    # Special format checking
    if rules.get("format") == "decimal":
        # Check if it's in decimal form (0.05 instead of 5)
        if param_type == "number" and param_value >= 1:
            return False  # Interest rate should not be greater than or equal to 1

    return True


def get_performance_rating(metric: str, value: float) -> str:
    """Get performance rating"""
    if metric not in PERFORMANCE_BENCHMARKS:
        return "unknown"

    benchmarks = PERFORMANCE_BENCHMARKS[metric]

    if metric in ["response_time", "token_usage"]:
        # Lower is better
        if value <= benchmarks["excellent"]:
            return "excellent"
        elif value <= benchmarks["good"]:
            return "good"
        elif value <= benchmarks["acceptable"]:
            return "acceptable"
        else:
            return "poor"
    else:
        # Special handling
        return "unknown"


def format_test_result(metric_name: str, score: float, passed: bool, details: str = "") -> str:
    """Format test result"""
    status = "✅" if passed else "❌"
    threshold = get_threshold(metric_name)

    result = f"{status} {metric_name}: {score:.2%}"

    if not passed:
        result += f" (threshold: {threshold:.2%})"

    if details:
        result += f"\n   {details}"

    return result