"""API Router for Personal Loan Advisor Agent.

This module provides REST API endpoints for the loan advisor agent.
It reuses the agent logic from loan_advisor_agent.py.
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agno.os import AgentOS
from src.agent.loan_advisor_agent import loan_advisor_agent, agent_os, app as agno_app
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Personal Loan Advisor API",
    description="AI-powered Personal Loan Advisory System API",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class ChatRequest(BaseModel):
    """Chat request model."""
    message: str
    user_id: Optional[str] = "default_user"
    session_id: Optional[str] = None
    stream: Optional[bool] = False

class ChatResponse(BaseModel):
    """Chat response model."""
    response: str
    session_id: Optional[str] = None
    user_id: str

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    agent_name: str
    model: str
    tools_count: int

# API Endpoints
@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - health check."""
    return HealthResponse(
        status="healthy",
        agent_name=loan_advisor_agent.name,
        model=str(loan_advisor_agent.model),
        tools_count=len(loan_advisor_agent.tools)
    )

@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return await root()

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat with the loan advisor agent.

    Args:
        request: ChatRequest with message and optional session info

    Returns:
        ChatResponse with agent's response
    """
    try:
        logger.info(f"Chat request from user: {request.user_id}")

        # Set session if provided
        if request.session_id:
            loan_advisor_agent.session_id = request.session_id
        if request.user_id:
            loan_advisor_agent.user_id = request.user_id

        # Get response from agent
        response = loan_advisor_agent.run(request.message, stream=request.stream)

        # Extract content
        if hasattr(response, 'content'):
            content = response.content
        else:
            content = str(response)

        return ChatResponse(
            response=content,
            session_id=loan_advisor_agent.session_id,
            user_id=request.user_id
        )

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Stream chat responses (Server-Sent Events).

    Args:
        request: ChatRequest with message

    Returns:
        StreamingResponse with agent's response
    """
    from fastapi.responses import StreamingResponse

    async def generate():
        try:
            # Get streaming response
            response = loan_advisor_agent.run(request.message, stream=True)

            # Stream chunks
            if hasattr(response, '__iter__'):
                for chunk in response:
                    if hasattr(chunk, 'content'):
                        yield f"data: {chunk.content}\n\n"
                    else:
                        yield f"data: {str(chunk)}\n\n"
            else:
                yield f"data: {str(response)}\n\n"

            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.error(f"Error in stream: {str(e)}")
            yield f"data: Error: {str(e)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )

# Mount the AgentOS app if needed
@app.get("/agno/health")
async def agno_health():
    """Check AgentOS health."""
    return {
        "status": "healthy",
        "agentOS": True,
        "agents": [loan_advisor_agent.name],
        "mongodb": loan_advisor_agent.db is not None
    }

if __name__ == "__main__":
    import uvicorn

    logger.info("=" * 60)
    logger.info("🚀 Starting Personal Loan Advisor API Server")
    logger.info("=" * 60)
    logger.info("📍 API Endpoints:")
    logger.info("   GET  /         - Health check")
    logger.info("   GET  /health   - Health check")
    logger.info("   POST /chat     - Chat with agent")
    logger.info("   POST /chat/stream - Stream responses")
    logger.info("   GET  /docs     - API documentation")
    logger.info("=" * 60)

    # Run the server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )