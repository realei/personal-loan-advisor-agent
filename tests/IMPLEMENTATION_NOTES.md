# Agent Evaluation System Implementation Notes

## ✅ Completed Implementation

### Core Features

1. **Automatic Tool Call Information Extraction**
   - Automatically extract tool calls from Agent response `messages`
   - Parse tool names and JSON-formatted parameters
   - No need to manually define `expected_tools` and `expected_tool_args`

2. **Tool Re-execution Mechanism**
   - Implemented `_reconstruct_context()` method
   - Re-execute tools using extracted parameters
   - Obtain actual tool return results as `retrieval_context`
   - Used for DeepEval's Faithfulness and Hallucination metrics

3. **Intelligent Serialization Support**
   - Automatically detect result types (Pydantic model or dataclass)
   - Pydantic models: Use `model_dump()`
   - Dataclasses: Use `dataclasses.asdict()`
   - Special handling: Convert pandas DataFrame to dict
   - Uniformly convert to JSON strings

## 🔧 Technical Details

### 1. Tool Call Extraction

```python
# Extract from agent response
for msg in response.messages:
    if hasattr(msg, 'tool_calls') and msg.tool_calls:
        for tc in msg.tool_calls:
            if isinstance(tc, dict) and 'function' in tc:
                function_name = tc['function'].get('name')
                arguments_str = tc['function'].get('arguments', '{}')
                arguments = json.loads(arguments_str)

                tool_calls_with_args.append({
                    'name': function_name,
                    'arguments': arguments
                })
```

### 2. Tool Re-execution

```python
def _reconstruct_context(self, tool_calls_with_args: list) -> list:
    """Re-execute tools to obtain accurate retrieval_context"""
    from dataclasses import asdict, is_dataclass

    # Initialize tool instances
    eligibility_checker = LoanEligibilityTool(...)
    loan_calculator = LoanCalculatorTool(...)

    # Define serialization helper function
    def serialize_result(result):
        if hasattr(result, 'model_dump'):
            return json.dumps(result.model_dump())
        elif is_dataclass(result):
            result_dict = asdict(result)
            # Handle pandas DataFrame
            if 'schedule' in result_dict and hasattr(result_dict['schedule'], 'to_dict'):
                result_dict['schedule'] = result_dict['schedule'].to_dict(orient='records')
            return json.dumps(result_dict, default=str)
        else:
            return json.dumps(str(result))

    # Re-execute based on tool name
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

### 3. Key Decisions

#### Why re-execute tools instead of extracting from messages?

1. **Accuracy**: Tool's actual return values are deterministic, re-execution ensures the same results
2. **Completeness**: Messages may only contain partial information, re-execution obtains complete results
3. **Verifiability**: Can verify if tools are working properly
4. **Faithfulness Evaluation**: DeepEval's Faithfulness metric requires accurate retrieval_context

#### Why use underlying tool classes instead of decorator functions?

- `@tool` decorator returns `Function` objects that cannot be called directly
- Underlying tool classes provide real method implementations
- Can directly pass parameters and obtain results

#### Why need intelligent serialization?

- Tool return types are not uniform:
  - `LoanEligibilityResult`: Pydantic model
  - `LoanCalculation`: Dataclass
  - `AmortizationSchedule`: Dataclass containing pandas DataFrame
- Need to uniformly convert to JSON strings for DeepEval
- `default=str` handles special types (e.g., datetime)

## 📊 Test Results

### Quick Validation (No LLM Calls)

```bash
# Tool call information display
uv run pytest tests/test_loan_advisor_agent.py::test_tool_calls_info -v -s
# Result: Successfully extracted tool names and parameters, completed in 14s

# Output keyword validation
uv run pytest tests/test_loan_advisor_agent.py::test_expected_output_keywords -v -s
# Result: Successfully verified output contains expected keywords, completed in 14s
```

### Complete Evaluation (Including LLM Metrics)

```bash
uv run pytest tests/test_loan_advisor_agent.py::test_individual_case_example -v -s
# Results:
# - AnswerRelevancyMetric: 0.79 ✅ PASS
# - FaithfulnessMetric: 1.00 ✅ PASS
# - HallucinationMetric: 0.33 ✅ PASS
```

## 🎯 Advantages Summary

### Compared to Manual Definition

| Aspect | Manual Definition | Auto Extraction + Tool Re-execution |
|------|---------|---------------------|
| Test case definition | Requires 5 fields | Only 3 fields needed |
| Expected tools | Manual writing | ✅ Auto extraction |
| Tool arguments | Manual writing | ✅ Auto extraction |
| Retrieval context | Manual construction | ✅ Re-execution obtains |
| Accuracy | May become outdated | ✅ Always accurate |
| Maintenance cost | High | ✅ Low |

### Key Metrics

- **Code Simplification**: TEST_CASES definition reduced by 40% code volume
- **Accuracy Improvement**: retrieval_context 100% accurate (re-execution)
- **Development Efficiency**: Adding new test cases requires only 3 lines of code
- **Maintainability**: No need to update test cases when tool signatures change

## 🚀 Future Improvements

### Optional Optimizations

1. **Cache Tool Execution Results**
   - If the same tool call appears multiple times, can cache results
   - Reduce redundant execution time

2. **Parallel Tool Execution**
   - Multiple tool calls can be executed in parallel
   - Use `asyncio` or `concurrent.futures`

3. **Support More Tool Types**
   - Currently supports loan_calculator and loan_eligibility
   - Can add re-execution logic for more tools

4. **Enhanced Error Handling**
   - Currently only catches exceptions and logs error messages
   - Can add more detailed error information and retry mechanisms

## 📝 Lessons Learned

### Problems Encountered

1. **Problem**: `'Function' object is not callable`
   - **Cause**: Attempting to call `@tool` decorator function
   - **Solution**: Import underlying tool classes

2. **Problem**: Method name mismatch
   - **Cause**: Assumed method name doesn't match actual
   - **Solution**: Check actual class definition

3. **Problem**: `'LoanCalculation' object has no attribute 'model_dump'`
   - **Cause**: Dataclass is not a Pydantic model
   - **Solution**: Use `dataclasses.asdict()` + type detection

### Best Practices

1. **Check Type Before Serialization**
   - Use `hasattr()` to check for Pydantic
   - Use `is_dataclass()` to check for dataclass

2. **Use default=str to Handle Special Types**
   - pandas DataFrame, datetime, etc.
   - Ensure JSON serialization doesn't fail

3. **Session-scoped Fixtures**
   - Agent runs slowly (5-10 seconds/case)
   - Use `scope="session"` to run only once

## 🔗 Related Files

- `tests/test_loan_advisor_agent.py` - Main test file
- `tests/README_EVALUATION.md` - Detailed usage documentation
- `tests/SUMMARY.md` - Feature summary
- `src/tools/loan_calculator.py` - Loan calculation tool
- `src/tools/loan_eligibility.py` - Eligibility check tool

## ✅ Verification Checklist

- [x] Automatically extract tool call information
- [x] Re-execute tools to obtain retrieval_context
- [x] Support Pydantic models serialization
- [x] Support dataclasses serialization
- [x] Handle pandas DataFrame
- [x] Tool call information test passed
- [x] Output keyword validation test passed
- [x] Reference-free metrics evaluation passed
- [x] Documentation updated
