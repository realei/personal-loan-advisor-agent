"""
MongoDB存储模块 - 用于持久化评估结果
包含两个集合：
1. eval_ci_results - CI/CD测试结果
2. eval_live_results - 实时评估结果
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum
import json
import hashlib
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError
import uuid


# ============= 数据模型定义 =============

class EvalType(Enum):
    """评估类型"""
    CI_TEST = "ci_test"           # CI/CD自动化测试
    LIVE_EVAL = "live_eval"        # 实时评估
    MANUAL_TEST = "manual_test"    # 手动测试
    BENCHMARK = "benchmark"        # 基准测试


class MetricStatus(Enum):
    """指标状态"""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class MetricResult:
    """单个指标的评估结果"""
    metric_name: str                          # 指标名称
    metric_type: str                          # 指标类型 (deepeval/custom)
    score: float                              # 分数
    threshold: float                          # 阈值
    status: MetricStatus                      # 状态
    passed: bool                              # 是否通过
    reason: Optional[str] = None             # 原因说明
    details: Optional[Dict] = None           # 详细信息
    error_message: Optional[str] = None      # 错误信息

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "metric_name": self.metric_name,
            "metric_type": self.metric_type,
            "score": self.score,
            "threshold": self.threshold,
            "status": self.status.value,
            "passed": self.passed,
            "reason": self.reason,
            "details": self.details,
            "error_message": self.error_message
        }


@dataclass
class TestCaseResult:
    """测试用例结果"""
    test_id: str                              # 测试ID
    session_id: str                           # 关联的session_id
    run_id: str                               # 关联的run_id
    input_text: str                           # 输入文本
    output_text: str                          # 输出文本
    metrics_results: List[MetricResult]       # 各项指标结果
    tool_calls: List[Dict] = field(default_factory=list)  # 工具调用
    performance_data: Dict = field(default_factory=dict)   # 性能数据
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "test_id": self.test_id,
            "session_id": self.session_id,
            "run_id": self.run_id,
            "input_text": self.input_text,
            "output_text": self.output_text[:500],  # 限制长度
            "metrics_results": [m.to_dict() for m in self.metrics_results],
            "tool_calls": self.tool_calls,
            "performance_data": self.performance_data,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class CITestResult:
    """CI测试结果 - 存储到 eval_ci_results collection"""
    _id: str = field(default_factory=lambda: str(uuid.uuid4()))  # MongoDB _id
    test_run_id: str = field(default_factory=lambda: str(uuid.uuid4()))  # 测试运行ID
    eval_type: EvalType = EvalType.CI_TEST

    # 测试环境信息
    environment: Dict = field(default_factory=dict)  # 环境信息
    git_commit: Optional[str] = None         # Git commit hash
    git_branch: Optional[str] = None         # Git branch
    triggered_by: str = "manual"             # 触发者 (manual/schedule/pr)

    # 测试配置
    test_suite: str = "default"              # 测试套件名称
    test_config: Dict = field(default_factory=dict)  # 测试配置

    # 测试结果
    test_cases: List[TestCaseResult] = field(default_factory=list)  # 测试用例结果
    total_tests: int = 0                     # 总测试数
    passed_tests: int = 0                    # 通过数
    failed_tests: int = 0                    # 失败数
    skipped_tests: int = 0                   # 跳过数

    # 汇总统计
    summary: Dict = field(default_factory=dict)  # 汇总信息
    metrics_summary: Dict = field(default_factory=dict)  # 指标汇总

    # 时间信息
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0

    # 状态
    status: str = "running"  # running/completed/failed/aborted
    error_message: Optional[str] = None

    def to_dict(self) -> Dict:
        """转换为MongoDB文档"""
        doc = {
            "_id": self._id,
            "test_run_id": self.test_run_id,
            "eval_type": self.eval_type.value,
            "environment": self.environment,
            "git_commit": self.git_commit,
            "git_branch": self.git_branch,
            "triggered_by": self.triggered_by,
            "test_suite": self.test_suite,
            "test_config": self.test_config,
            "test_cases": [tc.to_dict() for tc in self.test_cases],
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "skipped_tests": self.skipped_tests,
            "summary": self.summary,
            "metrics_summary": self.metrics_summary,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_seconds": self.duration_seconds,
            "status": self.status,
            "error_message": self.error_message
        }
        return doc


@dataclass
class LiveEvalResult:
    """实时评估结果 - 存储到 eval_live_results collection"""
    _id: str = field(default_factory=lambda: str(uuid.uuid4()))
    eval_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    eval_type: EvalType = EvalType.LIVE_EVAL

    # 关联信息
    session_id: str = ""                     # 关联的会话ID
    run_id: str = ""                         # 关联的运行ID
    user_id: Optional[str] = None            # 用户ID

    # 评估内容
    input_text: str = ""                     # 输入
    output_text: str = ""                    # 输出
    context: List[str] = field(default_factory=list)  # 上下文

    # 评估结果
    metrics_results: List[MetricResult] = field(default_factory=list)
    overall_score: float = 0                 # 总体评分

    # 工具相关
    tool_calls: List[Dict] = field(default_factory=list)
    tool_accuracy: Optional[float] = None
    parameter_correctness: Optional[float] = None

    # 性能数据
    performance: Dict = field(default_factory=dict)
    response_time: Optional[float] = None
    total_tokens: Optional[int] = None

    # 反馈
    feedback: Optional[str] = None           # 用户反馈
    recommendations: List[str] = field(default_factory=list)  # 改进建议

    # 时间戳
    evaluated_at: datetime = field(default_factory=datetime.now)

    # 元数据
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """转换为MongoDB文档"""
        doc = {
            "_id": self._id,
            "eval_id": self.eval_id,
            "eval_type": self.eval_type.value,
            "session_id": self.session_id,
            "run_id": self.run_id,
            "user_id": self.user_id,
            "input_text": self.input_text[:500],
            "output_text": self.output_text[:500],
            "context": self.context[:5] if self.context else [],  # 限制数量
            "metrics_results": [m.to_dict() for m in self.metrics_results],
            "overall_score": self.overall_score,
            "tool_calls": self.tool_calls,
            "tool_accuracy": self.tool_accuracy,
            "parameter_correctness": self.parameter_correctness,
            "performance": self.performance,
            "response_time": self.response_time,
            "total_tokens": self.total_tokens,
            "feedback": self.feedback,
            "recommendations": self.recommendations,
            "evaluated_at": self.evaluated_at,
            "metadata": self.metadata
        }
        return doc


# ============= MongoDB存储管理器 =============

class EvaluationStorage:
    """评估结果存储管理器"""

    def __init__(self,
                 mongodb_url: str = "mongodb://admin:password123@localhost:27017/",
                 db_name: str = "loan_advisor"):
        self.client = MongoClient(mongodb_url)
        self.db = self.client[db_name]

        # 创建collections
        self.ci_results = self.db["eval_ci_results"]
        self.live_results = self.db["eval_live_results"]

        # 创建索引
        self._create_indexes()

    def _create_indexes(self):
        """创建索引以优化查询"""
        # CI结果索引
        self.ci_results.create_index([("test_run_id", ASCENDING)])
        self.ci_results.create_index([("started_at", DESCENDING)])
        self.ci_results.create_index([("git_commit", ASCENDING)])
        self.ci_results.create_index([("git_branch", ASCENDING)])
        self.ci_results.create_index([("status", ASCENDING)])
        self.ci_results.create_index([
            ("test_suite", ASCENDING),
            ("started_at", DESCENDING)
        ])

        # 实时评估结果索引
        self.live_results.create_index([("eval_id", ASCENDING)])
        self.live_results.create_index([("session_id", ASCENDING)])
        self.live_results.create_index([("run_id", ASCENDING)])
        self.live_results.create_index([("evaluated_at", DESCENDING)])
        self.live_results.create_index([("user_id", ASCENDING)])
        self.live_results.create_index([
            ("session_id", ASCENDING),
            ("evaluated_at", DESCENDING)
        ])

    # ========== CI测试结果存储 ==========

    def save_ci_result(self, result: CITestResult) -> str:
        """保存CI测试结果"""
        try:
            doc = result.to_dict()
            self.ci_results.insert_one(doc)
            return result._id
        except DuplicateKeyError:
            # 更新现有记录
            self.ci_results.replace_one({"_id": result._id}, doc)
            return result._id

    def get_ci_result(self, test_run_id: str) -> Optional[Dict]:
        """获取CI测试结果"""
        return self.ci_results.find_one({"test_run_id": test_run_id})

    def get_latest_ci_results(self, limit: int = 10) -> List[Dict]:
        """获取最新的CI测试结果"""
        return list(self.ci_results.find().sort("started_at", DESCENDING).limit(limit))

    def get_ci_results_by_branch(self, branch: str, limit: int = 10) -> List[Dict]:
        """获取特定分支的CI测试结果"""
        return list(self.ci_results.find({"git_branch": branch})
                   .sort("started_at", DESCENDING)
                   .limit(limit))

    def get_ci_trend(self, days: int = 7) -> Dict:
        """获取CI测试趋势"""
        from datetime import datetime, timedelta

        start_date = datetime.now() - timedelta(days=days)

        pipeline = [
            {
                "$match": {
                    "started_at": {"$gte": start_date},
                    "status": "completed"
                }
            },
            {
                "$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$started_at"
                        }
                    },
                    "total_tests": {"$sum": "$total_tests"},
                    "passed_tests": {"$sum": "$passed_tests"},
                    "failed_tests": {"$sum": "$failed_tests"},
                    "avg_duration": {"$avg": "$duration_seconds"},
                    "runs": {"$sum": 1}
                }
            },
            {"$sort": {"_id": ASCENDING}}
        ]

        results = list(self.ci_results.aggregate(pipeline))
        return {
            "days": days,
            "trend": results
        }

    # ========== 实时评估结果存储 ==========

    def save_live_result(self, result: LiveEvalResult) -> str:
        """保存实时评估结果"""
        try:
            doc = result.to_dict()
            self.live_results.insert_one(doc)
            return result._id
        except DuplicateKeyError:
            self.live_results.replace_one({"_id": result._id}, doc)
            return result._id

    def get_live_result(self, eval_id: str) -> Optional[Dict]:
        """获取实时评估结果"""
        return self.live_results.find_one({"eval_id": eval_id})

    def get_session_evals(self, session_id: str) -> List[Dict]:
        """获取会话的所有评估"""
        return list(self.live_results.find({"session_id": session_id})
                   .sort("evaluated_at", DESCENDING))

    def get_recent_live_results(self, hours: int = 24, limit: int = 20) -> List[Dict]:
        """获取最近的实时评估结果"""
        from datetime import datetime, timedelta

        cutoff = datetime.now() - timedelta(hours=hours)

        return list(self.live_results.find({
            "evaluated_at": {"$gte": cutoff}
        }).sort("evaluated_at", DESCENDING).limit(limit))

    def get_metrics_statistics(self) -> Dict:
        """获取指标统计"""
        pipeline = [
            {"$unwind": "$metrics_results"},
            {
                "$group": {
                    "_id": "$metrics_results.metric_name",
                    "avg_score": {"$avg": "$metrics_results.score"},
                    "pass_count": {
                        "$sum": {
                            "$cond": ["$metrics_results.passed", 1, 0]
                        }
                    },
                    "fail_count": {
                        "$sum": {
                            "$cond": ["$metrics_results.passed", 0, 1]
                        }
                    },
                    "total_count": {"$sum": 1}
                }
            }
        ]

        results = list(self.live_results.aggregate(pipeline))

        stats = {}
        for r in results:
            stats[r["_id"]] = {
                "avg_score": r["avg_score"],
                "pass_rate": r["pass_count"] / r["total_count"] if r["total_count"] > 0 else 0,
                "total_evaluations": r["total_count"]
            }

        return stats

    # ========== 通用查询 ==========

    def get_evaluation_history(self,
                              session_id: Optional[str] = None,
                              user_id: Optional[str] = None,
                              days: int = 7) -> Dict:
        """获取评估历史"""
        from datetime import datetime, timedelta

        start_date = datetime.now() - timedelta(days=days)

        # 构建查询条件
        query = {"evaluated_at": {"$gte": start_date}}
        if session_id:
            query["session_id"] = session_id
        if user_id:
            query["user_id"] = user_id

        # 查询实时评估
        live_evals = list(self.live_results.find(query)
                         .sort("evaluated_at", DESCENDING))

        # 查询CI测试
        ci_query = {"started_at": {"$gte": start_date}}
        ci_tests = list(self.ci_results.find(ci_query)
                       .sort("started_at", DESCENDING))

        return {
            "period_days": days,
            "live_evaluations": len(live_evals),
            "ci_test_runs": len(ci_tests),
            "live_results": live_evals[:10],  # 最近10个
            "ci_results": ci_tests[:5]        # 最近5个
        }

    def generate_report(self, report_type: str = "daily") -> Dict:
        """生成评估报告"""
        from datetime import datetime, timedelta

        if report_type == "daily":
            days = 1
        elif report_type == "weekly":
            days = 7
        else:
            days = 30

        start_date = datetime.now() - timedelta(days=days)

        # CI测试统计
        ci_stats_list = list(self.ci_results.aggregate([
            {"$match": {"started_at": {"$gte": start_date}}},
            {
                "$group": {
                    "_id": None,
                    "total_runs": {"$sum": 1},
                    "total_tests": {"$sum": "$total_tests"},
                    "passed_tests": {"$sum": "$passed_tests"},
                    "failed_tests": {"$sum": "$failed_tests"},
                    "avg_duration": {"$avg": "$duration_seconds"}
                }
            }
        ]))

        # 实时评估统计
        live_stats_list = list(self.live_results.aggregate([
            {"$match": {"evaluated_at": {"$gte": start_date}}},
            {
                "$group": {
                    "_id": None,
                    "total_evals": {"$sum": 1},
                    "avg_overall_score": {"$avg": "$overall_score"},
                    "avg_response_time": {"$avg": "$response_time"},
                    "avg_tokens": {"$avg": "$total_tokens"}
                }
            }
        ]))

        # 指标性能
        metrics_perf = self.get_metrics_statistics()

        return {
            "report_type": report_type,
            "generated_at": datetime.now().isoformat(),
            "period_days": days,
            "ci_statistics": ci_stats_list[0] if ci_stats_list else {},
            "live_statistics": live_stats_list[0] if live_stats_list else {},
            "metrics_performance": metrics_perf
        }

    def cleanup_old_data(self, days_to_keep: int = 30):
        """清理旧数据"""
        from datetime import datetime, timedelta

        cutoff = datetime.now() - timedelta(days=days_to_keep)

        # 清理CI结果
        ci_result = self.ci_results.delete_many({
            "started_at": {"$lt": cutoff}
        })

        # 清理实时评估结果
        live_result = self.live_results.delete_many({
            "evaluated_at": {"$lt": cutoff}
        })

        return {
            "ci_deleted": ci_result.deleted_count,
            "live_deleted": live_result.deleted_count
        }

    def close(self):
        """关闭数据库连接"""
        self.client.close()


# ============= 使用示例 =============

if __name__ == "__main__":
    # 创建存储管理器
    storage = EvaluationStorage()

    # 示例：保存CI测试结果
    ci_result = CITestResult(
        test_suite="quality_metrics",
        git_commit="abc123",
        git_branch="main",
        triggered_by="github_actions"
    )

    # 添加测试用例结果
    test_case = TestCaseResult(
        test_id="test_001",
        session_id="session_123",
        run_id="run_456",
        input_text="计算5万美元贷款月供",
        output_text="月供为$1,498",
        metrics_results=[
            MetricResult(
                metric_name="answer_relevancy",
                metric_type="deepeval",
                score=0.85,
                threshold=0.7,
                status=MetricStatus.PASSED,
                passed=True
            )
        ]
    )
    ci_result.test_cases.append(test_case)

    # 保存
    ci_id = storage.save_ci_result(ci_result)
    print(f"CI结果已保存: {ci_id}")

    # 示例：保存实时评估结果
    live_result = LiveEvalResult(
        session_id="session_789",
        run_id="run_012",
        input_text="检查贷款资格",
        output_text="您符合贷款资格",
        overall_score=0.88
    )

    live_id = storage.save_live_result(live_result)
    print(f"实时评估结果已保存: {live_id}")

    # 生成报告
    report = storage.generate_report("daily")
    print(f"\n每日报告: {report}")

    storage.close()