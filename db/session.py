from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
import asyncio
from sqlalchemy.orm import declarative_base
from google.cloud.sql.connector import Connector, IPTypes
import os


CONNECTION_NAME = os.environ.get("CONNECTION_NAME")

if os.getenv('ENV', 'PROD') == "LOCAL":
    DATABASE_URL = (
        f"postgresql+asyncpg://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )
    engine = create_async_engine(DATABASE_URL, echo=False)

# The database connection for production
elif os.getenv('ENV', 'PROD') == "PROD":
    # Initialize a Connector object
    connector = Connector(IPTypes.PRIVATE if CONNECTION_NAME.split(':')[-1].lower() == 'private' else IPTypes.PUBLIC)

    # A function to get a connection from the connector
    # asyncpg is the driver for asynchronous connections
    async def get_async_connection():
        return await connector.connect(
            CONNECTION_NAME,
            driver="asyncpg",
            user=os.getenv('DB_USER_PROD'),
            db=os.getenv('DB_NAME'),
            enable_iam_auth=True,
        )

    # SQLAlchemy async engine using custom connection
    engine = create_async_engine(
        "postgresql+asyncpg://",  # Leave blank, overridden by creator
        async_creator=get_sync_connection,
        echo=False,
    )

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

# Dependency for FastAPI
async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session