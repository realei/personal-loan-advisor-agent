# DeepEval测试文件对比说明

## 📋 概述

项目中有3个DeepEval测试文件，各有不同的用途和数据源：

| 文件 | 数据源 | 是否Mock | 存储结果 | 主要用途 |
|------|--------|----------|----------|----------|
| `test_agent_evaluation.py` | **Mock数据** | ✅ | ❌ | CI/CD快速测试 |
| `test_mongodb_deepeval.py` | **真实MongoDB** | ❌ | ❌ | 从MongoDB读取真实对话评估 |
| `test_mongodb_deepeval_with_storage.py` | **真实MongoDB** | ❌ | ✅ | 读取真实数据+保存评估结果 |

---

## 📄 文件1: test_agent_evaluation.py

### 🎯 用途
**CI/CD快速测试** - 使用预定义的mock数据进行快速验证

### 📦 数据源
```python
# ❌ 使用Mock数据，不连接真实MongoDB
class MockMongoDataExtractor:
    """Mock MongoDB数据提取器用于测试"""

    @staticmethod
    def create_mock_run(test_case: Dict, ...):
        return {
            "session_id": f"test_session_{test_case['id']}",
            "input": test_case["input"],
            "output": actual_output,
            "tool_calls": [...],  # 模拟的工具调用
        }
```

### 📊 测试数据
```python
# 固定的测试用例
FIXED_TEST_CASES = [
    {
        "id": "loan_calculation_basic",
        "input": "计算5万美元，年利率5%，36个月的贷款月供",
        "expected_tools": ["calculate_loan_payment"],
        "expected_params": {...},
        "expected_output_contains": ["1,498", "月供", "总利息"],
    },
    # ... 更多预定义测试用例
]
```

### ✅ 优点
- ⚡ **快速**: 不需要连接真实数据库
- 🔒 **稳定**: 测试结果可预测
- 🚀 **CI友好**: 适合持续集成环境
- 📦 **独立**: 不依赖外部数据

### ❌ 缺点
- 🎭 **不真实**: 使用Mock数据，无法反映真实Agent行为
- 📉 **覆盖有限**: 只测试预定义场景
- 🔄 **需维护**: 测试数据需要手动更新

### 💡 使用场景
```bash
# CI/CD pipeline中运行
pytest tests/test_agent_evaluation.py -v

# 快速验证Agent基本功能
pytest tests/test_agent_evaluation.py::TestAgentWithExpectedOutputs -v
```

---

## 📄 文件2: test_mongodb_deepeval.py

### 🎯 用途
**从真实MongoDB读取数据进行评估** - 使用真实的Agent对话历史

### 📦 数据源
```python
# ✅ 从真实MongoDB读取数据
class MongoTestDataExtractor:
    def __init__(self,
                 mongodb_url: str = MONGODB_URL,  # 真实MongoDB连接
                 db_name: str = DATABASE_NAME,
                 collection_name: str = SESSION_COLLECTION):
        self.client = MongoClient(mongodb_url)  # 连接真实数据库
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def extract_test_cases(self, ...):
        # 从MongoDB的agno_sessions集合读取真实数据
        sessions = self.collection.find(filter_criteria).skip(skip).limit(limit)

        for session in sessions:
            for run in session.get("runs", []):
                test_case = self._extract_run_data(session_id, run)
                # 提取input, output, tool_calls, metrics等
```

### 🔍 数据提取方式
```python
# 1. 提取最近N小时的对话
extractor.extract_recent_cases(hours=24, limit=10)

# 2. 根据输入模式提取
extractor.extract_by_pattern(input_pattern="计算月供", limit=5)

# 3. 自定义过滤条件
extractor.extract_test_cases(
    filter_criteria={"runs.input": {"$regex": "贷款"}},
    limit=20
)
```

### 🔧 Context重构功能
```python
@dataclass
class MongoTestCase:
    def reconstruct_context(self) -> None:
        """从tool calls重构context"""
        if self.tool_calls and not self.context:
            reconstructor = ContextReconstructor()
            # 重新执行工具调用获取context
            self.context = reconstructor.reconstruct_context_from_tool_calls(
                self.tool_calls
            )
```

**这是创新点！** 通过重新执行工具调用来获取`retrieval_context`，解决Faithfulness指标评估问题。

### ✅ 优点
- 🎯 **真实数据**: 使用实际Agent运行的对话
- 📊 **全面覆盖**: 可以评估所有历史对话
- 🔍 **发现问题**: 能找到真实使用中的问题
- 🔄 **Context重构**: 创新的context获取方式

### ❌ 缺点
- 🗄️ **依赖MongoDB**: 需要数据库运行且有数据
- ⏱️ **较慢**: 需要从数据库读取和重构context
- 📝 **无结果存储**: 评估结果不保存（仅显示）

### 💡 使用场景
```bash
# 评估最近24小时的对话
pytest tests/test_mongodb_deepeval.py::TestMongoDBEvaluation::test_recent_conversations -v

# 评估特定模式的对话
pytest tests/test_mongodb_deepeval.py -v
```

---

## 📄 文件3: test_mongodb_deepeval_with_storage.py

### 🎯 用途
**从真实MongoDB读取数据评估 + 保存评估结果** - 完整的评估流程

### 📦 数据源
```python
# ✅ 继承test_mongodb_deepeval.py的数据提取功能
from tests.test_mongodb_deepeval import (
    MongoTestDataExtractor,  # 使用真实MongoDB提取
    MongoTestCase,
    ToolAccuracyMetric,
    ParameterValidationMetric
)
```

### 💾 结果存储
```python
from evaluation.mongodb_storage import (
    EvaluationStorage,      # 评估结果存储管理器
    CITestResult,          # CI测试结果模型
    LiveEvalResult,        # 生产评估结果模型
    TestCaseResult,        # 单个测试用例结果
    MetricResult,          # 指标结果
)

class TestWithStorage:
    @pytest.fixture(scope="class")
    def storage(self):
        """存储管理器fixture"""
        storage = EvaluationStorage()
        yield storage
        storage.close()

    def test_with_storage(self, storage, mongo_extractor):
        # 1. 从真实MongoDB读取数据
        test_cases = mongo_extractor.extract_recent_cases(hours=24, limit=5)

        # 2. 运行评估
        results = evaluate(test_cases, metrics)

        # 3. 保存结果到MongoDB
        storage.store_ci_test_result(ci_result)
```

### 📊 存储的数据结构

#### CI测试结果 (ci_test_runs collection)
```python
{
    "test_suite": "deepeval_mongodb_integration",
    "git_commit": "abc123",
    "git_branch": "main",
    "started_at": datetime.now(),
    "completed_at": datetime.now(),
    "status": "completed",
    "total_cases": 10,
    "passed_cases": 8,
    "failed_cases": 2,
    "metrics_summary": {
        "answer_relevancy": {"avg": 0.85, "passed": 8, "failed": 2},
        "faithfulness": {"avg": 0.90, "passed": 10, "failed": 0}
    },
    "environment": {...},
    "test_config": {...}
}
```

#### 单个测试用例结果 (test_case_results collection)
```python
{
    "test_run_id": "ci_run_xyz",
    "test_case_id": "case_123",
    "input": "计算月供...",
    "actual_output": "月供为$1,498...",
    "metrics": [
        {
            "name": "answer_relevancy",
            "score": 0.85,
            "threshold": 0.7,
            "status": "passed",
            "reason": "Answer is highly relevant"
        }
    ],
    "tool_calls": [...],
    "performance": {...}
}
```

### ✅ 优点
- 🎯 **真实数据**: 使用实际Agent运行的对话
- 💾 **结果持久化**: 评估结果保存到MongoDB
- 📈 **趋势分析**: 可以查看历史评估趋势
- 🔍 **详细追踪**: 每个测试用例的详细结果都保存
- 🚀 **CI/CD集成**: 支持Git信息、环境信息记录

### ❌ 缺点
- 🗄️ **依赖MongoDB**: 需要数据库运行且有数据
- ⏱️ **最慢**: 读取数据 + 评估 + 存储结果
- 💽 **存储开销**: 需要额外的存储空间

### 💡 使用场景
```bash
# 完整的评估流程（推荐用于定期质量检查）
pytest tests/test_mongodb_deepeval_with_storage.py -v

# 性能基准测试
pytest tests/test_mongodb_deepeval_with_storage.py::TestWithStorage::test_performance_benchmark_with_storage -v
```

---

## 🔄 三者对比总结

### 数据流对比

#### test_agent_evaluation.py (Mock)
```
固定测试数据 → DeepEval评估 → 显示结果 ✅
```

#### test_mongodb_deepeval.py (真实数据)
```
MongoDB真实对话 → 提取数据 → Context重构 → DeepEval评估 → 显示结果 ✅
```

#### test_mongodb_deepeval_with_storage.py (真实数据+存储)
```
MongoDB真实对话 → 提取数据 → Context重构 → DeepEval评估 → 保存结果到MongoDB 💾 → 显示结果 ✅
```

### 使用建议

| 场景 | 推荐文件 | 原因 |
|------|----------|------|
| **CI/CD Pipeline** | `test_agent_evaluation.py` | 快速、稳定、无外部依赖 |
| **开发调试** | `test_mongodb_deepeval.py` | 快速验证真实数据 |
| **定期质量检查** | `test_mongodb_deepeval_with_storage.py` | 完整评估+结果追踪 |
| **性能优化** | `test_mongodb_deepeval_with_storage.py` | 有性能基准测试 |
| **趋势分析** | `test_mongodb_deepeval_with_storage.py` | 结果持久化，可查看历史 |

---

## 💡 回答你的问题

### Q1: "有的mock db有的不是，都做了什么？"

**答案**:

1. **test_agent_evaluation.py** - ✅ **使用Mock**
   - 不连接真实MongoDB
   - 使用`MockMongoDataExtractor`创建假数据
   - 适合CI/CD快速测试

2. **test_mongodb_deepeval.py** - ❌ **不使用Mock**
   - 连接真实MongoDB (`MongoClient(MONGODB_URL)`)
   - 从`agno_sessions`集合读取真实对话
   - 适合评估真实Agent表现

3. **test_mongodb_deepeval_with_storage.py** - ❌ **不使用Mock**
   - 连接真实MongoDB读取数据
   - 同时将评估结果保存回MongoDB
   - 适合完整的评估流程

### Q2: "现在deepeval的metrics eval可以从真正的mongodb里面获取数据建立testcase吗？"

**答案**: ✅ **可以！而且已经实现了！**

这正是 `test_mongodb_deepeval.py` 和 `test_mongodb_deepeval_with_storage.py` 的核心功能：

```python
# 1. 从真实MongoDB提取数据
extractor = MongoTestDataExtractor(
    mongodb_url=MONGODB_URL,          # 真实MongoDB连接
    db_name="loan_advisor",
    collection_name="agno_sessions"   # Agent对话存储的集合
)

# 2. 提取最近24小时的真实对话
test_cases = extractor.extract_recent_cases(hours=24, limit=10)

# 3. 将MongoDB数据转换为DeepEval TestCase
for mongo_case in test_cases:
    # 自动从tool_calls重构context
    mongo_case.reconstruct_context()

    # 转换为DeepEval格式
    deepeval_case = mongo_case.to_deepeval_case()

    # 运行评估
    metric = AnswerRelevancyMetric(threshold=0.7)
    result = metric.measure(deepeval_case)
```

### 具体工作流程

```python
# 真实数据提取示例
def test_from_mongodb(mongo_extractor, storage):
    # Step 1: 从MongoDB提取真实对话
    test_cases = mongo_extractor.extract_recent_cases(
        hours=24,   # 最近24小时
        limit=5     # 最多5个对话
    )

    # Step 2: 为每个对话创建TestCase
    deepeval_cases = []
    for case in test_cases:
        # MongoDB数据结构:
        # {
        #   "input": "计算5万贷款...",
        #   "actual_output": "月供为$1,498...",
        #   "tool_calls": [{...}],
        #   "metrics": {...}
        # }

        # 重构context (从tool_calls重新执行)
        case.reconstruct_context()

        # 转换为DeepEval格式
        deepeval_case = case.to_deepeval_case()
        deepeval_cases.append(deepeval_case)

    # Step 3: 运行评估
    metrics = [
        AnswerRelevancyMetric(threshold=0.7),
        FaithfulnessMetric(threshold=0.75)
    ]

    results = evaluate(deepeval_cases, metrics)

    # Step 4: (可选) 保存结果回MongoDB
    storage.store_test_case_results(results)
```

---

## 🎯 最佳实践建议

### 日常开发
```bash
# 使用Mock快速验证
pytest tests/test_agent_evaluation.py -v
```

### 每日质量检查
```bash
# 从真实MongoDB评估最近24小时的对话
pytest tests/test_mongodb_deepeval.py::TestMongoDBEvaluation::test_recent_conversations -v
```

### 每周深度评估
```bash
# 完整评估+结果存储
pytest tests/test_mongodb_deepeval_with_storage.py -v

# 然后查看趋势
uv run python scripts/view_evaluations.py --days 7
```

### CI/CD Pipeline
```yaml
# .github/workflows/test.yml
- name: Run Fast Tests
  run: pytest tests/test_agent_evaluation.py -v

- name: Run MongoDB Integration Tests
  run: pytest tests/test_mongodb_deepeval_with_storage.py -v
  if: github.event_name == 'push' && github.ref == 'refs/heads/main'
```

---

**更新日期**: 2025-01-19
**版本**: 1.0
