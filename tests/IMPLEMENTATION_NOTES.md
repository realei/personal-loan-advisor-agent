# Agent 评估系统实现笔记

## ✅ 已完成的实现

### 核心功能

1. **自动提取工具调用信息**
   - 从 Agent response 的 `messages` 中自动提取工具调用
   - 解析工具名称和 JSON 格式的参数
   - 无需手动定义 `expected_tools` 和 `expected_tool_args`

2. **工具重新执行机制**
   - 实现 `_reconstruct_context()` 方法
   - 使用提取的参数重新执行工具
   - 获得真实的工具返回结果作为 `retrieval_context`
   - 用于 DeepEval 的 Faithfulness 和 Hallucination metrics

3. **智能序列化支持**
   - 自动检测结果类型（Pydantic model 或 dataclass）
   - Pydantic models: 使用 `model_dump()`
   - Dataclasses: 使用 `dataclasses.asdict()`
   - 特殊处理: pandas DataFrame 转换为 dict
   - 统一转换为 JSON 字符串

## 🔧 技术细节

### 1. 工具调用提取

```python
# 从 agent response 中提取
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

### 2. 工具重新执行

```python
def _reconstruct_context(self, tool_calls_with_args: list) -> list:
    """重新执行工具获得准确的 retrieval_context"""
    from dataclasses import asdict, is_dataclass

    # 初始化工具实例
    eligibility_checker = LoanEligibilityTool(...)
    loan_calculator = LoanCalculatorTool(...)

    # 定义序列化辅助函数
    def serialize_result(result):
        if hasattr(result, 'model_dump'):
            return json.dumps(result.model_dump())
        elif is_dataclass(result):
            result_dict = asdict(result)
            # 处理 pandas DataFrame
            if 'schedule' in result_dict and hasattr(result_dict['schedule'], 'to_dict'):
                result_dict['schedule'] = result_dict['schedule'].to_dict(orient='records')
            return json.dumps(result_dict, default=str)
        else:
            return json.dumps(str(result))

    # 根据工具名称重新执行
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

### 3. 关键决策

#### 为什么重新执行工具而不是从消息提取？

1. **准确性**: 工具的实际返回值是确定性的，重新执行确保获得相同结果
2. **完整性**: 消息中可能只包含部分信息，重新执行获得完整结果
3. **可验证性**: 可以验证工具是否正常工作
4. **Faithfulness 评估**: DeepEval 的 Faithfulness metric 需要准确的 retrieval_context

#### 为什么使用底层工具类而不是装饰器函数？

- `@tool` 装饰器返回的是 `Function` 对象，不能直接调用
- 底层工具类提供了真实的方法实现
- 可以直接传递参数并获得结果

#### 为什么需要智能序列化？

- 工具返回的类型不统一：
  - `LoanEligibilityResult`: Pydantic model
  - `LoanCalculation`: Dataclass
  - `AmortizationSchedule`: 包含 pandas DataFrame 的 dataclass
- 需要统一转换为 JSON 字符串供 DeepEval 使用
- `default=str` 处理特殊类型（如 datetime）

## 📊 测试结果

### 快速验证（无 LLM 调用）

```bash
# 工具调用信息展示
uv run pytest tests/test_loan_advisor_agent.py::test_tool_calls_info -v -s
# 结果: 成功提取工具名称和参数，14s 完成

# 输出关键词验证
uv run pytest tests/test_loan_advisor_agent.py::test_expected_output_keywords -v -s
# 结果: 成功验证输出包含预期关键词，14s 完成
```

### 完整评估（包含 LLM metrics）

```bash
uv run pytest tests/test_loan_advisor_agent.py::test_individual_case_example -v -s
# 结果:
# - AnswerRelevancyMetric: 0.79 ✅ PASS
# - FaithfulnessMetric: 1.00 ✅ PASS
# - HallucinationMetric: 0.33 ✅ PASS
```

## 🎯 优势总结

### 相比手动定义

| 方面 | 手动定义 | 自动提取 + 工具重执行 |
|------|---------|---------------------|
| 测试用例定义 | 需要 5 个字段 | 只需 3 个字段 |
| Expected tools | 手动写 | ✅ 自动提取 |
| Tool arguments | 手动写 | ✅ 自动提取 |
| Retrieval context | 手动构造 | ✅ 重新执行获得 |
| 准确性 | 可能过时 | ✅ 始终准确 |
| 维护成本 | 高 | ✅ 低 |

### 关键指标

- **代码简化**: TEST_CASES 定义减少 40% 代码量
- **准确性提升**: retrieval_context 100% 准确（重新执行）
- **开发效率**: 添加新测试用例只需 3 行代码
- **可维护性**: 工具签名变化时无需更新测试用例

## 🚀 未来改进

### 可选优化

1. **缓存工具执行结果**
   - 如果同一工具调用多次出现，可以缓存结果
   - 减少重复执行时间

2. **并行执行工具**
   - 多个工具调用可以并行执行
   - 使用 `asyncio` 或 `concurrent.futures`

3. **支持更多工具类型**
   - 当前支持 loan_calculator 和 loan_eligibility
   - 可以添加更多工具的重执行逻辑

4. **错误处理增强**
   - 当前只捕获异常并记录错误消息
   - 可以添加更详细的错误信息和重试机制

## 📝 经验教训

### 遇到的问题

1. **问题**: `'Function' object is not callable`
   - **原因**: 尝试调用 `@tool` 装饰器函数
   - **解决**: 导入底层工具类

2. **问题**: 方法名不匹配
   - **原因**: 假设的方法名与实际不符
   - **解决**: 检查实际类定义

3. **问题**: `'LoanCalculation' object has no attribute 'model_dump'`
   - **原因**: Dataclass 不是 Pydantic model
   - **解决**: 使用 `dataclasses.asdict()` + 类型检测

### 最佳实践

1. **先检查类型再序列化**
   - 使用 `hasattr()` 检查 Pydantic
   - 使用 `is_dataclass()` 检查 dataclass

2. **使用 default=str 处理特殊类型**
   - pandas DataFrame, datetime 等
   - 确保 JSON 序列化不失败

3. **Session-scoped fixtures**
   - Agent 运行较慢（5-10秒/用例）
   - 使用 `scope="session"` 只运行一次

## 🔗 相关文件

- `tests/test_loan_advisor_agent.py` - 主测试文件
- `tests/README_EVALUATION.md` - 详细使用文档
- `tests/SUMMARY.md` - 功能总结
- `src/tools/loan_calculator.py` - 贷款计算工具
- `src/tools/loan_eligibility.py` - 资格检查工具

## ✅ 验证清单

- [x] 自动提取工具调用信息
- [x] 重新执行工具获得 retrieval_context
- [x] 支持 Pydantic models 序列化
- [x] 支持 dataclasses 序列化
- [x] 处理 pandas DataFrame
- [x] 工具调用信息测试通过
- [x] 输出关键词验证测试通过
- [x] Reference-free metrics 评估通过
- [x] 文档更新完成
