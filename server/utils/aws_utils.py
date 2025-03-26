import boto3
from botocore.exceptions import ClientError
import json


def get_secret(secret_name: str):
    """
    Retrieve a secret from AWS Secrets Manager.
    Args:
        secret_name (str): The name of the secret to retrieve.
    Returns:
        dict: A dictionary containing the secret key-value pairs.
    Raises:
        ClientError: If there is an error retrieving the secret from AWS Secrets Manager.
    """
    region_name = "us-east-1"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    print(f"Getting secret: {secret_name}")

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        print(f"Error getting secret: {e}")
        raise e

    secret_str = get_secret_value_response['SecretString']
    secret_dict = json.loads(secret_str)
    return secret_dict
