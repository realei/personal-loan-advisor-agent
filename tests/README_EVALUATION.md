# Agent Evaluation Guide

## 📖 概述

`test_loan_advisor_agent.py` 使用 DeepEval 对 `src/agent/loan_advisor_agent.py` 进行全面评估。

## 🎯 核心设计

### 关键特性

✅ **简化的测试用例定义**（只需 input 和 expected_output_contains）
✅ **自动提取** expected_tools, expected_tool_args, context **从 Agent response**
✅ **在 pytest 中直接运行 Agent**（无需单独运行）
✅ **混合 Metrics**（Reference-based + Reference-free）
✅ **DeepEval 标准**（Golden, Dataset, LLMTestCase）
✅ **SOLID 原则**（简洁易懂）

## 📋 测试用例定义

现在你只需要定义：

```python
TEST_CASES = [
    {
        "id": "loan_calculation_basic",
        "input": "Calculate my monthly payment for a $50,000 loan...",
        "expected_output_contains": ["1,498", "monthly payment"],
        # ✨ 不需要手动定义 expected_tools 和 expected_tool_args！
        # 这些会自动从 Agent response 中提取
    },
]
```

### 自动提取的信息

`AgentRunner.run_test_case()` 会自动从 Agent 的 response 中提取：

- **tools_called**: 调用的工具名称列表
  例如: `['calculate_loan_payment']`

- **tool_calls_with_args**: 工具名称 + 参数
  例如:
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

- **retrieval_context**: 工具返回的结果（重新执行工具获得）
  例如: `["{\"monthly_payment\": 1498.54, \"total_payment\": 53947.61, ...}"]`
  注意: 这是通过重新执行工具（使用 Agent 使用的相同参数）获得的实际结果，用于 Faithfulness 和 Hallucination metrics

## 🔄 工作流程

```
1. 定义测试用例 (只需 id, input, expected_output_contains)
    ↓
2. Pytest 启动，创建 evaluation_dataset fixture
    ↓
3. AgentRunner 运行每个测试用例
    ↓
4. ✨ 自动提取: actual_output, tools_called, tool_args
    ↓
5. ✨ 重新执行工具调用: 使用提取的参数重新运行工具，获得 retrieval_context
    ↓
6. 创建 Golden (包含自动提取的信息和 retrieval_context)
    ↓
7. 创建 EvaluationDataset
    ↓
8. 运行评估测试：
    - Reference-free metrics (AnswerRelevancy, Faithfulness, Hallucination)
    - Tool calls info (显示自动提取的工具和参数)
    - Output keywords validation
    ↓
9. 生成测试结果
```

## 🚀 使用方法

### 运行所有测试

```bash
# 运行所有评估测试
uv run pytest tests/test_loan_advisor_agent.py -v -s

# 输出示例：
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

### 运行单个测试

```bash
# 查看自动提取的工具调用信息
uv run pytest tests/test_loan_advisor_agent.py::test_tool_calls_info -v -s

# 运行 reference-free metrics 评估
uv run pytest tests/test_loan_advisor_agent.py::test_agent_with_reference_free_metrics -v -s

# 运行关键词验证
uv run pytest tests/test_loan_advisor_agent.py::test_expected_output_keywords -v -s

# 测试单个用例示例
uv run pytest tests/test_loan_advisor_agent.py::test_individual_case_example -v -s
```

### 直接运行 Python 脚本

```bash
uv run python tests/test_loan_advisor_agent.py
```

## 📊 评估指标

### Reference-Free Metrics（不需要 expected_output）

#### 1. AnswerRelevancyMetric (回答相关性)
- **评估**: Agent 的回答是否与用户输入相关
- **阈值**: 0.7
- **说明**: 使用 LLM 评估回答是否切题

#### 2. FaithfulnessMetric (事实准确性)
- **评估**: Agent 的回答是否基于提供的 context（工具返回结果）
- **阈值**: 0.7
- **说明**: 确保回答不包含工具返回结果之外的信息

#### 3. HallucinationMetric (幻觉检测)
- **评估**: Agent 是否产生幻觉（编造信息）
- **阈值**: 0.5
- **说明**: 检测回答是否包含未经验证的信息

### Custom Validation（自定义验证）

#### 4. Tool Calls Info（工具调用信息展示）
- **展示**: 自动提取的工具名称和参数
- **示例**:
  ```
  🔧 Tool: calculate_loan_payment
     Arguments:
       - loan_amount: 50000
       - annual_interest_rate: 0.05
       - loan_term_months: 36
  ```

#### 5. Expected Output Keywords（输出关键词验证）
- **检查**: Agent 的回答是否包含预期的关键词
- **示例**: 贷款计算结果应该包含 "1,498" 或 "monthly payment"

## 🏗️ 代码结构

### TEST_CASES (全局常量)
```python
# 简化的测试用例定义，只需 input 和 expected_output_contains
TEST_CASES = [
    {
        "id": "...",
        "input": "...",
        "expected_output_contains": ["keyword1", "keyword2"],
    },
]
```

### AgentRunner (类)
```python
class AgentRunner:
    """负责运行测试用例并自动提取信息"""

    def run_test_case(self, test_input: str) -> Dict:
        # 运行 Agent
        # ✨ 自动提取: tools_called, tool_args, context
        # 返回完整信息
```

**自动提取的关键代码**:
```python
# 1. 提取工具调用和参数
for tc in msg.tool_calls:
    function_name = tc['function'].get('name')
    arguments = json.loads(tc['function'].get('arguments'))
    tool_calls_with_args.append({
        'name': function_name,
        'arguments': arguments
    })

# 2. 重新执行工具调用获得 retrieval_context
retrieval_context = self._reconstruct_context(tool_calls_with_args)
```

**工具重新执行的关键代码** (`_reconstruct_context`):
```python
def _reconstruct_context(self, tool_calls_with_args: list) -> list:
    """通过重新执行工具调用来重建 retrieval_context"""
    from dataclasses import asdict, is_dataclass
    retrieval_context = []

    # 初始化工具实例
    eligibility_checker = LoanEligibilityTool(...)
    loan_calculator = LoanCalculatorTool(...)

    # 序列化辅助函数（支持 Pydantic models 和 dataclasses）
    def serialize_result(result):
        if hasattr(result, 'model_dump'):
            return json.dumps(result.model_dump())  # Pydantic
        elif is_dataclass(result):
            return json.dumps(asdict(result), default=str)  # Dataclass
        else:
            return json.dumps(str(result))

    # 重新执行每个工具调用
    for tool_call in tool_calls_with_args:
        tool_name = tool_call['name']
        arguments = tool_call['arguments']

        if tool_name == 'calculate_loan_payment':
            loan_request = LoanRequest(**arguments)
            result = loan_calculator.calculate_monthly_payment(loan_request)
            retrieval_context.append(serialize_result(result))
        # ... 其他工具

    return retrieval_context
```

### Fixtures (Pytest)
```python
@pytest.fixture(scope="session")
def agent_runner():
    # 提供 AgentRunner 实例

@pytest.fixture(scope="session")
def evaluation_dataset(agent_runner):
    # 运行所有测试用例，自动提取信息，创建 EvaluationDataset

@pytest.fixture(scope="session")
def reference_free_metrics():
    # 定义 reference-free metrics
```

### Test Functions
```python
def test_agent_with_reference_free_metrics(...):
    # 使用 DeepEval metrics 评估

def test_tool_calls_info(...):
    # 显示自动提取的工具调用信息

def test_expected_output_keywords(...):
    # 验证输出关键词

def test_individual_case_example(...):
    # 单个用例示例
```

## 🎓 面试演示要点

### 展示流程

```bash
# 1. 展示简化的测试用例定义
# 打开 test_loan_advisor_agent.py，展示 TEST_CASES
# 强调：只需定义 input 和 expected_output_contains

# 2. 运行测试，展示自动提取的信息
uv run pytest tests/test_loan_advisor_agent.py::test_tool_calls_info -v -s

# 输出会显示:
# 🔧 Tool: calculate_loan_payment
#    Arguments:
#      - loan_amount: 50000
#      - annual_interest_rate: 0.05
#      - loan_term_months: 36

# 3. 解释自动提取机制
# 展示 AgentRunner.run_test_case() 的代码
# 解释如何从 response.messages 中提取工具调用和参数
```

### 优势说明

1. **无需手动定义 expected_tools 和 expected_tool_args**
   - 自动从 Agent response 中提取
   - 减少测试用例定义的工作量
   - 更准确（基于实际调用）

2. **自动获取准确的 retrieval_context**
   - 通过重新执行工具（使用 Agent 的参数）获得实际结果
   - 不是从消息历史提取，而是真实的工具执行结果
   - 确保 Faithfulness 和 Hallucination metrics 评估的准确性
   - 支持 Pydantic models 和 dataclasses 的自动序列化

3. **完整的可见性**
   - 可以看到 Agent 调用了哪些工具
   - 可以看到传递了什么参数
   - 可以看到工具返回的实际结果
   - 可以验证工具调用的正确性

4. **易于扩展**
   - 添加新测试用例：只需 input 和 expected keywords
   - 不需要手动分析 Agent 会调用什么工具
   - 添加新工具：在 `_reconstruct_context` 中添加对应的分支

## 🔧 自定义配置

### 添加新测试用例（超级简单！）

```python
TEST_CASES.append({
    "id": "new_test_case",
    "input": "Your test input here",
    "expected_output_contains": ["keyword1", "keyword2"],
    # 就这么简单！不需要定义 expected_tools 或 expected_tool_args
})
```

### 修改 Metrics 阈值

```python
@pytest.fixture(scope="session")
def reference_free_metrics():
    return [
        AnswerRelevancyMetric(threshold=0.8),  # 提高阈值
        FaithfulnessMetric(threshold=0.75),
    ]
```

### 添加新的 Metric

```python
from deepeval.metrics import ContextualRelevancyMetric

@pytest.fixture(scope="session")
def reference_free_metrics():
    return [
        AnswerRelevancyMetric(threshold=0.7),
        FaithfulnessMetric(threshold=0.7),
        ContextualRelevancyMetric(threshold=0.7),  # 新增
    ]
```

## ⚠️ 注意事项

1. **首次运行较慢**
   - 需要运行 2 次 Agent（2 个测试用例）
   - 每次 Agent 调用需要 5-10 秒
   - DeepEval metrics 需要调用 GPT-4 评估

2. **OpenAI API Rate Limits**
   - DeepEval 使用 GPT-4 评估
   - 建议从少量测试用例开始
   - 如遇 rate limit，等待 1 分钟后重试

3. **Session Scope Fixtures**
   - `evaluation_dataset` 使用 `scope="session"`
   - 所有测试用例只运行一次 Agent
   - 提高测试效率

4. **自动提取的准确性**
   - 工具调用和参数从 Agent response 中提取
   - 如果 Agent 没有调用工具，`tools_called` 会是空列表
   - 这是正常的，可以用来发现 Agent 行为问题

## 💡 最佳实践

### 开发时
```bash
# 快速验证 - 查看工具调用和关键词
uv run pytest tests/test_loan_advisor_agent.py::test_tool_calls_info -v
uv run pytest tests/test_loan_advisor_agent.py::test_expected_output_keywords -v
```

### 完整评估时
```bash
# 运行所有测试（包括 LLM metrics）
uv run pytest tests/test_loan_advisor_agent.py -v -s
```

### CI/CD 集成
```bash
# 在 CI 中只运行快速验证
pytest tests/test_loan_advisor_agent.py::test_tool_calls_info
pytest tests/test_loan_advisor_agent.py::test_expected_output_keywords

# 定期运行完整评估（cron job）
pytest tests/test_loan_advisor_agent.py
```

## 📚 参考资料

- [DeepEval Documentation](https://deepeval.com/docs/evaluation-introduction)
- [DeepEval Metrics](https://deepeval.com/docs/metrics-introduction)
- [DeepEval Test Cases](https://deepeval.com/docs/evaluation-test-cases)
- [pytest Fixtures](https://docs.pytest.org/en/stable/fixture.html)

## 🎯 总结

### 相比手动定义的优势

| 特性 | 手动定义 | 自动提取 + 工具重执行 |
|------|---------|---------------------|
| **测试用例定义** | 需要定义 tools, args, context | ✅ 只需 input + keywords |
| **准确性** | 可能过时 | ✅ 基于实际调用 |
| **维护成本** | 需要同步更新 | ✅ 自动同步 |
| **可见性** | 只看到预期值 | ✅ 看到实际调用 + 实际结果 |
| **调试** | 需要手动检查 | ✅ 自动展示 |
| **Retrieval Context** | 手动构造或从消息提取 | ✅ 重新执行工具获得真实结果 |
| **序列化支持** | 需要手动处理 | ✅ 自动处理 Pydantic/dataclass |

这就是为什么自动提取 + 工具重执行更好！🚀
