import imp
import os
import re
import uuid
import gunicorn
import uvicorn
from threading import Lock
from config import config
from cachetools import TTLCache 

from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from logs_management.log_manager import setup_logging #, correlation_context, log_error
from fastapi.middleware.cors import CORSMiddleware
import logging
from api.v1 import v1_router
from correlation_context import set_correlation_id


setup_logging() # setting up basic logging
#log_level = os.getenv("LOG_LEVEL", "INFO")
#structured_logging = os.getenv("STRUCTURED_LOGGING", "true").lower() == "true"
#setup_logging(log_level=log_level, structured_logging=structured_logging)

logger = logging.getLogger(__name__)

# TTL cache - automatically removes expired entries 
rate_limits = TTLCache(maxsize=10000, ttl=60) # 10k IPs, 60 second TTL
rate_limits_lock = Lock()




app = FastAPI(
    title="Mindmap",
    description="Mindmap is a tool for generating mindmaps from text",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.include_router(v1_router)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.on_event("startup")
async def clear_cache_on_startup():
    rate_limits.clear()
    print("✅ Cleared rate limit cache on startup")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def correlation_id_rate_limit(request: Request, call_next):
    """Add correlation ID to each request."""
    client_ip = request.client.host
    corr_id = str(uuid.uuid4())
    set_correlation_id(corr_id)

    with rate_limits_lock:
        count = rate_limits.get(client_ip, 0)
        if count > 10 :
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests from your IP. Try again later."}
            )
        else:
            rate_limits[client_ip] = count + 1        

    try:
        logger.info(f"Request Started: {request.method} {request.url.path}, {rate_limits}")
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = corr_id
        logger.info(f"Request completed: {request.method} {request.url.path} - Status: {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"Request failed: {request.method} {request.url.path}", exc_info=True)
        raise

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exce:Exception):
    """Global exception handler with proper logging."""

    logger.exception(f"Got the unhandlled exception.")

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred"
        }
    )

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8001))
    # for development, use reload=True
    uvicorn.run(app, host="0.0.0.0", port=port)
    # for production
    # gunicorn.run(app, 
    #              host="0.0.0.0",  # bind to all interfaces
    #              port=port, 
    #              workers=4,  # independent of CPU cores
    #              timeout=120,  # if a request takes longer than this, it will be terminated
    #              threads=4,  # for handling multiple requests concurrently no parallelism
    #              worker_class="uvicorn.workers.UvicornWorker")
