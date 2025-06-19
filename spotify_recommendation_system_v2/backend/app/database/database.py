"""
Database connection and session management for PostgreSQL
"""

import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from loguru import logger

from app.config import settings


class Base(DeclarativeBase):
    """Base class for all database models"""
    pass


# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    echo=settings.DEBUG,
    future=True,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_database() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function that yields database sessions.
    Use this as a FastAPI dependency.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_database():
    """Initialize database connection"""
    try:
        # Test the connection
        async with engine.begin() as conn:
            # Simple test query
            result = await conn.execute(text("SELECT 1"))
            result.scalar()
        logger.success("✅ Database connected successfully")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        raise


async def close_database():
    """Close database connection"""
    try:
        await engine.dispose()
        logger.info("🔌 Database disconnected")
    except Exception as e:
        logger.error(f"❌ Database disconnection error: {e}")


async def create_tables():
    """Create all database tables"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.success("✅ Database tables created successfully")
    except Exception as e:
        logger.error(f"❌ Failed to create tables: {e}")
        raise


async def drop_tables():
    """Drop all database tables (use with caution!)"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        logger.warning("⚠️ All database tables dropped")
    except Exception as e:
        logger.error(f"❌ Failed to drop tables: {e}")
        raise 