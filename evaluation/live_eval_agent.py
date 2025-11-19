"""
实时评估Agent - 作为工具集成到主Agent中
可以实时评估Agent的表现并提供反馈
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import json
from datetime import datetime
from pymongo import MongoClient
from deepeval.metrics import (
    AnswerRelevancyMetric,
    FaithfulnessMetric,
    ContextualRelevancyMetric
)
from deepeval.test_case import LLMTestCase
from agno.tools import tool
from evaluation.mongodb_storage import (
    EvaluationStorage,
    LiveEvalResult,
    MetricResult,
    MetricStatus,
    EvalType
)


# ============= 评估工具定义 =============

@tool(name="evaluate_last_response", show_result=True)
def evaluate_last_response(
    session_id: Optional[str] = None,
    metric_types: List[str] = ["relevancy", "faithfulness"]
) -> str:
    """
    评估最近一次响应的质量

    Args:
        session_id: 会话ID，如果不提供则使用当前会话
        metric_types: 要评估的指标类型列表

    Returns:
        评估报告的格式化字符串
    """
    evaluator = LiveEvaluator()

    # 获取最近的响应
    last_run = evaluator.get_last_run(session_id)

    if not last_run:
        return "❌ 无法找到最近的响应数据"

    # 执行评估
    results = evaluator.evaluate_run(last_run, metric_types)

    # 格式化报告（包含保存到MongoDB）
    return evaluator.format_report(results, last_run)


@tool(name="evaluate_session_quality", show_result=True)
def evaluate_session_quality(
    session_id: Optional[str] = None,
    include_metrics: bool = True,
    include_tools: bool = True
) -> str:
    """
    评估整个会话的质量

    Args:
        session_id: 会话ID
        include_metrics: 是否包含性能指标
        include_tools: 是否包含工具使用分析

    Returns:
        会话质量评估报告
    """
    evaluator = LiveEvaluator()

    # 获取会话数据
    session_data = evaluator.get_session_data(session_id)

    if not session_data:
        return "❌ 无法找到会话数据"

    # 执行会话级评估
    report = evaluator.evaluate_session(
        session_data,
        include_metrics=include_metrics,
        include_tools=include_tools
    )

    return report


@tool(name="query_evaluation_history", show_result=True)
def query_evaluation_history(
    hours: int = 24,
    eval_type: str = "all",
    limit: int = 10
) -> str:
    """
    查询评估历史记录

    Args:
        hours: 查看最近N小时的记录
        eval_type: 评估类型 (all/ci/live)
        limit: 返回记录数量限制

    Returns:
        评估历史报告
    """
    evaluator = LiveEvaluator()
    storage = evaluator.storage

    report = "## 📜 评估历史查询\n\n"
    report += f"时间范围: 最近{hours}小时\n"
    report += f"类型: {eval_type}\n\n"

    # 查询实时评估
    if eval_type in ["all", "live"]:
        live_results = storage.get_recent_live_results(hours=hours, limit=limit)
        report += f"### 实时评估记录 ({len(live_results)}条)\n\n"

        for i, result in enumerate(live_results[:5], 1):
            report += f"{i}. **评估ID**: {result.get('eval_id', 'N/A')[:8]}\n"
            report += f"   - 时间: {result.get('evaluated_at')}\n"
            report += f"   - 总体评分: {result.get('overall_score', 0):.2%}\n"
            report += f"   - Token: {result.get('total_tokens', 'N/A')}\n"

            # 显示指标结果
            if result.get('metrics_results'):
                report += "   - 指标:\n"
                for metric in result['metrics_results'][:3]:
                    status = "✅" if metric.get('passed') else "❌"
                    report += f"     * {metric.get('metric_name')}: {status} {metric.get('score', 0):.2%}\n"
            report += "\n"

    # 查询CI测试
    if eval_type in ["all", "ci"]:
        ci_results = storage.get_latest_ci_results(limit=limit)
        report += f"### CI测试记录 ({len(ci_results)}条)\n\n"

        for i, result in enumerate(ci_results[:3], 1):
            report += f"{i}. **测试运行**: {result.get('test_run_id', 'N/A')[:8]}\n"
            report += f"   - 时间: {result.get('started_at')}\n"
            report += f"   - 分支: {result.get('git_branch', 'unknown')}\n"
            report += f"   - 通过率: {result.get('passed_tests', 0)}/{result.get('total_tests', 0)}\n"
            report += f"   - 耗时: {result.get('duration_seconds', 0):.1f}秒\n\n"

    # 获取统计信息
    stats = storage.get_metrics_statistics()
    if stats:
        report += "### 📊 指标统计\n\n"
        for metric_name, metric_stats in list(stats.items())[:5]:
            report += f"- **{metric_name}**:\n"
            report += f"  - 平均分: {metric_stats['avg_score']:.2%}\n"
            report += f"  - 通过率: {metric_stats['pass_rate']:.1%}\n"

    return report


@tool(name="benchmark_agent_performance", show_result=True)
def benchmark_agent_performance(
    time_range_hours: int = 24,
    compare_with_baseline: bool = True
) -> str:
    """
    对Agent进行性能基准测试

    Args:
        time_range_hours: 分析的时间范围（小时）
        compare_with_baseline: 是否与基准线比较

    Returns:
        性能基准测试报告
    """
    evaluator = LiveEvaluator()

    # 获取指定时间范围的数据
    benchmark_data = evaluator.collect_benchmark_data(time_range_hours)

    # 生成基准报告
    report = evaluator.generate_benchmark_report(
        benchmark_data,
        compare_with_baseline=compare_with_baseline
    )

    return report


# ============= 评估器实现 =============

@dataclass
class RunData:
    """运行数据"""
    session_id: str
    run_id: str
    input: str
    output: str
    tool_calls: List[Dict]
    tool_responses: List[str]
    metrics: Dict[str, Any]
    timestamp: datetime


@dataclass
class EvaluationScore:
    """评估分数"""
    metric_name: str
    score: float
    passed: bool
    details: Optional[str] = None


class LiveEvaluator:
    """实时评估器"""

    def __init__(self, mongodb_url: str = "mongodb://admin:password123@localhost:27017/",
                 db_name: str = "loan_advisor"):
        self.client = MongoClient(mongodb_url)
        self.db = self.client[db_name]
        self.sessions_collection = self.db["agno_sessions"]

        # 初始化存储管理器
        self.storage = EvaluationStorage(mongodb_url, db_name)

        # 初始化DeepEval指标
        self.metrics = {
            "relevancy": AnswerRelevancyMetric(threshold=0.7),
            "faithfulness": FaithfulnessMetric(threshold=0.8),
            "contextual": ContextualRelevancyMetric(threshold=0.7)
        }

        # 基准线定义
        self.baseline = {
            "relevancy": 0.75,
            "faithfulness": 0.80,
            "tool_accuracy": 0.90,
            "avg_response_time": 3.0,
            "avg_tokens": 2000
        }

    def get_last_run(self, session_id: Optional[str] = None) -> Optional[RunData]:
        """获取最近的运行数据"""
        filter_query = {}
        if session_id:
            filter_query["session_id"] = session_id

        # 获取最新的会话
        session = self.sessions_collection.find_one(
            filter_query,
            sort=[("updated_at", -1)]
        )

        if not session or not session.get("runs"):
            return None

        # 获取最后一个run
        last_run = session["runs"][-1]

        # 提取数据
        tool_calls = []
        tool_responses = []

        for msg in last_run.get("messages", []):
            if msg.get("role") == "assistant" and msg.get("tool_calls"):
                tool_calls.extend(msg["tool_calls"])
            elif msg.get("role") == "tool":
                tool_responses.append(msg.get("content", ""))

        return RunData(
            session_id=session["session_id"],
            run_id=last_run.get("run_id"),
            input=last_run.get("input", ""),
            output=last_run.get("content", ""),
            tool_calls=tool_calls,
            tool_responses=tool_responses,
            metrics=last_run.get("metrics", {}),
            timestamp=datetime.fromtimestamp(last_run.get("created_at", 0))
        )

    def evaluate_run(self, run_data: RunData, metric_types: List[str]) -> List[EvaluationScore]:
        """评估单个运行"""
        results = []

        # 创建DeepEval测试用例
        test_case = LLMTestCase(
            input=run_data.input,
            actual_output=run_data.output,
            context=run_data.tool_responses if run_data.tool_responses else None
        )

        # 执行选定的评估
        for metric_type in metric_types:
            if metric_type in self.metrics:
                metric = self.metrics[metric_type]
                metric.measure(test_case)

                results.append(EvaluationScore(
                    metric_name=metric_type,
                    score=metric.score,
                    passed=metric.is_successful(),
                    details=metric.reason
                ))

        # 添加自定义评估
        if "tool_accuracy" in metric_types:
            tool_score = self._evaluate_tool_accuracy(run_data)
            results.append(tool_score)

        return results

    def _evaluate_tool_accuracy(self, run_data: RunData) -> EvaluationScore:
        """评估工具使用准确性"""
        # 简化的工具准确性评估
        expected_tools_map = {
            "贷款": ["check_loan_eligibility", "calculate_loan_payment"],
            "月供": ["calculate_loan_payment"],
            "资格": ["check_loan_eligibility"]
        }

        actual_tools = [
            tc["function"]["name"]
            for tc in run_data.tool_calls
            if "function" in tc
        ]

        # 根据输入判断期望的工具
        expected_tools = []
        for keyword, tools in expected_tools_map.items():
            if keyword in run_data.input:
                expected_tools.extend(tools)

        expected_tools = list(set(expected_tools))

        # 计算准确率
        if not expected_tools:
            score = 1.0
        else:
            correct = len(set(actual_tools) & set(expected_tools))
            score = correct / len(expected_tools)

        return EvaluationScore(
            metric_name="tool_accuracy",
            score=score,
            passed=score >= 0.8,
            details=f"Used: {actual_tools}, Expected: {expected_tools}"
        )

    def format_report(self, results: List[EvaluationScore], run_data: Optional[RunData] = None) -> str:
        """格式化评估报告并保存到MongoDB"""
        report = "## 📊 响应质量评估报告\n\n"

        # 总体评分
        avg_score = sum(r.score for r in results) / len(results) if results else 0
        report += f"**总体评分**: {avg_score:.2%}\n\n"

        # 详细指标
        report += "### 详细指标:\n"
        metrics_results = []
        recommendations = []

        for result in results:
            status = "✅" if result.passed else "❌"
            report += f"- **{result.metric_name}**: {status} {result.score:.2%}\n"
            if result.details:
                report += f"  - {result.details}\n"

            # 转换为MetricResult用于存储
            metrics_results.append(MetricResult(
                metric_name=result.metric_name,
                metric_type="deepeval" if result.metric_name in ["relevancy", "faithfulness", "contextual"] else "custom",
                score=result.score,
                threshold=0.7,  # 默认阈值
                status=MetricStatus.PASSED if result.passed else MetricStatus.FAILED,
                passed=result.passed,
                reason=result.details
            ))

            # 收集建议
            if not result.passed:
                if result.metric_name == "relevancy":
                    recommendations.append("提高回答与问题的相关性")
                elif result.metric_name == "faithfulness":
                    recommendations.append("确保回答基于工具返回的事实")
                elif result.metric_name == "tool_accuracy":
                    recommendations.append("优化工具选择策略")

        # 建议
        report += "\n### 💡 改进建议:\n"
        for rec in recommendations:
            report += f"- {rec}\n"

        # 保存到MongoDB
        if run_data:
            live_result = LiveEvalResult(
                session_id=run_data.session_id,
                run_id=run_data.run_id,
                input_text=run_data.input,
                output_text=run_data.output,
                context=run_data.tool_responses,
                metrics_results=metrics_results,
                overall_score=avg_score,
                tool_calls=run_data.tool_calls,
                response_time=run_data.metrics.get("duration") if run_data.metrics else None,
                total_tokens=run_data.metrics.get("total_tokens") if run_data.metrics else None,
                recommendations=recommendations
            )

            eval_id = self.storage.save_live_result(live_result)
            report += f"\n\n📝 评估结果已保存: {eval_id}\n"

        return report

    def get_session_data(self, session_id: Optional[str]) -> Optional[Dict]:
        """获取会话数据"""
        filter_query = {}
        if session_id:
            filter_query["session_id"] = session_id

        return self.sessions_collection.find_one(
            filter_query,
            sort=[("updated_at", -1)]
        )

    def evaluate_session(self, session_data: Dict,
                        include_metrics: bool = True,
                        include_tools: bool = True) -> str:
        """评估整个会话"""
        report = "## 📈 会话质量分析报告\n\n"

        runs = session_data.get("runs", [])
        report += f"**会话ID**: {session_data.get('session_id')}\n"
        report += f"**交互次数**: {len(runs)}\n\n"

        if include_metrics and runs:
            # 性能指标分析
            total_tokens = sum(r.get("metrics", {}).get("total_tokens", 0) for r in runs)
            avg_response_time = sum(r.get("metrics", {}).get("duration", 0) for r in runs) / len(runs)

            report += "### ⚡ 性能指标:\n"
            report += f"- 总Token消耗: {total_tokens}\n"
            report += f"- 平均响应时间: {avg_response_time:.2f}秒\n"
            report += f"- Token效率: {total_tokens / len(runs):.0f} tokens/交互\n\n"

        if include_tools and runs:
            # 工具使用分析
            all_tools = []
            for run in runs:
                for msg in run.get("messages", []):
                    if msg.get("role") == "assistant" and msg.get("tool_calls"):
                        for tc in msg["tool_calls"]:
                            if "function" in tc:
                                all_tools.append(tc["function"]["name"])

            if all_tools:
                tool_counts = {}
                for tool in all_tools:
                    tool_counts[tool] = tool_counts.get(tool, 0) + 1

                report += "### 🔧 工具使用统计:\n"
                for tool, count in sorted(tool_counts.items(), key=lambda x: x[1], reverse=True):
                    report += f"- {tool}: {count}次\n"

        return report

    def collect_benchmark_data(self, time_range_hours: int) -> Dict:
        """收集基准测试数据"""
        from datetime import datetime, timedelta

        cutoff_time = datetime.now() - timedelta(hours=time_range_hours)
        cutoff_timestamp = cutoff_time.timestamp()

        # 查询指定时间范围的会话
        sessions = self.sessions_collection.find({
            "updated_at": {"$gte": cutoff_timestamp}
        })

        # 聚合数据
        data = {
            "total_sessions": 0,
            "total_runs": 0,
            "total_tokens": 0,
            "total_duration": 0,
            "tool_usage": {},
            "scores": []
        }

        for session in sessions:
            data["total_sessions"] += 1
            for run in session.get("runs", []):
                data["total_runs"] += 1
                metrics = run.get("metrics", {})
                data["total_tokens"] += metrics.get("total_tokens", 0)
                data["total_duration"] += metrics.get("duration", 0)

        return data

    def generate_benchmark_report(self, benchmark_data: Dict,
                                 compare_with_baseline: bool = True) -> str:
        """生成基准测试报告"""
        report = "## 🎯 Agent性能基准测试报告\n\n"

        if benchmark_data["total_runs"] == 0:
            return report + "❌ 没有足够的数据进行基准测试\n"

        # 计算平均值
        avg_tokens = benchmark_data["total_tokens"] / benchmark_data["total_runs"]
        avg_duration = benchmark_data["total_duration"] / benchmark_data["total_runs"]

        report += "### 📊 性能统计:\n"
        report += f"- 总会话数: {benchmark_data['total_sessions']}\n"
        report += f"- 总交互次数: {benchmark_data['total_runs']}\n"
        report += f"- 平均Token消耗: {avg_tokens:.0f}\n"
        report += f"- 平均响应时间: {avg_duration:.2f}秒\n\n"

        if compare_with_baseline:
            report += "### 📈 与基准线对比:\n"

            # Token对比
            token_diff = (avg_tokens - self.baseline["avg_tokens"]) / self.baseline["avg_tokens"] * 100
            token_status = "🟢" if avg_tokens <= self.baseline["avg_tokens"] else "🔴"
            report += f"- Token消耗: {token_status} {token_diff:+.1f}% (基准: {self.baseline['avg_tokens']})\n"

            # 响应时间对比
            time_diff = (avg_duration - self.baseline["avg_response_time"]) / self.baseline["avg_response_time"] * 100
            time_status = "🟢" if avg_duration <= self.baseline["avg_response_time"] else "🔴"
            report += f"- 响应时间: {time_status} {time_diff:+.1f}% (基准: {self.baseline['avg_response_time']}s)\n"

        return report


# ============= 集成到Agent =============

def create_eval_tools():
    """创建评估工具列表，可以添加到主Agent中"""
    return [
        evaluate_last_response,
        evaluate_session_quality,
        query_evaluation_history,
        benchmark_agent_performance
    ]


# ============= 独立运行示例 =============

if __name__ == "__main__":
    # 示例：评估最近的响应
    result = evaluate_last_response(metric_types=["relevancy", "faithfulness", "tool_accuracy"])
    print(result)

    # 示例：评估会话质量
    session_report = evaluate_session_quality(include_metrics=True, include_tools=True)
    print(session_report)

    # 示例：基准测试
    benchmark = benchmark_agent_performance(time_range_hours=24)
    print(benchmark)