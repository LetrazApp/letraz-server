import logging
import os
from pathlib import Path


# Create logs directory if it doesn't exist
def get_settings_logger(BASE_DIR: Path, filename: str) -> logging.Logger:
    # Get the base directory path (same level as manage.py)
    logs_dir = BASE_DIR / 'logs'

    # Create logs directory if it doesn't exist
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    # Create log file with timestamp
    log_file = os.path.join(logs_dir, filename)

    # Basic logging setup
    logging.basicConfig(
        level=logging.ERROR,
        format='%(asctime)s [%(levelname)s] - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

    return logging.getLogger('settings_logger')
