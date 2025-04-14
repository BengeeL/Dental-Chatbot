from chalice import Chalice, Response, BadRequestError, CORSConfig
import uuid
import logging
import json
import boto3
import os
from chalicelib.utils.lex_utils import init_lex_client, send_message_to_lex
from chalicelib.utils.polly_utils import init_polly_client, text_to_speech
from chalicelib.utils.dynamo_utils import init_dynamodb, store_conversation, get_conversation_history
from chalicelib.utils.transcribe_utils import init_transcribe_client, speech_to_text
from chalicelib.utils.s3_utils import init_s3_client, store_conversation_in_s3
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the Chalice app
app = Chalice(app_name='dental-chatbot')

# Configure CORS for frontend integration
cors_config = CORSConfig(
    allow_origin='*',  # For development; restrict in production
    allow_headers=['Content-Type', 'X-Amz-Date', 'Authorization', 'X-Api-Key'],
    max_age=600,
    expose_headers=['X-Request-ID'],
    allow_credentials=True
)

# Initialize clients on cold starts
lex_initialized = init_lex_client()
polly_initialized = init_polly_client()
dynamo_initialized = init_dynamodb()
transcribe_initialized = init_transcribe_client()
s3_initialized = init_s3_client()

@app.route('/', methods=['GET'], cors=cors_config)
def index():
    """Root endpoint that returns basic API information"""
    return {
        'status': 'ok',
        'message': 'Dental Chatbot API is running (Serverless)',
        'version': '1.0',
        'endpoints': ['/chat', '/health', '/speech', '/transcribe', '/save-conversation']
    }

@app.route('/health', methods=['GET'], cors=cors_config)
def health_check():
    """Health check endpoint for the API"""
    return {
        'status': 'healthy',
        'timestamp': str(app.current_request.context['requestTimeEpoch'])
    }

@app.route('/chat', methods=['POST'], cors=cors_config)
def process_chat_message():
    """Process user message and return a response from Amazon Lex"""
    try:
        # Parse request body
        request_body = app.current_request.json_body
        if not request_body:
            return Response(
                body={'text': 'Missing request body', 'status': 'error'},
                status_code=400
            )
        
        message = request_body.get('message')
        session_id = request_body.get('session_id') or str(uuid.uuid4())
        
        if not message:
            return Response(
                body={'text': 'Missing message parameter', 'status': 'error'},
                status_code=400
            )
            
        logger.info(f"Received chat message: {message}")
        
        # Ensure Lex client is initialized
        global lex_initialized
        if not lex_initialized:
            lex_initialized = init_lex_client()
            if not lex_initialized:
                logger.error("Failed to initialize Lex client")
                return {
                    'text': 'Sorry, the dental assistant service is currently unavailable.',
                    'status': 'error'
                }
        
        # Send the message to Lex
        lex_response = send_message_to_lex(session_id, message)
        
        if "error" in lex_response:
            logger.error(f"Error from Lex: {lex_response['error']}")
            return {
                'text': lex_response["text"],
                'status': 'error'
            }
        
        # Store conversation in DynamoDB
        global dynamo_initialized
        if not dynamo_initialized:
            dynamo_initialized = init_dynamodb()
        
        if dynamo_initialized:
            store_conversation(
                session_id=session_id,
                message=message,
                response=lex_response["text"],
                intent=lex_response.get("intent")
            )
            logger.info(f"Conversation stored in DynamoDB for session {session_id}")
        else:
            logger.warning("DynamoDB not initialized, conversation not stored")
        
        return {
            'text': lex_response["text"],
            'intent': lex_response.get("intent"),
            'status': 'ok',
            'session_id': session_id
        }
        
    except Exception as e:
        logger.error(f"Error processing chat message: {str(e)}", exc_info=True)
        return Response(
            body={'text': f'Error processing message: {str(e)}', 'status': 'error'},
            status_code=500
        )

@app.route('/chat/health', methods=['GET'], cors=cors_config)
def chat_health():
    """Check if the chat service is healthy"""
    try:
        if not lex_initialized:
            if not init_lex_client():
                logger.warning("Lex client not initialized")
                return {"status": "warning", "message": "Lex client not connected"}
                
        return {"status": "ok", "message": "Chat service is healthy"}
    except Exception as e:
        logger.error(f"Error checking chat health: {str(e)}")
        return {"status": "error", "message": str(e)}

@app.route('/speech', methods=['POST'], cors=cors_config)
def text_to_speech_endpoint():
    """Convert text to speech using Amazon Polly"""
    try:
        # Parse request body
        request_body = app.current_request.json_body
        if not request_body:
            return Response(
                body={'error': 'Missing request body'},
                status_code=400
            )
        
        text = request_body.get('text')
        voice = request_body.get('voice', 'Joanna')
        
        if not text:
            return Response(
                body={'error': 'Missing text parameter'},
                status_code=400
            )
            
        logger.info(f"Converting text to speech: {text[:30]}...")
        
        # Ensure Polly client is initialized
        global polly_initialized
        if not polly_initialized:
            polly_initialized = init_polly_client()
            if not polly_initialized:
                logger.error("Failed to initialize Polly client")
                return {
                    'error': 'Speech synthesis service is currently unavailable.'
                }
        
        # Convert text to speech
        speech_response = text_to_speech(text, voice)
        
        if "error" in speech_response:
            logger.error(f"Error from Polly: {speech_response['error']}")
            return {
                'error': speech_response["error"]
            }
        
        return speech_response
        
    except Exception as e:
        logger.error(f"Error processing speech request: {str(e)}", exc_info=True)
        return Response(
            body={'error': f'Error processing request: {str(e)}'},
            status_code=500
        )

@app.route('/transcribe', methods=['POST'], cors=cors_config)
def transcribe_audio():
    """Convert audio to text using Amazon Transcribe"""
    try:
        # Parse request body
        request_body = app.current_request.json_body
        if not request_body:
            return Response(
                body={'error': 'Missing request body'},
                status_code=400
            )
        
        audio_data = request_body.get('audio')
        content_type = request_body.get('content_type', 'audio/webm')
        
        if not audio_data:
            return Response(
                body={'error': 'Missing audio parameter'},
                status_code=400
            )
            
        logger.info("Received audio for transcription")
        
        # Ensure Transcribe client is initialized
        global transcribe_initialized
        if not transcribe_initialized:
            transcribe_initialized = init_transcribe_client()
            if not transcribe_initialized:
                logger.error("Failed to initialize Transcribe client")
                return {
                    'error': 'Speech recognition service is currently unavailable.'
                }
        
        # Convert speech to text
        transcribe_response = speech_to_text(audio_data, content_type)
        
        if "error" in transcribe_response:
            logger.error(f"Error from Transcribe: {transcribe_response['error']}")
            return {
                'error': transcribe_response["error"]
            }
        
        return {
            'text': transcribe_response["text"]
        }
        
    except Exception as e:
        logger.error(f"Error processing transcription request: {str(e)}", exc_info=True)
        return Response(
            body={'error': f'Error processing request: {str(e)}'},
            status_code=500
        )

@app.route('/save-conversation', methods=['POST'], cors=cors_config)
def save_conversation():
    """Save a complete conversation to S3"""
    try:
        # Parse request body
        request_body = app.current_request.json_body
        if not request_body:
            return Response(
                body={'error': 'Missing request body'},
                status_code=400
            )
        
        session_id = request_body.get('session_id')
        messages = request_body.get('messages')
        
        if not session_id or not messages:
            return Response(
                body={'error': 'Missing required parameters'},
                status_code=400
            )
            
        logger.info(f"Saving conversation for session {session_id}")
        
        # Ensure S3 client is initialized
        global s3_initialized
        if not s3_initialized:
            s3_initialized = init_s3_client()
            if not s3_initialized:
                logger.error("Failed to initialize S3 client")
                return {
                    'success': False,
                    'error': 'Storage service is currently unavailable.'
                }
        
        # Format conversation data
        conversation_data = {
            'session_id': session_id,
            'timestamp': datetime.utcnow().isoformat(),
            'messages': messages
        }
        
        # Store in S3
        success = store_conversation_in_s3(session_id, conversation_data)
        
        if not success:
            return {
                'success': False,
                'error': 'Failed to store conversation'
            }
        
        return {
            'success': True
        }
        
    except Exception as e:
        logger.error(f"Error saving conversation: {str(e)}", exc_info=True)
        return Response(
            body={'error': f'Error saving conversation: {str(e)}', 'success': False},
            status_code=500
        )
