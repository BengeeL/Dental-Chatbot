import boto3
import logging
import os
import base64
import uuid
import time
from botocore.exceptions import ClientError
from io import BytesIO

logger = logging.getLogger(__name__)
transcribe_client = None

def init_transcribe_client():
    """Initialize Amazon Transcribe client"""
    global transcribe_client
    try:
        # Use Lambda environment AWS_REGION or get from our custom env var
        region = boto3.session.Session().region_name or os.environ.get('DEFAULT_REGION', 'ca-central-1')
        
        # Create Transcribe client using Lambda's IAM role
        transcribe_client = boto3.client('transcribe', region_name=region)
        
        logger.info(f"Transcribe client initialized in region {region}")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize Transcribe client: {str(e)}")
        return False

def wait_for_job_completion(job_name, max_tries=30, delay=2):
    """
    Poll for transcription job completion with timeout
    
    Args:
        job_name (str): Name of the transcription job
        max_tries (int): Maximum number of polling attempts
        delay (int): Seconds to wait between polls
        
    Returns:
        dict: Job response or None if timeout or error
    """
    global transcribe_client
    tries = 0
    
    while tries < max_tries:
        try:
            response = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
            status = response['TranscriptionJob']['TranscriptionJobStatus']
            
            if status == 'COMPLETED':
                return response
            elif status == 'FAILED':
                logger.error(f"Transcription job failed: {response['TranscriptionJob'].get('FailureReason', 'Unknown reason')}")
                return None
            
            tries += 1
            time.sleep(delay)
        except Exception as e:
            logger.error(f"Error checking job status: {str(e)}")
            return None
            
    logger.error(f"Transcription job timed out after {max_tries * delay} seconds")
    return None

def speech_to_text(audio_data_base64, content_type='audio/webm'):
    """
    Convert speech to text using Amazon Transcribe
    
    Args:
        audio_data_base64 (str): Base64 encoded audio data
        content_type (str): Content type of the audio data
        
    Returns:
        dict: Response containing transcribed text
    """
    if not transcribe_client:
        if not init_transcribe_client():
            return {
                "error": "Failed to initialize Transcribe client",
                "text": None
            }
    
    try:
        # Decode base64 audio data
        audio_data = base64.b64decode(audio_data_base64)
        
        # Use streaming transcription for short audio clips
        s3_client = boto3.client('s3')
        bucket_name = os.environ.get('S3_BUCKET_NAME', 'dental-chat-recordings')
        file_key = f"temp-recordings/{uuid.uuid4()}.webm"
        
        # Upload to S3
        s3_client.put_object(
            Body=audio_data,
            Bucket=bucket_name,
            Key=file_key,
            ContentType=content_type
        )
        
        # Start transcription job
        job_name = f"transcribe-{uuid.uuid4()}"
        transcribe_client.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'MediaFileUri': f"s3://{bucket_name}/{file_key}"},
            MediaFormat='webm',
            LanguageCode='en-US'
        )
        
        # Wait for completion using our custom polling function
        response = wait_for_job_completion(job_name)
        if not response:
            return {
                "error": "Transcription job failed or timed out",
                "text": None
            }
        
        # Get the transcription result
        transcript_uri = response['TranscriptionJob']['Transcript']['TranscriptFileUri']
        
        # Get the transcript content
        import requests
        transcript_response = requests.get(transcript_uri)
        transcript_data = transcript_response.json()
        transcribed_text = transcript_data['results']['transcripts'][0]['transcript']
        
        # Clean up
        transcribe_client.delete_transcription_job(TranscriptionJobName=job_name)
        s3_client.delete_object(Bucket=bucket_name, Key=file_key)
        
        return {
            "text": transcribed_text
        }
            
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        error_message = e.response.get('Error', {}).get('Message', str(e))
        
        logger.error(f"AWS Error ({error_code}): {error_message}")
        return {
            "error": error_message,
            "text": None
        }
            
    except Exception as e:
        logger.error(f"Error converting speech to text: {str(e)}")
        return {
            "error": str(e),
            "text": None
        }
