import boto3
import base64
import json

class SpeechService:
    def __init__(self):
        self.client = boto3.client('polly')

    def generate_speech(self, text, language_code="en-US", engine="standard"): 
        try:
            response = self.client.synthesize_speech(
                Text=text,
                OutputFormat='mp3',
                VoiceId='Joanna',
                LanguageCode=language_code,
                Engine=engine
            )
            audio_stream = response['AudioStream'].read()
            
            # Encode the audio stream to base64
            audio_base64 = base64.b64encode(audio_stream).decode('utf-8')
            
            # Return the base64 encoded audio in a JSON response
            return json.dumps({'audio_base64': audio_base64})
        
        except Exception as e:
            print(f"Error generating speech: {e}")
            return json.dumps({'error': str(e)}) #Return Json with error.