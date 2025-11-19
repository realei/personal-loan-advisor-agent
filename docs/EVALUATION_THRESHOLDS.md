# Evaluation Threshold Configuration Guide

## 📋 Overview

The project uses DeepEval for Agent quality evaluation. All evaluation metric thresholds can be configured through environment variables. Thresholds determine the minimum standard for Agent output to be considered "passing".

## 🎯 Threshold Descriptions

### Standard DeepEval Metrics

These are DeepEval's built-in standard evaluation metrics:

| Metric | Environment Variable | Default | Description | Higher is Better |
|------|----------|--------|------|---------|
| Answer Relevancy | `EVAL_THRESHOLD_ANSWER_RELEVANCY` | 0.7 | Relevance of answer to question | ✅ |
| Faithfulness | `EVAL_THRESHOLD_FAITHFULNESS` | 0.75 | Faithfulness of answer to context | ✅ |
| Hallucination | `EVAL_THRESHOLD_HALLUCINATION` | 0.3 | Degree of hallucination | ❌ |
| Bias | `EVAL_THRESHOLD_BIAS` | 0.3 | Degree of bias | ❌ |
| Toxicity | `EVAL_THRESHOLD_TOXICITY` | 0.2 | Degree of toxicity | ❌ |
| Contextual Relevancy | `EVAL_THRESHOLD_CONTEXTUAL_RELEVANCY` | 0.7 | Contextual relevance | ✅ |
| Contextual Precision | `EVAL_THRESHOLD_CONTEXTUAL_PRECISION` | 0.7 | Contextual precision | ✅ |
| Contextual Recall | `EVAL_THRESHOLD_CONTEXTUAL_RECALL` | 0.7 | Contextual recall | ✅ |

### Custom Agentic Metrics

These are custom metrics designed for Agent characteristics:

| Metric | Environment Variable | Default | Description | Higher is Better |
|------|----------|--------|------|---------|
| Tool Accuracy | `EVAL_THRESHOLD_TOOL_ACCURACY` | 0.8 | Tool selection accuracy | ✅ |
| Parameter Correctness | `EVAL_THRESHOLD_PARAMETER_CORRECTNESS` | 0.9 | Parameter correctness | ✅ |
| Response Time | `EVAL_THRESHOLD_RESPONSE_TIME` | 15.0 | Maximum response time (seconds) | ❌ |
| Token Limit | `EVAL_THRESHOLD_TOKEN_LIMIT` | 5000 | Token usage limit | ❌ |
| Tool Chain Logic | `EVAL_THRESHOLD_TOOL_CHAIN_LOGIC` | 0.85 | Tool chain logic | ✅ |

**Note**:
- ✅ Higher is better: Score needs to be **≥** threshold to pass
- ❌ Lower is better: Score needs to be **≤** threshold to pass

## 🔧 Configuration Methods

### Method 1: Use Default Values (Recommended)

**No need to configure in `.env`**, the system will automatically use the default values in the table above.

### Method 2: Custom Thresholds

Set the thresholds you want to adjust in the `.env` file:

```bash
# Only configure thresholds that need to change, others use default values

# Increase quality requirements
EVAL_THRESHOLD_ANSWER_RELEVANCY=0.8    # Increase from 0.7 to 0.8
EVAL_THRESHOLD_FAITHFULNESS=0.85       # Increase from 0.75 to 0.85

# Relax performance requirements (development environment)
EVAL_THRESHOLD_RESPONSE_TIME=30.0      # Relax from 15 seconds to 30 seconds

# Stricter tool accuracy
EVAL_THRESHOLD_TOOL_ACCURACY=0.9       # Increase from 0.8 to 0.9
```

## 💡 Use Cases

### Scenario 1: Development Environment (Relaxed Standards)

```bash
# .env configuration
# Lower requirements for quick iteration
EVAL_THRESHOLD_ANSWER_RELEVANCY=0.6
EVAL_THRESHOLD_FAITHFULNESS=0.65
EVAL_THRESHOLD_RESPONSE_TIME=30.0
EVAL_THRESHOLD_TOKEN_LIMIT=8000
```

**Suitable for**: Development phase, rapid iteration, allowing more trial and error

### Scenario 2: Test Environment (Default Standards)

```bash
# .env configuration
# Use default values, no configuration needed
```

**Suitable for**: Continuous integration, automated testing, routine quality checks

### Scenario 3: Production Environment (Strict Standards)

```bash
# .env configuration
# Increase standards to ensure high quality
EVAL_THRESHOLD_ANSWER_RELEVANCY=0.85
EVAL_THRESHOLD_FAITHFULNESS=0.9
EVAL_THRESHOLD_HALLUCINATION=0.2
EVAL_THRESHOLD_TOOL_ACCURACY=0.95
EVAL_THRESHOLD_PARAMETER_CORRECTNESS=0.95
EVAL_THRESHOLD_RESPONSE_TIME=10.0
```

**Suitable for**: Pre-production quality checks, critical feature validation

### Scenario 4: Performance Optimization (Focus on Performance Metrics)

```bash
# .env configuration
# Focus on optimizing performance metrics
EVAL_THRESHOLD_RESPONSE_TIME=8.0      # Stricter response time
EVAL_THRESHOLD_TOKEN_LIMIT=3000       # Stricter token limit
```

**Suitable for**: Performance optimization phase, cost control

## 📊 Threshold Adjustment Recommendations

### When to Increase Thresholds (Stricter)

1. **Before Production Release** - Ensure high quality
2. **Quality Issues Found** - Increase related metric requirements
3. **Cost Control** - Lower token and response time thresholds
4. **Poor User Feedback** - Increase relevance and accuracy requirements

### When to Decrease Thresholds (More Relaxed)

1. **Early Development** - Quick iteration, allow trial and error
2. **Experimental Features** - Explore possibilities
3. **Testing New Models** - Understand baseline performance
4. **Debugging Issues** - Facilitate locating specific problems

## 🔍 Verify Configuration

### View Current Thresholds

```bash
# Run configuration check script
uv run python scripts/check_config.py
```

Example output:
```
📊 Evaluation Threshold Configuration:
  Standard Metrics:
    answer_relevancy: 0.7 (default)
    faithfulness: 0.75 (default)
    ...

  Custom Metrics:
    tool_accuracy: 0.8 (default)
    parameter_correctness: 0.9 (default)
    ...
```

### Use in Code

```python
from tests.deepeval_config import METRIC_THRESHOLDS, CUSTOM_THRESHOLDS

# Get specific metric threshold
relevancy_threshold = METRIC_THRESHOLDS["answer_relevancy"]
tool_threshold = CUSTOM_THRESHOLDS["tool_accuracy"]

# Use in evaluation
from deepeval.metrics import AnswerRelevancyMetric

metric = AnswerRelevancyMetric(
    model="gpt-4o-mini",
    threshold=relevancy_threshold  # Use configured threshold
)
```

## 📈 Detailed Threshold Explanations

### Answer Relevancy

**Meaning**: How relevant the answer is to the user's question

**Examples**:
- Question: "How to calculate monthly payment?"
- Good answer (0.9): "The monthly payment formula is... need to pay monthly..."
- Bad answer (0.3): "We offer various loan products..." (off-topic)

**Recommended Thresholds**:
- Development: 0.6
- Testing: 0.7 (default)
- Production: 0.8-0.9

### Faithfulness

**Meaning**: Whether the answer is faithful to the provided context, not fabricating information

**Examples**:
- Context: "Minimum annual interest rate 5%"
- Good answer (0.95): "Annual interest rate starts at 5%"
- Bad answer (0.4): "Interest rate can be as low as 3%" (fabricated)

**Recommended Thresholds**:
- Development: 0.65
- Testing: 0.75 (default)
- Production: 0.85-0.95

### Hallucination

**Meaning**: Degree of fabricated or inaccurate information in answer (lower is better)

**Note**: This is a "lower is better" metric

**Recommended Thresholds**:
- Development: 0.4
- Testing: 0.3 (default)
- Production: 0.1-0.2

### Tool Accuracy

**Meaning**: Whether the tools selected by Agent match user intent

**Examples**:
- Input: "Calculate monthly payment"
- Correct tool: `calculate_loan_payment`
- Wrong tool: `check_loan_eligibility`

**Recommended Thresholds**:
- Development: 0.7
- Testing: 0.8 (default)
- Production: 0.9-0.95

### Response Time

**Meaning**: Time required for Agent's complete response (seconds)

**Recommended Thresholds**:
- Development: 30.0
- Testing: 15.0 (default)
- Production: 8.0-10.0

## ⚠️ Important Notes

### 1. Thresholds Are Not Always Better Higher/Lower

- Overly high thresholds may lead to many false negatives
- Overly low thresholds may miss real issues (false positives)
- Recommended to adjust based on actual data

### 2. Different Metric Weights

Not all metrics are equally important:

**High Priority** (critical metrics):
- Faithfulness - Prevent fabricating information
- Tool Accuracy - Ensure correct functionality
- Parameter Correctness - Ensure parameter accuracy

**Medium Priority**:
- Answer Relevancy - User experience
- Response Time - Performance metric

**Low Priority** (reference metrics):
- Contextual Precision/Recall - Supporting metrics

### 3. Environment Variable Types

Ensure using correct types:

```bash
# ✅ Correct - Float
EVAL_THRESHOLD_ANSWER_RELEVANCY=0.7

# ❌ Wrong - Integer (will be converted to 0.0)
EVAL_THRESHOLD_ANSWER_RELEVANCY=1

# ✅ Correct - Integer (Token limit)
EVAL_THRESHOLD_TOKEN_LIMIT=5000

# ❌ Wrong - Float (Token must be integer)
EVAL_THRESHOLD_TOKEN_LIMIT=5000.5
```

### 4. Threshold Adjustment Process

1. **Baseline Testing** - First run evaluation with default values, understand current performance
2. **Analyze Results** - See which metrics didn't pass, what's the pass rate
3. **Adjust Thresholds** - Adjust based on business needs
4. **Re-test** - Verify adjustment effects
5. **Continuous Optimization** - Continuously adjust based on feedback

## 🚀 Quick Start

### 1. Use Default Configuration (Recommended)

```bash
# No configuration needed, run evaluation directly
uv run pytest tests/test_mongodb_deepeval_with_storage.py -v
```

### 2. Custom Configuration

```bash
# Add to .env
EVAL_THRESHOLD_ANSWER_RELEVANCY=0.8
EVAL_THRESHOLD_TOOL_ACCURACY=0.9

# Verify configuration
uv run python scripts/check_config.py

# Run evaluation
uv run pytest tests/test_mongodb_deepeval_with_storage.py -v
```

## 📚 Related Documentation

- [DeepEval Official Documentation](https://docs.deepeval.com/)
- [Evaluation System Guide (EVALUATION_GUIDE.md)](./EVALUATION_GUIDE.md)
- [Configuration Management (MODEL_CONFIGURATION.md)](./MODEL_CONFIGURATION.md)
- [Environment Variable Example (.env.example)](../.env.example)

## 💡 Best Practices

### Development Phase
```bash
# Relaxed standards, quick iteration
EVAL_THRESHOLD_ANSWER_RELEVANCY=0.6
EVAL_THRESHOLD_FAITHFULNESS=0.65
EVAL_THRESHOLD_RESPONSE_TIME=30.0
```

### CI/CD Testing
```bash
# Use default values, no configuration needed
# Or slightly relax performance requirements
EVAL_THRESHOLD_RESPONSE_TIME=20.0
```

### Production Release
```bash
# Strict standards, ensure quality
EVAL_THRESHOLD_ANSWER_RELEVANCY=0.85
EVAL_THRESHOLD_FAITHFULNESS=0.9
EVAL_THRESHOLD_TOOL_ACCURACY=0.95
EVAL_THRESHOLD_RESPONSE_TIME=10.0
```

---

**Last Updated**: 2025-01-19
**Version**: 1.0
