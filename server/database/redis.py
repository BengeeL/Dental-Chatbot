import redis.asyncio as redis

from utils.aws_utils import get_secret

redis_client = None


# Initialize Redis connection
async def init_redis():
    global redis_client
    redis_creds = get_secret("redis")
    try:
        redis_client = redis.Redis(host=redis_creds["host"],
                                   port=redis_creds["port"],
                                   password=redis_creds["password"],
                                   ssl=True,
                                   decode_responses=True)
        print("Connected to Redis")
    except Exception as e:
        print(f"Error creating redis pool: {e}")
        raise


# Close Redis connection
async def close_redis():
    if redis_client:
        await redis_client.close()


async def get_redis_client():
    return redis_client
