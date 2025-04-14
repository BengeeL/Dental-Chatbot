import boto3
import logging
import os
import json
import uuid
from botocore.exceptions import ClientError
from datetime import datetime

logger = logging.getLogger(__name__)
dynamodb = None

# Get DynamoDB table name from Chalice config
CHAT_HISTORY_TABLE = os.environ.get('DYNAMODB_TABLE', 'dental-chat-history')

def init_dynamodb():
    """Initialize DynamoDB client"""
    global dynamodb
    try:
        # Use the AWS_REGION from Chalice config
        region = os.environ.get('AWS_REGION', 'ca-central-1')
        
        # Create DynamoDB resource using explicit region
        dynamodb = boto3.resource('dynamodb', region_name=region)
        
        # Check if table exists, create if it doesn't
        try:
            table = dynamodb.Table(CHAT_HISTORY_TABLE)
            table.load()
            logger.info(f"DynamoDB table '{CHAT_HISTORY_TABLE}' already exists")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                # Table doesn't exist, create it
                logger.info(f"Creating DynamoDB table '{CHAT_HISTORY_TABLE}'...")
                
                table = dynamodb.create_table(
                    TableName=CHAT_HISTORY_TABLE,
                    KeySchema=[
                        {'AttributeName': 'session_id', 'KeyType': 'HASH'},
                        {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                    ],
                    AttributeDefinitions=[
                        {'AttributeName': 'session_id', 'AttributeType': 'S'},
                        {'AttributeName': 'timestamp', 'AttributeType': 'S'}
                    ],
                    ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
                )
                
                # Wait for table creation
                table.meta.client.get_waiter('table_exists').wait(TableName=CHAT_HISTORY_TABLE)
                logger.info(f"DynamoDB table '{CHAT_HISTORY_TABLE}' created successfully")
            else:
                logger.error(f"Error checking DynamoDB table: {str(e)}")
                raise
        
        logger.info(f"DynamoDB initialized for table '{CHAT_HISTORY_TABLE}' in region {region}")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize DynamoDB: {str(e)}")
        return False

def store_conversation(session_id: str, message: str, response: str, intent: str = None):
    """
    Store conversation in DynamoDB
    
    Args:
        session_id (str): Session ID
        message (str): User message
        response (str): Bot response
        intent (str): Detected intent
    """
    if not dynamodb:
        if not init_dynamodb():
            logger.error("Failed to initialize DynamoDB")
            return False
    
    try:
        table = dynamodb.Table(CHAT_HISTORY_TABLE)
        timestamp = datetime.utcnow().isoformat()
        
        item = {
            'session_id': session_id,
            'timestamp': timestamp,
            'message': message,
            'response': response,
            'intent': intent if intent else 'unknown'
        }
        
        table.put_item(Item=item)
        logger.info(f"Stored conversation for session {session_id}")
        return True
    except Exception as e:
        logger.error(f"Error storing conversation: {str(e)}")
        return False

def get_conversation_history(session_id: str, limit: int = 10):
    """
    Get conversation history from DynamoDB
    
    Args:
        session_id (str): Session ID
        limit (int): Maximum number of messages to return
        
    Returns:
        list: List of conversation messages
    """
    if not dynamodb:
        if not init_dynamodb():
            logger.error("Failed to initialize DynamoDB")
            return []
    
    try:
        table = dynamodb.Table(CHAT_HISTORY_TABLE)
        
        response = table.query(
            KeyConditionExpression='session_id = :sid',
            ExpressionAttributeValues={
                ':sid': session_id
            },
            ScanIndexForward=True,  # ascending order by timestamp
            Limit=limit
        )
        
        return response.get('Items', [])
    except Exception as e:
        logger.error(f"Error getting conversation history: {str(e)}")
        return []
