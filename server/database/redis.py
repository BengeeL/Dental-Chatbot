import redis.asyncio as redis
import os

from utils.aws_utils import get_secret

redis_client = None


# Initialize Redis connection
async def init_redis():
    global redis_client
    try:
        # First try to get from AWS Secrets Manager
        try:
            redis_creds = get_secret("redis")
        except Exception as e:
            print(f"Could not get Redis credentials from AWS: {e}")
            # Fallback to environment variables
            redis_creds = {
                "host": os.environ.get("REDIS_HOST", "localhost"),
                "port": os.environ.get("REDIS_PORT", "6379"),
                "password": os.environ.get("REDIS_PASSWORD", ""),
                "ssl": os.environ.get("REDIS_SSL", "False").lower() == "true"
            }
            print("Using Redis credentials from environment variables")

        # Convert port to int
        port = int(redis_creds.get("port", 6379))
        
        # Ensure all required keys exist with default values if needed
        host = redis_creds.get("host", "localhost")
        password = redis_creds.get("password", "")
        
        # Handle missing 'ssl' key by providing a default value
        ssl_enabled = False
        if "ssl" in redis_creds:
            ssl_value = redis_creds["ssl"]
            if isinstance(ssl_value, str):
                ssl_enabled = ssl_value.lower() == "true"
            elif isinstance(ssl_value, bool):
                ssl_enabled = ssl_value
        
        print(f"Redis connection parameters: host={host}, port={port}, ssl={ssl_enabled}")
        
        redis_client = redis.Redis(
            host=host,
            port=port,
            password=password if password else None,
            ssl=ssl_enabled,
            decode_responses=True
        )
        
        # Test connection
        await redis_client.ping()
        print(f"Connected to Redis at {host}:{port}")
    except Exception as e:
        print(f"Error creating redis connection: {e}")
        raise


# Close Redis connection
async def close_redis():
    if redis_client:
        await redis_client.close()


async def get_redis_client():
    return redis_client
