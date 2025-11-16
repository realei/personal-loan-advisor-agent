#!/usr/bin/env python3
"""Simple Demo - Personal Loan Advisor Agent.

Most basic demo without MongoDB or complex features.
Just pure agent conversation.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.agent import PersonalLoanAgent
from src.utils.config import config


def main():
    """Run simple demo."""
    print("=" * 60)
    print("🏦 Personal Loan Advisor Agent - Simple Demo")
    print("=" * 60)
    print()

    # Check API key
    if not config.api.openai_api_key:
        print("❌ Error: OPENAI_API_KEY not found in .env file")
        print("   Please add your OpenAI API key to .env")
        return

    # Initialize agent (no MongoDB, no evaluation)
    print("🔧 Initializing agent...")
    agent = PersonalLoanAgent(
        model=config.api.openai_model,
        temperature=config.api.temperature,
        debug_mode=False,
        memory=None,  # No memory
    )
    print("✅ Agent ready!")
    print()

    # Example queries
    print("📝 Try these example queries:")
    print("   1. I'm 35, earn $10k/month, credit score 720, want $50k for 36 months")
    print("   2. Calculate payment for $50000 at 5% for 36 months")
    print("   3. Is $50k affordable with $8000 income and $500 existing debt?")
    print()
    print("Type 'quit' to exit")
    print()

    # Simple conversation loop
    while True:
        try:
            user_input = input("You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break

            # Run agent
            print("\nAgent: ")
            agent.run(user_input, stream=True)
            print()

        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")


if __name__ == "__main__":
    main()
