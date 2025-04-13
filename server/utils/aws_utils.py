import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import json
import os


def validate_aws_credentials():
    """
    Validate AWS credentials and connectivity to Secrets Manager.
    Returns:
        tuple: (bool, str) - (is_valid, message)
    """
    try:
        # Change the region to ca-central-1
        region_name = os.environ.get("AWS_REGION", "ca-central-1")
        session = boto3.session.Session()
        client = session.client(service_name='secretsmanager', region_name=region_name)
        
        # Test by listing secrets (doesn't require specific permissions)
        client.list_secrets(MaxResults=1)
        return True, f"AWS credentials are valid and Secrets Manager is accessible in region {region_name}"
    except NoCredentialsError:
        return False, "No AWS credentials found. Configure credentials using AWS CLI or set environment variables."
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code == 'AccessDeniedException':
            return False, "AWS credentials found but don't have permission to access Secrets Manager."
        elif error_code == 'UnrecognizedClientException':
            return False, "Invalid AWS credentials. Please check your configuration."
        else:
            return False, f"Error connecting to AWS Secrets Manager: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error checking AWS credentials: {str(e)}"


def get_secret_from_env(secret_name: str):
    """
    Try to get secret values from environment variables as fallback.
    This is useful for local development without AWS Secrets Manager.
    
    Format: SECRET_NAME_KEY=value (uppercase)
    Example: SUPABASE_JWT_SECRET=your-jwt-secret
    
    Args:
        secret_name (str): The name of the secret
    Returns:
        dict: Secret key-value pairs or None if not found
    """
    print(f"Attempting to get {secret_name} values from environment variables")
    prefix = f"{secret_name.upper()}_"
    secret_dict = {}
    
    # Check if we have any environment variables with the prefix
    found_any = False
    for key, value in os.environ.items():
        if key.startswith(prefix):
            found_any = True
            secret_key = key[len(prefix):].lower()  # Remove prefix and convert to lowercase
            secret_dict[secret_key] = value
    
    if found_any:
        print(f"Found {secret_name} values in environment variables")
        return secret_dict
    return None


def get_secret(secret_name: str, use_fallback=True):
    """
    Retrieve a secret from AWS Secrets Manager with fallback to environment variables.
    Args:
        secret_name (str): The name of the secret to retrieve.
        use_fallback (bool): Whether to try environment variables as fallback
    Returns:
        dict: A dictionary containing the secret key-value pairs.
    Raises:
        ClientError: If there is an error retrieving the secret and no fallback is available.
    """
    # Get region from environment or use ca-central-1 as default
    region_name = os.environ.get("AWS_REGION", "ca-central-1")

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    print(f"Getting secret: {secret_name} from region {region_name}")

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
        
        secret_str = get_secret_value_response['SecretString']
        secret_dict = json.loads(secret_str)
        print(f"Successfully retrieved secret {secret_name} from AWS Secrets Manager")
        return secret_dict
    
    except ClientError as e:
        print(f"Error getting secret: {e}")
        
        if use_fallback:
            # Try to get from environment variables instead
            env_secrets = get_secret_from_env(secret_name)
            if env_secrets:
                return env_secrets
            
            # For development, provide mock values if env var is set
            if os.environ.get('USE_MOCK_SECRETS', '').lower() == 'true':
                print(f"Using mock values for {secret_name}")
                if secret_name == 'supabase':
                    return {
                        "SUPABASE_URL": "https://example.supabase.co",
                        "SUPABASE_SERVICE_ROLE_KEY": "mock-service-key",
                        "JWT_SECRET": "mock-jwt-secret"
                    }
                elif secret_name == 'redis':
                    return {
                        "host": "localhost",
                        "port": "6379",
                        "password": "",
                        "ssl": "False"
                    }
                elif secret_name == 'postgres':
                    return {
                        "host": "localhost",
                        "port": "5432",
                        "username": "postgres",
                        "password": "postgres"
                    }
        
        # Re-raise the exception if no fallback is available
        raise e
    except Exception as e:
        print(f"Unexpected error getting secret: {e}")
        raise
