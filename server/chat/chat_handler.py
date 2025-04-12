import uuid
import logging
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any
from database.redis import get_redis_client
import json
from utils.lex_utils import init_lex_client, send_message_to_lex

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize Lex client on module load
lex_initialized = init_lex_client()

class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None

class ChatResponse(BaseModel):
    text: str
    intent: Optional[str] = None
    status: str

@router.post("/chat")
async def process_chat_message(request: ChatMessage):
    """Process user message and return a response from Lex"""
    try:
        logger.info(f"Received chat message: {request.message}")
        
        # Ensure Lex client is initialized
        if not lex_initialized:
            if not init_lex_client():
                logger.error("Failed to initialize Lex client")
                return {"text": "Sorry, the dental assistant service is currently unavailable.", "status": "error"}
        
        # Generate or use existing session ID
        session_id = request.session_id or str(uuid.uuid4())
        
        # Send the message to Lex
        lex_response = send_message_to_lex(session_id, request.message)
        
        if "error" in lex_response:
            logger.error(f"Error from Lex: {lex_response['error']}")
            return {"text": lex_response["text"], "status": "error"}
        
        # Store conversation state if user is identified
        if request.user_id:
            try:
                redis = await get_redis_client()
                await redis.setex(
                    f"chat_session:{request.user_id}", 
                    3600,  # 1 hour expiration
                    json.dumps({
                        "session_id": session_id,
                        "last_intent": lex_response.get("intent"),
                        "slots": lex_response.get("slots")
                    })
                )
            except Exception as e:
                logger.error(f"Failed to store conversation state: {str(e)}")
                # Continue even if Redis storage fails
        
        return {
            "text": lex_response["text"],
            "intent": lex_response.get("intent"),
            "status": "ok",
            "session_id": session_id
        }
        
    except Exception as e:
        logger.error(f"Error processing chat message: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

@router.get("/chat/health")
async def chat_health():
    """Check if the chat service is healthy"""
    try:
        if not lex_initialized:
            if not init_lex_client():
                logger.warning("Lex client not initialized")
                return {"status": "warning", "message": "Lex client not connected"}
                
        return {"status": "ok", "message": "Chat service is healthy"}
    except Exception as e:
        logger.error(f"Error checking chat health: {str(e)}")
        return {"status": "error", "message": str(e)}
