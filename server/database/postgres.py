import asyncpg
import os
from fastapi import HTTPException

from utils.aws_utils import get_secret

# Global variables for connections
postgres_pool = None


# Initialize PostgreSQL connection pool
async def init_postgres():
    global postgres_pool
    pg_creds = get_secret("postgres")
    try:
        postgres_pool = await asyncpg.create_pool(
            host=pg_creds["host"],
            port=pg_creds["port"],
            user=pg_creds["username"],
            password=pg_creds["password"],
            database="defaultdb",
            min_size=5,
            max_size=10,
            command_timeout=120,
            timeout=60
        )
    except Exception as e:
        print(f"Error creating postgres pool: {e}")
        raise

# Close PostgreSQL connection pool
async def close_postgres():
    if postgres_pool:
        await postgres_pool.close()


# Dependency to get a PostgreSQL connection from the pool
async def get_postgres_connection():
    if not postgres_pool:
        raise RuntimeError("PostgreSQL pool is not initialized")
    async with postgres_pool.acquire() as connection:
        yield connection



async def insert_query(query: str, *args):
    """
    Executes a database query (INSERT, UPDATE, DELETE)
    Args:
        query (str): The SQL query to execute
        *args: Query parameters
    Returns:
        None
    """
    try:
        async for connection in get_postgres_connection():
            await connection.execute(query, *args)
    except asyncpg.PostgresError as e:
        print(e)
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

async def fetch_query(query: str, *args):
    """
    Executes a database SELECT query and fetches the results
    Args:
        query (str): The SQL query to execute
        *args: Query parameters
    Returns:
        List[asyncpg.Record]: Query results
    """
    try:
        async for connection in get_postgres_connection():
            result = await connection.fetch(query, *args)
            return result
    except asyncpg.PostgresError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
