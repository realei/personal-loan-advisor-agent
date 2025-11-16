# Quick Start Guide

## ✅ MongoDB Memory is Working!

Your Personal Loan Advisor Agent now has **multi-user conversation memory** powered by MongoDB.

## Test Results

✅ MongoDB connection successful
✅ Memory module working
✅ Agent integration complete
✅ Conversation context is maintained
✅ Multi-user support enabled

## Run the Agent

```bash
# MongoDB is already running from docker-compose up -d
python main.py
```

## What to Expect

### 1. User Identification
```
👤 Enter your user ID (e.g., email or username): john@example.com
```

### 2. Session Management
If you have previous sessions, you'll see:
```
📋 Found 2 previous session(s):
   1. john@example.com_20251116_143022 - 8 messages
   2. john@example.com_20251116_120511 - 14 messages

🔄 Resume a session? (enter number, or press Enter for new session):
```

### 3. Conversation with Memory

**First message:**
```
👤 You: I'm 35 years old, earn $8000/month, credit score 720, want $50,000 for 36 months
🤖 Agent: [Checks eligibility and provides results]
```

**Follow-up (without repeating info):**
```
👤 You: What would my monthly payment be?
🤖 Agent: [Remembers $50,000 and 36 months, calculates payment immediately! ✅]
```

## MongoDB Web UI

View your conversations at http://localhost:8081:
- **Username**: admin
- **Password**: admin123

Browse collections:
- `sessions` - User sessions
- `messages` - Conversation history

## Key Features Tested

✅ **Multi-user support** - Each user has isolated conversations
✅ **Persistent memory** - Conversations survive restarts
✅ **Session resumption** - Continue previous conversations
✅ **Context awareness** - Agent remembers previous messages
✅ **MongoDB integration** - All messages stored in database

## Example Conversation

```
👤 You: I'm 35, earn $8000/month, credit score 720, want $100,000 for 60 months
🤖 Agent: ✅ You're eligible! Score: 91.4/100

👤 You: Calculate my monthly payments at 5% interest
🤖 Agent: [Uses $100,000 and 60 months from previous message]
         Monthly Payment: $1,887.12
         Total Interest: $13,227.12

👤 You: Is this affordable for my income?
🤖 Agent: [Uses $8000 income from first message]
         ✅ Affordable! DTI ratio: 23.6%
```

## Docker Commands

```bash
# Check MongoDB status
docker-compose ps

# View logs
docker-compose logs mongodb

# Stop MongoDB
docker-compose down

# Start MongoDB again
docker-compose up -d
```

## Troubleshooting

### MongoDB Connection Failed
```bash
# Make sure MongoDB is running
docker-compose up -d

# Check logs
docker-compose logs mongodb
```

### Agent Forgets Information
- Check that MongoDB is running: `docker-compose ps`
- Verify session was created successfully
- Check MongoDB UI at http://localhost:8081

## Architecture

```
User Input
    ↓
Agent (PersonalLoanAgent)
    ↓
Memory Module (ConversationMemory)
    ↓
MongoDB
```

**How it works:**
1. User message stored in MongoDB
2. Previous conversation loaded from MongoDB
3. Context prepended to current message
4. Agent processes with full context
5. Agent response stored in MongoDB
6. Cycle repeats with growing context

## Next Steps

- ✅ System is ready to use!
- Run `python main.py` to start chatting
- Try the multi-user features
- Resume previous sessions
- View data in MongoDB Express UI

**Happy lending!** 🏦
