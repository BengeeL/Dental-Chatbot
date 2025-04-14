import boto3
import logging
import os
import json
from datetime import datetime
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
s3_client = None

# Get S3 bucket name from Chalice config
CONVERSATION_BUCKET = os.environ.get('S3_BUCKET_NAME', 'dental-chat-conversations')

def init_s3_client():
    """Initialize S3 client"""
    global s3_client
    try:
        # Use the AWS_REGION from Chalice config
        region = os.environ.get('AWS_REGION', 'ca-central-1')
        
        # Create S3 client using explicit region
        s3_client = boto3.client('s3', region_name=region)
        
        # Ensure the bucket exists
        try:
            s3_client.head_bucket(Bucket=CONVERSATION_BUCKET)
            logger.info(f"S3 bucket '{CONVERSATION_BUCKET}' exists")
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                # Bucket doesn't exist, create it
                logger.info(f"Creating S3 bucket '{CONVERSATION_BUCKET}'...")
                s3_client.create_bucket(
                    Bucket=CONVERSATION_BUCKET,
                    CreateBucketConfiguration={
                        'LocationConstraint': region
                    }
                )
                logger.info(f"S3 bucket '{CONVERSATION_BUCKET}' created")
            else:
                logger.error(f"Error checking S3 bucket: {str(e)}")
                raise
                
        logger.info(f"S3 client initialized for bucket '{CONVERSATION_BUCKET}' in region {region}")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize S3 client: {str(e)}")
        return False

def store_conversation_in_s3(session_id, conversation_data):
    """
    Store conversation in S3
    
    Args:
        session_id (str): Session ID
        conversation_data (dict): Conversation data to store
        
    Returns:
        bool: Success status
    """
    if not s3_client:
        if not init_s3_client():
            logger.error("Failed to initialize S3 client")
            return False
    
    try:
        # Generate folder structure by date: year/month/day
        now = datetime.utcnow()
        date_folder = f"{now.year}/{now.month:02d}/{now.day:02d}"
        
        # Create a unique key for this conversation
        timestamp = now.strftime("%Y%m%d-%H%M%S")
        file_key = f"{date_folder}/{session_id}-{timestamp}.json"
        
        # Upload conversation data
        s3_client.put_object(
            Body=json.dumps(conversation_data, indent=2),
            Bucket=CONVERSATION_BUCKET,
            Key=file_key,
            ContentType='application/json'
        )
        
        logger.info(f"Stored conversation for session {session_id} at {file_key}")
        return True
    except Exception as e:
        logger.error(f"Error storing conversation in S3: {str(e)}")
        return False
