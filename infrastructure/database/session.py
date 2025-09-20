import os
import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from google.cloud.sql.connector import Connector, IPTypes

from core.config import config

logger = logging.getLogger(__name__)

# Base class for declarative models
Base = declarative_base()

# Global variables for engine and session
engine = None
async_session = None


def _create_local_engine():
    """Create engine for local development."""
    # Use config if available, otherwise fallback to env vars
    if hasattr(config, 'database') and config.database.url:
        database_url = config.database.url
        echo = config.database.echo
    else:
        database_url = (
            f"postgresql+asyncpg://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
            f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
        )
        echo = os.getenv('DB_ECHO', 'false').lower() == 'true'
    
    return create_async_engine(database_url, echo=echo)


async def _create_production_engine():
    """Create engine for production with Cloud SQL."""
    connection_name = os.environ.get("CONNECTION_NAME")
    
    if not connection_name:
        raise ValueError("CONNECTION_NAME environment variable is required for production")
    
    # Initialize a Connector object
    connector = Connector(
        IPTypes.PRIVATE if connection_name.split(':')[-1].lower() == 'private' else IPTypes.PUBLIC
    )

    # A function to get a connection from the connector
    async def get_async_connection():
        return await connector.connect_async(
            connection_name,
            driver="asyncpg",
            user=os.getenv('DB_USER_PROD'),
            db=os.getenv('DB_NAME'),
            enable_iam_auth=True,
        )

    # SQLAlchemy async engine using custom connection
    return create_async_engine(
        "postgresql+asyncpg://",  # Leave blank, overridden by creator
        async_creator=get_async_connection,
        echo=False,
    )


def init_database():
    """Initialize database engine and session maker."""
    global engine, async_session
    
    if engine is None:
        try:
            if os.getenv('ENV', 'PROD') == "LOCAL":
                logger.info("Initializing local database connection")
                engine = _create_local_engine()
            else:
                logger.info("Initializing production database connection")
                # Note: This is sync, but the engine creation is async
                # Consider refactoring if needed
                engine = None  # Will be created async when needed
                
            if engine:
                async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
                logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise


# Initialize on module import
init_database()


# Dependency for FastAPI
async def get_db() -> AsyncSession:
    """Database dependency for FastAPI."""
    if async_session is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    async with async_session() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()