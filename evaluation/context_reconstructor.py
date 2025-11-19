"""
Context重构器 - 从tool calls重新执行工具获取context
用于Faithfulness等需要retrieval_context的评估指标
"""

from typing import List, Dict, Any, Optional
import json
from src.agent.loan_advisor_tools import (
    check_loan_eligibility_raw,
    calculate_loan_payment_raw,
    generate_payment_schedule_raw,
    check_loan_affordability_raw,
    compare_loan_terms_raw,
    calculate_max_affordable_loan_raw
)


class ContextReconstructor:
    """从工具调用重构context"""

    def __init__(self):
        # 映射工具名称到实际函数
        self.tool_functions = {
            "check_loan_eligibility": check_loan_eligibility_raw,
            "calculate_loan_payment": calculate_loan_payment_raw,
            "generate_payment_schedule": generate_payment_schedule_raw,
            "check_loan_affordability": check_loan_affordability_raw,
            "compare_loan_terms": compare_loan_terms_raw,
            "calculate_max_affordable_loan": calculate_max_affordable_loan_raw
        }

    def reconstruct_context_from_tool_calls(self, tool_calls: List[Dict]) -> List[str]:
        """
        从工具调用列表重构context

        Args:
            tool_calls: 工具调用列表，格式为:
                [
                    {
                        "function": {
                            "name": "tool_name",
                            "arguments": "{...json...}"
                        }
                    }
                ]

        Returns:
            context列表，每个元素是工具返回的字符串结果
        """
        context = []

        for tool_call in tool_calls:
            if "function" not in tool_call:
                continue

            func_name = tool_call["function"]["name"]
            func_args_str = tool_call["function"].get("arguments", "{}")

            # 解析参数
            try:
                func_args = json.loads(func_args_str)
            except json.JSONDecodeError:
                print(f"⚠️  无法解析工具参数: {func_name}")
                continue

            # 执行工具获取结果
            try:
                result = self._execute_tool(func_name, func_args)
                if result:
                    context.append(result)
            except Exception as e:
                print(f"⚠️  执行工具 {func_name} 失败: {str(e)}")
                # 使用一个占位符，避免context为空
                context.append(f"[工具 {func_name} 执行失败: {str(e)}]")

        return context

    def _execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Optional[str]:
        """
        执行单个工具

        Args:
            tool_name: 工具名称
            args: 工具参数

        Returns:
            工具执行结果（字符串）
        """
        if tool_name not in self.tool_functions:
            print(f"⚠️  未知工具: {tool_name}")
            return None

        func = self.tool_functions[tool_name]

        try:
            # 调用工具函数
            result = func(**args)
            return result
        except Exception as e:
            print(f"⚠️  工具 {tool_name} 执行错误: {str(e)}")
            # 返回错误信息作为context
            return f"工具 {tool_name} 执行错误: {str(e)}"

    def get_context_summary(self, context: List[str]) -> str:
        """获取context摘要"""
        if not context:
            return "无context"

        summary = f"共{len(context)}个工具响应:\n"
        for i, ctx in enumerate(context, 1):
            preview = ctx[:200] + "..." if len(ctx) > 200 else ctx
            summary += f"{i}. {preview}\n"

        return summary


# ============= 使用示例 =============

def reconstruct_context_for_test_case(tool_calls: List[Dict]) -> List[str]:
    """
    便捷函数：为测试用例重构context

    Args:
        tool_calls: 工具调用列表

    Returns:
        context列表
    """
    reconstructor = ContextReconstructor()
    return reconstructor.reconstruct_context_from_tool_calls(tool_calls)


if __name__ == "__main__":
    # 测试示例
    print("测试Context重构器")
    print("=" * 60)

    # 示例工具调用
    sample_tool_calls = [
        {
            "function": {
                "name": "calculate_loan_payment",
                "arguments": json.dumps({
                    "loan_amount": 50000,
                    "annual_interest_rate": 0.05,
                    "loan_term_months": 36
                })
            }
        },
        {
            "function": {
                "name": "check_loan_eligibility",
                "arguments": json.dumps({
                    "age": 35,
                    "monthly_income": 8000,
                    "credit_score": 720,
                    "employment_status": "full_time",
                    "employment_length_years": 5,
                    "requested_loan_amount": 50000,
                    "loan_term_months": 36
                })
            }
        }
    ]

    # 重构context
    reconstructor = ContextReconstructor()
    context = reconstructor.reconstruct_context_from_tool_calls(sample_tool_calls)

    print(f"\n重构的Context ({len(context)}条):")
    for i, ctx in enumerate(context, 1):
        print(f"\n{i}. {ctx[:300]}...")

    # 获取摘要
    summary = reconstructor.get_context_summary(context)
    print(f"\nContext摘要:\n{summary}")