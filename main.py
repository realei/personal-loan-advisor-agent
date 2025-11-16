"""Personal Loan Advisor Agent - CLI Interface."""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.agent import PersonalLoanAgent
from src.utils.config import config
from src.utils.memory import ConversationMemory


def print_banner():
    """Print welcome banner."""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║       🏦 Personal Loan Advisor Agent                        ║
║                                                              ║
║       AI-Powered Loan Advisory System                       ║
║       Powered by Agno 2.0 + OpenAI GPT-4                   ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

Welcome! I'm your personal loan advisor. I can help you with:
  ✓ Checking loan eligibility
  ✓ Calculating monthly payments
  ✓ Generating amortization schedules
  ✓ Assessing loan affordability
  ✓ Comparing different loan terms
  ✓ Finding your maximum affordable loan amount

Type 'help' for example questions, or 'quit' to exit.
"""
    print(banner)


def print_help():
    """Print help information."""
    help_text = """
📚 Example Questions:

1. Eligibility Check:
   "I'm 35 years old, earn $8000/month, have a credit score of 720,
    work full-time for 5 years, and want to borrow $50,000 for 36 months.
    Am I eligible?"

2. Payment Calculation:
   "Calculate my monthly payment for a $60,000 loan at 5.5% for 48 months"

3. Affordability Check:
   "I earn $10,000/month with $2,000 existing debt. Can I afford a
    $70,000 loan at 4.99% for 60 months?"

4. Compare Terms:
   "Compare loan terms for $50,000 at 5% interest for 24, 36, 48, and 60 months"

5. Max Loan Amount:
   "What's the maximum loan I can afford with $12,000 monthly income
    and $1,500 existing debt for a 36-month term at 5.2%?"

Type your question naturally - the AI will understand! 🤖
"""
    print(help_text)


def check_api_key():
    """Check if OpenAI API key is configured."""
    if not config.api.openai_api_key:
        print("\n⚠️  ERROR: OpenAI API key not found!")
        print("\n📝 Please set up your API key:")
        print("   1. Copy .env.example to .env")
        print("   2. Add your OpenAI API key to .env")
        print("   3. Run the program again\n")
        sys.exit(1)


def main():
    """Run the Personal Loan Advisor Agent CLI."""
    # Check API key
    check_api_key()

    # Print banner
    print_banner()

    # Initialize MongoDB memory
    print("🔧 Connecting to MongoDB...")
    try:
        memory = ConversationMemory(
            mongodb_uri="mongodb://admin:password123@localhost:27017/",
            database_name="loan_advisor"
        )
        print("✅ MongoDB connected!")
    except Exception as e:
        print(f"⚠️  MongoDB connection failed: {e}")
        print("💡 Make sure MongoDB is running: docker-compose up -d")
        print("   Continuing without memory (conversation history won't be saved)...\n")
        memory = None

    # Get or create user session
    if memory:
        user_id = input("\n👤 Enter your user ID (e.g., email or username): ").strip()
        if not user_id:
            user_id = "default_user"

        # Check for existing sessions
        sessions = memory.get_user_sessions(user_id, limit=5)
        if sessions:
            print(f"\n📋 Found {len(sessions)} previous session(s):")
            for i, session in enumerate(sessions, 1):
                print(f"   {i}. {session['session_id']} - {session['message_count']} messages")

            resume = input("\n🔄 Resume a session? (enter number, or press Enter for new session): ").strip()
            if resume.isdigit() and 1 <= int(resume) <= len(sessions):
                session_id = sessions[int(resume) - 1]['session_id']
                memory.resume_session(session_id)
                print(f"✅ Resumed session: {session_id}\n")
            else:
                session_id = memory.start_session(user_id)
                print(f"✅ Started new session: {session_id}\n")
        else:
            session_id = memory.start_session(user_id)
            print(f"✅ Started new session: {session_id}\n")

    # Initialize agent
    print("🔧 Initializing agent...")
    try:
        agent = PersonalLoanAgent(
            model=config.api.openai_model,
            temperature=config.api.temperature,
            debug_mode=False,
            memory=memory,
        )
        print("✅ Agent ready!\n")
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        sys.exit(1)

    # Main conversation loop
    print("💬 Start chatting (or type 'help' for examples):\n")

    while True:
        try:
            # Get user input
            user_input = input("\n👤 You: ").strip()

            # Handle special commands
            if not user_input:
                continue

            if user_input.lower() in ['quit', 'exit', 'bye']:
                if memory:
                    memory.close()
                print("\n👋 Thank you for using Personal Loan Advisor! Goodbye!\n")
                break

            if user_input.lower() in ['help', '?']:
                print_help()
                continue

            if user_input.lower() == 'clear':
                os.system('clear' if os.name == 'posix' else 'cls')
                print_banner()
                continue

            # Process with agent
            print("\n🤖 Agent: ")
            agent.run(user_input, stream=True)

        except KeyboardInterrupt:
            if memory:
                memory.close()
            print("\n\n👋 Interrupted. Goodbye!\n")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Please try again or type 'help' for examples.\n")


if __name__ == "__main__":
    main()
