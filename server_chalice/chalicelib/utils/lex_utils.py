import boto3
import logging
import os
import json
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
lex_client = None

def init_lex_client():
    """Initialize Amazon Lex client using Chalice environment variables"""
    global lex_client
    try:
        # Get region from Lambda environment or fallback to DEFAULT_REGION
        # This works in both local and Lambda environments
        region = os.environ.get('AWS_LAMBDA_FUNCTION_REGION', 
                  os.environ.get('DEFAULT_REGION', 'ca-central-1'))
        
        # Get Lex configuration from environment (Chalice config)
        bot_id = os.environ.get('LEX_BOT_ID')
        bot_alias_id = os.environ.get('LEX_BOT_ALIAS_ID')
        locale_id = os.environ.get('LEX_BOT_LOCALE_ID', 'en_US')
        
        if not bot_id or not bot_alias_id:
            logger.error("Missing LEX_BOT_ID or LEX_BOT_ALIAS_ID in environment variables")
            return False
            
        # Create Lex client using explicit region
        lex_client = boto3.client('lexv2-runtime', region_name=region)
        
        logger.info(f"Lex client initialized for bot: {bot_id} in region {region}")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize Lex client: {str(e)}")
        return False

def send_message_to_lex(session_id: str, message: str):
    """
    Send a message to Amazon Lex and get the response
    
    Args:
        session_id (str): Unique session identifier for the conversation
        message (str): Message text from the user
        
    Returns:
        dict: Response from Lex containing message and session state
    """
    if not lex_client:
        if not init_lex_client():
            return {
                "text": "Sorry, I couldn't connect to the dental assistant service.",
                "session_state": None,
                "error": "Lex client not initialized"
            }
    
    try:
        bot_id = os.environ.get('LEX_BOT_ID')
        bot_alias_id = os.environ.get('LEX_BOT_ALIAS_ID')
        locale_id = os.environ.get('LEX_BOT_LOCALE_ID', 'en_CA')
        
        if not bot_id or not bot_alias_id:
            logger.error("Missing LEX_BOT_ID or LEX_BOT_ALIAS_ID in environment variables")
            return {
                "text": "Sorry, the chatbot service is not properly configured.",
                "session_state": None,
                "error": "Missing Lex bot configuration"
            }
        
        response = lex_client.recognize_text(
            botId=bot_id,
            botAliasId=bot_alias_id,
            localeId=locale_id,
            sessionId=session_id,
            text=message
        )
        
        # Process the response
        messages = response.get('messages', [])
        combined_message = " ".join([msg.get('content', '') for msg in messages]) if messages else "I'm sorry, I couldn't process your request."
        
        return {
            "text": combined_message,
            "session_state": response.get('sessionState'),
            "intent": response.get('interpretations', [{}])[0].get('intent', {}).get('name') if response.get('interpretations') else None,
            "slots": response.get('interpretations', [{}])[0].get('intent', {}).get('slots') if response.get('interpretations') else None
        }
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        error_message = e.response.get('Error', {}).get('Message', str(e))
        
        logger.error(f"AWS Error ({error_code}): {error_message}")
        
        if error_code == 'AccessDeniedException':
            return {
                "text": "Sorry, the chatbot doesn't have permission to access Lex.",
                "error": error_message
            }
        else:
            return {
                "text": "Sorry, I encountered an error while processing your request.",
                "error": error_message
            }
            
    except Exception as e:
        logger.error(f"Error sending message to Lex: {str(e)}")
        return {
            "text": "Sorry, I encountered an error while processing your request.",
            "error": str(e),
            "session_state": None
        }
