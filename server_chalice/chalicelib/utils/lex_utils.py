import boto3
import logging
import os
import json
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
lex_client = None

# AWS Lambda environment already has AWS credentials via IAM roles
# so we don't need to explicitly fetch them from Secrets Manager

def init_lex_client():
    """Initialize Amazon Lex client using AWS Lambda's environment variables or IAM role"""
    global lex_client
    try:
        # Use Lambda environment AWS_REGION or get from our custom env var
        region = boto3.session.Session().region_name or os.environ.get('DEFAULT_REGION', 'ca-central-1')
        
        # Store Lex bot configuration
        if not os.environ.get('LEX_BOT_ID'):
            # Only set these if not already set during deployment
            os.environ['LEX_BOT_ID'] = os.environ.get('LEX_BOT_ID', '')
            os.environ['LEX_BOT_ALIAS_ID'] = os.environ.get('LEX_BOT_ALIAS_ID', '')
            os.environ['LEX_BOT_LOCALE_ID'] = os.environ.get('LEX_BOT_LOCALE_ID', 'en_CA')
            
        # Create Lex client using Lambda's IAM role
        lex_client = boto3.client('lexv2-runtime', region_name=region)
        
        logger.info(f"Lex client initialized for bot: {os.environ['LEX_BOT_ID']} in region {region}")
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
