"""
Application-level error coordination for TQQQ analysis workflow.

This module provides the ErrorCoordinator class for managing errors across
all application components, determining final application state, and
generating appropriate email content for different error scenarios.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from enum import Enum

from .error_handler import ErrorHandler
from .exceptions import (
    TQQQAnalyzerError,
    EnhancedTQQQAnalysisError,
    APIError,
    NetworkError,
    RateLimitError,
    DataValidationError,
    ConfigurationError,
    EmailError
)
from .logging import get_logger


class ApplicationState(Enum):
    """Application execution states."""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    RECOVERABLE_ERROR = "recoverable_error"
    CRITICAL_ERROR = "critical_error"
    CONFIGURATION_ERROR = "configuration_error"


class ErrorCoordinator:
    """
    Coordinates error handling across all application components.
    
    Manages workflow error handling, determines final application state,
    generates error email content, and coordinates error escalation.
    """
    
    def __init__(self, logger_name: str = "error_coordinator"):
        """
        Initialize error coordinator.
        
        Args:
            logger_name: Name for the logger instance
        """
        self.logger = get_logger(logger_name)
        self.error_handler = ErrorHandler("coordinator_handler")
        self.component_errors: Dict[str, List[Dict[str, Any]]] = {}
        self.workflow_state = ApplicationState.SUCCESS
    
    def handle_workflow_error(self, error: Exception, component: str) -> Dict[str, Any]:
        """
        Handle errors at the application workflow level.
        
        Args:
            error: The exception that occurred
            component: Component where the error occurred
            
        Returns:
            dict: Error handling result with metadata
        """
        error_type = self.error_handler.categorize_error(error)
        standard_message = self.error_handler.get_standard_error_message(error_type)
        should_retry = self.error_handler.should_retry(error)
        error_code = self.error_handler.get_error_code(error_type)
        
        # Create error record
        error_record = {
            "error_type": error_type,
            "error_code": error_code,
            "component": component,
            "message": standard_message,
            "original_message": str(error),
            "should_retry": should_retry,
            "timestamp": datetime.utcnow().isoformat(),
            "context": getattr(error, 'context', {}) if hasattr(error, 'context') else {}
        }
        
        # Store error by component
        if component not in self.component_errors:
            self.component_errors[component] = []
        self.component_errors[component].append(error_record)
        
        # Update workflow state
        self._update_workflow_state(error, component)
        
        # Log the workflow error
        self.logger.error(
            f"Workflow error in {component}: {error_type}",
            extra={
                "component": component,
                "error_type": error_type,
                "error_code": error_code,
                "should_retry": should_retry,
                "workflow_state": self.workflow_state.value,
                "error_message": str(error)
            }
        )
        
        return error_record
    
    def determine_final_state(self, errors: Optional[List[Dict[str, Any]]] = None) -> str:
        """
        Determine final application state based on error types.
        
        Args:
            errors: Optional list of errors to evaluate (uses stored errors if None)
            
        Returns:
            str: Final application state
        """
        if errors is None:
            # Use all stored errors
            all_errors = []
            for component_errors in self.component_errors.values():
                all_errors.extend(component_errors)
            errors = all_errors
        
        if not errors:
            return ApplicationState.SUCCESS.value
        
        # Categorize errors by severity
        critical_errors = []
        recoverable_errors = []
        configuration_errors = []
        
        for error in errors:
            error_type = error.get("error_type", "UNKNOWN_ERROR")
            
            if error_type == "CONFIGURATION_ERROR":
                configuration_errors.append(error)
            elif error.get("should_retry", False):
                recoverable_errors.append(error)
            else:
                critical_errors.append(error)
        
        # Determine state based on error categories
        if configuration_errors:
            return ApplicationState.CONFIGURATION_ERROR.value
        elif critical_errors:
            return ApplicationState.CRITICAL_ERROR.value
        elif recoverable_errors:
            return ApplicationState.RECOVERABLE_ERROR.value
        else:
            return ApplicationState.PARTIAL_SUCCESS.value
    
    def generate_error_email_content(self, error_type: str, 
                                   details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate appropriate email content for different error scenarios.
        
        Args:
            error_type: Type of error that occurred
            details: Error details and context
            
        Returns:
            dict: Email content with subject, body, and metadata
        """
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        # Base email content
        email_content = {
            "timestamp": timestamp,
            "error_type": error_type,
            "priority": "normal",
            "requires_action": False
        }
        
        # Generate content based on error type
        if error_type == "CONFIGURATION_ERROR":
            email_content.update({
                "subject": "TQQQ Analysis - Configuration Error",
                "priority": "high",
                "requires_action": True,
                "body": self._generate_configuration_error_body(details, timestamp),
                "html_body": self._generate_configuration_error_html(details, timestamp)
            })
        
        elif error_type == "CRITICAL_ERROR":
            email_content.update({
                "subject": "TQQQ Analysis - Critical Error",
                "priority": "high",
                "requires_action": True,
                "body": self._generate_critical_error_body(details, timestamp),
                "html_body": self._generate_critical_error_html(details, timestamp)
            })
        
        elif error_type == "RECOVERABLE_ERROR":
            email_content.update({
                "subject": "TQQQ Analysis - Temporary Error",
                "priority": "normal",
                "requires_action": False,
                "body": self._generate_recoverable_error_body(details, timestamp),
                "html_body": self._generate_recoverable_error_html(details, timestamp)
            })
        
        elif error_type == "RATE_LIMIT_ERROR":
            email_content.update({
                "subject": "TQQQ Analysis - Rate Limit Exceeded",
                "priority": "low",
                "requires_action": False,
                "body": self._generate_rate_limit_error_body(details, timestamp),
                "html_body": self._generate_rate_limit_error_html(details, timestamp)
            })
        
        else:
            email_content.update({
                "subject": "TQQQ Analysis - Error Notification",
                "priority": "normal",
                "requires_action": True,
                "body": self._generate_generic_error_body(details, timestamp),
                "html_body": self._generate_generic_error_html(details, timestamp)
            })
        
        return email_content
    
    def should_send_error_notification(self, error: Exception) -> bool:
        """
        Determine if error notification should be sent.
        
        Args:
            error: The exception to evaluate
            
        Returns:
            bool: True if notification should be sent
        """
        error_type = self.error_handler.categorize_error(error)
        
        # Always send notifications for critical errors
        if error_type in ["CONFIGURATION_ERROR", "CRITICAL_ERROR"]:
            return True
        
        # Send notifications for API errors (no data available)
        if error_type == "API_ERROR":
            return True
        
        # Send notifications for data validation errors
        if error_type == "DATA_VALIDATION_ERROR":
            return True
        
        # Don't send notifications for rate limits (expected)
        if error_type == "RATE_LIMIT_ERROR":
            return False
        
        # Send notifications for network errors if they persist
        if error_type == "NETWORK_ERROR":
            return True
        
        # Default to sending notification
        return True
    
    def get_error_summary(self) -> Dict[str, Any]:
        """
        Get summary of all errors encountered during workflow.
        
        Returns:
            dict: Error summary with counts and details
        """
        total_errors = sum(len(errors) for errors in self.component_errors.values())
        
        # Count errors by type
        error_type_counts = {}
        component_counts = {}
        
        for component, errors in self.component_errors.items():
            component_counts[component] = len(errors)
            
            for error in errors:
                error_type = error.get("error_type", "UNKNOWN_ERROR")
                error_type_counts[error_type] = error_type_counts.get(error_type, 0) + 1
        
        return {
            "total_errors": total_errors,
            "error_type_counts": error_type_counts,
            "component_counts": component_counts,
            "workflow_state": self.workflow_state.value,
            "final_state": self.determine_final_state(),
            "components_affected": list(self.component_errors.keys())
        }
    
    def reset_error_state(self) -> None:
        """Reset error coordinator state for new workflow execution."""
        self.component_errors.clear()
        self.workflow_state = ApplicationState.SUCCESS
        self.logger.info("Error coordinator state reset for new workflow")
    
    def _update_workflow_state(self, error: Exception, component: str) -> None:
        """Update workflow state based on new error."""
        error_type = self.error_handler.categorize_error(error)
        
        # Configuration errors are most critical
        if error_type == "CONFIGURATION_ERROR":
            self.workflow_state = ApplicationState.CONFIGURATION_ERROR
        
        # Don't downgrade from configuration error
        elif self.workflow_state != ApplicationState.CONFIGURATION_ERROR:
            if error_type in ["API_ERROR", "DATA_VALIDATION_ERROR"]:
                self.workflow_state = ApplicationState.CRITICAL_ERROR
            elif self.error_handler.should_retry(error):
                if self.workflow_state == ApplicationState.SUCCESS:
                    self.workflow_state = ApplicationState.RECOVERABLE_ERROR
            else:
                self.workflow_state = ApplicationState.CRITICAL_ERROR
    
    def _generate_configuration_error_body(self, details: Dict[str, Any], timestamp: str) -> str:
        """Generate plain text body for configuration errors."""
        return f"""TQQQ Analysis Configuration Error

Time: {timestamp}

A configuration error has occurred that prevents the TQQQ analysis from running.
This requires immediate attention to resolve.

Error Details:
{details.get('message', 'Configuration error - please check settings.')}

Component: {details.get('component', 'Unknown')}

Please check the application configuration and resolve the issue.

This is an automated message from the TQQQ Analysis system.
"""
    
    def _generate_configuration_error_html(self, details: Dict[str, Any], timestamp: str) -> str:
        """Generate HTML body for configuration errors."""
        return f"""
<html>
<body>
<h2 style="color: #d32f2f;">TQQQ Analysis Configuration Error</h2>
<p><strong>Time:</strong> {timestamp}</p>
<p>A configuration error has occurred that prevents the TQQQ analysis from running.</p>
<p><strong>Error:</strong> {details.get('message', 'Configuration error - please check settings.')}</p>
<p><strong>Component:</strong> {details.get('component', 'Unknown')}</p>
<p style="color: #d32f2f;"><strong>Action Required:</strong> Please check the application configuration and resolve the issue.</p>
<hr>
<p><em>This is an automated message from the TQQQ Analysis system.</em></p>
</body>
</html>
"""
    
    def _generate_critical_error_body(self, details: Dict[str, Any], timestamp: str) -> str:
        """Generate plain text body for critical errors."""
        return f"""TQQQ Analysis Critical Error

Time: {timestamp}

A critical error has occurred during TQQQ analysis execution.

Error Details:
{details.get('message', 'A critical error occurred.')}

Component: {details.get('component', 'Unknown')}

The analysis could not be completed. Please investigate and resolve the issue.

This is an automated message from the TQQQ Analysis system.
"""
    
    def _generate_critical_error_html(self, details: Dict[str, Any], timestamp: str) -> str:
        """Generate HTML body for critical errors."""
        return f"""
<html>
<body>
<h2 style="color: #d32f2f;">TQQQ Analysis Critical Error</h2>
<p><strong>Time:</strong> {timestamp}</p>
<p>A critical error has occurred during TQQQ analysis execution.</p>
<p><strong>Error:</strong> {details.get('message', 'A critical error occurred.')}</p>
<p><strong>Component:</strong> {details.get('component', 'Unknown')}</p>
<p style="color: #d32f2f;"><strong>Action Required:</strong> Please investigate and resolve the issue.</p>
<hr>
<p><em>This is an automated message from the TQQQ Analysis system.</em></p>
</body>
</html>
"""
    
    def _generate_recoverable_error_body(self, details: Dict[str, Any], timestamp: str) -> str:
        """Generate plain text body for recoverable errors."""
        return f"""TQQQ Analysis Temporary Error

Time: {timestamp}

A temporary error occurred during TQQQ analysis execution.
The system will automatically retry the operation.

Error Details:
{details.get('message', 'A temporary error occurred.')}

Component: {details.get('component', 'Unknown')}

No immediate action is required. The system will attempt to recover automatically.

This is an automated message from the TQQQ Analysis system.
"""
    
    def _generate_recoverable_error_html(self, details: Dict[str, Any], timestamp: str) -> str:
        """Generate HTML body for recoverable errors."""
        return f"""
<html>
<body>
<h2 style="color: #ff9800;">TQQQ Analysis Temporary Error</h2>
<p><strong>Time:</strong> {timestamp}</p>
<p>A temporary error occurred during TQQQ analysis execution.</p>
<p><strong>Error:</strong> {details.get('message', 'A temporary error occurred.')}</p>
<p><strong>Component:</strong> {details.get('component', 'Unknown')}</p>
<p style="color: #ff9800;"><strong>Status:</strong> The system will automatically retry the operation.</p>
<hr>
<p><em>This is an automated message from the TQQQ Analysis system.</em></p>
</body>
</html>
"""
    
    def _generate_rate_limit_error_body(self, details: Dict[str, Any], timestamp: str) -> str:
        """Generate plain text body for rate limit errors."""
        return f"""TQQQ Analysis Rate Limit Notice

Time: {timestamp}

The API rate limit has been exceeded. The analysis will be retried automatically
at the next scheduled time.

Error Details:
{details.get('message', 'API rate limit exceeded - please try again later.')}

No action is required. This is a normal occurrence with API usage limits.

This is an automated message from the TQQQ Analysis system.
"""
    
    def _generate_rate_limit_error_html(self, details: Dict[str, Any], timestamp: str) -> str:
        """Generate HTML body for rate limit errors."""
        return f"""
<html>
<body>
<h2 style="color: #2196f3;">TQQQ Analysis Rate Limit Notice</h2>
<p><strong>Time:</strong> {timestamp}</p>
<p>The API rate limit has been exceeded.</p>
<p><strong>Message:</strong> {details.get('message', 'API rate limit exceeded - please try again later.')}</p>
<p style="color: #2196f3;"><strong>Status:</strong> The analysis will be retried automatically at the next scheduled time.</p>
<p>No action is required. This is a normal occurrence with API usage limits.</p>
<hr>
<p><em>This is an automated message from the TQQQ Analysis system.</em></p>
</body>
</html>
"""
    
    def _generate_generic_error_body(self, details: Dict[str, Any], timestamp: str) -> str:
        """Generate plain text body for generic errors."""
        return f"""TQQQ Analysis Error Notification

Time: {timestamp}

An error occurred during TQQQ analysis execution.

Error Details:
{details.get('message', 'An unexpected error occurred.')}

Component: {details.get('component', 'Unknown')}

Please review the error details and take appropriate action.

This is an automated message from the TQQQ Analysis system.
"""
    
    def _generate_generic_error_html(self, details: Dict[str, Any], timestamp: str) -> str:
        """Generate HTML body for generic errors."""
        return f"""
<html>
<body>
<h2 style="color: #f44336;">TQQQ Analysis Error Notification</h2>
<p><strong>Time:</strong> {timestamp}</p>
<p>An error occurred during TQQQ analysis execution.</p>
<p><strong>Error:</strong> {details.get('message', 'An unexpected error occurred.')}</p>
<p><strong>Component:</strong> {details.get('component', 'Unknown')}</p>
<p style="color: #f44336;"><strong>Action:</strong> Please review the error details and take appropriate action.</p>
<hr>
<p><em>This is an automated message from the TQQQ Analysis system.</em></p>
</body>
</html>
"""