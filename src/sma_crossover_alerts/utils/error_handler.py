"""
Centralized error handling and recovery logic for TQQQ analysis application.

This module provides the main ErrorHandler class for categorizing errors,
generating standard messages, determining retry strategies, and coordinating
error recovery across all application components.
"""

import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

from .exceptions import (
    TQQQAnalyzerError,
    EnhancedTQQQAnalysisError,
    APIError,
    NetworkError,
    RateLimitError,
    DataValidationError,
    ConfigurationError,
    EmailError,
    DataSynchronizationError
)
from .logging import get_logger


class ErrorHandler:
    """
    Centralized error handler for the TQQQ analysis application.
    
    Provides error categorization, standard message generation,
    retry coordination, and recovery strategy determination.
    """
    
    # Standard error messages as specified in requirements
    STANDARD_MESSAGES = {
        "API_ERROR": "No API data available.",
        "DATA_VALIDATION_ERROR": "Data validation failed - please try again.",
        "NETWORK_ERROR": "Network connection failed - please try again.",
        "RATE_LIMIT_ERROR": "API rate limit exceeded - please try again later.",
        "CONFIGURATION_ERROR": "Configuration error - please check settings.",
        "EMAIL_ERROR": "Email delivery failed - please check configuration.",
        "DATA_SYNC_ERROR": "Data synchronization failed - please try again.",
        "UNKNOWN_ERROR": "An unexpected error occurred."
    }
    
    # Error codes for programmatic handling
    ERROR_CODES = {
        "API_ERROR": "API_001",
        "DATA_VALIDATION_ERROR": "DATA_001",
        "NETWORK_ERROR": "NET_001",
        "RATE_LIMIT_ERROR": "RATE_001",
        "CONFIGURATION_ERROR": "CONFIG_001",
        "EMAIL_ERROR": "EMAIL_001",
        "DATA_SYNC_ERROR": "SYNC_001",
        "UNKNOWN_ERROR": "UNK_001"
    }
    
    # Recoverable error types that should be retried
    RECOVERABLE_ERRORS = {
        NetworkError,
        RateLimitError,
        EmailError  # Email errors can be retried
    }
    
    # Non-recoverable error types that should not be retried
    NON_RECOVERABLE_ERRORS = {
        DataValidationError,
        ConfigurationError,
        DataSynchronizationError
    }
    
    def __init__(self, logger_name: str = "error_handler"):
        """
        Initialize error handler.
        
        Args:
            logger_name: Name for the logger instance
        """
        self.logger = get_logger(logger_name)
    
    def handle_api_error(self, error: Exception) -> str:
        """
        Handle API-related errors.
        
        Args:
            error: The exception that occurred
            
        Returns:
            str: Standard error message for API errors
        """
        error_type = self.categorize_error(error)
        standard_message = self.get_standard_error_message(error_type)
        
        # Log the error with context
        self.logger.error(
            f"API Error handled: {error_type}",
            extra={
                "error_message": str(error),
                "error_type": error_type,
                "standard_message": standard_message,
                "should_retry": self.should_retry(error)
            }
        )
        
        return standard_message
    
    def handle_data_validation_error(self, error: Exception) -> str:
        """
        Handle data validation errors.
        
        Args:
            error: The exception that occurred
            
        Returns:
            str: Standard error message for data validation errors
        """
        error_type = self.categorize_error(error)
        standard_message = self.get_standard_error_message(error_type)
        
        # Extract validation context if available
        context = {}
        if hasattr(error, 'field_name') and getattr(error, 'field_name', None):
            context['field_name'] = getattr(error, 'field_name')
        if hasattr(error, 'invalid_value') and getattr(error, 'invalid_value', None):
            context['invalid_value'] = getattr(error, 'invalid_value')
        
        self.logger.error(
            f"Data Validation Error handled: {error_type}",
            extra={
                "error_message": str(error),
                "error_type": error_type,
                "standard_message": standard_message,
                "validation_context": context
            }
        )
        
        return standard_message
    
    def handle_network_error(self, error: Exception) -> str:
        """
        Handle network-related errors.
        
        Args:
            error: The exception that occurred
            
        Returns:
            str: Standard error message for network errors
        """
        error_type = self.categorize_error(error)
        standard_message = self.get_standard_error_message(error_type)
        
        # Extract network error context
        context = {}
        if hasattr(error, 'original_error') and getattr(error, 'original_error', None):
            original_error = getattr(error, 'original_error')
            context['original_error'] = str(original_error)
            context['original_error_type'] = type(original_error).__name__
        
        self.logger.error(
            f"Network Error handled: {error_type}",
            extra={
                "error_message": str(error),
                "error_type": error_type,
                "standard_message": standard_message,
                "should_retry": self.should_retry(error),
                "network_context": context
            }
        )
        
        return standard_message
    
    def categorize_error(self, error: Exception) -> str:
        """
        Categorize errors for appropriate handling.
        
        Args:
            error: The exception to categorize
            
        Returns:
            str: Error category string
        """
        if isinstance(error, NetworkError):
            return "NETWORK_ERROR"
        elif isinstance(error, RateLimitError):
            return "RATE_LIMIT_ERROR"
        elif isinstance(error, DataValidationError):
            return "DATA_VALIDATION_ERROR"
        elif isinstance(error, DataSynchronizationError):
            return "DATA_SYNC_ERROR"
        elif isinstance(error, APIError):
            return "API_ERROR"
        elif isinstance(error, ConfigurationError):
            return "CONFIGURATION_ERROR"
        elif isinstance(error, EmailError):
            return "EMAIL_ERROR"
        else:
            return "UNKNOWN_ERROR"
    
    def should_retry(self, error: Exception) -> bool:
        """
        Determine if error is recoverable and should be retried.
        
        Args:
            error: The exception to evaluate
            
        Returns:
            bool: True if error should be retried, False otherwise
        """
        # Check if error type is explicitly recoverable
        if any(isinstance(error, recoverable_type) for recoverable_type in self.RECOVERABLE_ERRORS):
            return True
        
        # Check if error type is explicitly non-recoverable
        if any(isinstance(error, non_recoverable_type) for non_recoverable_type in self.NON_RECOVERABLE_ERRORS):
            return False
        
        # For enhanced errors, check retry hint
        if hasattr(error, 'retry_hint'):
            return getattr(error, 'retry_hint', False)
        
        # Conservative approach for unknown errors
        return False
    
    def get_standard_error_message(self, error_type: str) -> str:
        """
        Generate standard error messages as specified in requirements.
        
        Args:
            error_type: The categorized error type
            
        Returns:
            str: Standard error message
        """
        return self.STANDARD_MESSAGES.get(error_type, self.STANDARD_MESSAGES["UNKNOWN_ERROR"])
    
    def get_error_code(self, error_type: str) -> str:
        """
        Get error code for programmatic handling.
        
        Args:
            error_type: The categorized error type
            
        Returns:
            str: Error code
        """
        return self.ERROR_CODES.get(error_type, self.ERROR_CODES["UNKNOWN_ERROR"])
    
    def create_enhanced_error(self, original_error: Exception, 
                            additional_context: Optional[Dict[str, Any]] = None) -> EnhancedTQQQAnalysisError:
        """
        Create an enhanced error with full context and metadata.
        
        Args:
            original_error: The original exception
            additional_context: Additional context to include
            
        Returns:
            EnhancedTQQQAnalysisError: Enhanced error with full metadata
        """
        error_type = self.categorize_error(original_error)
        error_code = self.get_error_code(error_type)
        retry_hint = self.should_retry(original_error)
        
        # Build context
        context = additional_context or {}
        context.update({
            "original_error_type": type(original_error).__name__,
            "original_error_message": str(original_error),
            "error_category": error_type,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Add specific error attributes if available
        if hasattr(original_error, 'status_code'):
            context['status_code'] = getattr(original_error, 'status_code')
        if hasattr(original_error, 'field_name'):
            context['field_name'] = getattr(original_error, 'field_name')
        if hasattr(original_error, 'retry_after'):
            context['retry_after'] = getattr(original_error, 'retry_after')
        
        return EnhancedTQQQAnalysisError(
            message=self.get_standard_error_message(error_type),
            error_code=error_code,
            retry_hint=retry_hint,
            context=context,
            component=getattr(original_error, 'component', None)
        )
    
    def log_error_recovery(self, error: Exception, recovery_action: str, 
                          success: bool = True) -> None:
        """
        Log error recovery attempts and results.
        
        Args:
            error: The original error
            recovery_action: Description of recovery action taken
            success: Whether recovery was successful
        """
        error_type = self.categorize_error(error)
        
        log_level = logging.INFO if success else logging.WARNING
        status = "successful" if success else "failed"
        
        self.logger.log(
            log_level,
            f"Error recovery {status}: {recovery_action}",
            extra={
                "error_type": error_type,
                "recovery_action": recovery_action,
                "recovery_success": success,
                "original_error": str(error)
            }
        )
    
    def get_retry_strategy(self, error: Exception) -> Dict[str, Any]:
        """
        Get retry strategy configuration for specific error types.
        
        Args:
            error: The exception to get retry strategy for
            
        Returns:
            dict: Retry strategy configuration
        """
        error_type = self.categorize_error(error)
        
        # Default retry strategy
        strategy = {
            "should_retry": self.should_retry(error),
            "max_attempts": 3,
            "initial_delay": 1.0,
            "max_delay": 60.0,
            "exponential_multiplier": 2.0,
            "jitter": True
        }
        
        # Customize strategy based on error type
        if error_type == "RATE_LIMIT_ERROR":
            strategy.update({
                "max_attempts": 1,  # Don't retry rate limits immediately
                "initial_delay": getattr(error, 'retry_after', 3600),  # Use API's retry-after
                "exponential_multiplier": 1.0  # No exponential backoff for rate limits
            })
        elif error_type == "NETWORK_ERROR":
            strategy.update({
                "max_attempts": 3,
                "initial_delay": 2.0,
                "max_delay": 30.0
            })
        elif error_type == "EMAIL_ERROR":
            strategy.update({
                "max_attempts": 3,
                "initial_delay": 5.0,
                "max_delay": 60.0
            })
        
        return strategy