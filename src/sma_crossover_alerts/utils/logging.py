"""
Logging configuration and setup for TQQQ analysis application.

This module provides centralized logging configuration with
file rotation, structured formatting, and multiple log levels.
"""

import logging
import logging.config
import logging.handlers
import os
import time
import json
from pathlib import Path
from typing import Optional, Dict, Any


def setup_logging(log_level: str = "INFO", 
                 log_file: str = "logs/tqqq_analysis.log",
                 max_file_size: str = "10MB",
                 backup_count: int = 5,
                 console_output: bool = True) -> None:
    """
    Set up application logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file
        max_file_size: Maximum size of log file before rotation
        backup_count: Number of backup files to keep
        console_output: Whether to output logs to console
    """
    # Create logs directory if it doesn't exist
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert max_file_size to bytes
    size_bytes = _parse_file_size(max_file_size)
    
    # Configure logging
    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'detailed': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'simple': {
                'format': '%(levelname)s - %(message)s'
            },
            'json': {
                'format': '{"timestamp": "%(asctime)s", "logger": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            }
        },
        'handlers': {
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': log_file,
                'maxBytes': size_bytes,
                'backupCount': backup_count,
                'formatter': 'detailed',
                'level': log_level
            }
        },
        'loggers': {
            'tqqq_analysis': {
                'level': log_level,
                'handlers': ['file'],
                'propagate': False
            },
            'root': {
                'level': log_level,
                'handlers': ['file']
            }
        }
    }
    
    # Add console handler if requested
    if console_output:
        logging_config['handlers']['console'] = {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            'level': log_level
        }
        logging_config['loggers']['tqqq_analysis']['handlers'].append('console')
        logging_config['loggers']['root']['handlers'].append('console')
    
    # Apply configuration
    logging.config.dictConfig(logging_config)
    
    # Log startup message
    logger = logging.getLogger('tqqq_analysis.setup')
    logger.info(f"Logging initialized - Level: {log_level}, File: {log_file}")


def _parse_file_size(size_str: str) -> int:
    """
    Parse file size string to bytes.
    
    Args:
        size_str: Size string (e.g., '10MB', '1GB')
        
    Returns:
        int: Size in bytes
    """
    size_str = size_str.upper().strip()
    
    # Extract number and unit
    if size_str.endswith('B'):
        size_str = size_str[:-1]
    
    multipliers = {
        'K': 1024,
        'M': 1024 ** 2,
        'G': 1024 ** 3,
        'T': 1024 ** 4
    }
    
    if size_str[-1] in multipliers:
        number = float(size_str[:-1])
        multiplier = multipliers[size_str[-1]]
        return int(number * multiplier)
    else:
        return int(size_str)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(f'tqqq_analysis.{name}')


class StructuredLogger:
    """
    Structured logger for consistent log formatting.
    
    Provides methods for logging with structured data
    and consistent formatting across the application.
    """
    
    def __init__(self, name: str):
        """
        Initialize structured logger.
        
        Args:
            name: Logger name
        """
        self.logger = get_logger(name)
    
    def info(self, message: str, **kwargs):
        """Log info message with structured data."""
        self._log_with_data(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with structured data."""
        self._log_with_data(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with structured data."""
        self._log_with_data(logging.ERROR, message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with structured data."""
        self._log_with_data(logging.DEBUG, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message with structured data."""
        self._log_with_data(logging.CRITICAL, message, **kwargs)
    
    def _log_with_data(self, level: int, message: str, **kwargs):
        """
        Log message with structured data.
        
        Args:
            level: Logging level
            message: Log message
            **kwargs: Additional structured data
        """
        if kwargs:
            # Format additional data
            data_str = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
            full_message = f"{message} | {data_str}"
        else:
            full_message = message
        
        self.logger.log(level, full_message)


def log_function_call(func):
    """
    Decorator to log function calls with parameters and results.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        func_name = func.__name__
        
        # Log function entry
        logger.debug(f"Entering {func_name} with args={args}, kwargs={kwargs}")
        
        try:
            result = func(*args, **kwargs)
            logger.debug(f"Exiting {func_name} successfully")
            return result
        except Exception as e:
            logger.error(f"Error in {func_name}: {str(e)}")
            raise
    
    return wrapper


def log_performance(func):
    """
    Decorator to log function performance metrics.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        func_name = func.__name__
        
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            end_time = time.time()
            duration = end_time - start_time
            logger.info(f"Performance: {func_name} completed in {duration:.3f}s")
            return result
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            logger.error(f"Performance: {func_name} failed after {duration:.3f}s - {str(e)}")
            raise
    
    return wrapper


class APILogger:
    """
    Specialized logger for API requests and responses.
    
    Provides structured logging for HTTP requests, responses,
    retry attempts, and error scenarios.
    """
    
    def __init__(self, name: str = "api"):
        """
        Initialize API logger.
        
        Args:
            name: Logger name
        """
        self.logger = get_logger(name)
    
    def log_request(self, method: str, url: str, headers: Optional[Dict[str, str]] = None,
                   params: Optional[Dict[str, Any]] = None) -> None:
        """
        Log API request details.
        
        Args:
            method: HTTP method
            url: Request URL
            headers: Request headers
            params: Request parameters
        """
        request_data: Dict[str, Any] = {
            "method": method,
            "url": url,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        if headers:
            # Sanitize sensitive headers
            safe_headers = {k: v if k.lower() not in ['authorization', 'x-api-key']
                          else '***REDACTED***' for k, v in headers.items()}
            request_data["headers"] = safe_headers
        
        if params:
            # Sanitize API key from params
            safe_params = {k: v if k.lower() not in ['apikey', 'api_key']
                         else '***REDACTED***' for k, v in params.items()}
            request_data["params"] = safe_params
        
        self.logger.info(f"API Request: {json.dumps(request_data, indent=2)}")
    
    def log_response(self, status_code: int, response_time: float,
                    response_size: Optional[int] = None,
                    error_message: Optional[str] = None) -> None:
        """
        Log API response details.
        
        Args:
            status_code: HTTP status code
            response_time: Response time in seconds
            response_size: Response size in bytes
            error_message: Error message if applicable
        """
        response_data: Dict[str, Any] = {
            "status_code": status_code,
            "response_time": f"{response_time:.3f}s",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        if response_size is not None:
            response_data["response_size"] = f"{response_size} bytes"
        
        if error_message:
            response_data["error"] = error_message
            self.logger.error(f"API Response Error: {json.dumps(response_data, indent=2)}")
        else:
            self.logger.info(f"API Response Success: {json.dumps(response_data, indent=2)}")
    
    def log_retry_attempt(self, attempt: int, max_attempts: int, delay: float,
                         error: str) -> None:
        """
        Log retry attempt details.
        
        Args:
            attempt: Current attempt number
            max_attempts: Maximum number of attempts
            delay: Delay before retry in seconds
            error: Error that triggered the retry
        """
        retry_data: Dict[str, Any] = {
            "attempt": attempt,
            "max_attempts": max_attempts,
            "delay": f"{delay:.1f}s",
            "error": error,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self.logger.warning(f"API Retry Attempt: {json.dumps(retry_data, indent=2)}")
    
    def log_rate_limit(self, retry_after: Optional[int] = None) -> None:
        """
        Log rate limit exceeded event.
        
        Args:
            retry_after: Seconds to wait before retrying
        """
        rate_limit_data: Dict[str, Any] = {
            "event": "rate_limit_exceeded",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        if retry_after:
            rate_limit_data["retry_after"] = f"{retry_after}s"
        
        self.logger.error(f"API Rate Limit: {json.dumps(rate_limit_data, indent=2)}")
    
    def log_network_error(self, error: Exception, url: str) -> None:
        """
        Log network error details.
        
        Args:
            error: Network error exception
            url: URL that failed
        """
        error_data: Dict[str, Any] = {
            "event": "network_error",
            "error_type": type(error).__name__,
            "error_message": str(error),
            "url": url,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self.logger.error(f"Network Error: {json.dumps(error_data, indent=2)}")


class ErrorLogger:
    """
    Specialized logger for error handling with context preservation.
    
    Provides enhanced error logging with categorization, context preservation,
    error correlation, and recovery tracking.
    """
    
    def __init__(self, name: str = "error"):
        """
        Initialize error logger.
        
        Args:
            name: Logger name
        """
        self.logger = get_logger(name)
    
    def log_error_with_context(self, error: Exception, component: str,
                              context: Dict[str, Any]) -> None:
        """
        Log error with full context information.
        
        Args:
            error: The exception that occurred
            component: Component where the error occurred
            context: Additional context information
        """
        error_data = {
            "event": "error_with_context",
            "component": component,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Add error-specific attributes if available
        if hasattr(error, 'error_code'):
            error_data["error_code"] = getattr(error, 'error_code')
        if hasattr(error, 'retry_hint'):
            error_data["retry_hint"] = getattr(error, 'retry_hint')
        if hasattr(error, 'status_code'):
            error_data["status_code"] = getattr(error, 'status_code')
        
        self.logger.error(f"Error with Context: {json.dumps(error_data, indent=2)}")
    
    def log_retry_attempt(self, error: Exception, attempt: int, delay: float) -> None:
        """
        Log retry attempt with error context.
        
        Args:
            error: Error that triggered the retry
            attempt: Current attempt number
            delay: Delay before retry in seconds
        """
        retry_data = {
            "event": "retry_attempt",
            "attempt": attempt,
            "delay": f"{delay:.1f}s",
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Add error-specific context
        if hasattr(error, 'error_code'):
            retry_data["error_code"] = getattr(error, 'error_code')
        if hasattr(error, 'context'):
            retry_data["error_context"] = getattr(error, 'context')
        
        self.logger.warning(f"Retry Attempt: {json.dumps(retry_data, indent=2)}")
    
    def log_error_recovery(self, error: Exception, recovery_action: str) -> None:
        """
        Log error recovery attempt.
        
        Args:
            error: Original error being recovered from
            recovery_action: Description of recovery action
        """
        recovery_data = {
            "event": "error_recovery",
            "recovery_action": recovery_action,
            "original_error_type": type(error).__name__,
            "original_error_message": str(error),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        if hasattr(error, 'error_code'):
            recovery_data["error_code"] = getattr(error, 'error_code')
        
        self.logger.info(f"Error Recovery: {json.dumps(recovery_data, indent=2)}")
    
    def log_final_error_state(self, error_type: str, message: str,
                             component: Optional[str] = None) -> None:
        """
        Log final error state when recovery is not possible.
        
        Args:
            error_type: Categorized error type
            message: Final error message
            component: Component where error occurred
        """
        final_state_data = {
            "event": "final_error_state",
            "error_type": error_type,
            "message": message,
            "component": component,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self.logger.critical(f"Final Error State: {json.dumps(final_state_data, indent=2)}")
    
    def log_error_correlation(self, primary_error: Exception, related_errors: list,
                             correlation_id: str) -> None:
        """
        Log correlated errors that occurred together.
        
        Args:
            primary_error: Main error that occurred
            related_errors: List of related errors
            correlation_id: Unique ID to correlate related errors
        """
        correlation_data = {
            "event": "error_correlation",
            "correlation_id": correlation_id,
            "primary_error": {
                "type": type(primary_error).__name__,
                "message": str(primary_error)
            },
            "related_errors": [
                {
                    "type": type(err).__name__,
                    "message": str(err)
                } for err in related_errors
            ],
            "total_errors": len(related_errors) + 1,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self.logger.error(f"Error Correlation: {json.dumps(correlation_data, indent=2)}")
    
    def log_error_metrics(self, error_counts: Dict[str, int],
                         component_errors: Dict[str, int]) -> None:
        """
        Log error metrics and statistics.
        
        Args:
            error_counts: Count of errors by type
            component_errors: Count of errors by component
        """
        metrics_data = {
            "event": "error_metrics",
            "error_type_counts": error_counts,
            "component_error_counts": component_errors,
            "total_errors": sum(error_counts.values()),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self.logger.info(f"Error Metrics: {json.dumps(metrics_data, indent=2)}")


def log_api_call(logger_name: str = "api"):
    """
    Decorator to automatically log API calls with timing and error handling.
    
    Args:
        logger_name: Name of the logger to use
        
    Returns:
        Decorator function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            api_logger = APILogger(logger_name)
            func_name = func.__name__
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                end_time = time.time()
                duration = end_time - start_time
                
                api_logger.logger.info(
                    f"API Call Success: {func_name} completed in {duration:.3f}s"
                )
                return result
                
            except Exception as e:
                end_time = time.time()
                duration = end_time - start_time
                
                api_logger.logger.error(
                    f"API Call Failed: {func_name} failed after {duration:.3f}s - {str(e)}"
                )
                raise
        
        return wrapper
    return decorator