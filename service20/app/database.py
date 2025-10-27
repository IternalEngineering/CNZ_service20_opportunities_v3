"""Database connection pool and query execution for Service20 API."""

import asyncpg
import logging
from typing import Optional
from contextlib import asynccontextmanager

from .config import settings

logger = logging.getLogger(__name__)

# Global connection pool
_pool: Optional[asyncpg.Pool] = None


async def create_pool() -> asyncpg.Pool:
    """Create and return a connection pool."""
    global _pool

    if _pool is not None:
        logger.info("Database pool already exists")
        return _pool

    try:
        _pool = await asyncpg.create_pool(
            dsn=settings.database_url,
            min_size=settings.db_pool_min_size,
            max_size=settings.db_pool_max_size,
            max_queries=settings.db_pool_max_queries,
            max_inactive_connection_lifetime=settings.db_pool_max_inactive_connection_lifetime,
            command_timeout=60
        )
        logger.info(f"Database pool created (min={settings.db_pool_min_size}, max={settings.db_pool_max_size})")
        return _pool

    except Exception as e:
        logger.error(f"Failed to create database pool: {str(e)}")
        raise


async def close_pool():
    """Close the database connection pool."""
    global _pool

    if _pool is not None:
        await _pool.close()
        logger.info("Database pool closed")
        _pool = None


async def get_pool() -> asyncpg.Pool:
    """Get the connection pool, creating it if necessary."""
    if _pool is None:
        return await create_pool()
    return _pool


@asynccontextmanager
async def get_connection():
    """Get a database connection from the pool."""
    pool = await get_pool()
    async with pool.acquire() as connection:
        yield connection


async def test_connection() -> bool:
    """Test database connectivity."""
    try:
        async with get_connection() as conn:
            result = await conn.fetchval("SELECT 1")
            logger.info(f"Database connection test successful: {result}")
            return True
    except Exception as e:
        logger.error(f"Database connection test failed: {str(e)}")
        return False
