"""
评估框架设计 - 基于MongoDB数据的DeepEval集成
符合SOLID原则的评估系统架构
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
from pymongo import MongoClient
from deepeval import evaluate
from deepeval.metrics import (
    AnswerRelevancyMetric,
    FaithfulnessMetric,
    HallucinationMetric,
    BiasMetric,
    ToxicityMetric
)
from deepeval.test_case import LLMTestCase


# ============= 数据模型 =============

@dataclass
class AgentRun:
    """Agent运行数据模型"""
    session_id: str
    run_id: str
    input: str
    output: str
    messages: List[Dict[str, Any]]
    tool_calls: List[Dict[str, Any]]
    tool_responses: List[str]
    metrics: Dict[str, Any]


@dataclass
class EvaluationResult:
    """评估结果"""
    metric_name: str
    score: float
    passed: bool
    reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class MetricType(Enum):
    """评估指标类型"""
    # DeepEval标准指标
    ANSWER_RELEVANCY = "answer_relevancy"
    FAITHFULNESS = "faithfulness"
    HALLUCINATION = "hallucination"
    BIAS = "bias"
    TOXICITY = "toxicity"

    # Agentic指标
    TOOL_ACCURACY = "tool_accuracy"
    PARAMETER_CORRECTNESS = "parameter_correctness"
    TOOL_SEQUENCE = "tool_sequence"
    TASK_COMPLETION = "task_completion"

    # RAG指标
    CONTEXT_RELEVANCY = "context_relevancy"
    ANSWER_ATTRIBUTION = "answer_attribution"


# ============= 抽象接口（SOLID - Interface Segregation） =============

class DataExtractor(ABC):
    """数据提取器接口"""

    @abstractmethod
    def extract_runs(self, filter_criteria: Dict[str, Any]) -> List[AgentRun]:
        """从数据源提取Agent运行数据"""
        pass


class Evaluator(ABC):
    """评估器基础接口"""

    @abstractmethod
    def evaluate(self, run: AgentRun) -> EvaluationResult:
        """评估单个运行"""
        pass

    @abstractmethod
    def get_metric_type(self) -> MetricType:
        """获取评估指标类型"""
        pass


class BatchEvaluator(ABC):
    """批量评估器接口"""

    @abstractmethod
    def evaluate_batch(self, runs: List[AgentRun]) -> List[EvaluationResult]:
        """批量评估"""
        pass


# ============= 具体实现（SOLID - Single Responsibility） =============

class MongoDataExtractor(DataExtractor):
    """MongoDB数据提取器"""

    def __init__(self, connection_url: str, db_name: str, collection_name: str):
        self.client = MongoClient(connection_url)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def extract_runs(self, filter_criteria: Dict[str, Any] = None) -> List[AgentRun]:
        """从MongoDB提取运行数据"""
        filter_criteria = filter_criteria or {}
        sessions = self.collection.find(filter_criteria)

        runs = []
        for session in sessions:
            session_id = session.get("session_id")

            for run_data in session.get("runs", []):
                # 提取工具调用和响应
                tool_calls = []
                tool_responses = []

                messages = run_data.get("messages", [])
                for msg in messages:
                    if msg.get("role") == "assistant" and msg.get("tool_calls"):
                        tool_calls.extend(msg["tool_calls"])
                    elif msg.get("role") == "tool":
                        tool_responses.append(msg.get("content", ""))

                runs.append(AgentRun(
                    session_id=session_id,
                    run_id=run_data.get("run_id"),
                    input=run_data.get("input", ""),
                    output=run_data.get("content", ""),
                    messages=messages,
                    tool_calls=tool_calls,
                    tool_responses=tool_responses,
                    metrics=run_data.get("metrics", {})
                ))

        return runs


class DeepEvalRelevancyEvaluator(Evaluator):
    """答案相关性评估器"""

    def __init__(self, threshold: float = 0.7):
        self.metric = AnswerRelevancyMetric(threshold=threshold)

    def evaluate(self, run: AgentRun) -> EvaluationResult:
        """评估答案相关性"""
        test_case = LLMTestCase(
            input=run.input,
            actual_output=run.output
        )

        self.metric.measure(test_case)

        return EvaluationResult(
            metric_name="Answer Relevancy",
            score=self.metric.score,
            passed=self.metric.is_successful(),
            reason=self.metric.reason
        )

    def get_metric_type(self) -> MetricType:
        return MetricType.ANSWER_RELEVANCY


class ToolAccuracyEvaluator(Evaluator):
    """工具调用准确性评估器（Agentic）"""

    def __init__(self, expected_tools: Dict[str, List[str]]):
        """
        expected_tools: {问题模式: [期望的工具列表]}
        """
        self.expected_tools = expected_tools

    def evaluate(self, run: AgentRun) -> EvaluationResult:
        """评估工具调用准确性"""
        actual_tools = [
            tc["function"]["name"]
            for tc in run.tool_calls
            if "function" in tc
        ]

        # 根据输入匹配期望的工具
        expected = self._match_expected_tools(run.input)

        # 计算准确率
        if not expected:
            score = 1.0  # 没有期望则默认正确
        else:
            correct = len(set(actual_tools) & set(expected))
            score = correct / len(expected) if expected else 0

        return EvaluationResult(
            metric_name="Tool Accuracy",
            score=score,
            passed=score >= 0.8,
            reason=f"Used tools: {actual_tools}, Expected: {expected}",
            metadata={
                "actual_tools": actual_tools,
                "expected_tools": expected
            }
        )

    def _match_expected_tools(self, input_text: str) -> List[str]:
        """根据输入匹配期望的工具"""
        for pattern, tools in self.expected_tools.items():
            if pattern.lower() in input_text.lower():
                return tools
        return []

    def get_metric_type(self) -> MetricType:
        return MetricType.TOOL_ACCURACY


class ParameterCorrectnessEvaluator(Evaluator):
    """参数正确性评估器（Referenceless）"""

    def evaluate(self, run: AgentRun) -> EvaluationResult:
        """评估工具参数的正确性"""
        errors = []
        total_params = 0
        correct_params = 0

        for tool_call in run.tool_calls:
            if "function" not in tool_call:
                continue

            func_name = tool_call["function"]["name"]
            args = json.loads(tool_call["function"].get("arguments", "{}"))

            # 验证参数逻辑
            validation = self._validate_parameters(func_name, args, run.input)
            total_params += len(validation)
            correct_params += sum(1 for v in validation.values() if v["valid"])

            for param, result in validation.items():
                if not result["valid"]:
                    errors.append(f"{func_name}.{param}: {result['reason']}")

        score = correct_params / total_params if total_params > 0 else 1.0

        return EvaluationResult(
            metric_name="Parameter Correctness",
            score=score,
            passed=score >= 0.9,
            reason="; ".join(errors) if errors else "All parameters valid",
            metadata={
                "total_parameters": total_params,
                "correct_parameters": correct_params
            }
        )

    def _validate_parameters(self, func_name: str, args: Dict, input_text: str) -> Dict:
        """验证参数的业务逻辑正确性"""
        validation = {}

        # 贷款计算相关验证
        if func_name == "calculate_loan_payment":
            # 验证利率范围
            rate = args.get("annual_interest_rate", 0)
            validation["annual_interest_rate"] = {
                "valid": 0 < rate < 1,  # 应该是小数而非百分比
                "reason": "Rate should be decimal (0.05 not 5)"
            }

            # 验证贷款金额
            amount = args.get("loan_amount", 0)
            validation["loan_amount"] = {
                "valid": amount > 0,
                "reason": "Amount should be positive"
            }

            # 验证期限
            term = args.get("loan_term_months", 0)
            validation["loan_term_months"] = {
                "valid": term > 0 and term <= 360,
                "reason": "Term should be 1-360 months"
            }

        elif func_name == "check_loan_eligibility":
            # 验证信用分数
            score = args.get("credit_score", 0)
            validation["credit_score"] = {
                "valid": 300 <= score <= 850,
                "reason": "Credit score should be 300-850"
            }

            # 验证年龄
            age = args.get("age", 0)
            validation["age"] = {
                "valid": 18 <= age <= 100,
                "reason": "Age should be 18-100"
            }

        return validation

    def get_metric_type(self) -> MetricType:
        return MetricType.PARAMETER_CORRECTNESS


# ============= 评估管道（SOLID - Open/Closed） =============

class EvaluationPipeline:
    """评估管道 - 可扩展新的评估器"""

    def __init__(self, data_extractor: DataExtractor):
        self.data_extractor = data_extractor
        self.evaluators: List[Evaluator] = []

    def add_evaluator(self, evaluator: Evaluator) -> 'EvaluationPipeline':
        """添加评估器（链式调用）"""
        self.evaluators.append(evaluator)
        return self

    def run(self, filter_criteria: Dict[str, Any] = None) -> Dict[str, List[EvaluationResult]]:
        """运行评估管道"""
        runs = self.data_extractor.extract_runs(filter_criteria)
        results = {}

        for evaluator in self.evaluators:
            metric_type = evaluator.get_metric_type().value
            results[metric_type] = []

            for run in runs:
                result = evaluator.evaluate(run)
                results[metric_type].append(result)

        return results

    def generate_report(self, results: Dict[str, List[EvaluationResult]]) -> Dict:
        """生成评估报告"""
        report = {
            "summary": {},
            "details": {}
        }

        for metric_type, metric_results in results.items():
            scores = [r.score for r in metric_results]
            passed = [r.passed for r in metric_results]

            report["summary"][metric_type] = {
                "average_score": sum(scores) / len(scores) if scores else 0,
                "pass_rate": sum(passed) / len(passed) if passed else 0,
                "total_evaluated": len(metric_results)
            }

            report["details"][metric_type] = [
                {
                    "score": r.score,
                    "passed": r.passed,
                    "reason": r.reason
                }
                for r in metric_results
            ]

        return report


# ============= 使用示例 =============

def create_evaluation_pipeline(mongodb_url: str, db_name: str) -> EvaluationPipeline:
    """创建评估管道实例"""

    # 数据提取器
    extractor = MongoDataExtractor(
        connection_url=mongodb_url,
        db_name=db_name,
        collection_name="agno_sessions"
    )

    # 期望的工具映射
    expected_tools = {
        "贷款": ["check_loan_eligibility", "calculate_loan_payment"],
        "月供": ["calculate_loan_payment"],
        "资格": ["check_loan_eligibility"],
        "负担": ["check_loan_affordability"],
        "比较": ["compare_loan_terms"]
    }

    # 创建管道并添加评估器
    pipeline = EvaluationPipeline(extractor)
    pipeline.add_evaluator(DeepEvalRelevancyEvaluator(threshold=0.7))
    pipeline.add_evaluator(ToolAccuracyEvaluator(expected_tools))
    pipeline.add_evaluator(ParameterCorrectnessEvaluator())

    return pipeline