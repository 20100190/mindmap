import os
import logging
from logging.handlers import RotatingFileHandler


# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

def setup_logging():
    os.makedirs("logs", exist_ok=True)

    log_format = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"

    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            RotatingFileHandler("logs/app.log", maxBytes=10*1024*1024, backupCount=5),
            logging.StreamHandler()  # logs to console too
        ]
    )