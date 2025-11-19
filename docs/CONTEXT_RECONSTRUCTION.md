# Context重构功能说明

## 概述

为了支持DeepEval的Faithfulness和Hallucination指标评估，我们实现了Context重构功能。该功能可以从agent的工具调用历史中重新执行工具，获取工具返回的结果作为评估所需的`retrieval_context`。

## 为什么需要Context重构？

某些DeepEval指标需要`retrieval_context`（检索上下文）来评估：

- **Faithfulness（忠实度）**: 评估agent的回答是否基于工具返回的事实
- **Hallucination（幻觉检测）**: 检测agent是否编造了工具中没有的信息

如果没有`retrieval_context`，这些指标会报错：
```
'retrieval_context' cannot be None for the 'Faithfulness' metric
'context' cannot be None for the 'Hallucination' metric
```

## 实现方案

### 1. Context来源

Context可以从两个来源获取：

#### 方案A：从MongoDB读取（已实现）
- MongoDB `agno_sessions` 集合中的 `runs[].messages[]` 包含了完整的对话历史
- 提取 `role="tool"` 的消息内容作为context
- **优点**: 直接使用真实的工具响应，无需重新执行
- **缺点**: 依赖MongoDB中数据的完整性

#### 方案B：重新执行工具（备用方案）
- 从 `tool_calls` 中提取工具名称和参数
- 使用原始工具函数重新执行
- **优点**: 即使MongoDB数据不完整也能工作
- **缺点**: 需要访问工具函数，可能有副作用

### 2. 实现细节

#### ContextReconstructor类
位置：`evaluation/context_reconstructor.py`

```python
class ContextReconstructor:
    """从工具调用重构context"""

    def __init__(self):
        # 映射工具名称到实际函数
        self.tool_functions = {
            "check_loan_eligibility": check_loan_eligibility_raw,
            "calculate_loan_payment": calculate_loan_payment_raw,
            # ... 其他工具
        }

    def reconstruct_context_from_tool_calls(self, tool_calls: List[Dict]) -> List[str]:
        """
        从工具调用列表重构context

        Args:
            tool_calls: 格式为 [{"function": {"name": "...", "arguments": "{...}"}}]

        Returns:
            context列表，每个元素是工具返回的字符串结果
        """
        context = []
        for tool_call in tool_calls:
            func_name = tool_call["function"]["name"]
            func_args = json.loads(tool_call["function"]["arguments"])

            # 执行工具
            result = self._execute_tool(func_name, func_args)
            if result:
                context.append(result)

        return context
```

#### MongoTestCase集成
位置：`tests/test_mongodb_deepeval.py`

```python
@dataclass
class MongoTestCase:
    # ... 其他字段
    context: Optional[List[str]] = None
    retrieval_context: Optional[List[str]] = None

    def reconstruct_context(self) -> None:
        """从tool calls重构context"""
        if self.tool_calls and not self.context:
            reconstructor = ContextReconstructor()
            self.context = reconstructor.reconstruct_context_from_tool_calls(self.tool_calls)
            self.retrieval_context = self.context

    def to_deepeval_case(self, expected_output: Optional[str] = None) -> LLMTestCase:
        """转换为DeepEval测试用例"""
        # 自动重构context（如果需要）
        if not self.context and self.tool_calls:
            self.reconstruct_context()

        return LLMTestCase(
            input=self.input,
            actual_output=self.actual_output,
            expected_output=expected_output,
            context=self.context,
            retrieval_context=self.retrieval_context
        )
```

## 使用方法

### 1. 在pytest测试中自动使用

```python
from tests.test_mongodb_deepeval import MongoTestDataExtractor

extractor = MongoTestDataExtractor()
test_cases = extractor.extract_recent_cases(hours=24, limit=10)

for case in test_cases:
    # to_deepeval_case会自动重构context
    deepeval_case = case.to_deepeval_case()

    # 现在可以使用需要context的指标
    faithfulness = FaithfulnessMetric(threshold=0.75)
    faithfulness.measure(deepeval_case)
```

### 2. 在run_evaluation.py中使用

```bash
# 评估有工具调用的测试用例
uv run python run_evaluation.py --mode recent --hours 168 --limit 5 --with-tools

# 保存结果到文件
uv run python run_evaluation.py --mode recent --limit 10 --with-tools --output results.json
```

添加了 `--with-tools` 参数，只评估有工具调用的测试用例，这样Faithfulness和Hallucination指标才有意义。

### 3. 手动重构context

```python
from evaluation.context_reconstructor import ContextReconstructor

# 假设有工具调用数据
tool_calls = [
    {
        "function": {
            "name": "calculate_loan_payment",
            "arguments": '{"loan_amount": 50000, "annual_interest_rate": 0.05, "loan_term_months": 36}'
        }
    }
]

# 重构context
reconstructor = ContextReconstructor()
context = reconstructor.reconstruct_context_from_tool_calls(tool_calls)

print(f"Context: {context[0][:100]}...")
```

## 数据流程

```
MongoDB agno_sessions
    ↓
MongoTestDataExtractor
    ↓ 提取 tool_calls 和 tool_responses
MongoTestCase
    ↓ to_deepeval_case()
    ↓ (自动检测：如果没有context但有tool_calls)
    ↓
ContextReconstructor
    ↓ 重新执行工具
    ↓
Context (List[str])
    ↓
LLMTestCase (with retrieval_context)
    ↓
DeepEval Metrics (Faithfulness, Hallucination)
```

## 当前状态

### ✅ 已实现
1. MongoDB数据提取时自动获取tool_responses作为context
2. ContextReconstructor类用于重新执行工具（备用）
3. MongoTestCase自动context重构
4. run_evaluation.py支持 `--with-tools` 参数

### 📊 测试结果

最近的评估结果（5个测试用例）：

```
指标通过率:
  relevancy:    80.0% (4/5), 平均分: 85.67%
  faithfulness: 100.0% (5/5), 平均分: 94.92% ✅
  hallucination: 60.0% (3/5), 平均分: 16.67% ✅
  bias:         100.0% (5/5), 平均分: 0.00%

工具调用准确率: 100.0%
```

### 🔍 发现

1. **MongoDB已包含完整context**: 所有有工具调用的测试用例都已经有context（从tool_responses提取）
2. **重构功能作为备用**: ContextReconstructor主要用于MongoDB数据不完整的情况
3. **自动化工作良好**: `to_deepeval_case()`自动处理context，无需手动干预

## 注意事项

1. **工具函数必须是纯函数**: 重新执行工具不应该有副作用（如修改数据库）
2. **参数格式**: tool_calls中的arguments必须是JSON字符串
3. **错误处理**: 如果工具执行失败，会使用错误信息作为context占位符
4. **只在必要时重构**: 如果MongoDB已有context，不会重新执行工具

## 未来改进

1. **缓存机制**: 缓存重构的context，避免重复执行
2. **异步执行**: 并行执行多个工具调用
3. **工具模拟**: 对于有副作用的工具，提供模拟版本
4. **Context质量评估**: 检测context是否完整和有效
