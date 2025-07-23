import logging
import os
from typing import List
from .s3_utils import S3FileHandler

def setup_logging(log_level=logging.INFO, log_file=None):
    """
    Set up centralized logging for the project.
    Logs to both console and (optionally) a file or S3, with consistent formatting.
    """
    log_format = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
    handlers: List[logging.Handler] = [logging.StreamHandler()]
    
    if log_file:
        if log_file.startswith('s3://'):
            # Use S3 handler for S3 URIs
            s3_handler = S3FileHandler(log_file)
            s3_handler.setFormatter(logging.Formatter(log_format))
            handlers.append(s3_handler)
        else:
            # Ensure directory exists for local files
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            file_handler = logging.FileHandler(log_file, mode='a')
            handlers.append(file_handler)
    
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(
            level=log_level,
            format=log_format,
            handlers=handlers
        )
        logging.info(f"Logging initialized. Level: {logging.getLevelName(log_level)} | File: {log_file or 'console only'}")
