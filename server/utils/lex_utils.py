import boto3
import logging
import os
from utils.aws_utils import get_secret

logger = logging.getLogger(__name__)
lex_client = None

def init_lex_client():
    """Initialize Amazon Lex client with credentials from AWS Secrets Manager"""
    global lex_client
    try:
        # Get Lex credentials from AWS Secrets Manager
        lex_creds = get_secret("lex")
        logger.info("Retrieved Lex credentials from AWS Secrets Manager")
        
        # Create Lex client
        lex_client = boto3.client(
            'lexv2-runtime',
            region_name=lex_creds.get('AWS_REGION', 'ca-central-1'),
            aws_access_key_id=lex_creds.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=lex_creds.get('AWS_SECRET_ACCESS_KEY')
        )
        
        # Store Lex bot configuration
        os.environ['LEX_BOT_ID'] = lex_creds.get('LEX_BOT_ID', '')
        os.environ['LEX_BOT_ALIAS_ID'] = lex_creds.get('LEX_BOT_ALIAS_ID', '')
        os.environ['LEX_BOT_LOCALE_ID'] = lex_creds.get('LEX_BOT_LOCALE_ID', 'en_CA')
        
        logger.info(f"Lex client initialized for bot: {os.environ['LEX_BOT_ID']}")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize Lex client: {str(e)}")
        return False

def validate_lex_credentials():
    """Test connection to Amazon Lex using stored credentials"""
    if not lex_client:
        if not init_lex_client():
            return False, "Failed to initialize Lex client"
    
    try:
        # Try to get a session to validate credentials
        response = lex_client.get_session(
            botId=os.environ.get('LEX_BOT_ID', ''),
            botAliasId=os.environ.get('LEX_BOT_ALIAS_ID', ''),
            localeId=os.environ.get('LEX_BOT_LOCALE_ID', 'en_CA'),
            sessionId='test-session'
        )
        logger.info("Successfully validated Lex credentials")
        return True, "Successfully connected to Amazon Lex"
    except lex_client.exceptions.ResourceNotFoundException:
        # This can happen if the session doesn't exist, which is fine
        logger.info("Lex credentials valid but no session exists")
        return True, "Connection to Amazon Lex verified"
    except Exception as e:
        logger.error(f"Failed to validate Lex credentials: {str(e)}")
        return False, f"Error connecting to Lex: {str(e)}"

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
        print(f"Sending message to Lex: {message}")
        
        print(f"Lex Bot ID: {os.environ.get('LEX_BOT_ID')}")
        print(f"Lex Bot Alias ID: {os.environ.get('LEX_BOT_ALIAS_ID')}")
        print(f"Lex Bot Locale ID: {os.environ.get('LEX_BOT_LOCALE_ID', 'en_CA')}")
        print(f"Session ID: {session_id}")
        print(f"Message: {message}")

        # Send message to Lex
        response = lex_client.recognize_text(
            botId=os.environ.get('LEX_BOT_ID'),
            botAliasId=os.environ.get('LEX_BOT_ALIAS_ID'),
            localeId=os.environ.get('LEX_BOT_LOCALE_ID', 'en_CA'),
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
    except Exception as e:
        logger.error(f"Error sending message to Lex: {str(e)}")
        return {
            "text": "Sorry, I encountered an error while processing your request.",
            "error": str(e),
            "session_state": None
        }
