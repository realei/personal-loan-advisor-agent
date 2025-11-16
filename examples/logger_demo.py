#!/usr/bin/env python3
"""Demo script showing the logging system in action."""

from src.utils.logger import get_logger, setup_logger
from src.agent import PersonalLoanAgent
from src.utils.memory import ConversationMemory


def demo_basic_logging():
    """Demonstrate basic logging."""
    print("\n" + "="*60)
    print("DEMO 1: Basic Logging")
    print("="*60 + "\n")

    logger = get_logger("demo_basic")

    logger.debug("This is a DEBUG message (detailed info)")
    logger.info("This is an INFO message (general info)")
    logger.warning("This is a WARNING message (something to watch)")
    logger.error("This is an ERROR message (something went wrong)")
    logger.critical("This is a CRITICAL message (severe error)")


def demo_contextual_logging():
    """Demonstrate logging with context."""
    print("\n" + "="*60)
    print("DEMO 2: Contextual Logging")
    print("="*60 + "\n")

    logger = get_logger("demo_context")

    user_id = "alice_2024"
    session_id = "alice_2024_20240115_143022"
    loan_amount = 50000
    dti_ratio = 0.42

    logger.info(f"User {user_id} started session {session_id}")
    logger.info(f"Loan request: ${loan_amount:,} for user {user_id}")
    logger.warning(f"DTI ratio {dti_ratio:.1%} is approaching limit (50%)")


def demo_exception_logging():
    """Demonstrate exception logging."""
    print("\n" + "="*60)
    print("DEMO 3: Exception Logging")
    print("="*60 + "\n")

    logger = get_logger("demo_exception")

    try:
        result = 10 / 0
    except ZeroDivisionError as e:
        logger.error("Division by zero occurred", exc_info=True)
        logger.info("Continuing after error...")


def demo_agent_logging():
    """Demonstrate logging in actual agent usage."""
    print("\n" + "="*60)
    print("DEMO 4: Agent Logging (requires MongoDB)")
    print("="*60 + "\n")

    try:
        # Create memory (with evaluation disabled to avoid API key requirement)
        memory = ConversationMemory(
            mongodb_uri="mongodb://admin:password123@localhost:27017/",
            database_name="loan_advisor_demo",
            enable_evaluation=False
        )

        # Start session
        user_id = "demo_user"
        session_id = memory.start_session(user_id)

        print(f"✅ Session started: {session_id}")
        print("   Check the logs above for INFO messages from ConversationMemory\n")

        # Cleanup
        memory.delete_session(session_id)
        memory.close()

    except Exception as e:
        logger = get_logger("demo_agent")
        logger.error(f"Demo failed: {e}")
        print(f"\n⚠️  MongoDB not available. Start with: docker-compose up -d\n")


def demo_file_logging():
    """Demonstrate file logging."""
    print("\n" + "="*60)
    print("DEMO 5: File Logging")
    print("="*60 + "\n")

    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / "demo.log"

        logger = setup_logger(
            name="demo_file",
            level="DEBUG",
            log_file=str(log_file),
            console_output=True
        )

        logger.info("This message goes to both console and file")
        logger.debug("Debug messages also logged to file")

        print(f"\n✅ Log file created at: {log_file}")
        print("📄 Log file contents:\n")
        print(log_file.read_text())


def main():
    """Run all demos."""
    print("\n" + "🎨 "*30)
    print("   LOGGING SYSTEM DEMONSTRATION")
    print("🎨 "*30 + "\n")

    demo_basic_logging()
    demo_contextual_logging()
    demo_exception_logging()
    demo_file_logging()
    demo_agent_logging()

    print("\n" + "="*60)
    print("✨ All demos completed!")
    print("="*60 + "\n")

    print("💡 Tips:")
    print("  - Set LOG_LEVEL env var to control verbosity")
    print("  - Set LOG_FILE env var to enable file logging")
    print("  - Use logger.debug() for detailed troubleshooting")
    print("  - Use logger.error(..., exc_info=True) for stack traces\n")


if __name__ == "__main__":
    main()
