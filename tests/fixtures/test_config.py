"""
Test configuration data and utilities.

This module provides test-specific configuration data, environment settings,
and utilities for creating test configurations.
"""

import os
from typing import Dict, Any, List
from pathlib import Path


class TestConfig:
    """Test configuration management."""
    
    @staticmethod
    def get_test_api_config() -> Dict[str, Any]:
        """Get test API configuration."""
        return {
            'alpha_vantage_key': os.getenv('TEST_API_KEY', 'TEST_API_KEY_123456789'),
            'base_url': 'https://www.alphavantage.co/query',
            'timeout': 30,
            'max_retries': 3
        }
    
    @staticmethod
    def get_test_email_config() -> Dict[str, Any]:
        """Get test email configuration."""
        return {
            'smtp_server': os.getenv('TEST_SMTP_SERVER', 'smtp.test.com'),
            'smtp_port': int(os.getenv('TEST_SMTP_PORT', '587')),
            'username': os.getenv('TEST_SMTP_USERNAME', 'test@example.com'),
            'password': os.getenv('TEST_SMTP_PASSWORD', 'test_password'),
            'use_tls': True,
            'from_address': os.getenv('TEST_FROM_ADDRESS', 'tqqq@example.com'),
            'from_name': 'TQQQ Test System',
            'to_addresses': ['recipient1@example.com', 'recipient2@example.com']
        }
    
    @staticmethod
    def get_test_analysis_config() -> Dict[str, Any]:
        """Get test analysis configuration."""
        return {
            'symbol': 'TQQQ',
            'sma_period': 200,
            'max_data_age_days': 5
        }
    
    @staticmethod
    def get_test_logging_config() -> Dict[str, Any]:
        """Get test logging configuration."""
        return {
            'level': 'DEBUG',
            'log_file': 'logs/test.log',
            'max_file_size': '10MB',
            'backup_count': 5
        }
    
    @staticmethod
    def get_test_system_config() -> Dict[str, Any]:
        """Get test system configuration."""
        return {
            'rate_limit_file': '.test_api_usage',
            'timezone': 'UTC'
        }
    
    @staticmethod
    def get_complete_test_config() -> Dict[str, Any]:
        """Get complete test configuration."""
        return {
            'api': TestConfig.get_test_api_config(),
            'email': TestConfig.get_test_email_config(),
            'analysis': TestConfig.get_test_analysis_config(),
            'logging': TestConfig.get_test_logging_config(),
            'system': TestConfig.get_test_system_config()
        }
    
    @staticmethod
    def create_test_config_file(config_path: str, config_data: Dict[str, Any] = None) -> str:
        """Create a test configuration file."""
        if config_data is None:
            config_data = TestConfig.get_complete_test_config()
        
        config_content = f"""
[api]
alpha_vantage_key = {config_data['api']['alpha_vantage_key']}
base_url = {config_data['api']['base_url']}
timeout = {config_data['api']['timeout']}
max_retries = {config_data['api']['max_retries']}

[email]
smtp_server = {config_data['email']['smtp_server']}
smtp_port = {config_data['email']['smtp_port']}
username = {config_data['email']['username']}
password = {config_data['email']['password']}
use_tls = {str(config_data['email']['use_tls']).lower()}
from_address = {config_data['email']['from_address']}
from_name = {config_data['email']['from_name']}
to_addresses = {','.join(config_data['email']['to_addresses'])}

[analysis]
symbol = {config_data['analysis']['symbol']}
sma_period = {config_data['analysis']['sma_period']}
max_data_age_days = {config_data['analysis']['max_data_age_days']}

[logging]
level = {config_data['logging']['level']}
log_file = {config_data['logging']['log_file']}
max_file_size = {config_data['logging']['max_file_size']}
backup_count = {config_data['logging']['backup_count']}

[system]
rate_limit_file = {config_data['system']['rate_limit_file']}
timezone = {config_data['system']['timezone']}
"""
        
        Path(config_path).write_text(config_content)
        return config_path


class IntegrationTestConfig:
    """Configuration for integration tests."""
    
    @staticmethod
    def should_use_real_api() -> bool:
        """Check if integration tests should use real API."""
        return os.getenv('USE_REAL_API', 'false').lower() == 'true'
    
    @staticmethod
    def should_use_real_smtp() -> bool:
        """Check if integration tests should use real SMTP."""
        return os.getenv('USE_REAL_SMTP', 'false').lower() == 'true'
    
    @staticmethod
    def get_real_api_key() -> str:
        """Get real API key for integration tests."""
        return os.getenv('ALPHA_VANTAGE_API_KEY', '0000000000000000')
    
    @staticmethod
    def get_real_smtp_config() -> Dict[str, Any]:
        """Get real SMTP configuration for integration tests."""
        return {
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp-relay.brevo.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'username': os.getenv('SMTP_USERNAME', ''),
            'password': os.getenv('SMTP_PASSWORD', ''),
            'use_tls': True,
            'from_address': os.getenv('FROM_ADDRESS', 'tqqq@example.com'),
            'from_name': 'TQQQ Integration Test',
            'to_addresses': [os.getenv('TEST_RECIPIENT', 'test@example.com')]
        }
    
    @staticmethod
    def get_integration_config() -> Dict[str, Any]:
        """Get complete integration test configuration."""
        config = TestConfig.get_complete_test_config()
        
        if IntegrationTestConfig.should_use_real_api():
            config['api']['alpha_vantage_key'] = IntegrationTestConfig.get_real_api_key()
        
        if IntegrationTestConfig.should_use_real_smtp():
            config['email'] = IntegrationTestConfig.get_real_smtp_config()
        
        return config


class PerformanceTestConfig:
    """Configuration for performance tests."""
    
    @staticmethod
    def get_performance_thresholds() -> Dict[str, float]:
        """Get performance test thresholds in seconds."""
        return {
            'api_call_timeout': 10.0,
            'email_send_timeout': 5.0,
            'full_workflow_timeout': 30.0,
            'data_processing_timeout': 2.0,
            'analysis_timeout': 1.0
        }
    
    @staticmethod
    def get_load_test_config() -> Dict[str, Any]:
        """Get load test configuration."""
        return {
            'concurrent_requests': int(os.getenv('LOAD_TEST_CONCURRENT', '5')),
            'total_requests': int(os.getenv('LOAD_TEST_TOTAL', '50')),
            'request_delay': float(os.getenv('LOAD_TEST_DELAY', '1.0')),
            'timeout': float(os.getenv('LOAD_TEST_TIMEOUT', '60.0'))
        }


class TestEnvironment:
    """Test environment utilities."""
    
    @staticmethod
    def is_ci_environment() -> bool:
        """Check if running in CI environment."""
        ci_indicators = ['CI', 'CONTINUOUS_INTEGRATION', 'GITHUB_ACTIONS', 'TRAVIS', 'JENKINS']
        return any(os.getenv(indicator) for indicator in ci_indicators)
    
    @staticmethod
    def get_test_data_dir() -> Path:
        """Get test data directory."""
        return Path(__file__).parent.parent / "fixtures"
    
    @staticmethod
    def get_temp_dir() -> Path:
        """Get temporary directory for tests."""
        import tempfile
        return Path(tempfile.gettempdir()) / "tqqq_tests"
    
    @staticmethod
    def setup_test_environment():
        """Setup test environment."""
        # Create necessary directories
        temp_dir = TestEnvironment.get_temp_dir()
        temp_dir.mkdir(exist_ok=True)
        
        (temp_dir / "logs").mkdir(exist_ok=True)
        (temp_dir / "config").mkdir(exist_ok=True)
        
        return temp_dir
    
    @staticmethod
    def cleanup_test_environment():
        """Cleanup test environment."""
        import shutil
        temp_dir = TestEnvironment.get_temp_dir()
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)


# Test data constants
TEST_SYMBOL = "TQQQ"
TEST_SMA_PERIOD = 200
TEST_API_KEY = "TEST_API_KEY_123456789"
TEST_EMAIL = "test@example.com"

# Test date constants
TEST_DATE = "2024-01-15"
TEST_TIMESTAMP = "2024-01-15 18:00:00 UTC"

# Test price constants
TEST_CURRENT_PRICE = 46.23
TEST_SMA_VALUE = 42.15
TEST_PERCENTAGE_DIFF = 9.68

# Test email recipients
TEST_RECIPIENTS = ["recipient1@example.com", "recipient2@example.com"]

# Test error messages
TEST_ERROR_MESSAGES = {
    "api_error": "Test API error message",
    "network_error": "Test network error message",
    "rate_limit_error": "Test rate limit error message",
    "validation_error": "Test validation error message"
}
