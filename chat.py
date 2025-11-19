#!/usr/bin/env python
"""Personal Loan Advisor with In-Memory Session.

This script provides a simple chat interface with memory that persists
throughout the conversation session (no MongoDB required).
"""

import os
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from src.agent.loan_advisor_tools import (
    check_loan_eligibility,
    calculate_loan_payment,
    generate_payment_schedule,
    check_loan_affordability,
    compare_loan_terms,
    calculate_max_affordable_loan,
)
from src.utils.config import config

print("=" * 60)
print("🏦 Personal Loan Advisor Agent - With Session Memory")
print("=" * 60)
print("Your conversation is remembered during this session")
print("Commands: 'help' for examples, 'clear' to reset, 'quit' to exit")
print("=" * 60)

# System instructions
system_instructions = """You are a helpful and professional Personal Loan Advisor.
Your goal is to help customers understand their loan options and make informed decisions.

IMPORTANT: You have access to conversation history. Remember what the user told you earlier in the conversation.
When a user refers to previous information (like "I told you my income is $8000"), check the conversation history.

## Your Capabilities:
1. Check loan eligibility based on customer profile
2. Calculate monthly payments and total costs
3. Generate detailed amortization schedules
4. Assess loan affordability
5. Compare different loan term options
6. Calculate maximum affordable loan amount

## Guidelines:
- Remember information from earlier in the conversation
- Don't ask for information the user already provided
- Be friendly, clear, and professional
- Provide specific numbers and calculations
- Warn about potential risks (high DTI, unaffordable loans)

## Response Style:
- Use bullet points for clarity
- Include specific dollar amounts
- Highlight important warnings using **bold**
- Reference previous conversation when relevant
"""

# Conversation history (in-memory storage)
conversation_history = []


def add_to_history(role, content):
    """Add message to conversation history."""
    conversation_history.append({
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat()
    })


def get_conversation_context():
    """Build conversation context from history."""
    if not conversation_history:
        return ""

    context = "\n## Previous Conversation:\n"
    for msg in conversation_history[-10:]:  # Last 10 messages
        role = "User" if msg["role"] == "user" else "Advisor"
        context += f"{role}: {msg['content'][:200]}...\n" if len(msg['content']) > 200 else f"{role}: {msg['content']}\n"

    return context


def show_help():
    """Show help information."""
    print("\n📚 Example Questions:")
    print("• Calculate payment for $50,000 at 5% for 36 months")
    print("• I'm 35, earn $8000/month, credit score 720, want $50k for 36 months")
    print("• What was my DTI ratio?")
    print("• Show me the payment schedule")
    print("• Compare different loan terms\n")


def clear_history():
    """Clear conversation history."""
    global conversation_history
    conversation_history = []
    print("\n🧹 Conversation history cleared.\n")


# Create agent with session capability
print("\nInitializing agent with session memory...")

# Create session ID for this conversation
session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

agent = Agent(
    name="Personal Loan Advisor",
    model=OpenAIChat(
        id=config.api.openai_model,
        temperature=config.api.temperature,
        timeout=60,
        max_retries=2
    ),
    session_id=session_id,
    tools=[
        check_loan_eligibility,
        calculate_loan_payment,
        generate_payment_schedule,
        check_loan_affordability,
        compare_loan_terms,
        calculate_max_affordable_loan,
    ],
    instructions=[system_instructions],
    # Enable message history in prompt
    add_messages_to_prompt=True,
    add_history_to_context=True,
    num_history_messages=20,  # Remember last 20 messages
    markdown=True,
    debug_mode=False
)

print(f"✅ Ready! Session: {session_id}\n")

# Interactive chat loop
while True:
    try:
        user_input = input("You: ").strip()

        if not user_input:
            continue

        if user_input.lower() in ['quit', 'exit', 'bye', 'q']:
            print("\n👋 Goodbye! Your conversation will be lost when you exit.\n")
            break

        if user_input.lower() in ['help', '?']:
            show_help()
            continue

        if user_input.lower() == 'clear':
            clear_history()
            # Reset agent session
            agent.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            continue

        if user_input.lower() == 'history':
            # Show conversation history
            if conversation_history:
                print("\n📜 Conversation History:")
                for i, msg in enumerate(conversation_history, 1):
                    role = "You" if msg["role"] == "user" else "Advisor"
                    print(f"{i}. {role}: {msg['content'][:100]}...")
                print()
            else:
                print("\n📜 No conversation history yet.\n")
            continue

        # Add user message to history
        add_to_history("user", user_input)

        # Build context-aware prompt
        context = get_conversation_context()
        prompt_with_context = f"{context}\n\nCurrent question: {user_input}"

        print("\nAdvisor: ", end="")

        # Get response with context
        response = agent.run(user_input, stream=False)

        # Extract content
        if hasattr(response, 'content'):
            content = response.content
        else:
            content = str(response)

        print(content)
        print()

        # Add response to history
        add_to_history("assistant", content)

    except KeyboardInterrupt:
        print("\n\n👋 Interrupted. Goodbye!\n")
        break
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("Please try again.\n")