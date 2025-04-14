import boto3
import logging
import os
import base64
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
polly_client = None

def init_polly_client():
    """Initialize Amazon Polly client"""
    global polly_client
    try:
        # Get region from Lambda environment or fallback to DEFAULT_REGION
        region = os.environ.get('AWS_LAMBDA_FUNCTION_REGION', 
                  os.environ.get('DEFAULT_REGION', 'ca-central-1'))
        
        # Create Polly client using explicit region
        polly_client = boto3.client('polly', region_name=region)
        
        logger.info(f"Polly client initialized in region {region}")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize Polly client: {str(e)}")
        return False

def text_to_speech(text: str, voice_id: str = 'Joanna'):
    """
    Convert text to speech using Amazon Polly
    
    Args:
        text (str): Text to convert to speech
        voice_id (str): Voice ID to use
        
    Returns:
        dict: Response containing audio data as base64
    """
    if not polly_client:
        if not init_polly_client():
            return {
                "error": "Failed to initialize Polly client",
                "audio": None
            }
    
    try:
        response = polly_client.synthesize_speech(
            Text=text,
            OutputFormat='mp3',
            VoiceId=voice_id
        )
        
        # Get audio data
        if "AudioStream" in response:
            # Read audio data and encode as base64
            audio_data = response["AudioStream"].read()
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            return {
                "audio": audio_base64,
                "format": "mp3",
                "voice": voice_id
            }
        else:
            logger.error("No AudioStream in Polly response")
            return {
                "error": "No audio stream returned",
                "audio": None
            }
            
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        error_message = e.response.get('Error', {}).get('Message', str(e))
        
        logger.error(f"AWS Error ({error_code}): {error_message}")
        return {
            "error": error_message,
            "audio": None
        }
            
    except Exception as e:
        logger.error(f"Error converting text to speech: {str(e)}")
        return {
            "error": str(e),
            "audio": None
        }
