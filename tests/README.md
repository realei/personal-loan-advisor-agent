# Test Files Overview

## 📋 Test File Structure

```
tests/
├── test_loan_calculator_simple.py     # Tool unit tests - Loan calculator
├── test_loan_eligibility_simple.py    # Tool unit tests - Eligibility checker
├── test_loan_advisor_agent.py         # Agent evaluation tests (DeepEval)
└── README_EVALUATION.md               # Agent evaluation detailed documentation
```

## 🎯 Test Categories

### 1. Tool Unit Tests (2 files)

**Files**:
- `test_loan_calculator_simple.py`
- `test_loan_eligibility_simple.py`

**Purpose**:
- Quick validation of tool function logic
- Fast CI/CD testing
- No dependency on Agent, LLM, or MongoDB

**Run**:
```bash
pytest tests/test_loan_calculator_simple.py -v
pytest tests/test_loan_eligibility_simple.py -v
```

---

### 2. Agent Evaluation Tests (1 file)

**File**: `test_loan_advisor_agent.py`

**Features**:
- ✅ Uses DeepEval standards (Golden, Dataset, Metrics)
- ✅ Test target: `src/agent/loan_advisor_agent.py`
- ✅ Data source: Real conversations from MongoDB `agno_sessions`
- ✅ Follows SOLID principles
- ✅ Concise, all evaluation in one file

**Run**:
```bash
# See README_EVALUATION.md for details
pytest tests/test_loan_advisor_agent.py -v
```

**Evaluation Metrics**:
- AnswerRelevancyMetric (Answer relevancy)
- FaithfulnessMetric (Factual accuracy)

---

## 🚀 Quick Start

### Daily Development
```bash
# Validate tool logic
pytest tests/test_loan_*_simple.py -v
```

### Agent Evaluation
```bash
# 1. First run Agent to generate conversation data
uv run python src/agent/loan_advisor_agent.py

# 2. Run evaluation
pytest tests/test_loan_advisor_agent.py -v
```

---

## 📊 Comparison Table

| Test Type | Files | Data Source | Dependencies | Use Case |
|-----------|-------|-------------|-------------|----------|
| Tool Unit Tests | `test_loan_*_simple.py` | Hardcoded | pytest | CI/CD |
| Agent Evaluation | `test_loan_advisor_agent.py` | MongoDB | DeepEval + pytest | Quality Assessment |

---

## 📚 More Information

- Agent evaluation detailed documentation: [README_EVALUATION.md](./README_EVALUATION.md)
- DeepEval official documentation: https://deepeval.com/docs/evaluation-introduction
