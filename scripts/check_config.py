#!/usr/bin/env python3
"""
检查配置文件是否正确加载
验证Agent模型和DeepEval模型的配置
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.config import config
from tests.deepeval_config import AGENT_MODEL, EVAL_MODEL, METRIC_THRESHOLDS, CUSTOM_THRESHOLDS


def check_config():
    """检查配置"""
    print("=" * 60)
    print("配置检查")
    print("=" * 60)

    # 检查环境变量
    print("\n📋 环境变量:")
    print(f"  OPENAI_API_KEY: {'✅ 已设置' if os.getenv('OPENAI_API_KEY') else '❌ 未设置'}")
    print(f"  AGENT_MODEL: {os.getenv('AGENT_MODEL', '(未设置，使用默认值)')}")
    print(f"  DEEPEVAL_MODEL: {os.getenv('DEEPEVAL_MODEL', '(未设置，使用默认值)')}")
    print(f"  MONGODB_URI: {os.getenv('MONGODB_URI', '(未设置，使用默认值)')}")

    # 检查config对象
    print("\n🔧 API Config (src/utils/config.py):")
    print(f"  agent_model: {config.api.agent_model}")
    print(f"  deepeval_model: {config.api.deepeval_model}")
    print(f"  temperature: {config.api.temperature}")

    print("\n🗄️  MongoDB Config (src/utils/config.py):")
    print(f"  mongodb_uri: {config.mongodb.mongodb_uri}")
    print(f"  database_name: {config.mongodb.database_name}")
    print(f"  session_collection: {config.mongodb.session_collection}")
    print(f"  memory_collection: {config.mongodb.memory_collection}")
    print(f"  metrics_collection: {config.mongodb.metrics_collection}")

    # 检查DeepEval配置
    print("\n🧪 DeepEval模型配置 (tests/deepeval_config.py):")
    print(f"  AGENT_MODEL: {AGENT_MODEL}")
    print(f"  EVAL_MODEL: {EVAL_MODEL}")

    # 检查评估阈值
    print("\n📊 评估阈值配置:")
    print("  标准指标:")
    for metric, threshold in METRIC_THRESHOLDS.items():
        env_var = f"EVAL_THRESHOLD_{metric.upper()}"
        is_default = os.getenv(env_var) is None
        status = "(默认值)" if is_default else "(自定义)"
        print(f"    {metric}: {threshold} {status}")

    print("\n  自定义指标:")
    for metric, threshold in CUSTOM_THRESHOLDS.items():
        env_var = f"EVAL_THRESHOLD_{metric.upper()}"
        is_default = os.getenv(env_var) is None
        status = "(默认值)" if is_default else "(自定义)"
        print(f"    {metric}: {threshold} {status}")

    # 验证是否一致
    print("\n✅ 验证:")
    agent_match = config.api.agent_model == AGENT_MODEL
    eval_match = config.api.deepeval_model == EVAL_MODEL

    print(f"  Agent模型一致性: {'✅ 一致' if agent_match else '❌ 不一致'}")
    print(f"  DeepEval模型一致性: {'✅ 一致' if eval_match else '❌ 不一致'}")

    # 说明
    print("\n💡 说明:")
    print("  - Agent模型: 用于实际对话和工具调用")
    print("  - DeepEval模型: 用于评估Agent的输出质量")
    print("  - MongoDB配置: 用于存储会话、记忆和指标")
    print("  - 评估阈值: 控制质量评估的通过标准")
    print("  - 所有配置都可以在.env中设置，未设置则使用默认值")

    print("\n📝 配置方式:")
    print("  在 .env 文件中设置:")
    print("    # 模型配置")
    print("    AGENT_MODEL=gpt-4o-mini")
    print("    DEEPEVAL_MODEL=gpt-4o-mini")
    print("")
    print("    # MongoDB配置")
    print("    MONGODB_URI=mongodb://admin:password123@localhost:27017/")
    print("    MONGODB_DATABASE=loan_advisor")
    print("")
    print("    # 评估阈值（可选，有默认值）")
    print("    EVAL_THRESHOLD_ANSWER_RELEVANCY=0.7")
    print("    EVAL_THRESHOLD_FAITHFULNESS=0.75")

    print("\n" + "=" * 60)

    if agent_match and eval_match:
        print("✅ 配置检查通过！")
        return 0
    else:
        print("⚠️  配置不一致，请检查")
        return 1


if __name__ == "__main__":
    exit(check_config())
