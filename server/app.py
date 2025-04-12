import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

import uvicorn
from fastapi import FastAPI, Depends, Request, HTTPException
from contextlib import asynccontextmanager
import sys

from fastapi.middleware.cors import CORSMiddleware

from database.postgres import init_postgres, close_postgres, get_postgres_connection
from database.redis import init_redis, close_redis, get_redis_client
from utils.aws_utils import get_secret, validate_aws_credentials
from utils.lex_utils import init_lex_client

from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Validate AWS credentials first
aws_valid, aws_message = validate_aws_credentials()
logger.info(f"AWS Credentials check: {aws_message}")

# Verify environment variable is set
supabase_secret_name = os.getenv("supabase_secret_name")
if not supabase_secret_name:
    logger.error("Missing environment variable: supabase_secret_name")
    raise RuntimeError("Missing environment variable: supabase_secret_name")

# Only try to get secrets if AWS credentials are valid
if aws_valid:
    try:
        # Get and validate Supabase credentials
        jwt_secret = get_secret(supabase_secret_name)
        SUPABASE_JWT_SECRET = jwt_secret["JWT_SECRET"]
        
        # Import auth module only after confirming secrets are accessible
        try:
            from auth.auth import validate_token, router as auth_router
            from models.Models import User
            from chat.chat_handler import router as chat_router
            logger.info("Successfully imported auth and chat modules")
        except (ImportError, ValueError, RuntimeError) as module_error:
            logger.critical(f"Failed to initialize modules: {str(module_error)}")
            sys.exit(f"Application startup failed: {str(module_error)}")
            
    except Exception as e:
        logger.critical(f"Failed to get secrets: {str(e)}")
        sys.exit(f"Could not access required secrets: {str(e)}")
else:
    logger.critical("AWS credentials are invalid - cannot proceed")
    sys.exit("AWS credentials are invalid - application cannot start")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    try:
        logger.info("Initializing database connections")
        await init_postgres()
        await init_redis()
        
        # Initialize Lex client
        logger.info("Initializing Amazon Lex client")
        if init_lex_client():
            logger.info("Amazon Lex client initialized successfully")
        else:
            logger.warning("Failed to initialize Amazon Lex client")
            
        logger.info("All connections initialized successfully")
        yield  # Application runs here
    except Exception as e:
        logger.critical(f"Failed to initialize connections: {str(e)}")
        raise
    finally:
        # Shutdown logic
        logger.info("Shutting down connections")
        await close_postgres()
        await close_redis()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # More permissive during development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]  # Add this to expose all response headers
)

# Include routers
app.include_router(auth_router)
app.include_router(chat_router)  # Add the chat router


@app.get("/protected-route")
async def protected_route(user: User = Depends(validate_token)):
    return {
        "message": "Access granted",
        "user": user,
    }


@app.get("/health", include_in_schema=False)
async def health_check(connection=Depends(get_postgres_connection)):
    postgres_status = await connection.fetchrow("SELECT 1")
    print(postgres_status)
    redis = await get_redis_client()
    redis_status = await redis.ping()
    return {
        "status": "healthy",
        "postgres": "connected" if postgres_status['?column?'] == 1 else "error",
        "redis": "connected" if redis_status else "error"
    }


@app.get("/")
async def read_root(connection=Depends(get_postgres_connection)):
    # Assuming you have Redis and PostgreSQL connection methods set up in your app
    postgres_time = await connection.fetchrow("SELECT now() AS current_time")
    redis = await get_redis_client()
    await redis.set("example_key", "example_value")
    redis_value = await redis.get("example_key")

    if postgres_time["current_time"] and redis_value:
        return {
            "status": "ok",
            "message": "Application is running"
        }
    else:
        return {
            "status": "error",
            "message": "Something went wrong"
        }


if __name__ == '__main__':
    uvicorn.run(app, port=8085)
