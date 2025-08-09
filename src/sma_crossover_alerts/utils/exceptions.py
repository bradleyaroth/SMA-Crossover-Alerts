"""
Custom exception classes for TQQQ analysis application.

This module defines the exception hierarchy for the application,
providing specific error types for different components.
"""

from typing import Optional, Dict, Any
from datetime import datetime


class TQQQAnalyzerError(Exception):
    """
    Base exception for TQQQ Analyzer application.
    
    All custom exceptions in the application should inherit from this class.
    """
    
    def __init__(self, message: str, component: Optional[str] = None):
        """
        Initialize the base exception.
        
        Args:
            message: Error message
            component: Component where the error occurred
        """
        self.message = message
        self.component = component
        super().__init__(message)
    
    def __str__(self) -> str:
        """Return string representation of the error."""
        if self.component:
            return f"[{self.component}] {self.message}"
        return self.message


class EnhancedTQQQAnalysisError(TQQQAnalyzerError):
    """
    Enhanced base exception with error codes, retry hints, and context.
    
    Provides additional metadata for programmatic error handling,
    recovery strategies, and debugging support.
    """
    
    def __init__(self, message: str, error_code: Optional[str] = None,
                 retry_hint: bool = False, context: Optional[Dict[str, Any]] = None,
                 component: Optional[str] = None):
        """
        Initialize enhanced exception.
        
        Args:
            message: Error message
            error_code: Error code for programmatic handling
            retry_hint: Whether this error might be recoverable with retry
            context: Additional context information for debugging
            component: Component where the error occurred
        """
        self.error_code = error_code
        self.retry_hint = retry_hint
        self.context = context or {}
        self.timestamp = datetime.utcnow().isoformat()
        super().__init__(message, component)
    
    def __str__(self) -> str:
        """Return detailed string representation."""
        base_str = super().__str__()
        if self.error_code:
            base_str += f" [Code: {self.error_code}]"
        if self.retry_hint:
            base_str += " [Retryable]"
        return base_str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for serialization."""
        return {
            "message": self.message,
            "error_code": self.error_code,
            "retry_hint": self.retry_hint,
            "context": self.context,
            "component": self.component,
            "timestamp": self.timestamp,
            "exception_type": self.__class__.__name__
        }


# Maintain backward compatibility
TQQQAnalysisError = TQQQAnalyzerError


class APIError(TQQQAnalyzerError):
    """
    API-related errors.
    
    Raised when there are issues with external API calls,
    including network errors, authentication failures, and rate limits.
    """
    
    def __init__(self, message: str, status_code: Optional[int] = None, 
                 response_data: Optional[str] = None, component: str = "API"):
        """
        Initialize API error.
        
        Args:
            message: Error message
            status_code: HTTP status code if applicable
            response_data: Raw response data if available
            component: Component name (defaults to "API")
        """
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(message, component)
    
    def __str__(self) -> str:
        """Return detailed string representation."""
        base_str = super().__str__()
        if self.status_code:
            base_str += f" (HTTP {self.status_code})"
        return base_str


class DataValidationError(TQQQAnalyzerError):
    """
    Data validation errors.
    
    Raised when data fails validation checks, including
    malformed API responses, missing fields, or invalid values.
    """
    
    def __init__(self, message: str, field_name: Optional[str] = None, 
                 invalid_value: Optional[str] = None, component: str = "DataValidation"):
        """
        Initialize data validation error.
        
        Args:
            message: Error message
            field_name: Name of the field that failed validation
            invalid_value: The invalid value that caused the error
            component: Component name (defaults to "DataValidation")
        """
        self.field_name = field_name
        self.invalid_value = invalid_value
        super().__init__(message, component)
    
    def __str__(self) -> str:
        """Return detailed string representation."""
        base_str = super().__str__()
        if self.field_name:
            base_str += f" (Field: {self.field_name}"
            if self.invalid_value:
                base_str += f", Value: {self.invalid_value}"
            base_str += ")"
        return base_str


class EmailError(TQQQAnalyzerError):
    """
    Email sending errors.
    
    Raised when there are issues with email delivery,
    including SMTP authentication failures and send errors.
    """
    
    def __init__(self, message: str, smtp_error: Optional[str] = None, 
                 recipients: Optional[list] = None, component: str = "Email"):
        """
        Initialize email error.
        
        Args:
            message: Error message
            smtp_error: SMTP-specific error message
            recipients: List of intended recipients
            component: Component name (defaults to "Email")
        """
        self.smtp_error = smtp_error
        self.recipients = recipients
        super().__init__(message, component)
    
    def __str__(self) -> str:
        """Return detailed string representation."""
        base_str = super().__str__()
        if self.recipients:
            base_str += f" (Recipients: {', '.join(self.recipients)})"
        if self.smtp_error:
            base_str += f" [SMTP: {self.smtp_error}]"
        return base_str


class ConfigurationError(TQQQAnalyzerError):
    """
    Configuration-related errors.
    
    Raised when there are issues with application configuration,
    including missing settings, invalid values, or file access problems.
    """
    
    def __init__(self, message: str, config_section: Optional[str] = None, 
                 config_key: Optional[str] = None, component: str = "Configuration"):
        """
        Initialize configuration error.
        
        Args:
            message: Error message
            config_section: Configuration section name
            config_key: Configuration key name
            component: Component name (defaults to "Configuration")
        """
        self.config_section = config_section
        self.config_key = config_key
        super().__init__(message, component)
    
    def __str__(self) -> str:
        """Return detailed string representation."""
        base_str = super().__str__()
        if self.config_section and self.config_key:
            base_str += f" (Section: {self.config_section}, Key: {self.config_key})"
        elif self.config_section:
            base_str += f" (Section: {self.config_section})"
        return base_str


class NetworkError(APIError):
    """
    Network-related errors.
    
    Raised when there are network connectivity issues,
    including connection timeouts, DNS resolution failures, and connection refused errors.
    """
    
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        """
        Initialize network error.
        
        Args:
            message: Error message
            original_error: Original exception that caused the network error
        """
        self.original_error = original_error
        super().__init__(message, component="Network")
    
    def __str__(self) -> str:
        """Return detailed string representation."""
        base_str = super().__str__()
        if self.original_error:
            base_str += f" (Caused by: {type(self.original_error).__name__}: {self.original_error})"
        return base_str


class RateLimitError(APIError):
    """
    API rate limit exceeded error.
    
    Specialized API error for rate limit scenarios.
    """
    
    def __init__(self, message: str = "API rate limit exceeded",
                 retry_after: Optional[int] = None):
        """
        Initialize rate limit error.
        
        Args:
            message: Error message
            retry_after: Seconds to wait before retrying
        """
        self.retry_after = retry_after
        super().__init__(message, status_code=429, component="RateLimit")
    
    def __str__(self) -> str:
        """Return detailed string representation."""
        base_str = super().__str__()
        if self.retry_after:
            base_str += f" (Retry after: {self.retry_after}s)"
        return base_str


class DataSynchronizationError(DataValidationError):
    """
    Data synchronization error.
    
    Raised when price data and SMA data cannot be synchronized
    due to missing or mismatched dates.
    """
    
    def __init__(self, message: str, price_dates: Optional[list] = None, 
                 sma_dates: Optional[list] = None):
        """
        Initialize data synchronization error.
        
        Args:
            message: Error message
            price_dates: Available price data dates
            sma_dates: Available SMA data dates
        """
        self.price_dates = price_dates
        self.sma_dates = sma_dates
        super().__init__(message, component="DataSynchronization")
    
    def __str__(self) -> str:
        """Return detailed string representation."""
        base_str = super().__str__()
        if self.price_dates and self.sma_dates:
            price_count = len(self.price_dates)
            sma_count = len(self.sma_dates)
            base_str += f" (Price dates: {price_count}, SMA dates: {sma_count})"
        return base_str