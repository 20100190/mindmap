import os
import logging
import json
import uuid
import threading
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Optional, Dict, Any
from contextlib import contextmanager

# Thread-local storage for correlation IDs
_local = threading.local()

class CorrelationIdFilter(logging.Filter):
    """Filter to add correlation ID to log records."""
    
    def filter(self, record):
        record.correlation_id = getattr(_local, 'correlation_id', 'N/A')
        return True

class StructuredFormatter(logging.Formatter):
    """Structured JSON formatter for logs."""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'correlation_id': getattr(record, 'correlation_id', 'N/A'),
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
            
        # Add extra fields
        if hasattr(record, 'extra_data'):
            log_entry['extra'] = record.extra_data
            
        return json.dumps(log_entry)

class ConsoleFormatter(logging.Formatter):
    """Human-readable formatter for console output."""
    
    def format(self, record):
        correlation_id = getattr(record, 'correlation_id', 'N/A')
        return f"{record.asctime} | {correlation_id[:8]} | {record.name} | {record.levelname} | {record.getMessage()}"

def setup_logging(log_level: str = "INFO", structured_logging: bool = True):
    """
    Setup enhanced logging with structured output and correlation IDs.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        structured_logging: Whether to use structured JSON logging
    """
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Clear existing handlers to avoid duplicates
    logging.getLogger().handlers.clear()
    
    # Set log level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create correlation ID filter
    correlation_filter = CorrelationIdFilter()
    
    # Setup file handler with structured logging
    file_handler = RotatingFileHandler(
        "logs/app.log", 
        maxBytes=50*1024*1024,  # 50MB
        backupCount=10
    )
    file_handler.addFilter(correlation_filter)
    file_handler.setFormatter(StructuredFormatter())
    file_handler.setLevel(numeric_level)
    
    # Setup console handler
    console_handler = logging.StreamHandler()
    console_handler.addFilter(correlation_filter)
    
    if structured_logging:
        console_handler.setFormatter(StructuredFormatter())
    else:
        console_formatter = ConsoleFormatter()
        console_formatter.datefmt = '%Y-%m-%d %H:%M:%S'
        console_handler.setFormatter(console_formatter)
    
    console_handler.setLevel(numeric_level)
    
    # Setup error file handler
    error_handler = RotatingFileHandler(
        "logs/errors.log",
        maxBytes=50*1024*1024,
        backupCount=10
    )
    error_handler.addFilter(correlation_filter)
    error_handler.setFormatter(StructuredFormatter())
    error_handler.setLevel(logging.ERROR)
    
    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        handlers=[file_handler, console_handler, error_handler],
        force=True  # Force reconfiguration
    )
    
    # Configure specific loggers
    # Reduce noise from external libraries
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
    logging.getLogger('google').setLevel(logging.WARNING)
    logging.getLogger('openai').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    
    logging.info(f"Logging setup complete with level: {log_level}")

def set_correlation_id(correlation_id: Optional[str] = None) -> str:
    """Set correlation ID for current thread."""
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())
    _local.correlation_id = correlation_id
    return correlation_id

def get_correlation_id() -> Optional[str]:
    """Get current correlation ID."""
    return getattr(_local, 'correlation_id', None)

def clear_correlation_id():
    """Clear correlation ID for current thread."""
    if hasattr(_local, 'correlation_id'):
        delattr(_local, 'correlation_id')

@contextmanager
def correlation_context(correlation_id: Optional[str] = None):
    """Context manager for correlation ID."""
    old_id = get_correlation_id()
    try:
        set_correlation_id(correlation_id)
        yield get_correlation_id()
    finally:
        if old_id:
            set_correlation_id(old_id)
        else:
            clear_correlation_id()

def log_performance(logger: logging.Logger, operation: str, start_time: float, end_time: float, **kwargs):
    """Log performance metrics."""
    duration = end_time - start_time
    logger.info(
        f"Performance: {operation} completed in {duration:.3f}s",
        extra={'extra_data': {
            'operation': operation,
            'duration_seconds': duration,
            **kwargs
        }}
    )

def log_error(logger: logging.Logger, error: Exception, context: Dict[str, Any] = None):
    """Log error with structured context."""
    error_data = {
        'error_type': type(error).__name__,
        'error_message': str(error),
        'context': context or {}
    }
    logger.error(
        f"Error occurred: {type(error).__name__}: {str(error)}",
        extra={'extra_data': error_data},
        exc_info=True
    )