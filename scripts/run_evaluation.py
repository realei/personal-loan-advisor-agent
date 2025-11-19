#!/usr/bin/env python
"""
快速运行评估的脚本
可以直接运行评估而不需要pytest
"""

import sys
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import json

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from tests.test_mongodb_deepeval import MongoTestDataExtractor, MongoTestCase
from tests.deepeval_config import (
    EXPECTED_TOOLS_MAP,
    METRIC_THRESHOLDS,
    CUSTOM_THRESHOLDS,
    get_expected_tools,
    format_test_result
)
from deepeval.metrics import (
    AnswerRelevancyMetric,
    FaithfulnessMetric,
    HallucinationMetric,
    BiasMetric
)
from deepeval.test_case import LLMTestCase


class QuickEvaluator:
    """快速评估器"""

    def __init__(self):
        self.extractor = MongoTestDataExtractor()
        self.metrics = self._initialize_metrics()

    def _initialize_metrics(self) -> Dict:
        """初始化评估指标"""
        return {
            "relevancy": AnswerRelevancyMetric(
                threshold=METRIC_THRESHOLDS["answer_relevancy"],
                model="gpt-4o-mini"
            ),
            "faithfulness": FaithfulnessMetric(
                threshold=METRIC_THRESHOLDS["faithfulness"],
                model="gpt-4o-mini"
            ),
            "hallucination": HallucinationMetric(
                threshold=METRIC_THRESHOLDS["hallucination"],
                model="gpt-4o-mini"
            ),
            "bias": BiasMetric(
                threshold=METRIC_THRESHOLDS["bias"],
                model="gpt-4o-mini"
            )
        }

    def evaluate_recent(self, hours: int = 24, limit: int = 5, with_tools: bool = False) -> Dict:
        """评估最近的运行

        Args:
            hours: 查询最近N小时的数据
            limit: 最多返回N个测试用例
            with_tools: 是否只返回有工具调用的测试用例
        """
        print(f"\n{'='*60}")
        print(f"📊 评估最近{hours}小时的{limit}个运行")
        if with_tools:
            print(f"   （仅包含有工具调用的用例）")
        print(f"{'='*60}\n")

        # 获取测试用例
        all_cases = self.extractor.extract_recent_cases(hours=hours, limit=limit * 3 if with_tools else limit)

        # 过滤：只要有工具调用的
        if with_tools:
            test_cases = [c for c in all_cases if c.tool_calls][:limit]
        else:
            test_cases = all_cases[:limit]

        if not test_cases:
            print("❌ 未找到测试用例")
            return {}

        print(f"找到 {len(test_cases)} 个测试用例")
        if with_tools:
            print(f"  其中 {len([c for c in test_cases if c.context])} 个已有context\n")

        results = {}
        for i, case in enumerate(test_cases, 1):
            print(f"\n--- 测试用例 {i}/{len(test_cases)} ---")
            result = self._evaluate_single_case(case)
            results[case.test_id] = result

        return results

    def evaluate_by_pattern(self, pattern: str, limit: int = 3) -> Dict:
        """按模式评估"""
        print(f"\n{'='*60}")
        print(f"🔍 评估匹配模式 '{pattern}' 的{limit}个运行")
        print(f"{'='*60}\n")

        # 获取测试用例
        test_cases = self.extractor.extract_by_pattern(pattern, limit)

        if not test_cases:
            print(f"❌ 未找到匹配 '{pattern}' 的测试用例")
            return {}

        results = {}
        for i, case in enumerate(test_cases, 1):
            print(f"\n--- 测试用例 {i}/{len(test_cases)} ---")
            result = self._evaluate_single_case(case)
            results[case.test_id] = result

        return results

    def _evaluate_single_case(self, case: MongoTestCase) -> Dict:
        """评估单个测试用例"""
        print(f"ID: {case.test_id}")
        print(f"输入: {str(case.input)[:100]}...")
        print(f"输出: {str(case.actual_output)[:100]}...")

        # 确保context可用（用于Faithfulness等指标）
        if not case.context and case.tool_calls:
            print(f"  🔧 重构context: 从 {len(case.tool_calls)} 个工具调用")
            case.reconstruct_context()
            if case.context:
                print(f"  ✅ Context已重构: {len(case.context)} 条")
            else:
                print(f"  ⚠️ Context重构失败")

        result = {
            "test_id": case.test_id,
            "input": case.input,
            "output_preview": case.actual_output[:200],
            "metrics": {},
            "tools": self._evaluate_tools(case),
            "performance": self._evaluate_performance(case),
            "context_available": len(case.context) if case.context else 0
        }

        # 转换为DeepEval测试用例
        deepeval_case = case.to_deepeval_case()

        # 评估各项指标
        for metric_name, metric in self.metrics.items():
            try:
                metric.measure(deepeval_case)
                score = metric.score
                passed = metric.is_successful()
                reason = getattr(metric, 'reason', '')

                result["metrics"][metric_name] = {
                    "score": score,
                    "passed": passed,
                    "reason": reason
                }

                # 打印结果
                status = "✅" if passed else "❌"
                print(f"  {status} {metric_name}: {score:.2%}")

            except Exception as e:
                print(f"  ⚠️ {metric_name}: 评估失败 - {str(e)}")
                result["metrics"][metric_name] = {
                    "score": 0,
                    "passed": False,
                    "reason": str(e)
                }

        return result

    def _evaluate_tools(self, case: MongoTestCase) -> Dict:
        """评估工具使用"""
        actual_tools = []
        for tc in case.tool_calls:
            if "function" in tc:
                actual_tools.append(tc["function"]["name"])

        expected_tools = get_expected_tools(case.input)

        # 计算准确率
        if not expected_tools:
            accuracy = 1.0
        else:
            correct = len(set(actual_tools) & set(expected_tools))
            accuracy = correct / len(expected_tools) if expected_tools else 0

        return {
            "actual": actual_tools,
            "expected": expected_tools,
            "accuracy": accuracy,
            "passed": accuracy >= CUSTOM_THRESHOLDS["tool_accuracy"]
        }

    def _evaluate_performance(self, case: MongoTestCase) -> Dict:
        """评估性能"""
        perf = {}

        if case.metrics_data:
            tokens = case.metrics_data.get("total_tokens", 0)
            duration = case.metrics_data.get("duration", 0)

            perf["tokens"] = tokens
            perf["duration"] = duration
            perf["tokens_passed"] = tokens <= CUSTOM_THRESHOLDS["token_limit"]
            perf["duration_passed"] = duration <= CUSTOM_THRESHOLDS["response_time"]

        return perf

    def generate_summary(self, results: Dict) -> None:
        """生成汇总报告"""
        if not results:
            return

        print(f"\n{'='*60}")
        print(f"📈 评估汇总")
        print(f"{'='*60}\n")

        # 计算汇总统计
        total = len(results)
        metrics_summary = {}

        for test_id, result in results.items():
            for metric_name, metric_result in result["metrics"].items():
                if metric_name not in metrics_summary:
                    metrics_summary[metric_name] = {
                        "passed": 0,
                        "failed": 0,
                        "scores": []
                    }

                if metric_result["passed"]:
                    metrics_summary[metric_name]["passed"] += 1
                else:
                    metrics_summary[metric_name]["failed"] += 1

                metrics_summary[metric_name]["scores"].append(metric_result["score"])

        # 打印汇总
        print(f"总测试用例数: {total}\n")

        print("指标通过率:")
        for metric_name, summary in metrics_summary.items():
            pass_rate = summary["passed"] / total * 100
            avg_score = sum(summary["scores"]) / len(summary["scores"])
            print(f"  {metric_name}:")
            print(f"    - 通过率: {pass_rate:.1f}% ({summary['passed']}/{total})")
            print(f"    - 平均分: {avg_score:.2%}")

        # 工具准确率
        tool_accuracies = [r["tools"]["accuracy"] for r in results.values()]
        if tool_accuracies:
            avg_tool_accuracy = sum(tool_accuracies) / len(tool_accuracies)
            print(f"\n工具调用准确率: {avg_tool_accuracy:.1%}")

        # 性能统计
        durations = [r["performance"].get("duration", 0) for r in results.values() if r["performance"]]
        tokens = [r["performance"].get("tokens", 0) for r in results.values() if r["performance"]]

        if durations:
            print(f"\n性能统计:")
            print(f"  平均响应时间: {sum(durations)/len(durations):.2f}秒")
            print(f"  最大响应时间: {max(durations):.2f}秒")

        if tokens:
            print(f"  平均Token使用: {sum(tokens)/len(tokens):.0f}")
            print(f"  最大Token使用: {max(tokens)}")

    def cleanup(self):
        """清理资源"""
        self.extractor.close()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="运行Agent评估")

    parser.add_argument(
        "--mode",
        choices=["recent", "pattern", "report"],
        default="recent",
        help="评估模式"
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=24,
        help="查看最近N小时的数据（mode=recent时）"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="评估的测试用例数量"
    )
    parser.add_argument(
        "--pattern",
        type=str,
        help="搜索模式（mode=pattern时）"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="保存结果到文件"
    )
    parser.add_argument(
        "--with-tools",
        action="store_true",
        help="只评估有工具调用的测试用例"
    )

    args = parser.parse_args()

    # 创建评估器
    evaluator = QuickEvaluator()

    try:
        results = {}

        if args.mode == "recent":
            # 评估最近的运行
            results = evaluator.evaluate_recent(
                hours=args.hours,
                limit=args.limit,
                with_tools=args.with_tools
            )

        elif args.mode == "pattern" and args.pattern:
            # 按模式评估
            results = evaluator.evaluate_by_pattern(args.pattern, limit=args.limit)

        elif args.mode == "report":
            # 生成完整报告
            print("生成评估报告...")
            recent_results = evaluator.evaluate_recent(hours=24, limit=10)
            results.update(recent_results)

        # 生成汇总
        evaluator.generate_summary(results)

        # 保存结果
        if args.output and results:
            output_path = Path(args.output)
            output_path.write_text(json.dumps(results, indent=2, ensure_ascii=False))
            print(f"\n✅ 结果已保存到: {output_path}")

    finally:
        evaluator.cleanup()


if __name__ == "__main__":
    main()