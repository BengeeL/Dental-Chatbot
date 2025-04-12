import re
import logging
from typing import Dict, Tuple
import requests

logger = logging.getLogger(__name__)

def validate_supabase_credentials(credentials: Dict) -> Tuple[bool, str]:
    """
    Validate Supabase credentials retrieved from AWS Secrets Manager.
    
    Args:
        credentials (Dict): Dictionary containing Supabase credentials
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    # Check if all required keys exist
    required_keys = ["SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "JWT_SECRET"]
    missing_keys = [key for key in required_keys if key not in credentials]
    
    if missing_keys:
        return False, f"Missing required keys in Supabase credentials: {', '.join(missing_keys)}"
    
    # Basic format validation
    url = credentials.get("SUPABASE_URL", "")
    api_key = credentials.get("SUPABASE_SERVICE_ROLE_KEY", "")
    jwt_secret = credentials.get("JWT_SECRET", "")
    
    # URL validation
    if not url or not url.startswith(("http://", "https://")):
        return False, f"Invalid Supabase URL format: '{url}'"
    
    # API key validation (Supabase keys typically start with 'eyJ' for JWT format)
    if not api_key or len(api_key) < 20:  # Arbitrary minimum length
        return False, "Supabase API key is missing or too short"
    
    if not api_key.startswith("eyJ"):
        logger.warning(f"Supabase API key has unusual format: {api_key[:5]}...")
    
    # JWT secret validation
    if not jwt_secret or len(jwt_secret) < 20:  # JWT secrets should be reasonably long
        return False, "JWT secret is missing or too short"
    
    # Test the connection to Supabase
    try:
        # Make a simple request to Supabase health endpoint
        headers = {
            "apikey": api_key,
            "Authorization": f"Bearer {api_key}"
        }
        
        # Try to access the REST API to verify the URL and key
        response = requests.get(
            f"{url}/rest/v1/",
            headers=headers,
            timeout=5
        )
        
        # Check response
        if response.status_code == 401:
            return False, "Authentication failed with provided Supabase credentials"
        elif response.status_code >= 400:
            return False, f"Supabase connection test failed with status code: {response.status_code}"
            
        logger.info("Successfully verified Supabase credentials")
        return True, "Supabase credentials validated successfully"
        
    except requests.RequestException as e:
        return False, f"Failed to connect to Supabase: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error validating Supabase connection: {str(e)}"
