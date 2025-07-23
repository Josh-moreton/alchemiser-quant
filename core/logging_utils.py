import logging
import os

def setup_logging(log_level=logging.INFO, log_file=None):
    """
    Set up centralized logging for the project.
    Logs to both console and (optionally) a file, with consistent formatting.
    """
    log_format = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
    handlers = [logging.StreamHandler()]
    
    if log_file:
        # Ensure directory exists
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        handlers.append(logging.FileHandler(log_file, mode='a'))
    
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=handlers
    )
    logging.info(f"Logging initialized. Level: {logging.getLevelName(log_level)} | File: {log_file or 'console only'}")
