"""
DeepEval配置文件
集中管理所有评估相关的配置
"""

from typing import Dict, List, Any
import os


# ============= DeepEval配置 =============

# DeepEval评估使用的模型
# 可以在.env中配置DEEPEVAL_MODEL，默认为gpt-4o-mini
EVAL_MODEL = os.getenv("DEEPEVAL_MODEL", "gpt-4o-mini")

# API密钥（如果需要）
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Agent使用的模型（用于对话和工具调用）
# 可以在.env中配置AGENT_MODEL，默认为gpt-4o-mini
AGENT_MODEL = os.getenv("AGENT_MODEL", "gpt-4o-mini")

# 评估阈值 - 可以通过环境变量配置，未设置则使用默认值
METRIC_THRESHOLDS = {
    "answer_relevancy": float(os.getenv("EVAL_THRESHOLD_ANSWER_RELEVANCY", "0.7")),
    "faithfulness": float(os.getenv("EVAL_THRESHOLD_FAITHFULNESS", "0.75")),
    "hallucination": float(os.getenv("EVAL_THRESHOLD_HALLUCINATION", "0.3")),
    "bias": float(os.getenv("EVAL_THRESHOLD_BIAS", "0.3")),
    "toxicity": float(os.getenv("EVAL_THRESHOLD_TOXICITY", "0.2")),
    "contextual_relevancy": float(os.getenv("EVAL_THRESHOLD_CONTEXTUAL_RELEVANCY", "0.7")),
    "contextual_precision": float(os.getenv("EVAL_THRESHOLD_CONTEXTUAL_PRECISION", "0.7")),
    "contextual_recall": float(os.getenv("EVAL_THRESHOLD_CONTEXTUAL_RECALL", "0.7")),
}

# 自定义指标阈值 - 可以通过环境变量配置
CUSTOM_THRESHOLDS = {
    "tool_accuracy": float(os.getenv("EVAL_THRESHOLD_TOOL_ACCURACY", "0.8")),
    "parameter_correctness": float(os.getenv("EVAL_THRESHOLD_PARAMETER_CORRECTNESS", "0.9")),
    "response_time": float(os.getenv("EVAL_THRESHOLD_RESPONSE_TIME", "15.0")),
    "token_limit": int(os.getenv("EVAL_THRESHOLD_TOKEN_LIMIT", "5000")),
    "tool_chain_logic": float(os.getenv("EVAL_THRESHOLD_TOOL_CHAIN_LOGIC", "0.85")),
}

# 期望的工具映射
EXPECTED_TOOLS_MAP = {
    # 中文关键词
    "计算月供": ["calculate_loan_payment"],
    "计算还款": ["calculate_loan_payment"],
    "月供多少": ["calculate_loan_payment"],
    "每月还款": ["calculate_loan_payment"],

    "检查资格": ["check_loan_eligibility"],
    "是否符合": ["check_loan_eligibility"],
    "能否贷款": ["check_loan_eligibility"],
    "贷款资格": ["check_loan_eligibility"],

    "负担得起": ["check_loan_affordability"],
    "是否可负担": ["check_loan_affordability"],
    "承受能力": ["check_loan_affordability"],

    "比较贷款": ["compare_loan_terms"],
    "对比期限": ["compare_loan_terms"],
    "哪个划算": ["compare_loan_terms"],

    "还款计划": ["generate_payment_schedule"],
    "还款明细": ["generate_payment_schedule"],
    "分期表": ["generate_payment_schedule"],

    "最大贷款": ["calculate_max_affordable_loan"],
    "最多能贷": ["calculate_max_affordable_loan"],
    "贷款额度": ["calculate_max_affordable_loan"],

    # 英文关键词
    "calculate payment": ["calculate_loan_payment"],
    "monthly payment": ["calculate_loan_payment"],
    "check eligibility": ["check_loan_eligibility"],
    "loan eligibility": ["check_loan_eligibility"],
    "affordability": ["check_loan_affordability"],
    "compare loans": ["compare_loan_terms"],
    "payment schedule": ["generate_payment_schedule"],
    "maximum loan": ["calculate_max_affordable_loan"],

    # 复合场景
    "检查资格并计算": ["check_loan_eligibility", "calculate_loan_payment"],
    "计算并评估": ["calculate_loan_payment", "check_loan_affordability"],
    "全面分析": ["check_loan_eligibility", "calculate_loan_payment", "check_loan_affordability"],
}

# 参数验证规则
PARAMETER_VALIDATION_RULES = {
    "calculate_loan_payment": {
        "loan_amount": {
            "type": "number",
            "min": 1000,
            "max": 10000000,
            "required": True
        },
        "annual_interest_rate": {
            "type": "number",
            "min": 0.001,
            "max": 0.5,  # 必须是小数形式，不是百分比
            "required": True,
            "format": "decimal"  # 特殊标记：必须是小数
        },
        "loan_term_months": {
            "type": "integer",
            "min": 1,
            "max": 360,
            "required": True
        }
    },
    "check_loan_eligibility": {
        "age": {
            "type": "integer",
            "min": 18,
            "max": 100,
            "required": True
        },
        "monthly_income": {
            "type": "number",
            "min": 0,
            "required": True
        },
        "credit_score": {
            "type": "integer",
            "min": 300,
            "max": 850,
            "required": True
        },
        "requested_loan_amount": {
            "type": "number",
            "min": 1000,
            "required": True
        },
        "employment_status": {
            "type": "string",
            "enum": ["full_time", "part_time", "self_employed", "unemployed", "retired"],
            "required": True
        }
    },
    "check_loan_affordability": {
        "loan_amount": {
            "type": "number",
            "min": 1000,
            "required": True
        },
        "annual_interest_rate": {
            "type": "number",
            "min": 0.001,
            "max": 0.5,
            "required": True,
            "format": "decimal"
        },
        "loan_term_months": {
            "type": "integer",
            "min": 1,
            "max": 360,
            "required": True
        },
        "monthly_income": {
            "type": "number",
            "min": 0,
            "required": True
        },
        "existing_monthly_debt": {
            "type": "number",
            "min": 0,
            "required": False,
            "default": 0
        }
    }
}

# 性能基准（基于实际agent表现）
PERFORMANCE_BENCHMARKS = {
    "response_time": {
        "excellent": 5.0,    # 秒
        "good": 8.0,         # 根据实际数据：平均8.64秒
        "acceptable": 15.0,  # 阈值设为15秒
        "poor": 30.0         # 超过30秒则太慢
    },
    "token_usage": {
        "excellent": 2000,
        "good": 3500,        # 根据实际数据：平均3512 tokens
        "acceptable": 5000,  # 阈值设为5000
        "poor": 8000
    },
    "tool_calls": {
        "simple_query": 1,      # 简单查询应该只调用1个工具
        "moderate_query": 2,    # 中等查询2个工具
        "complex_query": 3,     # 复杂查询3个工具
        "max_allowed": 5        # 最多不超过5个
    }
}

# 测试数据筛选条件
TEST_DATA_FILTERS = {
    "recent": {
        "hours": 24,
        "limit": 20
    },
    "performance": {
        "hours": 168,  # 一周
        "limit": 100
    },
    "quality": {
        "hours": 48,
        "limit": 30
    }
}

# 报告配置
REPORT_CONFIG = {
    "include_details": True,
    "include_metrics": True,
    "include_tools": True,
    "include_performance": True,
    "output_format": "markdown",  # 可选: markdown, json, html
    "save_to_file": False,
    "file_path": "evaluation_report.md"
}

# 测试套件定义
TEST_SUITES = {
    "basic_quality": {
        "name": "基础质量测试",
        "metrics": ["answer_relevancy", "faithfulness"],
        "required": True
    },
    "advanced_quality": {
        "name": "高级质量测试",
        "metrics": ["hallucination", "bias", "toxicity"],
        "required": False
    },
    "context_evaluation": {
        "name": "上下文评估",
        "metrics": ["contextual_relevancy", "contextual_precision"],
        "required": False
    },
    "tool_evaluation": {
        "name": "工具评估",
        "metrics": ["tool_accuracy", "parameter_correctness"],
        "required": True
    },
    "performance": {
        "name": "性能评估",
        "metrics": ["response_time", "token_usage"],
        "required": True
    }
}

# CI/CD配置
CI_CONFIG = {
    "fail_on_threshold_breach": True,  # 低于阈值时失败
    "parallel_execution": True,        # 并行执行测试
    "max_workers": 4,                  # 最大并行数
    "retry_failed": True,              # 重试失败的测试
    "max_retries": 2,                  # 最大重试次数
    "generate_report": True,           # 生成测试报告
    "upload_results": False            # 上传结果到外部服务
}


# ============= 辅助函数 =============

def get_threshold(metric_name: str) -> float:
    """获取指标阈值"""
    if metric_name in METRIC_THRESHOLDS:
        return METRIC_THRESHOLDS[metric_name]
    elif metric_name in CUSTOM_THRESHOLDS:
        return CUSTOM_THRESHOLDS[metric_name]
    else:
        return 0.7  # 默认阈值


def get_expected_tools(input_text: str) -> List[str]:
    """根据输入文本获取期望的工具"""
    expected_tools = []
    input_lower = input_text.lower()

    for pattern, tools in EXPECTED_TOOLS_MAP.items():
        if pattern.lower() in input_lower:
            expected_tools.extend(tools)

    # 去重并返回
    return list(set(expected_tools))


def validate_parameter(func_name: str, param_name: str, param_value: Any) -> bool:
    """验证单个参数"""
    if func_name not in PARAMETER_VALIDATION_RULES:
        return True  # 未定义规则的函数默认通过

    rules = PARAMETER_VALIDATION_RULES[func_name].get(param_name, {})

    if not rules:
        return True  # 未定义规则的参数默认通过

    # 类型检查
    param_type = rules.get("type")
    if param_type == "number":
        if not isinstance(param_value, (int, float)):
            return False
    elif param_type == "integer":
        if not isinstance(param_value, int):
            return False
    elif param_type == "string":
        if not isinstance(param_value, str):
            return False

    # 范围检查
    if "min" in rules and param_value < rules["min"]:
        return False
    if "max" in rules and param_value > rules["max"]:
        return False

    # 枚举检查
    if "enum" in rules and param_value not in rules["enum"]:
        return False

    # 特殊格式检查
    if rules.get("format") == "decimal":
        # 检查是否是小数形式（0.05而不是5）
        if param_type == "number" and param_value >= 1:
            return False  # 利率不应该大于等于1

    return True


def get_performance_rating(metric: str, value: float) -> str:
    """获取性能评级"""
    if metric not in PERFORMANCE_BENCHMARKS:
        return "unknown"

    benchmarks = PERFORMANCE_BENCHMARKS[metric]

    if metric in ["response_time", "token_usage"]:
        # 越低越好
        if value <= benchmarks["excellent"]:
            return "excellent"
        elif value <= benchmarks["good"]:
            return "good"
        elif value <= benchmarks["acceptable"]:
            return "acceptable"
        else:
            return "poor"
    else:
        # 特殊处理
        return "unknown"


def format_test_result(metric_name: str, score: float, passed: bool, details: str = "") -> str:
    """格式化测试结果"""
    status = "✅" if passed else "❌"
    threshold = get_threshold(metric_name)

    result = f"{status} {metric_name}: {score:.2%}"

    if not passed:
        result += f" (threshold: {threshold:.2%})"

    if details:
        result += f"\n   {details}"

    return result