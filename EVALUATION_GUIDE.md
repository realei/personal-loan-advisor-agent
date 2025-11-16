# Evaluation System Guide

## Overview

The Personal Loan Advisor Agent integrates a **100% asynchronous evaluation system** that uses DeepEval to automatically assess the quality of every conversation. Results are stored in MongoDB for analysis and monitoring.

---

## Key Features

### 1. **100% Asynchronous Evaluation**
- Every conversation is automatically evaluated
- Evaluations run in background threads without blocking user responses
- Zero latency impact on user experience

### 2. **Multi-Dimensional Metrics**
| Metric | Description | Threshold |
|--------|-------------|-----------|
| **Answer Relevancy** | How relevant the answer is to the question | ≥ 0.7 |
| **Faithfulness** | Whether answer is grounded in context facts | ≥ 0.8 |
| **Hallucination** | Detection of fabricated information | ≤ 0.3 |
| **Bias** | Detection of unfair bias (critical for financial services) | ≤ 0.3 |

### 3. **MongoDB Persistence**
- All evaluation results stored in database
- Supports historical queries and statistical analysis
- Automatically linked to users and sessions

### 4. **Automatic Context Extraction**
The system automatically extracts from conversations:
- Monthly income
- Credit score
- Age
- Loan amount and term
- Employment status

---

## MongoDB Data Model

### Evaluations Collection

```javascript
{
  "evaluation_id": "eval_user123_20240115_143022_001",
  "session_id": "user123_20240115_143022",
  "user_id": "user123",
  "status": "completed",  // pending | in_progress | completed | failed

  "user_input": "I want a $50,000 loan for 36 months",
  "agent_output": "For a $50,000 loan at 5% interest...",

  "context": {
    "monthly_income": 10000,
    "credit_score": 720,
    "loan_amount": 50000,
    "loan_term_months": 36
  },

  "metadata": {
    "agent_model": "gpt-4",
    "stream_mode": true
  },

  "scores": {
    "answer_relevancy": 0.89,
    "faithfulness": 0.92,
    "hallucination": 0.15,
    "bias": 0.05
  },

  "metrics_passed": {
    "answer_relevancy": true,
    "faithfulness": true,
    "hallucination": true,
    "bias": true
  },

  "overall_passed": true,
  "critical_issues": [],

  "created_at": ISODate("2024-01-15T14:30:22.123Z"),
  "started_at": ISODate("2024-01-15T14:30:23.456Z"),
  "completed_at": ISODate("2024-01-15T14:30:28.789Z"),

  "error": null
}
```

---

## Quick Start

### 1. Start MongoDB

```bash
# Start MongoDB container
docker-compose up -d

# Verify it's running
docker-compose ps
```

### 2. Set Environment Variables

```bash
# Set OpenAI API Key (required for evaluation)
export OPENAI_API_KEY=sk-your-key-here
```

### 3. Use Agent with Evaluation

```python
from src.agent import PersonalLoanAgent
from src.utils.memory import ConversationMemory

# Create memory with evaluation enabled
memory = ConversationMemory(
    mongodb_uri="mongodb://admin:password123@localhost:27017/",
    database_name="loan_advisor",
    enable_evaluation=True  # Enabled by default
)

# Start user session
user_id = "user123"
session_id = memory.start_session(user_id)

# Create agent
agent = PersonalLoanAgent(
    model="gpt-4",
    temperature=0.7,
    memory=memory
)

# Use normally (evaluation runs automatically in background)
agent.run("I'm 35, earn $10k/month, credit score 720. Can I get a $50k loan?")
```

### 4. View Evaluation Results

#### Method 1: Using Query Script

```bash
# View evaluations for a session
python scripts/view_evaluations.py --session-id user123_20240115_143022

# View statistics for a user
python scripts/view_evaluations.py --user-id user123

# View specific evaluation details
python scripts/view_evaluations.py --eval-id eval_xxx_yyy

# View summary only
python scripts/view_evaluations.py --session-id xxx --summary

# Filter by status
python scripts/view_evaluations.py --session-id xxx --status completed
```

#### Method 2: Programmatic Access

```python
# Get evaluations for current session
evaluations = memory.get_session_evaluations(limit=10)

for eval_doc in evaluations:
    print(f"Status: {eval_doc['status']}")
    print(f"Scores: {eval_doc.get('scores', {})}")
    print(f"Passed: {eval_doc.get('overall_passed', False)}")

# Get session statistics
stats = memory.get_session_evaluation_stats()
print(f"Pass Rate: {stats['pass_rate']*100:.1f}%")
print(f"Average Scores: {stats['average_scores']}")
print(f"Critical Issues: {stats['critical_issues_count']}")

# Get user statistics (across all sessions)
user_stats = memory.evaluation_manager.get_user_statistics("user123")
print(f"Total Evaluations: {user_stats['total_evaluations']}")
print(f"Sessions: {user_stats['sessions_count']}")
```

---

## Evaluation Status Flow

```
PENDING → IN_PROGRESS → COMPLETED
                ↓
              FAILED
```

1. **PENDING**: Evaluation submitted, waiting to execute
2. **IN_PROGRESS**: Evaluation running (calling DeepEval API)
3. **COMPLETED**: Evaluation finished with results
4. **FAILED**: Evaluation failed (e.g., API error)

---

## Configuration Options

### Disable Evaluation

To disable evaluation:

```python
memory = ConversationMemory(
    enable_evaluation=False  # Disable evaluation
)
```

### Custom Evaluation Thresholds

```python
from src.evaluation import EvaluationManager

eval_manager = EvaluationManager(
    evaluations_collection=memory.evaluations,
    answer_relevancy_threshold=0.8,  # Higher requirement
    faithfulness_threshold=0.9,
    hallucination_threshold=0.2,     # Stricter
    bias_threshold=0.1,              # Zero tolerance for financial services
    max_workers=5                     # Number of concurrent evaluation threads
)
```

---

## Monitoring and Analysis

### Key Metrics Monitoring

```python
# Real-time session quality monitoring
stats = memory.get_session_evaluation_stats()

if stats['pass_rate'] < 0.7:
    print("⚠️ WARNING: Low quality session detected!")

if stats['critical_issues_count'] > 0:
    print("🚨 CRITICAL: Bias or hallucination detected!")
    # Trigger human review
    trigger_human_review(session_id)
```

### Batch Analysis

```python
# Analyze evaluation quality across all users
from pymongo import MongoClient

client = MongoClient("mongodb://admin:password123@localhost:27017/")
db = client["loan_advisor"]

# Find all evaluations with critical issues
critical_evals = db.evaluations.find({
    "critical_issues": {"$ne": []},
    "status": "completed"
})

for eval_doc in critical_evals:
    print(f"Session: {eval_doc['session_id']}")
    print(f"Issues: {eval_doc['critical_issues']}")
```

---

## Testing

### Run Evaluation Tests

```bash
# Basic tests (no OpenAI API needed)
pytest tests/test_evaluation.py::TestEvaluationManager -v

# Full tests (requires API key)
export OPENAI_API_KEY=sk-xxx
pytest tests/test_evaluation.py::TestEvaluationWithAPI -v -s

# All tests
pytest tests/test_evaluation.py -v
```

### Test Coverage

- ✅ Evaluation submission and async execution
- ✅ Status transitions
- ✅ Multi-user isolation
- ✅ Statistics calculation
- ✅ Context extraction
- ✅ Metadata storage
- ✅ Full API call cycle

---

## Best Practices

### 1. **Production Configuration**

```python
# Recommended configuration
memory = ConversationMemory(
    mongodb_uri=os.getenv("MONGODB_URI"),
    database_name="loan_advisor_prod",
    enable_evaluation=True  # 100% evaluation
)

agent = PersonalLoanAgent(
    model="gpt-4",
    temperature=0.3,  # Lower temperature for production
    debug_mode=False,
    memory=memory
)
```

### 2. **Monitoring and Alerts**

```python
# Check evaluation results and trigger alerts
def check_evaluation_quality(session_id):
    stats = memory.evaluation_manager.get_session_statistics(session_id)

    # Alert conditions
    if stats['critical_issues_count'] > 0:
        send_alert(f"Critical issues in session {session_id}")

    if stats['pass_rate'] < 0.6:
        send_alert(f"Low pass rate: {stats['pass_rate']}")
```

### 3. **Periodic Cleanup**

```python
# Clean up old evaluation data (e.g., 30 days old)
from datetime import datetime, timedelta

cutoff_date = datetime.now() - timedelta(days=30)

db.evaluations.delete_many({
    "created_at": {"$lt": cutoff_date},
    "status": "completed"
})
```

---

## Troubleshooting

### Evaluation Stuck in PENDING

**Cause**: Background thread may not have started or API call failed

**Solution**:
```python
# Check evaluation status
eval_doc = memory.evaluation_manager.get_evaluation_result(eval_id)
print(f"Status: {eval_doc['status']}")
print(f"Error: {eval_doc.get('error')}")

# Check OpenAI API key
import os
print(f"API Key set: {bool(os.getenv('OPENAI_API_KEY'))}")
```

### Evaluation FAILED

**Common Causes**:
1. OpenAI API rate limiting
2. Invalid API key
3. Network issues

**Solution**:
```python
# View error message
eval_doc = memory.evaluation_manager.get_evaluation_result(eval_id)
print(f"Error: {eval_doc.get('error')}")
```

---

## API Reference

### ConversationMemory

```python
# Evaluation-related methods
memory.evaluate_interaction(user_input, agent_output, context, metadata)
memory.get_session_evaluations(limit=10)
memory.get_session_evaluation_stats()
```

### EvaluationManager

```python
eval_manager.evaluate_async(session_id, user_id, user_input, agent_output, context, metadata)
eval_manager.get_evaluation_result(evaluation_id)
eval_manager.get_session_evaluations(session_id, limit=None)
eval_manager.get_session_statistics(session_id)
eval_manager.get_user_statistics(user_id)
```

---

## Example Output

```bash
$ python scripts/view_evaluations.py --session-id user123_20240115_143022

================================================================================
Evaluation ID: eval_user123_20240115_143022_001
Session ID: user123_20240115_143022
User ID: user123
Status: completed
Created: 2024-01-15 14:30:22
Completed: 2024-01-15 14:30:28

--- User Input ---
I'm 35, earn $10k/month, credit score 720. Can I get a $50k loan?

--- Agent Output ---
Based on your profile, you appear to be eligible for the loan...

--- Context ---
  monthly_income: 10000
  credit_score: 720
  age: 35
  loan_amount: 50000

--- Evaluation Scores ---
  answer_relevancy    : 0.892 ✅ PASS
  faithfulness        : 0.945 ✅ PASS
  hallucination       : 0.123 ✅ PASS
  bias                : 0.045 ✅ PASS

  Overall: ✅ PASSED

================================================================================
```

---

## Next Steps

1. **Production Deployment**: Configure production MongoDB and API keys
2. **Monitoring Dashboard**: Consider Grafana/Kibana for visualization
3. **A/B Testing**: Use evaluation data to compare models or prompts
4. **Human Review**: Manual review of low-scoring conversations

---

## Contributing

To improve the evaluation system, refer to:
- `src/evaluation/evaluation_manager.py` - Core evaluation logic
- `src/utils/memory.py` - Memory integration
- `tests/test_evaluation.py` - Test cases
