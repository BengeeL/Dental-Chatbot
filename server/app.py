import os

import uvicorn
from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager

from fastapi.middleware.cors import CORSMiddleware

from database.postgres import init_postgres, close_postgres, get_postgres_connection
from database.redis import init_redis, close_redis, get_redis_client
from auth.auth import validate_token
from models.Models import User
from auth.auth import router as auth_router
from utils.aws_utils import get_secret

jwt_secret = get_secret(os.getenv("supabase_secret_name"))
SUPABASE_JWT_SECRET = jwt_secret["JWT_SECRET"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    await init_postgres()
    await init_redis()
    yield  # Application runs here
    # Shutdown logic
    await close_postgres()
    await close_redis()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)


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
    await redis.set("", "example_value")
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
    uvicorn.run(app, port=8080, host='0.0.0.0')
