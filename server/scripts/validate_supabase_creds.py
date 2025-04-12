import os
import sys
from dotenv import load_dotenv

# Add parent directory to path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables from .env file
load_dotenv()

from utils.aws_utils import get_secret, validate_aws_credentials
from utils.supabase_utils import validate_supabase_credentials

def check_supabase_credentials():
    """Script to validate Supabase credentials from AWS Secrets Manager"""
    print("Supabase Credential Validation Tool")
    print("==================================")
    
    # Check AWS credentials first
    aws_valid, aws_message = validate_aws_credentials()
    print(f"\nAWS Credentials check: {aws_message}")
    
    if not aws_valid:
        print("Cannot continue without valid AWS credentials")
        return False
    
    # Get secret name from environment
    supabase_secret_name = os.getenv("supabase_secret_name")
    if not supabase_secret_name:
        print("ERROR: Missing environment variable 'supabase_secret_name'")
        return False
        
    print(f"\nAttempting to retrieve Supabase credentials from secret '{supabase_secret_name}'...")
    
    try:
        # Retrieve the credentials
        credentials = get_secret(supabase_secret_name)
        print("Successfully retrieved credentials from AWS Secrets Manager")
        
        # Print credential details (safely)
        for key in credentials:
            value = credentials[key]
            if isinstance(value, str):
                masked_value = value[:5] + "..." if len(value) > 5 else "[empty]"
                print(f"  - {key}: {masked_value}")
            else:
                print(f"  - {key}: {type(value).__name__}")
        
        # Validate the credentials
        print("\nValidating Supabase credentials...")
        is_valid, message = validate_supabase_credentials(credentials)
        
        if is_valid:
            print(f"SUCCESS: {message}")
            return True
        else:
            print(f"VALIDATION FAILED: {message}")
            
            # Provide additional troubleshooting info
            if "URL" in message:
                print("\nURL Troubleshooting:")
                print("- Ensure URL starts with https://")
                print("- Confirm the format is: https://[project-ref].supabase.co")
                
            if "API key" in message:
                print("\nAPI Key Troubleshooting:")
                print("- Service role keys should start with 'eyJ' (JWT format)")
                print("- Check for whitespace or newline characters")
                print("- Verify you're using the service role key, not the anon key")
                
            if "JWT secret" in message:
                print("\nJWT Secret Troubleshooting:")
                print("- This should be a long string")
                print("- Ensure it was saved correctly in AWS Secrets Manager")
                
            if "401" in message or "Authentication failed" in message:
                print("\nAuthentication Error:")
                print("- Your API key has the wrong value or is invalid")
                print("- Verify the key in your Supabase dashboard")
                
            return False
        
    except Exception as e:
        print(f"ERROR: Failed to validate Supabase credentials: {str(e)}")
        return False
        
if __name__ == "__main__":
    success = check_supabase_credentials()
    print("\nValidation complete.")
    sys.exit(0 if success else 1)
