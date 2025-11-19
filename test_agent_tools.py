#!/usr/bin/env python
"""Test agent with tools directly."""

import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from src.agent.loan_advisor_tools import calculate_loan_payment
from src.utils.config import config

print("Testing Agent with timeout handling...")

# Create simple agent with just one tool
agent = Agent(
    name="Test Agent",
    model=OpenAIChat(
        id=config.api.openai_model,
        temperature=0.7,
        timeout=60,  # 60 second timeout
        max_retries=2
    ),
    tools=[calculate_loan_payment],
    instructions=["You are a loan calculator. Help users calculate loan payments."],
    debug_mode=True  # Show what's happening
)

# Test simple calculation
test_query = "Calculate payment for $30,000 at 5% for 24 months"
print(f"\nQuery: {test_query}")
print("="*50)

try:
    response = agent.run(test_query, stream=False)
    if hasattr(response, 'content'):
        print(f"Response: {response.content}")
    else:
        print(f"Response: {response}")
except Exception as e:
    print(f"Error: {e}")
    print("\nTrying without tools...")

    # Try without tools to see if it's a tool problem
    agent_no_tools = Agent(
        name="Test Agent No Tools",
        model=OpenAIChat(
            id=config.api.openai_model,
            temperature=0.7,
            timeout=60,
            max_retries=2
        ),
        instructions=["You are a helpful assistant."]
    )

    response = agent_no_tools.run("Hello, are you working?", stream=False)
    if hasattr(response, 'content'):
        print(f"No-tools response: {response.content}")
    else:
        print(f"No-tools response: {response}")