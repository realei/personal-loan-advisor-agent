"""Personal Loan Advisor Agent - AgentOS UI Compatible Version.

This module is designed to work seamlessly with AgentOS UI:
- Proper session management for UI chat interface
- MongoDB persistence for conversation history
- Clean agent responses for UI display
- Compatible with AgentOS UI's session tracking

Structured Output Mode:
- Uses Pydantic response models for deterministic output
- Temperature set to 0.0 for consistency
- All responses follow LoanAdvisorResponse schema
"""

import os
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.db.mongo import MongoDb
from agno.os import AgentOS
from fastapi.middleware.cors import CORSMiddleware

from src.agent.loan_advisor_tools import (
    check_loan_eligibility,
    calculate_loan_payment,
    generate_payment_schedule,
    check_loan_affordability,
    compare_loan_terms,
    calculate_max_affordable_loan,
)
from src.agent.response_models import LoanAdvisorResponse
from src.agent.output_formatter import OutputMode, get_formatter
from src.utils.config import config
from src.utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)

# MongoDB Configuration for AgentOS UI
# Get MongoDB configuration from config object (read from .env, or use defaults if not set)
MONGODB_URL = config.mongodb.mongodb_uri
DATABASE_NAME = config.mongodb.database_name
SESSION_COLLECTION = config.mongodb.session_collection
MEMORY_COLLECTION = config.mongodb.memory_collection
METRICS_COLLECTION = config.mongodb.metrics_collection

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

## STRUCTURED OUTPUT FORMAT:
Your response MUST follow the LoanAdvisorResponse schema:

1. **action**: Choose from:
   - "eligibility_check" - when checking if someone qualifies
   - "payment_calculation" - when calculating monthly payments
   - "payment_schedule" - when generating amortization schedule
   - "affordability_check" - when assessing if loan is affordable
   - "term_comparison" - when comparing different loan terms
   - "max_loan_calculation" - when finding max affordable loan
   - "home_affordability" - when calculating home buying capacity
   - "mortgage_payment" - when calculating mortgage payments
   - "car_loan" - when calculating auto loan
   - "car_loan_comparison" - when comparing car loan terms
   - "early_payoff" - when calculating early payoff savings
   - "general_response" - for general questions

2. **tool_called**: The name of the tool you called (or null)

3. **Populate the appropriate result field** based on action:
   - eligibility, payment, affordability, term_comparison, max_loan
   - home_affordability, mortgage, car_loan, early_payoff

4. **summary**: One clear sentence summarizing the result

5. **details**: Detailed explanation in markdown

6. **recommendations**: List of actionable advice

7. **warnings**: List any concerns (high DTI, large loan, etc.)

8. **follow_up_questions**: Suggest 1-2 relevant follow-up questions
"""

# Determine output mode from environment
# Set OUTPUT_MODE=structured in .env for Pydantic output
OUTPUT_MODE = OutputMode.from_env()
IS_STRUCTURED = OUTPUT_MODE == OutputMode.STRUCTURED

# Create formatter for output formatting
formatter = get_formatter(OUTPUT_MODE)

# Create the Agent for AgentOS UI
# Use structured output for deterministic responses when enabled
loan_advisor_agent = Agent(
    name="Personal Loan Advisor",
    model=OpenAIChat(
        id=config.api.agent_model,
        # Use temperature 0.0 for deterministic output in structured mode
        temperature=0.0 if IS_STRUCTURED else config.api.temperature
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
    # Structured output configuration
    response_model=LoanAdvisorResponse if IS_STRUCTURED else None,
    structured_outputs=IS_STRUCTURED,
    # Context configuration
    add_datetime_to_context=True,
    add_session_state_to_context=True,
    enable_session_summaries=True,
    add_session_summary_to_context=True,
    # Important for UI: Enable conversation history
    add_history_to_context=True,
    read_chat_history=True,
    # System prompt
    instructions=SYSTEM_INSTRUCTIONS,
    # Number of previous messages to include
    num_history_runs=10,
    # Format responses in markdown for UI display (disabled in structured mode)
    markdown=not IS_STRUCTURED
)

logger.info(f"Output mode: {OUTPUT_MODE.value}")
if IS_STRUCTURED:
    logger.info("Using LoanAdvisorResponse model with temperature=0.0")
else:
    logger.info("Using MarkdownFormatter for streaming output")

# Create AgentOS instance for UI
# Note: Bearer token authentication is automatically enabled when OS_SECURITY_KEY
# environment variable is set. All API requests will then require:
# Authorization: Bearer <your_key>
agent_os = AgentOS(
    agents=[loan_advisor_agent],
    description="Personal Loan Advisor - AI-powered loan consultation system",
)

# Get the FastAPI app
app = agent_os.get_app()

# Configure CORS for AgentUI access
# Allow AgentUI to connect from any origin (localhost or deployed)
# In production, you can restrict origins via ALLOWED_ORIGINS environment variable
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info(f"CORS configured with allowed origins: {allowed_origins}")

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