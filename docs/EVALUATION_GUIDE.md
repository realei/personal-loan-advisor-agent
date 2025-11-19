# 🎯 Agent Evaluation System User Guide

## Overview

This evaluation system directly extracts Agent's real runtime data from MongoDB and uses the DeepEval framework for multi-dimensional evaluation. **No modification to existing Agent code required**.

## Features

✅ **Get Test Data Directly from MongoDB** - Use real production data for evaluation
✅ **Support Multiple Evaluation Metrics** - Each testcase can evaluate multiple metrics simultaneously
✅ **Reference-based and Referenceless Mixed** - Flexible evaluation methods
✅ **Custom Metrics** - Domain-specific metrics like tool accuracy, parameter validation
✅ **CI/CD Integration** - Support for pytest and automated testing

## Quick Start

### 1. Run Quick Evaluation

```bash
# Evaluate 5 runs from the last 24 hours
uv run python run_evaluation.py --mode recent --hours 24 --limit 5

# Evaluate runs containing "calculate monthly payment"
uv run python run_evaluation.py --mode pattern --pattern "calculate monthly payment" --limit 3

# Generate complete report
uv run python run_evaluation.py --mode report --output evaluation_results.json
```

### 2. Run Pytest Tests

```bash
# Run all evaluation tests
uv run pytest tests/test_mongodb_deepeval.py -v

# Run quality tests only
uv run pytest tests/test_mongodb_deepeval.py::TestMongoDBDeepEval::test_recent_runs_quality -v

# Run performance benchmarks
uv run pytest tests/test_mongodb_deepeval.py -m benchmark -v

# Generate test report
uv run pytest tests/test_mongodb_deepeval.py --html=report.html
```

### 3. Generate Evaluation Report

```bash
# Generate report directly (without running tests)
uv run python tests/test_mongodb_deepeval.py report
```

## Evaluation Metrics Description

### DeepEval Standard Metrics

| Metric | Description | Threshold | Data Source |
|------|------|------|--------|
| Answer Relevancy | Relevance of answer to question | 0.7 | input vs output |
| Faithfulness | Degree of answer based on facts | 0.75 | tool_responses vs output |
| Hallucination | Fabricated information detection | 0.3↓ | Check for fabrications in output |
| Bias | Bias detection | 0.3↓ | Analyze output content |
| Contextual Relevancy | Context relevance | 0.7 | context vs output |

### Custom Agentic Metrics

| Metric | Description | Threshold | Evaluation Method |
|------|------|------|----------|
| Tool Accuracy | Tool selection accuracy | 0.8 | actual vs expected tools |
| Parameter Correctness | Parameter reasonableness | 0.9 | Referenceless validation |
| Tool Chain Logic | Tool call sequence logic | 0.85 | Sequence reasonableness check |
| Response Time | Response time | 5.0s | From metrics |
| Token Efficiency | Token usage efficiency | 4000 | Total token consumption |

## File Structure

```
evaluation/
├── evaluation_framework.py    # Evaluation framework (SOLID design)
└── live_eval_agent.py        # Real-time evaluation Agent tool

tests/
├── test_mongodb_deepeval.py  # MongoDB integration tests
├── test_agent_evaluation.py  # Original tests (updated)
└── deepeval_config.py       # Configuration file

run_evaluation.py            # Quick run script
EVALUATION_GUIDE.md         # This document
```

## Configuration

### Modify Evaluation Thresholds

Edit `tests/deepeval_config.py`:

```python
METRIC_THRESHOLDS = {
    "answer_relevancy": 0.7,    # Modify relevancy threshold
    "faithfulness": 0.75,        # Modify faithfulness threshold
    # ...
}
```

### Add Expected Tools Mapping

```python
EXPECTED_TOOLS_MAP = {
    "new keyword": ["expected_tool_name"],
    # ...
}
```

### Parameter Validation Rules

```python
PARAMETER_VALIDATION_RULES = {
    "tool_name": {
        "param_name": {
            "type": "number",
            "min": 0,
            "max": 1,
            "format": "decimal"  # Special format requirements
        }
    }
}
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Agent Evaluation

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 0 * * *'  # Run daily

jobs:
  evaluate:
    runs-on: ubuntu-latest

    services:
      mongodb:
        image: mongo:5
        ports:
          - 27017:27017

    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install uv
          uv venv
          uv pip install -r requirements.txt

      - name: Run evaluations
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          uv run pytest tests/test_mongodb_deepeval.py -v

      - name: Generate report
        if: always()
        run: |
          uv run python run_evaluation.py --mode report --output report.json

      - name: Upload report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: evaluation-report
          path: report.json
```

## Real-time Evaluation Integration

Add evaluation tools to main Agent:

```python
from evaluation.live_eval_agent import create_eval_tools

# Add evaluation tools when initializing Agent
agent = Agent(
    ...,
    tools=[
        ...existing_tools,
        *create_eval_tools()  # Add evaluation tools
    ]
)
```

Then can use in conversation:
- "Evaluate recent response quality"
- "Check session performance metrics"
- "Run performance benchmarks"

## Best Practices

### 1. Regular Evaluation
- Run benchmarks daily
- Automatic evaluation on PR
- Monitor key metric trends

### 2. Test Case Management
- Select representative cases from production data
- Regularly update expected tools mapping
- Adjust thresholds to reflect actual needs

### 3. Performance Optimization
- Monitor token usage trends
- Identify response time bottlenecks
- Optimize tool call chains

## Common Questions

### Q: How to handle evaluation failures?
A: Check failure reasons, may need to:
- Adjust thresholds (if too strict)
- Optimize Agent prompts
- Improve tool selection logic

### Q: How to add new evaluation metrics?
A: Add configuration in `deepeval_config.py`, then implement evaluation logic in tests.

### Q: How long does evaluation take?
A: Depends on number of test cases and API calls:
- Quick evaluation (5 cases): about 30 seconds
- Full test (20 cases): about 2-3 minutes
- Benchmark (100 cases): about 5-10 minutes

## Interpreting Evaluation Results

### Good Metric Ranges

✅ **Excellent**
- Answer Relevancy: > 0.85
- Faithfulness: > 0.85
- Tool Accuracy: > 0.90
- Response Time: < 2s

🟡 **Acceptable**
- Answer Relevancy: 0.70 - 0.85
- Faithfulness: 0.75 - 0.85
- Tool Accuracy: 0.80 - 0.90
- Response Time: 2-5s

❌ **Needs Improvement**
- Answer Relevancy: < 0.70
- Faithfulness: < 0.75
- Tool Accuracy: < 0.80
- Response Time: > 5s

## Troubleshooting

### MongoDB Connection Failed
```bash
# Check if MongoDB is running
docker ps | grep mongo

# Start MongoDB
docker run -d -p 27017:27017 --name mongodb mongo:5
```

### OpenAI API Error
```bash
# Ensure API key is set
export OPENAI_API_KEY="your-key-here"

# Or set in .env file
echo "OPENAI_API_KEY=your-key-here" >> .env
```

### No Test Data
```bash
# First run Agent to generate data
uv run python src/agent/loan_advisor_agent.py

# Or use analyze_agent_behavior.py to generate
uv run python analyze_agent_behavior.py
```

## Summary

This evaluation system provides:
1. ✅ **Zero Intrusion** - No modification to existing Agent code
2. ✅ **Real Data** - Get production data from MongoDB
3. ✅ **Multi-dimensional Evaluation** - Quality, performance, tool usage, etc.
4. ✅ **Flexible Configuration** - Easy to adjust and extend
5. ✅ **CI/CD Friendly** - Support for automated testing

Start using:
```bash
uv run python run_evaluation.py --mode recent
```

Happy Evaluating! 🚀
