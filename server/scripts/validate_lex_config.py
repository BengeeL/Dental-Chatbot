import os
import sys
import boto3
import uuid
from dotenv import load_dotenv

# Add parent directory to path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables from .env file
load_dotenv()

from utils.aws_utils import get_secret, validate_aws_credentials

def check_lex_bot_exists():
    """Check if the specified Lex bot exists and is properly configured"""
    print("Amazon Lex Bot Configuration Validator")
    print("=====================================")
    
    # Check AWS credentials first
    aws_valid, aws_message = validate_aws_credentials()
    print(f"\nAWS Credentials check: {aws_message}")
    
    if not aws_valid:
        print("Cannot continue without valid AWS credentials")
        return False
    
    # Get Lex credentials from Secrets Manager
    print("\nRetrieving Lex credentials...")
    try:
        lex_creds = get_secret("lex")
        
        bot_id = lex_creds.get('LEX_BOT_ID')
        bot_alias_id = lex_creds.get('LEX_BOT_ALIAS_ID')
        locale_id = lex_creds.get('LEX_BOT_LOCALE_ID', 'en_US')
        region = lex_creds.get('AWS_REGION', 'ca-central-1')
        
        print("\nLex configuration retrieved from Secrets Manager:")
        print(f"- Bot ID: {bot_id}")
        print(f"- Bot Alias ID: {bot_alias_id}")
        print(f"- Locale ID: {locale_id}")
        print(f"- Region: {region}")
        
        # Check for placeholder values
        if not bot_id or bot_id == "XPYCUV8WOV":
            print("\n⚠️ Warning: Bot ID appears to be a placeholder (XPYCUV8WOV)")
        
        if not bot_alias_id or bot_alias_id == "TSTALIASID":
            print("\n⚠️ Warning: Bot Alias ID appears to be a placeholder (TSTALIASID)")
        
        # Create Lex V2 client
        session = boto3.session.Session()
        lex_models_client = session.client(
            'lexv2-models',
            region_name=region,
            aws_access_key_id=lex_creds.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=lex_creds.get('AWS_SECRET_ACCESS_KEY')
        )
        
        lex_runtime_client = session.client(
            'lexv2-runtime',
            region_name=region,
            aws_access_key_id=lex_creds.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=lex_creds.get('AWS_SECRET_ACCESS_KEY')
        )
        
        # Step 1: Check if the bot exists
        print("\nChecking if bot exists...")
        try:
            bot_response = lex_models_client.describe_bot(
                botId=bot_id
            )
            print(f"✅ Bot found: {bot_response.get('botName', 'Unknown')}")
        except Exception as e:
            print(f"❌ Bot not found: {str(e)}")
            print("\nAvailable bots in your account:")
            try:
                bots = lex_models_client.list_bots()
                if bots.get('botSummaries'):
                    for bot in bots.get('botSummaries'):
                        print(f"- {bot.get('botName')} (ID: {bot.get('botId')})")
                else:
                    print("No bots found in this account/region")
            except Exception as list_e:
                print(f"Could not list bots: {str(list_e)}")
            return False
            
        # Step 2: Check if the alias exists
        print("\nChecking if bot alias exists...")
        try:
            alias_response = lex_models_client.describe_bot_alias(
                botId=bot_id,
                botAliasId=bot_alias_id
            )
            print(f"✅ Bot alias found: {alias_response.get('botAliasName', 'Unknown')}")
        except Exception as e:
            print(f"❌ Bot alias not found: {str(e)}")
            print("\nAvailable aliases for this bot:")
            try:
                aliases = lex_models_client.list_bot_aliases(botId=bot_id)
                if aliases.get('botAliasSummaries'):
                    for alias in aliases.get('botAliasSummaries'):
                        print(f"- {alias.get('botAliasName')} (ID: {alias.get('botAliasId')})")
                else:
                    print("No aliases found for this bot")
            except Exception as list_e:
                print(f"Could not list aliases: {str(list_e)}")
            return False
            
        # Step 3: Check if the locale exists
        print("\nChecking if bot locale exists...")
        try:
            locale_response = lex_models_client.describe_bot_locale(
                botId=bot_id,
                botVersion='DRAFT',
                localeId=locale_id
            )
            print(f"✅ Bot locale found: {locale_id}")
        except Exception as e:
            print(f"❌ Bot locale not found: {str(e)}")
            print("\nAvailable locales for this bot:")
            try:
                locales = lex_models_client.list_bot_locales(botId=bot_id, botVersion='DRAFT')
                if locales.get('botLocaleSummaries'):
                    for locale in locales.get('botLocaleSummaries'):
                        print(f"- {locale.get('localeId')}")
                else:
                    print("No locales found for this bot")
            except Exception as list_e:
                print(f"Could not list locales: {str(list_e)}")
            return False
            
        # Step 4: Test a sample conversation
        print("\nTesting a sample conversation with the bot...")
        try:
            session_id = str(uuid.uuid4())
            response = lex_runtime_client.recognize_text(
                botId=bot_id,
                botAliasId=bot_alias_id,
                localeId=locale_id,
                sessionId=session_id,
                text="Hello"
            )
            
            messages = response.get('messages', [])
            if messages:
                print("✅ Bot responded to test message:")
                for msg in messages:
                    print(f"   {msg.get('content')}")
            else:
                print("⚠️ Bot responded but no messages were returned")
                
            return True
        except Exception as e:
            print(f"❌ Failed to test conversation: {str(e)}")
            return False
            
    except Exception as e:
        print(f"ERROR: Failed to check Lex configuration: {str(e)}")
        return False
        
if __name__ == "__main__":
    success = check_lex_bot_exists()
    print("\nValidation complete.")
    
    if not success:
        print("\nTroubleshooting Guide:")
        print("1. Check that your bot is properly created in the Lex V2 console")
        print("2. Verify the Bot ID - this is NOT the bot name, but its unique ID")
        print("3. Verify the Bot Alias ID - this is NOT the alias name")
        print("4. Check that the specified locale (e.g., en_US, en_CA) is configured for your bot")
        print("5. Make sure your bot is built and published to the alias you're trying to use")
        print("6. Update your AWS Secrets Manager with the correct values")
    
    sys.exit(0 if success else 1)
