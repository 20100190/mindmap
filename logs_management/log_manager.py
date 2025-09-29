import os
import logging
from logging.handlers import RotatingFileHandler
from correlation_context import get_correlation_id

class CorrelationIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = get_correlation_id()
        return True

def setup_logging():


    os.makedirs("logs", exist_ok=True)

    log_format = (
        "%(correlation_id)s | %(asctime)s | %(levelname)s | %(name)s | %(funcName)s | %(lineno)d | %(message)s"
    )

    handler_file = RotatingFileHandler("logs/app.log", maxBytes=10*1024*1024, backupCount=5)
    handler_stream = logging.StreamHandler()

    correlation_filter = CorrelationIdFilter()
    handler_file.addFilter(correlation_filter)
    handler_stream.addFilter(correlation_filter)

    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[handler_file, handler_stream]
    )