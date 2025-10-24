"""
FastAPI endpoints for chat functionality.

Provides API for chatting with OpenAI GPT models.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging
import openai
import os
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])

# OpenAI client setup
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ChatMessage(BaseModel):
    """Model for a single chat message."""
    role: str = Field(..., description="Role of the message sender (user/assistant)")
    content: str = Field(..., description="Content of the message")

class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str = Field(..., description="User's message")
    messages: List[ChatMessage] = Field(default=[], description="Previous conversation history")

class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    response: str = Field(..., description="Assistant's response")
    timestamp: str = Field(..., description="Timestamp of the response")
    model_used: str = Field(..., description="OpenAI model used for the response")

@router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest) -> ChatResponse:
    """
    Chat with the AI agent using OpenAI API.
    
    Args:
        request: Chat request containing user message and conversation history
        
    Returns:
        Chat response from the AI agent
    """
    try:
        logger.info(f"Chat request received: '{request.message[:50]}...'")
        
        # Prepare messages for OpenAI API
        messages = []
        
        # Add system message to establish agent personality
        system_message = {
            "role": "system",
            "content": """You are AgentMind, an AI assistant designed to help with the AgentMind project - a platform for managing AI agent memory. 

Your capabilities:
- Help with Python development, especially FastAPI, Pydantic, and Docker
- Assist with graph databases (FalkorDB) and memory management
- Provide technical guidance on AI agent architecture
- Support with Next.js frontend development

Your personality:
- Be helpful, technical, and precise
- Ask clarifying questions when needed
- Provide code examples when appropriate
- Be encouraging and supportive

Remember: You're part of the AgentMind project, so you understand the context of memory management, graph databases, and AI agent architecture."""
        }
        messages.append(system_message)
        
        # Add conversation history
        for msg in request.messages:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Add current user message
        messages.append({
            "role": "user",
            "content": request.message
        })
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=1000,
            temperature=0.7,
            presence_penalty=0.1,
            frequency_penalty=0.1
        )
        
        assistant_response = response.choices[0].message.content
        model_used = response.model
        
        logger.info(f"Chat response generated successfully using {model_used}")
        
        return ChatResponse(
            response=assistant_response,
            timestamp=datetime.now().isoformat(),
            model_used=model_used
        )
        
    except openai.AuthenticationError:
        logger.error("OpenAI API authentication failed")
        raise HTTPException(
            status_code=401,
            detail="OpenAI API key is invalid or missing"
        )
    except openai.RateLimitError:
        logger.error("OpenAI API rate limit exceeded")
        raise HTTPException(
            status_code=429,
            detail="OpenAI API rate limit exceeded. Please try again later."
        )
    except openai.APIError as e:
        logger.error(f"OpenAI API error: {e}")
        raise HTTPException(
            status_code=502,
            detail=f"OpenAI API error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in chat endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/chat/status")
async def get_chat_status() -> Dict[str, Any]:
    """
    Get chat system status.
    
    Returns:
        Status information about the chat system
    """
    try:
        # Check if OpenAI API key is configured
        api_key_configured = bool(os.getenv("OPENAI_API_KEY"))
        
        return {
            "status": "ready" if api_key_configured else "not_configured",
            "openai_configured": api_key_configured,
            "timestamp": datetime.now().isoformat(),
            "available_models": ["gpt-4o-mini", "gpt-3.5-turbo"]
        }
        
    except Exception as e:
        logger.error(f"Failed to get chat status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get status: {str(e)}"
        )
