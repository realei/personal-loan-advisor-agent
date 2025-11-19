"""Personal Loan Advisor Agent - AgentOS UI Compatible Version.

This module is designed to work seamlessly with AgentOS UI:
- Proper session management for UI chat interface
- MongoDB persistence for conversation history
- Clean agent responses for UI display
- Compatible with AgentOS UI's session tracking
"""

from doctest import debug
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.db.mongo import MongoDb
from agno.os import AgentOS

from src.agent.loan_advisor_tools import (
    check_loan_eligibility,
    calculate_loan_payment,
    generate_payment_schedule,
    check_loan_affordability,
    compare_loan_terms,
    calculate_max_affordable_loan,
)
from src.utils.config import config
from src.utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)

# MongoDB Configuration for AgentOS UI
MONGODB_URL = getattr(config, 'mongodb_uri', "mongodb://admin:password123@localhost:27017/")
DATABASE_NAME = "loan_advisor"
SESSION_COLLECTION = "agno_sessions"
MEMORY_COLLECTION = "agno_memories"
METRICS_COLLECTION = "agno_metrics"

# System Instructions for the Agent
SYSTEM_INSTRUCTIONS = """You are a helpful and professional Personal Loan Advisor.
Your goal is to help customers understand their loan options and make informed decisions.

## Your Capabilities:
1. Check loan eligibility based on customer profile
2. Calculate monthly payments and total costs
3. Generate detailed amortization schedules
4. Assess loan affordability
5. Compare different loan term options
6. Calculate maximum affordable loan amount

## Guidelines:
- Always be friendly, clear, and professional
- Explain financial terms in simple language
- Provide specific numbers and calculations
- Warn about potential risks (high DTI, unaffordable loans)
- Suggest alternatives when loans are not affordable
- Never make guarantees about loan approval
- Always mention that final approval depends on full application review

## IMPORTANT: Information Extraction
- ALWAYS extract information from the user's message first
- If user mentions age, income, credit score, etc., USE THAT INFORMATION immediately
- DO NOT ask for information that the user has already provided
- For missing non-critical info, use reasonable defaults:
  * monthly_debt_obligations: assume 0 if not mentioned
  * has_existing_loans: assume False if not mentioned
  * previous_defaults: assume False if not mentioned
- Only ask for missing CRITICAL information (age, income, credit score, loan amount, term)

## When customers ask about loans:
1. Extract all information from their message
2. If you have enough information, IMMEDIATELY call the appropriate tool
3. Only ask follow-up questions if critical information is truly missing
4. Provide clear recommendations based on tool results

## Response Style:
- Use bullet points for clarity
- Include specific dollar amounts
- Highlight important warnings using **bold**
- End with next steps or recommendations
"""

# Create the Agent for AgentOS UI
loan_advisor_agent = Agent(
    name="Personal Loan Advisor",
    model=OpenAIChat(
        id=config.api.openai_model,
        temperature=config.api.temperature
    ),
    # MongoDB configuration for UI session persistence
    db=MongoDb(
        db_url=MONGODB_URL,
        db_name=DATABASE_NAME,
        session_collection=SESSION_COLLECTION,
        memory_collection=MEMORY_COLLECTION,
        metrics_collection=METRICS_COLLECTION
    ),
    # Tools available to the agent
    tools=[
        check_loan_eligibility,
        calculate_loan_payment,
        generate_payment_schedule,
        check_loan_affordability,
        compare_loan_terms,
        calculate_max_affordable_loan,
    ],
    # System prompt
    instructions=SYSTEM_INSTRUCTIONS,
    # Important for UI: Enable conversation history
    add_history_to_context=True,
    # Number of previous messages to include
    num_history_runs=10,
    # Format responses in markdown for UI display
    markdown=True
)

# Create AgentOS instance for UI
agent_os = AgentOS(
    agents=[loan_advisor_agent],
    description="Personal Loan Advisor - AI-powered loan consultation system",
)

# Get the FastAPI app
app = agent_os.get_app()

# The AgentOS UI will automatically:
# 1. Create a chat interface at http://localhost:3000
# 2. Handle session management
# 3. Store conversations in MongoDB
# 4. Display agent responses with markdown formatting
# 5. Show tool calls if enabled

if __name__ == "__main__":
    import sys

    # Check if running API server or interactive mode
    if len(sys.argv) > 1 and sys.argv[1] == "--api":
        # Run as API server
        import uvicorn

        logger.info("=" * 60)
        logger.info("🚀 Starting Personal Loan Advisor API Server")
        logger.info("=" * 60)
        logger.info("Using AgentOS with loan_advisor_agent instance")
        logger.info("API will be available at http://localhost:8000")
        logger.info("API Docs at http://localhost:8000/docs")
        logger.info("=" * 60)

        # Use the app from agent_os which uses loan_advisor_agent
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

    else:
        # Run interactive chat using the same loan_advisor_agent instance
        print("=" * 60)
        print("🏦 Personal Loan Advisor Agent - Interactive Mode")
        print("=" * 60)
        print("Using loan_advisor_agent.cli_app() for interactive chat")
        print("=" * 60)

        # Run agent as an interactive CLI app using the existing instance
        loan_advisor_agent.cli_app(stream=True)