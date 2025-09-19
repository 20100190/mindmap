import os
import logging
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from api import query
from logs_management import log_manager
from logs_management.log_manager import correlation_context, set_correlation_id

# Load environment variables from .env file in the project root
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    # Fallback to loading from environment
    load_dotenv()

# Setup enhanced logging
log_level = os.getenv("LOG_LEVEL", "INFO")
structured_logging = os.getenv("STRUCTURED_LOGGING", "true").lower() == "true"
log_manager.setup_logging(log_level=log_level, structured_logging=structured_logging)

logger = logging.getLogger(__name__)

# Validate critical environment variables
required_env_vars = ["OPENAI_API_KEY"]
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    logger.error(f"Missing required environment variables: {missing_vars}")
    raise EnvironmentError(f"Missing required environment variables: {missing_vars}")

# Create FastAPI app with enhanced configuration
app = FastAPI(
    title="Mindmap API",
    description="API for generating mindmaps using LLM",
    version="1.0.0",
    docs_url="/docs" if os.getenv("ENV", "PROD") == "LOCAL" else None,
    redoc_url="/redoc" if os.getenv("ENV", "PROD") == "LOCAL" else None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_correlation_id_middleware(request: Request, call_next):
    """Add correlation ID to each request."""
    correlation_id = request.headers.get("X-Correlation-ID")
    with correlation_context(correlation_id) as corr_id:
        request.state.correlation_id = corr_id
        logger.info(f"Request started: {request.method} {request.url.path}")
        
        try:
            response = await call_next(request)
            response.headers["X-Correlation-ID"] = corr_id
            logger.info(f"Request completed: {request.method} {request.url.path} - Status: {response.status_code}")
            return response
        except Exception as e:
            logger.error(f"Request failed: {request.method} {request.url.path}", exc_info=True)
            raise

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler with proper logging."""
    log_manager.log_error(logger, exc, {
        'request_path': request.url.path,
        'request_method': request.method,
        'correlation_id': getattr(request.state, 'correlation_id', None)
    })
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "correlation_id": getattr(request.state, 'correlation_id', None),
            "message": "An unexpected error occurred"
        }
    )

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "mindmap-api"}

# Include API routers
app.include_router(query.router, prefix="/api/v1")

logger.info("Application startup complete")

def run_development():
    """Run development server."""
    port = int(os.getenv('PORT', 8001))
    logger.info(f"Starting development server on port {port}")
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=port, 
        reload=True,
        log_config=None  # Use our custom logging instead of uvicorn's
    )

def run_production():
    """Run production server with gunicorn."""
    port = int(os.getenv('PORT', 8001))
    workers = int(os.getenv('WORKERS', 4))
    logger.info(f"Starting production server on port {port} with {workers} workers")
    
    # This would be called externally via gunicorn command
    # gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8001
    pass

if __name__ == "__main__":
    env = os.getenv("ENV", "PROD")
    if env == "LOCAL":
        run_development()
    else:
        # In production, this should be run via gunicorn
        logger.warning("Running in production mode directly. Consider using gunicorn.")
        run_development()
