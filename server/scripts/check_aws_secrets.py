import os
import sys
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

# Add parent directory to path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.aws_utils import validate_aws_credentials


def list_available_secrets():
    """List all secrets available to the current AWS credentials"""
    try:
        # Use the Canada region where secrets are stored
        region_name = os.environ.get("AWS_REGION", "ca-central-1")
        session = boto3.session.Session()
        client = session.client(service_name='secretsmanager', region_name=region_name)
        
        print(f"\nAttempting to list available secrets in region {region_name}...")
        response = client.list_secrets(MaxResults=100)
        secrets = response.get('SecretList', [])
        
        if not secrets:
            print("No secrets found or no permission to list secrets.")
            return
        
        print(f"\nFound {len(secrets)} secrets:")
        for secret in secrets:
            print(f"- {secret.get('Name')}")
            
    except NoCredentialsError:
        print("No AWS credentials found.")
    except ClientError as e:
        print(f"Error listing secrets: {e}")


def check_specific_secret(secret_name):
    """Check if a specific secret exists and is accessible"""
    try:
        region_name = os.environ.get("AWS_REGION", "ca-central-1")
        session = boto3.session.Session()
        client = session.client(service_name='secretsmanager', region_name=region_name)
        
        print(f"\nChecking if secret '{secret_name}' exists and is accessible in region {region_name}...")
        try:
            response = client.describe_secret(SecretId=secret_name)
            print(f"Secret '{secret_name}' found! Details:")
            print(f"- ARN: {response.get('ARN')}")
            print(f"- Last accessed: {response.get('LastAccessedDate')}")
            print(f"- Last changed: {response.get('LastChangedDate')}")
            return True
        except ClientError as e:
            if e.response.get('Error', {}).get('Code') == 'ResourceNotFoundException':
                print(f"Secret '{secret_name}' does not exist in {region_name} region.")
            else:
                print(f"Error accessing secret '{secret_name}': {e}")
            return False
            
    except NoCredentialsError:
        print("No AWS credentials found.")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False


def check_aws_configuration():
    """Check AWS configuration details"""
    try:
        session = boto3.session.Session()
        
        print("\nAWS Configuration:")
        print(f"- Region: {session.region_name or 'Not set (using default)'}")
        
        sts = session.client('sts')
        try:
            identity = sts.get_caller_identity()
            print(f"- Account ID: {identity.get('Account')}")
            print(f"- User/Role ARN: {identity.get('Arn')}")
        except Exception as e:
            print(f"- Could not get identity information: {e}")
            
        try:
            available_regions = session.get_available_regions('secretsmanager')
            print(f"- Available regions for Secrets Manager: {', '.join(available_regions)}")
        except Exception as e:
            print(f"- Could not get available regions: {e}")
            
    except Exception as e:
        print(f"Error checking AWS configuration: {e}")


if __name__ == "__main__":
    print("AWS Secrets Manager Diagnostics Tool")
    print("===================================")
    
    # Check AWS credentials
    is_valid, message = validate_aws_credentials()
    print(f"\nAWS Credentials check: {message}")
    
    if is_valid:
        check_aws_configuration()
        list_available_secrets()
        
        # Check the specific secret we're trying to access
        secret_name = os.getenv("supabase_secret_name", "supabase")
        check_specific_secret(secret_name)
        
        print("\nTips if you're having trouble with AWS Secrets:")
        print("1. Check that the secret name is correct")
        print(f"2. Verify the secret exists in region '{os.environ.get('AWS_REGION', 'ca-central-1')}' (or change the AWS_REGION environment variable)")
        print("3. Make sure your AWS credentials have permission to access this secret")
        print("4. If using named profiles, check that you've set AWS_PROFILE in your environment")
    
    print("\nFor local development without AWS Secrets:")
    print("1. Set USE_MOCK_SECRETS=true in your environment")
    print("2. Or set individual environment variables for each credential")
