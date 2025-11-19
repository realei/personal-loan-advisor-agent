#!/usr/bin/env python3
"""
Check if configuration file is loaded correctly
Verify Agent Model and DeepEval Model configuration
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
    """Check Configuration"""
    print("=" * 60)
    print("Configuration Check")
    print("=" * 60)

    # Check environment variables
    print("\n📋 Environment Variables:")
    print(f"  OPENAI_API_KEY: {'✅ Set' if os.getenv('OPENAI_API_KEY') else '❌ Not set'}")
    print(f"  AGENT_MODEL: {os.getenv('AGENT_MODEL', '(Not set, using defaults)')}")
    print(f"  DEEPEVAL_MODEL: {os.getenv('DEEPEVAL_MODEL', '(Not set, using defaults)')}")
    print(f"  MONGODB_URI: {os.getenv('MONGODB_URI', '(Not set, using defaults)')}")

    # Check config object
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

    # Check DeepEval configuration
    print("\n🧪 DeepEval Model Configuration (tests/deepeval_config.py):")
    print(f"  AGENT_MODEL: {AGENT_MODEL}")
    print(f"  EVAL_MODEL: {EVAL_MODEL}")

    # Check evaluation thresholds
    print("\n📊 Evaluation Threshold Configuration:")
    print("  Standard Metrics:")
    for metric, threshold in METRIC_THRESHOLDS.items():
        env_var = f"EVAL_THRESHOLD_{metric.upper()}"
        is_default = os.getenv(env_var) is None
        status = "(default)" if is_default else "(custom)"
        print(f"    {metric}: {threshold} {status}")

    print("\n  Custom Metrics:")
    for metric, threshold in CUSTOM_THRESHOLDS.items():
        env_var = f"EVAL_THRESHOLD_{metric.upper()}"
        is_default = os.getenv(env_var) is None
        status = "(default)" if is_default else "(custom)"
        print(f"    {metric}: {threshold} {status}")

    # Verify consistency
    print("\n✅ Verification:")
    agent_match = config.api.agent_model == AGENT_MODEL
    eval_match = config.api.deepeval_model == EVAL_MODEL

    print(f"  Agent Model consistency: {'✅ Consistent' if agent_match else '❌ Inconsistent'}")
    print(f"  DeepEval Model consistency: {'✅ Consistent' if eval_match else '❌ Inconsistent'}")

    # Description
    print("\n💡 Description:")
    print("  - Agent Model: Used for actual conversations and tool calls")
    print("  - DeepEval Model: Used to evaluate Agent output quality")
    print("  - MongoDB Configuration: Used to store sessions, memory and metrics")
    print("  - Evaluation Thresholds: Control quality evaluation pass criteria")
    print("  - All config can be set in .env, defaults used if not set")

    print("\n📝 Configuration Method:")
    print("  Set in .env file:")
    print("    # Model configuration")
    print("    AGENT_MODEL=gpt-4o-mini")
    print("    DEEPEVAL_MODEL=gpt-4o-mini")
    print("")
    print("    # MongoDB configuration")
    print("    MONGODB_URI=mongodb://admin:password123@localhost:27017/")
    print("    MONGODB_DATABASE=loan_advisor")
    print("")
    print("    # Evaluation thresholds (optional, has defaults)")
    print("    EVAL_THRESHOLD_ANSWER_RELEVANCY=0.7")
    print("    EVAL_THRESHOLD_FAITHFULNESS=0.75")

    print("\n" + "=" * 60)

    if agent_match and eval_match:
        print("✅ Configuration Check Passed!")
        return 0
    else:
        print("⚠️  Configuration inconsistent, please check")
        return 1


if __name__ == "__main__":
    exit(check_config())
