import os
import sys
import json
import uuid
from dotenv import load_dotenv

# Add parent directory to path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables from .env file
load_dotenv()

from utils.aws_utils import get_secret, validate_aws_credentials
from utils.lex_utils import init_lex_client, validate_lex_credentials, send_message_to_lex

def check_lex_connection():
    """Script to validate Amazon Lex connectivity and credentials"""
    print("Amazon Lex Connectivity Test")
    print("============================")
    
    # Check AWS credentials first
    aws_valid, aws_message = validate_aws_credentials()
    print(f"\nAWS Credentials check: {aws_message}")
    
    if not aws_valid:
        print("Cannot continue without valid AWS credentials")
        return False
    
    # Get Lex credentials from Secrets Manager
    print("\nAttempting to retrieve Lex credentials...")
    try:
        lex_creds = get_secret("lex")
        print("Successfully retrieved Lex credentials")
        
        # Display Lex configuration (safely)
        print("\nLex configuration:")
        print(f"- Bot ID: {lex_creds.get('LEX_BOT_ID')}")
        print(f"- Bot Alias ID: {lex_creds.get('LEX_BOT_ALIAS_ID')}")
        print(f"- Locale ID: {lex_creds.get('LEX_BOT_LOCALE_ID', 'en_CA')}")
        print(f"- Region: {lex_creds.get('AWS_REGION', 'ca-central-1')}")
        
        # Initialize Lex client
        print("\nInitializing Lex client...")
        if init_lex_client():
            print("✓ Lex client initialized successfully")
        else:
            print("✗ Failed to initialize Lex client")
            return False
        
        # Validate the Lex credentials
        print("\nValidating Lex credentials...")
        is_valid, message = validate_lex_credentials()
        if is_valid:
            print(f"✓ {message}")
        else:
            print(f"✗ {message}")
            return False
        
        # Test a sample message
        print("\nSending test message to Lex...")
        session_id = str(uuid.uuid4())
        response = send_message_to_lex(session_id, "Hello")
        
        if "error" in response:
            print(f"✗ Error testing Lex: {response['error']}")
            return False
            
        print(f"✓ Successfully sent message to Lex")
        print(f"✓ Response: {response['text']}")
        
        # Show intent if available
        if response.get("intent"):
            print(f"✓ Detected intent: {response['intent']}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to test Lex connection: {str(e)}")
        return False
        
if __name__ == "__main__":
    success = check_lex_connection()
    print("\nValidation complete.")
    sys.exit(0 if success else 1)
