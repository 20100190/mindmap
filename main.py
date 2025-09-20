import os
import logging
from fastapi import FastAPI

# Import configuration (loads environment)
from core.config import config

# Import new API structure
from api.v1 import v1_router

# Import logging setup
from infrastructure.logging.config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Mindmap API",
    description="API for generating structured mindmaps from user queries",
    version="2.0.0"
)

# Include routers
app.include_router(v1_router)

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.environ.get('PORT', 8001))
    host = os.environ.get('HOST', '0.0.0.0')
    reload = os.environ.get('ENV', 'PROD') == 'LOCAL'
    
    logger.info(f"Starting server on {host}:{port} (reload={reload})")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level=config.log_level.lower()
    )
