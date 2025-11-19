# Agent Evaluation Guide

## 📖 Overview

`test_loan_advisor_agent.py` uses DeepEval to comprehensively evaluate `src/agent/loan_advisor_agent.py`.

## 🎯 Core Design

### Key Features

✅ **Simplified Test Case Definition** (only requires input and expected_output_contains)
✅ **Automatically Extract** expected_tools, expected_tool_args, context **from Agent response**
✅ **Run Agent Directly in Pytest** (no separate run needed)
✅ **Hybrid Metrics** (Reference-based + Reference-free)
✅ **DeepEval Standards** (Golden, Dataset, LLMTestCase)
✅ **SOLID Principles** (concise and understandable)

## 📋 Test Case Definition

Now you only need to define:

```python
TEST_CASES = [
    {
        "id": "loan_calculation_basic",
        "input": "Calculate my monthly payment for a $50,000 loan...",
        "expected_output_contains": ["1,498", "monthly payment"],
        # ✨ No need to manually define expected_tools and expected_tool_args!
        # These are automatically extracted from Agent response
    },
]
```

### Automatically Extracted Information

`AgentRunner.run_test_case()` automatically extracts from Agent's response:

- **tools_called**: List of tool names called
  Example: `['calculate_loan_payment']`

- **tool_calls_with_args**: Tool names + parameters
  Example:
  ```python
  [{
      'name': 'calculate_loan_payment',
      'arguments': {
          'loan_amount': 50000,
          'annual_interest_rate': 0.05,
          'loan_term_months': 36
      }
  }]
  ```

- **retrieval_context**: Tool return results (obtained by re-executing tools)
  Example: `["{\"monthly_payment\": 1498.54, \"total_payment\": 53947.61, ...}"]`
  Note: This is the actual result obtained by re-executing tools (using the same parameters the Agent used), used for Faithfulness and Hallucination metrics

## 🔄 Workflow

```
1. Define test cases (only need id, input, expected_output_contains)
    ↓
2. Pytest starts, creates evaluation_dataset fixture
    ↓
3. AgentRunner runs each test case
    ↓
4. ✨ Auto extract: actual_output, tools_called, tool_args
    ↓
5. ✨ Re-execute tool calls: re-run tools with extracted parameters, obtain retrieval_context
    ↓
6. Create Golden (including auto-extracted info and retrieval_context)
    ↓
7. Create EvaluationDataset
    ↓
8. Run evaluation tests:
    - Reference-free metrics (AnswerRelevancy, Faithfulness, Hallucination)
    - Tool calls info (display auto-extracted tools and parameters)
    - Output keywords validation
    ↓
9. Generate test results
```

## 🚀 Usage

### Run All Tests

```bash
# Run all evaluation tests
uv run pytest tests/test_loan_advisor_agent.py -v -s

# Example output:
# 🤖 Running test case: loan_calculation_basic
# 🤖 Running test case: eligibility_check
#
# 🔧 Tool: calculate_loan_payment
#    Arguments:
#      - loan_amount: 50000
#      - annual_interest_rate: 0.05
#      - loan_term_months: 36
#
# ✅ Tool call information extracted successfully
# ✅ All outputs contain expected keywords
```

### Run Single Test

```bash
# View auto-extracted tool call information
uv run pytest tests/test_loan_advisor_agent.py::test_tool_calls_info -v -s

# Run reference-free metrics evaluation
uv run pytest tests/test_loan_advisor_agent.py::test_agent_with_reference_free_metrics -v -s

# Run keyword validation
uv run pytest tests/test_loan_advisor_agent.py::test_expected_output_keywords -v -s

# Test individual case example
uv run pytest tests/test_loan_advisor_agent.py::test_individual_case_example -v -s
```

### Run Python Script Directly

```bash
uv run python tests/test_loan_advisor_agent.py
```

## 📊 Evaluation Metrics

### Reference-Free Metrics (no expected_output needed)

#### 1. AnswerRelevancyMetric (Answer Relevancy)
- **Evaluates**: Whether Agent's answer is relevant to user input
- **Threshold**: 0.7
- **Description**: Uses LLM to evaluate if answer is on topic

#### 2. FaithfulnessMetric (Factual Accuracy)
- **Evaluates**: Whether Agent's answer is based on provided context (tool return results)
- **Threshold**: 0.7
- **Description**: Ensures answer doesn't include information beyond tool return results

#### 3. HallucinationMetric (Hallucination Detection)
- **Evaluates**: Whether Agent hallucinates (fabricates information)
- **Threshold**: 0.5
- **Description**: Detects if answer contains unverified information

### Custom Validation

#### 4. Tool Calls Info (Tool Call Information Display)
- **Displays**: Auto-extracted tool names and parameters
- **Example**:
  ```
  🔧 Tool: calculate_loan_payment
     Arguments:
       - loan_amount: 50000
       - annual_interest_rate: 0.05
       - loan_term_months: 36
  ```

#### 5. Expected Output Keywords (Output Keyword Validation)
- **Checks**: Whether Agent's answer contains expected keywords
- **Example**: Loan calculation results should include "1,498" or "monthly payment"

## 🏗️ Code Structure

### TEST_CASES (Global Constant)
```python
# Simplified test case definition, only need input and expected_output_contains
TEST_CASES = [
    {
        "id": "...",
        "input": "...",
        "expected_output_contains": ["keyword1", "keyword2"],
    },
]
```

### AgentRunner (Class)
```python
class AgentRunner:
    """Responsible for running test cases and automatically extracting information"""

    def run_test_case(self, test_input: str) -> Dict:
        # Run Agent
        # ✨ Auto extract: tools_called, tool_args, context
        # Return complete information
```

**Key auto-extraction code**:
```python
# 1. Extract tool calls and parameters
for tc in msg.tool_calls:
    function_name = tc['function'].get('name')
    arguments = json.loads(tc['function'].get('arguments'))
    tool_calls_with_args.append({
        'name': function_name,
        'arguments': arguments
    })

# 2. Re-execute tool calls to obtain retrieval_context
retrieval_context = self._reconstruct_context(tool_calls_with_args)
```

**Key code for tool re-execution** (`_reconstruct_context`):
```python
def _reconstruct_context(self, tool_calls_with_args: list) -> list:
    """Reconstruct retrieval_context by re-executing tool calls"""
    from dataclasses import asdict, is_dataclass
    retrieval_context = []

    # Initialize tool instances
    eligibility_checker = LoanEligibilityTool(...)
    loan_calculator = LoanCalculatorTool(...)

    # Serialization helper function (supports Pydantic models and dataclasses)
    def serialize_result(result):
        if hasattr(result, 'model_dump'):
            return json.dumps(result.model_dump())  # Pydantic
        elif is_dataclass(result):
            return json.dumps(asdict(result), default=str)  # Dataclass
        else:
            return json.dumps(str(result))

    # Re-execute each tool call
    for tool_call in tool_calls_with_args:
        tool_name = tool_call['name']
        arguments = tool_call['arguments']

        if tool_name == 'calculate_loan_payment':
            loan_request = LoanRequest(**arguments)
            result = loan_calculator.calculate_monthly_payment(loan_request)
            retrieval_context.append(serialize_result(result))
        # ... other tools

    return retrieval_context
```

### Fixtures (Pytest)
```python
@pytest.fixture(scope="session")
def agent_runner():
    # Provide AgentRunner instance

@pytest.fixture(scope="session")
def evaluation_dataset(agent_runner):
    # Run all test cases, auto-extract info, create EvaluationDataset

@pytest.fixture(scope="session")
def reference_free_metrics():
    # Define reference-free metrics
```

### Test Functions
```python
def test_agent_with_reference_free_metrics(...):
    # Evaluate using DeepEval metrics

def test_tool_calls_info(...):
    # Display auto-extracted tool call information

def test_expected_output_keywords(...):
    # Validate output keywords

def test_individual_case_example(...):
    # Individual case example
```

## 🎓 Interview Demonstration Points

### Demonstration Flow

```bash
# 1. Show simplified test case definition
# Open test_loan_advisor_agent.py, show TEST_CASES
# Emphasize: only need to define input and expected_output_contains

# 2. Run tests, show auto-extracted information
uv run pytest tests/test_loan_advisor_agent.py::test_tool_calls_info -v -s

# Output will display:
# 🔧 Tool: calculate_loan_payment
#    Arguments:
#      - loan_amount: 50000
#      - annual_interest_rate: 0.05
#      - loan_term_months: 36

# 3. Explain auto-extraction mechanism
# Show AgentRunner.run_test_case() code
# Explain how to extract tool calls and parameters from response.messages
```

### Advantages Explanation

1. **No need to manually define expected_tools and expected_tool_args**
   - Automatically extracted from Agent response
   - Reduces test case definition workload
   - More accurate (based on actual calls)

2. **Automatically obtain accurate retrieval_context**
   - Obtain actual results by re-executing tools (using Agent's parameters)
   - Not extracted from message history, but actual tool execution results
   - Ensures accuracy of Faithfulness and Hallucination metrics evaluation
   - Supports automatic serialization of Pydantic models and dataclasses

3. **Complete Visibility**
   - Can see which tools Agent called
   - Can see what parameters were passed
   - Can see actual tool return results
   - Can verify correctness of tool calls

4. **Easy to Extend**
   - Add new test case: only need input and expected keywords
   - No need to manually analyze what tools Agent will call
   - Add new tool: add corresponding branch in `_reconstruct_context`

## 🔧 Custom Configuration

### Add New Test Case (Super Simple!)

```python
TEST_CASES.append({
    "id": "new_test_case",
    "input": "Your test input here",
    "expected_output_contains": ["keyword1", "keyword2"],
    # That's it! No need to define expected_tools or expected_tool_args
})
```

### Modify Metrics Thresholds

```python
@pytest.fixture(scope="session")
def reference_free_metrics():
    return [
        AnswerRelevancyMetric(threshold=0.8),  # Increase threshold
        FaithfulnessMetric(threshold=0.75),
    ]
```

### Add New Metric

```python
from deepeval.metrics import ContextualRelevancyMetric

@pytest.fixture(scope="session")
def reference_free_metrics():
    return [
        AnswerRelevancyMetric(threshold=0.7),
        FaithfulnessMetric(threshold=0.7),
        ContextualRelevancyMetric(threshold=0.7),  # New
    ]
```

## ⚠️ Notes

1. **First Run is Slower**
   - Need to run Agent 2 times (2 test cases)
   - Each Agent call takes 5-10 seconds
   - DeepEval metrics require GPT-4 calls for evaluation

2. **OpenAI API Rate Limits**
   - DeepEval uses GPT-4 for evaluation
   - Recommended to start with a small number of test cases
   - If encountering rate limit, wait 1 minute and retry

3. **Session Scope Fixtures**
   - `evaluation_dataset` uses `scope="session"`
   - All test cases run Agent only once
   - Improves test efficiency

4. **Auto-extraction Accuracy**
   - Tool calls and parameters extracted from Agent response
   - If Agent doesn't call tools, `tools_called` will be an empty list
   - This is normal, can be used to discover Agent behavior issues

## 💡 Best Practices

### During Development
```bash
# Quick validation - check tool calls and keywords
uv run pytest tests/test_loan_advisor_agent.py::test_tool_calls_info -v
uv run pytest tests/test_loan_advisor_agent.py::test_expected_output_keywords -v
```

### Complete Evaluation
```bash
# Run all tests (including LLM metrics)
uv run pytest tests/test_loan_advisor_agent.py -v -s
```

### CI/CD Integration
```bash
# Only run quick validation in CI
pytest tests/test_loan_advisor_agent.py::test_tool_calls_info
pytest tests/test_loan_advisor_agent.py::test_expected_output_keywords

# Run complete evaluation periodically (cron job)
pytest tests/test_loan_advisor_agent.py
```

## 📚 References

- [DeepEval Documentation](https://deepeval.com/docs/evaluation-introduction)
- [DeepEval Metrics](https://deepeval.com/docs/metrics-introduction)
- [DeepEval Test Cases](https://deepeval.com/docs/evaluation-test-cases)
- [pytest Fixtures](https://docs.pytest.org/en/stable/fixture.html)

## 🎯 Summary

### Advantages Over Manual Definition

| Feature | Manual Definition | Auto Extraction + Tool Re-execution |
|------|---------|---------------------|
| **Test Case Definition** | Need to define tools, args, context | ✅ Only need input + keywords |
| **Accuracy** | May become outdated | ✅ Based on actual calls |
| **Maintenance Cost** | Need to sync updates | ✅ Auto sync |
| **Visibility** | Only see expected values | ✅ See actual calls + actual results |
| **Debugging** | Manual checking needed | ✅ Auto display |
| **Retrieval Context** | Manual construction or message extraction | ✅ Re-execute tools to obtain real results |
| **Serialization Support** | Manual handling needed | ✅ Auto handle Pydantic/dataclass |

This is why auto extraction + tool re-execution is better! 🚀
