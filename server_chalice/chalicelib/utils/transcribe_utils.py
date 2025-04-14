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
recordings_bucket = "dental-chat-recordings"

def init_transcribe_client():
    """Initialize Amazon Transcribe client"""
    global transcribe_client
    try:
        # Get region from Lambda environment or fallback to DEFAULT_REGION
        region = os.environ.get('AWS_LAMBDA_FUNCTION_REGION', 
                  os.environ.get('DEFAULT_REGION', 'ca-central-1'))
        
        # Create Transcribe client using explicit region
        transcribe_client = boto3.client('transcribe', region_name=region)
        
        # Initialize S3 bucket for recordings
        s3_client = boto3.client('s3', region_name=region)
        try:
            # Check if bucket exists
            s3_client.head_bucket(Bucket=recordings_bucket)
            logger.info(f"S3 bucket '{recordings_bucket}' exists")
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code')
            if error_code == '404' or error_code == 'NoSuchBucket':
                # Bucket doesn't exist, create it
                logger.info(f"Creating S3 bucket '{recordings_bucket}'...")
                try:
                    # Handle different region configurations
                    if region == 'us-east-1':
                        s3_client.create_bucket(Bucket=recordings_bucket)
                    else:
                        s3_client.create_bucket(
                            Bucket=recordings_bucket,
                            CreateBucketConfiguration={'LocationConstraint': region}
                        )
                    logger.info(f"S3 bucket '{recordings_bucket}' created")
                except Exception as create_error:
                    logger.error(f"Error creating S3 bucket: {str(create_error)}")
                    return False
            else:
                logger.error(f"Error checking S3 bucket: {str(e)}")
                return False
        
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
            logger.error("Failed to initialize Transcribe client")
            return {
                "error": "Failed to initialize Transcribe client",
                "text": None
            }
    
    try:
        # Decode base64 audio data
        logger.info("Decoding audio data")
        try:
            audio_data = base64.b64decode(audio_data_base64)
            logger.info(f"Audio data decoded, size: {len(audio_data)} bytes")
        except Exception as e:
            logger.error(f"Failed to decode base64 audio: {str(e)}")
            return {
                "error": f"Invalid audio data: {str(e)}",
                "text": None
            }
        
        # Get region for S3 client
        region = os.environ.get('AWS_LAMBDA_FUNCTION_REGION', 
                  os.environ.get('DEFAULT_REGION', 'ca-central-1'))
        
        # Upload to S3
        s3_client = boto3.client('s3', region_name=region)
        file_key = f"temp-recordings/{uuid.uuid4()}.webm"
        
        logger.info(f"Uploading audio to S3 bucket '{recordings_bucket}', key: {file_key}")
        try:
            s3_client.put_object(
                Body=audio_data,
                Bucket=recordings_bucket,
                Key=file_key,
                ContentType=content_type
            )
            logger.info("Audio uploaded to S3 successfully")
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code')
            error_message = e.response.get('Error', {}).get('Message')
            logger.error(f"S3 upload error ({error_code}): {error_message}")
            return {
                "error": f"Failed to upload audio to S3: {error_message}",
                "text": None
            }
        
        # Start transcription job
        job_name = f"transcribe-{uuid.uuid4()}"
        try:
            logger.info(f"Starting transcription job: {job_name}")
            transcribe_client.start_transcription_job(
                TranscriptionJobName=job_name,
                Media={'MediaFileUri': f"s3://{recordings_bucket}/{file_key}"},
                MediaFormat='webm',
                LanguageCode='en-US'
            )
            logger.info("Transcription job started successfully")
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code')
            error_message = e.response.get('Error', {}).get('Message')
            logger.error(f"Transcribe start job error ({error_code}): {error_message}")
            return {
                "error": f"Failed to start transcription: {error_message}",
                "text": None
            }
        
        # Wait for completion using our custom polling function
        logger.info("Waiting for transcription job to complete...")
        response = wait_for_job_completion(job_name)
        if not response:
            logger.error("Transcription job failed or timed out")
            return {
                "error": "Transcription job failed or timed out",
                "text": None
            }
        
        # Get the transcription result
        try:
            transcript_uri = response['TranscriptionJob']['Transcript']['TranscriptFileUri']
            logger.info(f"Transcription completed, retrieving results from: {transcript_uri}")
            
            # Get the transcript content
            import requests
            transcript_response = requests.get(transcript_uri)
            transcript_data = transcript_response.json()
            
            if 'results' not in transcript_data or 'transcripts' not in transcript_data['results'] or len(transcript_data['results']['transcripts']) == 0:
                logger.error("Invalid transcript format received")
                return {
                    "error": "Invalid transcript format received",
                    "text": None
                }
                
            transcribed_text = transcript_data['results']['transcripts'][0]['transcript']
            logger.info(f"Transcription result: '{transcribed_text}'")
        except Exception as e:
            logger.error(f"Error retrieving transcript: {str(e)}")
            return {
                "error": f"Error retrieving transcript: {str(e)}",
                "text": None
            }
        
        # Clean up
        try:
            logger.info(f"Cleaning up: deleting transcription job {job_name}")
            transcribe_client.delete_transcription_job(TranscriptionJobName=job_name)
            
            logger.info(f"Cleaning up: deleting S3 object {file_key}")
            s3_client.delete_object(Bucket=recordings_bucket, Key=file_key)
        except Exception as e:
            logger.warning(f"Cleanup error (non-critical): {str(e)}")
        
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
        logger.error(f"Error converting speech to text: {str(e)}", exc_info=True)
        return {
            "error": str(e),
            "text": None
        }
