import logging
import os
from pathlib import Path


# Create logs directory if it doesn't exist
def get_settings_logger(BASE_DIR: Path, filename: str, instance_id: str, logging_level=logging.INFO ) -> logging.Logger:
    # Get the base directory path (same level as manage.py)
    logs_dir = BASE_DIR / 'logs'

    # Create logs directory if it doesn't exist
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    # Create log file with timestamp
    log_file = os.path.join(logs_dir, filename)

    # Basic logging setup
    logging.basicConfig(
        level=logging_level,
        format=f'%(asctime)s [%(levelname)s] [instance_id - {instance_id}] - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

    return logging.getLogger('settings_logger')
