import os
import sys
from dotenv import load_dotenv

# Add parent directory to path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables from .env file
load_dotenv()

from utils.aws_utils import get_secret, validate_aws_credentials

def check_redis_credentials():
    """Script to validate Redis credentials from AWS Secrets Manager"""
    print("Redis Credential Validation Tool")
    print("===============================")
    
    # Check AWS credentials first
    aws_valid, aws_message = validate_aws_credentials()
    print(f"\nAWS Credentials check: {aws_message}")
    
    if not aws_valid:
        print("Cannot continue without valid AWS credentials")
        return False
    
    # Retrieve the Redis credentials
    print("\nAttempting to retrieve Redis credentials...")
    try:
        redis_creds = get_secret("redis")
        print("Successfully retrieved Redis credentials from AWS Secrets Manager")
        
        # Check for required keys
        required_keys = ["host", "port", "password"]
        optional_keys = ["ssl", "db", "timeout", "encoding"]
        
        print("\nValidating Redis credential structure:")
        
        # Check required keys
        missing_keys = [key for key in required_keys if key not in redis_creds]
        if missing_keys:
            print(f"WARNING: Missing recommended keys: {', '.join(missing_keys)}")
        
        # Display all keys found
        print("\nRedis credential details:")
        for key in redis_creds:
            value = str(redis_creds[key])
            # Mask password for security
            if key == "password":
                if value:
                    masked_value = value[:2] + "*" * (len(value) - 2) if len(value) > 2 else "***"
                else:
                    masked_value = "[empty]"
                print(f"  - {key}: {masked_value}")
            else:
                print(f"  - {key}: {value}")
        
        # Check if ssl key exists
        if "ssl" not in redis_creds:
            print("\nNOTICE: The 'ssl' key is missing from Redis credentials.")
            print("A default value of 'False' will be used when connecting.")
            print("If your Redis requires SSL, you should add 'ssl': 'true' to your AWS Secret.")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to validate Redis credentials: {str(e)}")
        return False
        
if __name__ == "__main__":
    success = check_redis_credentials()
    print("\nValidation complete.")
    sys.exit(0 if success else 1)
