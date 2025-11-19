#!/usr/bin/env python3
"""
模型配置使用示例
演示如何使用AGENT_MODEL和DEEPEVAL_MODEL配置
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.config import config
from tests.deepeval_config import AGENT_MODEL, EVAL_MODEL


def demo_config_usage():
    """演示配置使用"""

    print("=" * 70)
    print("模型配置使用示例")
    print("=" * 70)

    # 示例1: 查看当前配置
    print("\n📋 示例1: 查看当前配置\n")
    print(f"Agent模型: {config.api.agent_model}")
    print(f"DeepEval模型: {config.api.deepeval_model}")
    print(f"Temperature: {config.api.temperature}")

    # 示例2: Agent使用场景
    print("\n🤖 示例2: Agent使用配置\n")
    print("在创建Agent时使用:")
    print(f"""
from src.utils.config import config
from agno import Agent, OpenAIChat

agent = Agent(
    name="Personal Loan Advisor",
    model=OpenAIChat(
        id=config.api.agent_model,  # 使用AGENT_MODEL环境变量
        temperature=config.api.temperature
    ),
)
    """)
    print(f"✅ 当前会使用模型: {config.api.agent_model}")

    # 示例3: DeepEval使用场景
    print("\n🧪 示例3: DeepEval评估使用配置\n")
    print("在评估时使用:")
    print(f"""
from tests.deepeval_config import EVAL_MODEL
from deepeval.metrics import AnswerRelevancyMetric

metric = AnswerRelevancyMetric(
    model=EVAL_MODEL,  # 使用DEEPEVAL_MODEL环境变量
    threshold=0.7
)
    """)
    print(f"✅ 当前会使用模型: {EVAL_MODEL}")

    # 示例4: 切换配置
    print("\n🔄 示例4: 如何切换配置\n")
    print("方式1 - 修改 .env 文件:")
    print("""
# 开发环境 - 成本优化
AGENT_MODEL=gpt-4o-mini
DEEPEVAL_MODEL=gpt-4o-mini

# 生产环境 - 性能优先
AGENT_MODEL=gpt-4o
DEEPEVAL_MODEL=gpt-4o-mini
    """)

    print("\n方式2 - 临时环境变量:")
    print("  AGENT_MODEL=gpt-4o uv run python src/agent/loan_advisor_agent.py")

    # 示例5: 成本估算
    print("\n💰 示例5: 成本对比\n")

    costs = {
        "gpt-4o-mini": {"input": 0.150, "output": 0.600},  # per 1M tokens
        "gpt-4o": {"input": 2.50, "output": 10.00},
    }

    print("假设每次对话平均使用3000 tokens (2000输入 + 1000输出):")
    print()

    for model, price in costs.items():
        input_cost = (2000 / 1_000_000) * price["input"]
        output_cost = (1000 / 1_000_000) * price["output"]
        total_cost = input_cost + output_cost
        print(f"{model}:")
        print(f"  单次对话成本: ${total_cost:.6f}")
        print(f"  1000次对话成本: ${total_cost * 1000:.2f}")
        print()

    # 示例6: 推荐配置
    print("\n⭐ 示例6: 推荐配置\n")

    scenarios = {
        "开发/测试": {
            "agent": "gpt-4o-mini",
            "eval": "gpt-4o-mini",
            "理由": "成本低，迭代快",
        },
        "面试演示": {
            "agent": "gpt-4o-mini",
            "eval": "gpt-4o-mini",
            "理由": "性能足够，成本可控",
        },
        "生产环境": {
            "agent": "gpt-4o",
            "eval": "gpt-4o-mini",
            "理由": "用户体验好，评估成本低",
        },
    }

    for scenario, conf in scenarios.items():
        print(f"{scenario}:")
        print(f"  AGENT_MODEL={conf['agent']}")
        print(f"  DEEPEVAL_MODEL={conf['eval']}")
        print(f"  理由: {conf['理由']}")
        print()

    print("=" * 70)
    print("💡 提示: 运行 'uv run python scripts/check_config.py' 检查当前配置")
    print("=" * 70)


if __name__ == "__main__":
    demo_config_usage()
