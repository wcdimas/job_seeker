import logging
import os
from datetime import datetime

class ProjectLogger:
    """
    A utility class to generate and configure loggers for the project.
    It logs to both the console and a file in the /logs directory.
    """
    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        logger = logging.getLogger(name)
        
        # Prevent adding handlers multiple times if the logger already exists
        if not logger.handlers:
            logger.setLevel(logging.INFO)
            
            # Setup logs directory at the root of the project
            # __file__ is in src/job_seeker/logger.py, so root is 3 levels up
            root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            log_dir = os.path.join(root_dir, 'logs')
            os.makedirs(log_dir, exist_ok=True)
            
            # Create a file handler with today's date
            log_file = os.path.join(log_dir, f"job_seeker_{datetime.now().strftime('%Y-%m-%d')}.log")
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.INFO)
            
            # Create a console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            
            # Define the log format
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            # Add handlers to the logger
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)
            
        return logger
