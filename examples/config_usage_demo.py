#!/usr/bin/env python3
"""
Model Configuration Usage Example
Demonstrates how to use AGENT_MODEL and DEEPEVAL_MODEL configuration
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
    """Configuration Usage Demo"""

    print("=" * 70)
    print("Model Configuration Usage Example")
    print("=" * 70)

    # Example 1: View Current Configuration
    print("\n📋 Example 1: View Current Configuration\n")
    print(f"Agent Model: {config.api.agent_model}")
    print(f"DeepEval Model: {config.api.deepeval_model}")
    print(f"Temperature: {config.api.temperature}")

    # Example 2: Agent Usage Configuration
    print("\n🤖 Example 2: Agent Usage Configuration\n")
    print("Used when creating Agent:")
    print(f"""
from src.utils.config import config
from agno import Agent, OpenAIChat

agent = Agent(
    name="Personal Loan Advisor",
    model=OpenAIChat(
        id=config.api.agent_model,  # Using AGENT_MODEL environment variable
        temperature=config.api.temperature
    ),
)
    """)
    print(f"✅ Currently using model: {config.api.agent_model}")

    # Example 3: DeepEval Evaluation Configuration
    print("\n🧪 Example 3: DeepEval Evaluation Configuration\n")
    print("Used during evaluation:")
    print(f"""
from tests.deepeval_config import EVAL_MODEL
from deepeval.metrics import AnswerRelevancyMetric

metric = AnswerRelevancyMetric(
    model=EVAL_MODEL,  # Using DEEPEVAL_MODEL environment variable
    threshold=0.7
)
    """)
    print(f"✅ Currently using model: {EVAL_MODEL}")

    # Example 4: Switch Configuration
    print("\n🔄 Example 4: How to Switch Configuration\n")
    print("Method 1 - Modify .env file:")
    print("""
# Development - Cost Optimized
AGENT_MODEL=gpt-4o-mini
DEEPEVAL_MODEL=gpt-4o-mini

# Production - Performance Priority
AGENT_MODEL=gpt-4o
DEEPEVAL_MODEL=gpt-4o-mini
    """)

    print("\nMethod 2 - Temporary Environment Variable:")
    print("  AGENT_MODEL=gpt-4o uv run python src/agent/loan_advisor_agent.py")

    # Example 5: Cost Estimation
    print("\n💰 Example 5: Cost Comparison\n")

    costs = {
        "gpt-4o-mini": {"input": 0.150, "output": 0.600},  # per 1M tokens
        "gpt-4o": {"input": 2.50, "output": 10.00},
    }

    print("Assuming average per conversation 3000 tokens (2000 input + 1000 output):")
    print()

    for model, price in costs.items():
        input_cost = (2000 / 1_000_000) * price["input"]
        output_cost = (1000 / 1_000_000) * price["output"]
        total_cost = input_cost + output_cost
        print(f"{model}:")
        print(f"  Single conversation cost: ${total_cost:.6f}")
        print(f"  1000 conversations cost: ${total_cost * 1000:.2f}")
        print()

    # Example 6: Recommended Configuration
    print("\n⭐ Example 6: Recommended Configuration\n")

    scenarios = {
        "Development/Testing": {
            "agent": "gpt-4o-mini",
            "eval": "gpt-4o-mini",
            "Reason": "Low cost, fast iteration",
        },
        "Interview Demo": {
            "agent": "gpt-4o-mini",
            "eval": "gpt-4o-mini",
            "Reason": "Sufficient performance, manageable cost",
        },
        "Production": {
            "agent": "gpt-4o",
            "eval": "gpt-4o-mini",
            "Reason": "Good UX, low evaluation cost",
        },
    }

    for scenario, conf in scenarios.items():
        print(f"{scenario}:")
        print(f"  AGENT_MODEL={conf['agent']}")
        print(f"  DEEPEVAL_MODEL={conf['eval']}")
        print(f"  Reason: {conf['Reason']}")
        print()

    print("=" * 70)
    print("💡 Tip: Run 'uv run python scripts/check_config.py' to check current configuration")
    print("=" * 70)


if __name__ == "__main__":
    demo_config_usage()
