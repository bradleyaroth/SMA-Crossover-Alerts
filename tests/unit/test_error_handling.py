"""
Unit tests for enhanced error handling components.

This module tests the ErrorHandler, ErrorCoordinator, and enhanced exception
classes to ensure proper error categorization, standard message generation,
and workflow coordination.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from sma_crossover_alerts.utils.exceptions import (
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
from sma_crossover_alerts.utils.error_handler import ErrorHandler
from sma_crossover_alerts.utils.error_coordinator import ErrorCoordinator, ApplicationState
from sma_crossover_alerts.utils.logging import ErrorLogger


class TestEnhancedExceptions:
    """Test enhanced exception classes."""
    
    def test_enhanced_exception_creation(self):
        """Test enhanced exception with all parameters."""
        context = {"test_key": "test_value"}
        error = EnhancedTQQQAnalysisError(
            message="Test error",
            error_code="TEST_001",
            retry_hint=True,
            context=context,
            component="TestComponent"
        )
        
        assert error.message == "Test error"
        assert error.error_code == "TEST_001"
        assert error.retry_hint is True
        assert error.context == context
        assert error.component == "TestComponent"
        assert error.timestamp is not None
    
    def test_enhanced_exception_to_dict(self):
        """Test exception serialization to dictionary."""
        context = {"test_key": "test_value"}
        error = EnhancedTQQQAnalysisError(
            message="Test error",
            error_code="TEST_001",
            retry_hint=True,
            context=context,
            component="TestComponent"
        )
        
        error_dict = error.to_dict()
        
        assert error_dict["message"] == "Test error"
        assert error_dict["error_code"] == "TEST_001"
        assert error_dict["retry_hint"] is True
        assert error_dict["context"] == context
        assert error_dict["component"] == "TestComponent"
        assert error_dict["exception_type"] == "EnhancedTQQQAnalysisError"
        assert "timestamp" in error_dict
    
    def test_enhanced_exception_string_representation(self):
        """Test string representation of enhanced exception."""
        error = EnhancedTQQQAnalysisError(
            message="Test error",
            error_code="TEST_001",
            retry_hint=True,
            component="TestComponent"
        )
        
        error_str = str(error)
        assert "[TestComponent] Test error [Code: TEST_001] [Retryable]" == error_str


class TestErrorHandler:
    """Test ErrorHandler class."""
    
    @pytest.fixture
    def error_handler(self):
        """Create ErrorHandler instance for testing."""
        return ErrorHandler("test_handler")
    
    def test_categorize_network_error(self, error_handler):
        """Test categorization of network errors."""
        error = NetworkError("Network failed")
        category = error_handler.categorize_error(error)
        assert category == "NETWORK_ERROR"
    
    def test_categorize_rate_limit_error(self, error_handler):
        """Test categorization of rate limit errors."""
        error = RateLimitError("Rate limit exceeded")
        category = error_handler.categorize_error(error)
        assert category == "RATE_LIMIT_ERROR"
    
    def test_categorize_data_validation_error(self, error_handler):
        """Test categorization of data validation errors."""
        error = DataValidationError("Invalid data")
        category = error_handler.categorize_error(error)
        assert category == "DATA_VALIDATION_ERROR"
    
    def test_categorize_api_error(self, error_handler):
        """Test categorization of API errors."""
        error = APIError("API failed")
        category = error_handler.categorize_error(error)
        assert category == "API_ERROR"
    
    def test_categorize_configuration_error(self, error_handler):
        """Test categorization of configuration errors."""
        error = ConfigurationError("Config invalid")
        category = error_handler.categorize_error(error)
        assert category == "CONFIGURATION_ERROR"
    
    def test_categorize_unknown_error(self, error_handler):
        """Test categorization of unknown errors."""
        error = ValueError("Unknown error")
        category = error_handler.categorize_error(error)
        assert category == "UNKNOWN_ERROR"
    
    def test_standard_error_messages(self, error_handler):
        """Test standard error message generation."""
        # Test all required standard messages
        assert error_handler.get_standard_error_message("API_ERROR") == "No API data available."
        assert error_handler.get_standard_error_message("DATA_VALIDATION_ERROR") == "Data validation failed - please try again."
        assert error_handler.get_standard_error_message("NETWORK_ERROR") == "Network connection failed - please try again."
        assert error_handler.get_standard_error_message("RATE_LIMIT_ERROR") == "API rate limit exceeded - please try again later."
        assert error_handler.get_standard_error_message("CONFIGURATION_ERROR") == "Configuration error - please check settings."
    
    def test_should_retry_recoverable_errors(self, error_handler):
        """Test retry decision for recoverable errors."""
        network_error = NetworkError("Network failed")
        rate_limit_error = RateLimitError("Rate limited")
        email_error = EmailError("Email failed")
        
        assert error_handler.should_retry(network_error) is True
        assert error_handler.should_retry(rate_limit_error) is True
        assert error_handler.should_retry(email_error) is True
    
    def test_should_not_retry_non_recoverable_errors(self, error_handler):
        """Test retry decision for non-recoverable errors."""
        data_error = DataValidationError("Invalid data")
        config_error = ConfigurationError("Config invalid")
        sync_error = DataSynchronizationError("Sync failed")
        
        assert error_handler.should_retry(data_error) is False
        assert error_handler.should_retry(config_error) is False
        assert error_handler.should_retry(sync_error) is False
    
    def test_create_enhanced_error(self, error_handler):
        """Test creation of enhanced error from original error."""
        original_error = APIError("API failed", status_code=500)
        context = {"additional_info": "test"}
        
        enhanced_error = error_handler.create_enhanced_error(original_error, context)
        
        assert isinstance(enhanced_error, EnhancedTQQQAnalysisError)
        assert enhanced_error.message == "No API data available."
        assert enhanced_error.error_code == "API_001"
        assert enhanced_error.retry_hint is False
        assert "additional_info" in enhanced_error.context
        assert "original_error_type" in enhanced_error.context
    
    def test_get_retry_strategy_rate_limit(self, error_handler):
        """Test retry strategy for rate limit errors."""
        error = RateLimitError("Rate limited", retry_after=3600)
        strategy = error_handler.get_retry_strategy(error)
        
        assert strategy["should_retry"] is True
        assert strategy["max_attempts"] == 1
        assert strategy["initial_delay"] == 3600
        assert strategy["exponential_multiplier"] == 1.0
    
    def test_get_retry_strategy_network_error(self, error_handler):
        """Test retry strategy for network errors."""
        error = NetworkError("Network failed")
        strategy = error_handler.get_retry_strategy(error)
        
        assert strategy["should_retry"] is True
        assert strategy["max_attempts"] == 3
        assert strategy["initial_delay"] == 2.0
        assert strategy["max_delay"] == 30.0


class TestErrorCoordinator:
    """Test ErrorCoordinator class."""
    
    @pytest.fixture
    def error_coordinator(self):
        """Create ErrorCoordinator instance for testing."""
        return ErrorCoordinator("test_coordinator")
    
    def test_handle_workflow_error(self, error_coordinator):
        """Test workflow error handling."""
        error = APIError("API failed")
        result = error_coordinator.handle_workflow_error(error, "TestComponent")
        
        assert result["error_type"] == "API_ERROR"
        assert result["component"] == "TestComponent"
        assert result["message"] == "No API data available."
        assert result["should_retry"] is False
        assert "timestamp" in result
    
    def test_determine_final_state_success(self, error_coordinator):
        """Test final state determination with no errors."""
        state = error_coordinator.determine_final_state([])
        assert state == ApplicationState.SUCCESS.value
    
    def test_determine_final_state_configuration_error(self, error_coordinator):
        """Test final state determination with configuration errors."""
        errors = [{"error_type": "CONFIGURATION_ERROR", "should_retry": False}]
        state = error_coordinator.determine_final_state(errors)
        assert state == ApplicationState.CONFIGURATION_ERROR.value
    
    def test_determine_final_state_critical_error(self, error_coordinator):
        """Test final state determination with critical errors."""
        errors = [{"error_type": "API_ERROR", "should_retry": False}]
        state = error_coordinator.determine_final_state(errors)
        assert state == ApplicationState.CRITICAL_ERROR.value
    
    def test_determine_final_state_recoverable_error(self, error_coordinator):
        """Test final state determination with recoverable errors."""
        errors = [{"error_type": "NETWORK_ERROR", "should_retry": True}]
        state = error_coordinator.determine_final_state(errors)
        assert state == ApplicationState.RECOVERABLE_ERROR.value
    
    def test_should_send_error_notification(self, error_coordinator):
        """Test error notification decision logic."""
        # Should send notifications
        config_error = ConfigurationError("Config invalid")
        api_error = APIError("API failed")
        data_error = DataValidationError("Data invalid")
        network_error = NetworkError("Network failed")
        
        assert error_coordinator.should_send_error_notification(config_error) is True
        assert error_coordinator.should_send_error_notification(api_error) is True
        assert error_coordinator.should_send_error_notification(data_error) is True
        assert error_coordinator.should_send_error_notification(network_error) is True
        
        # Should not send notifications
        rate_limit_error = RateLimitError("Rate limited")
        assert error_coordinator.should_send_error_notification(rate_limit_error) is False
    
    def test_generate_error_email_content_configuration(self, error_coordinator):
        """Test email content generation for configuration errors."""
        details = {"message": "Config invalid", "component": "TestComponent"}
        content = error_coordinator.generate_error_email_content("CONFIGURATION_ERROR", details)
        
        assert content["subject"] == "TQQQ Analysis - Configuration Error"
        assert content["priority"] == "high"
        assert content["requires_action"] is True
        assert "Config invalid" in content["body"]
        assert "TestComponent" in content["body"]
    
    def test_generate_error_email_content_rate_limit(self, error_coordinator):
        """Test email content generation for rate limit errors."""
        details = {"message": "Rate limited", "component": "TestComponent"}
        content = error_coordinator.generate_error_email_content("RATE_LIMIT_ERROR", details)
        
        assert content["subject"] == "TQQQ Analysis - Rate Limit Exceeded"
        assert content["priority"] == "low"
        assert content["requires_action"] is False
        assert "Rate limited" in content["body"]
    
    def test_get_error_summary(self, error_coordinator):
        """Test error summary generation."""
        # Add some errors
        error1 = APIError("API failed")
        error2 = NetworkError("Network failed")
        
        error_coordinator.handle_workflow_error(error1, "Component1")
        error_coordinator.handle_workflow_error(error2, "Component2")
        
        summary = error_coordinator.get_error_summary()
        
        assert summary["total_errors"] == 2
        assert "API_ERROR" in summary["error_type_counts"]
        assert "NETWORK_ERROR" in summary["error_type_counts"]
        assert "Component1" in summary["component_counts"]
        assert "Component2" in summary["component_counts"]
    
    def test_reset_error_state(self, error_coordinator):
        """Test error state reset."""
        # Add an error
        error = APIError("API failed")
        error_coordinator.handle_workflow_error(error, "TestComponent")
        
        # Verify error was recorded
        assert len(error_coordinator.component_errors) > 0
        
        # Reset state
        error_coordinator.reset_error_state()
        
        # Verify state is reset
        assert len(error_coordinator.component_errors) == 0
        assert error_coordinator.workflow_state == ApplicationState.SUCCESS


class TestErrorIntegration:
    """Test integration between error handling components."""
    
    def test_end_to_end_error_handling(self):
        """Test complete error handling workflow."""
        # Create components
        error_handler = ErrorHandler("integration_test")
        error_coordinator = ErrorCoordinator("integration_test")
        
        # Simulate API error
        original_error = APIError("API service unavailable", status_code=503)
        
        # Handle error through coordinator
        error_record = error_coordinator.handle_workflow_error(original_error, "APIClient")
        
        # Verify error was properly categorized and handled
        assert error_record["error_type"] == "API_ERROR"
        assert error_record["message"] == "No API data available."
        assert error_record["component"] == "APIClient"
        
        # Check final state
        final_state = error_coordinator.determine_final_state()
        assert final_state == ApplicationState.CRITICAL_ERROR.value
        
        # Check notification decision
        should_notify = error_coordinator.should_send_error_notification(original_error)
        assert should_notify is True
        
        # Generate email content
        email_content = error_coordinator.generate_error_email_content(
            "CRITICAL_ERROR", 
            {"message": error_record["message"], "component": "APIClient"}
        )
        assert email_content["priority"] == "high"
        assert email_content["requires_action"] is True
    
    def test_multiple_error_coordination(self):
        """Test coordination of multiple errors."""
        error_coordinator = ErrorCoordinator("multi_error_test")
        
        # Add multiple errors
        errors = [
            (NetworkError("Connection timeout"), "APIClient"),
            (DataValidationError("Invalid JSON"), "DataProcessor"),
            (RateLimitError("Rate exceeded"), "APIClient")
        ]
        
        for error, component in errors:
            error_coordinator.handle_workflow_error(error, component)
        
        # Check summary
        summary = error_coordinator.get_error_summary()
        assert summary["total_errors"] == 3
        assert len(summary["error_type_counts"]) == 3
        assert "APIClient" in summary["component_counts"]
        assert "DataProcessor" in summary["component_counts"]
        
        # Check final state (should be recoverable due to network error)
        final_state = error_coordinator.determine_final_state()
        assert final_state == ApplicationState.RECOVERABLE_ERROR.value


if __name__ == "__main__":
    pytest.main([__file__])