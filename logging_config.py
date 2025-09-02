import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path

class LoggerSetup:
    """Setup comprehensive logging for the ServiceNow Ticket Agent"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Create loggers
        self.setup_main_logger()
        self.setup_validation_logger()
        self.setup_api_logger()
        self.setup_error_logger()
    
    def setup_main_logger(self):
        """Setup main application logger"""
        main_logger = logging.getLogger('main')
        main_logger.setLevel(logging.INFO)
        
        # Prevent duplicate handlers
        if not main_logger.handlers:
            # File handler for main logs
            main_handler = logging.handlers.RotatingFileHandler(
                self.log_dir / 'main.log',
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
            main_handler.setLevel(logging.INFO)
            
            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            
            # Formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            main_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            main_logger.addHandler(main_handler)
            main_logger.addHandler(console_handler)
    
    def setup_validation_logger(self):
        """Setup validation logger for all validation events"""
        validation_logger = logging.getLogger('validation')
        validation_logger.setLevel(logging.INFO)
        
        if not validation_logger.handlers:
            # File handler for validation logs
            validation_handler = logging.handlers.RotatingFileHandler(
                self.log_dir / 'validation.log',
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
            validation_handler.setLevel(logging.INFO)
            
            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            
            # Formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            validation_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            validation_logger.addHandler(validation_handler)
            validation_logger.addHandler(console_handler)
    
    def setup_api_logger(self):
        """Setup API logger for all API requests and responses"""
        api_logger = logging.getLogger('api')
        api_logger.setLevel(logging.INFO)
        
        if not api_logger.handlers:
            # File handler for API logs
            api_handler = logging.handlers.RotatingFileHandler(
                self.log_dir / 'api.log',
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
            api_handler.setLevel(logging.INFO)
            
            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            
            # Formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            api_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            api_logger.addHandler(api_handler)
            api_logger.addHandler(console_handler)
    
    def setup_error_logger(self):
        """Setup error logger for all errors and exceptions"""
        error_logger = logging.getLogger('error')
        error_logger.setLevel(logging.ERROR)
        
        if not error_logger.handlers:
            # File handler for error logs
            error_handler = logging.handlers.RotatingFileHandler(
                self.log_dir / 'error.log',
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
            error_handler.setLevel(logging.ERROR)
            
            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.ERROR)
            
            # Formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            error_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            error_logger.addHandler(error_handler)
            error_logger.addHandler(console_handler)

# Global logger instances
logger_setup = LoggerSetup()

def get_main_logger():
    """Get main application logger"""
    return logging.getLogger('main')

def get_validation_logger():
    """Get validation logger"""
    return logging.getLogger('validation')

def get_api_logger():
    """Get API logger"""
    return logging.getLogger('api')

def get_error_logger():
    """Get error logger"""
    return logging.getLogger('error')

# Convenience functions for logging
def log_validation_event(event_type: str, ticket_number: int, details: str, level: str = "INFO"):
    """Log validation events"""
    logger = get_validation_logger()
    message = f"VALIDATION_{event_type.upper()} - Ticket #{ticket_number}: {details}"
    
    if level.upper() == "ERROR":
        logger.error(message)
    elif level.upper() == "WARNING":
        logger.warning(message)
    else:
        logger.info(message)

def log_api_request(method: str, endpoint: str, status_code: int, response_time: float = None):
    """Log API requests"""
    logger = get_api_logger()
    message = f"API_REQUEST - {method} {endpoint} - Status: {status_code}"
    if response_time:
        message += f" - Response Time: {response_time:.3f}s"
    logger.info(message)

def log_ticket_processing(ticket_number: int, action: str, details: str = ""):
    """Log ticket processing events"""
    logger = get_main_logger()
    message = f"TICKET_PROCESSING - #{ticket_number} - {action}"
    if details:
        message += f" - {details}"
    logger.info(message)

def log_error(error_type: str, message: str, exception: Exception = None):
    """Log errors and exceptions"""
    logger = get_error_logger()
    error_msg = f"ERROR_{error_type.upper()} - {message}"
    if exception:
        error_msg += f" - Exception: {str(exception)}"
    logger.error(error_msg)
