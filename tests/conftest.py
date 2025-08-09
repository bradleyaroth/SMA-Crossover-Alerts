"""
Pytest configuration and shared fixtures for TQQQ Analysis test suite.

This module provides common fixtures, test configuration, and utilities
used across all test modules in the TQQQ analysis application.
"""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List
import aiohttp
from datetime import datetime, timedelta

# Import application modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sma_crossover_alerts.api.client import AlphaVantageClient
from sma_crossover_alerts.analysis.processor import StockDataProcessor
from sma_crossover_alerts.analysis.comparator import StockComparator, PriceComparator
from sma_crossover_alerts.notification.email_sender import EmailSender
from sma_crossover_alerts.notification.templates import EmailTemplates
from sma_crossover_alerts.config.settings import Settings
from sma_crossover_alerts.utils.exceptions import *
from tests.fixtures.mock_data import MockAPIResponses, MockAnalysisData


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "network: mark test as requiring network access"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as a performance test"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test location."""
    for item in items:
        # Add unit marker to tests in unit directory
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        
        # Add integration marker to tests in integration directory
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        
        # Add slow marker to integration tests
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.slow)


# ============================================================================
# EVENT LOOP FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# CONFIGURATION FIXTURES
# ============================================================================

@pytest.fixture
def test_config_dict():
    """Provide test configuration dictionary."""
    return {
        'api': {
            'alpha_vantage_key': 'TEST_API_KEY_123456789',
            'base_url': 'https://www.alphavantage.co/query',
            'timeout': 30,
            'max_retries': 3
        },
        'email': {
            'smtp_server': 'smtp.test.com',
            'smtp_port': 587,
            'username': 'test@example.com',
            'password': 'test_password',
            'use_tls': True,
            'from_address': 'tqqq@example.com',
            'from_name': 'TQQQ Test System',
            'to_addresses': ['recipient1@example.com', 'recipient2@example.com']
        },
        'analysis': {
            'symbol': 'TQQQ',
            'sma_period': 200,
            'max_data_age_days': 5
        },
        'logging': {
            'level': 'INFO',
            'log_file': 'logs/test.log',
            'max_file_size': '10MB',
            'backup_count': 5
        },
        'system': {
            'rate_limit_file': '.test_api_usage',
            'timezone': 'UTC'
        }
    }


@pytest.fixture
def test_config_file(test_config_dict, tmp_path):
    """Create a temporary test configuration file."""
    config_content = """
[api]
alpha_vantage_key = TEST_API_KEY_123456789
base_url = https://www.alphavantage.co/query
timeout = 30
max_retries = 3

[email]
smtp_server = smtp.test.com
smtp_port = 587
username = test@example.com
password = test_password
use_tls = true
from_address = tqqq@example.com
from_name = TQQQ Test System
to_addresses = recipient1@example.com,recipient2@example.com

[analysis]
symbol = TQQQ
sma_period = 200
max_data_age_days = 5

[logging]
level = INFO
log_file = logs/test.log
max_file_size = 10MB
backup_count = 5

[system]
rate_limit_file = .test_api_usage
timezone = UTC
"""
    config_file = tmp_path / "test_config.ini"
    config_file.write_text(config_content)
    return str(config_file)


@pytest.fixture
def test_settings(test_config_file):
    """Provide test Settings instance."""
    return Settings(test_config_file)


# ============================================================================
# API CLIENT FIXTURES
# ============================================================================

@pytest.fixture
def mock_api_client():
    """Provide mock AlphaVantageClient for testing."""
    client = Mock(spec=AlphaVantageClient)
    client.fetch_daily_prices = AsyncMock()
    client.fetch_sma = AsyncMock()
    client.health_check = AsyncMock()
    client.close = AsyncMock()
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)
    return client


@pytest.fixture
def api_client():
    """Provide real AlphaVantageClient for integration tests."""
    return AlphaVantageClient("TEST_API_KEY_123456789", timeout=30)


@pytest.fixture
def mock_aiohttp_session():
    """Provide mock aiohttp session."""
    session = Mock(spec=aiohttp.ClientSession)
    response = Mock()
    response.status = 200
    response.json = AsyncMock()
    response.__aenter__ = AsyncMock(return_value=response)
    response.__aexit__ = AsyncMock(return_value=None)
    session.get = Mock(return_value=response)
    return session, response


# ============================================================================
# DATA PROCESSING FIXTURES
# ============================================================================

@pytest.fixture
def stock_data_processor():
    """Provide StockDataProcessor instance."""
    return StockDataProcessor()


@pytest.fixture
def stock_comparator():
    """Provide StockComparator instance."""
    return StockComparator()


@pytest.fixture
def price_comparator():
    """Provide PriceComparator instance."""
    return PriceComparator()


# ============================================================================
# MOCK DATA FIXTURES
# ============================================================================

@pytest.fixture
def mock_daily_response():
    """Provide mock daily price response."""
    return MockAPIResponses.get_sample_daily_response()


@pytest.fixture
def mock_sma_response():
    """Provide mock SMA response."""
    return MockAPIResponses.get_sample_sma_response()


@pytest.fixture
def mock_error_response():
    """Provide mock error response."""
    return MockAPIResponses.get_error_response()


@pytest.fixture
def mock_rate_limit_response():
    """Provide mock rate limit response."""
    return MockAPIResponses.get_rate_limit_response()


@pytest.fixture
def sample_analysis_result():
    """Provide sample analysis result."""
    return MockAnalysisData.get_sample_analysis_result()


@pytest.fixture
def bearish_analysis_result():
    """Provide bearish analysis result."""
    return MockAnalysisData.get_bearish_analysis_result()


@pytest.fixture
def strong_bullish_result():
    """Provide strong bullish analysis result."""
    return MockAnalysisData.get_strong_bullish_result()


# ============================================================================
# EMAIL FIXTURES
# ============================================================================

@pytest.fixture
def mock_smtp_server():
    """Provide mock SMTP server."""
    with patch('smtplib.SMTP') as mock_smtp:
        server = Mock()
        server.starttls = Mock()
        server.login = Mock()
        server.send_message = Mock()
        server.quit = Mock()
        mock_smtp.return_value = server
        yield server


@pytest.fixture
def email_sender(test_config_dict):
    """Provide EmailSender instance."""
    return EmailSender(test_config_dict['email'])


@pytest.fixture
def email_templates():
    """Provide EmailTemplates instance."""
    return EmailTemplates()


@pytest.fixture
def mock_email_sender():
    """Provide mock EmailSender."""
    sender = Mock(spec=EmailSender)
    sender.send_email = Mock(return_value=True)
    sender.send_analysis_result = Mock(return_value=True)
    sender.send_error_notification = Mock(return_value=True)
    sender.test_connection = Mock(return_value=True)
    return sender


# ============================================================================
# TEMPORARY DIRECTORY FIXTURES
# ============================================================================

@pytest.fixture
def temp_log_dir(tmp_path):
    """Provide temporary log directory."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    return log_dir


@pytest.fixture
def temp_config_dir(tmp_path):
    """Provide temporary config directory."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir


# ============================================================================
# PERFORMANCE TEST FIXTURES
# ============================================================================

@pytest.fixture
def performance_timer():
    """Provide performance timing utility."""
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = datetime.now()
        
        def stop(self):
            self.end_time = datetime.now()
        
        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return (self.end_time - self.start_time).total_seconds()
            return None
    
    return Timer()


# ============================================================================
# INTEGRATION TEST FIXTURES
# ============================================================================

@pytest.fixture
def integration_config():
    """Provide configuration for integration tests."""
    return {
        'use_real_api': os.getenv('USE_REAL_API', 'false').lower() == 'true',
        'use_real_smtp': os.getenv('USE_REAL_SMTP', 'false').lower() == 'true',
        'api_key': os.getenv('ALPHA_VANTAGE_API_KEY', 'TEST_KEY'),
        'smtp_config': {
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.test.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'username': os.getenv('SMTP_USERNAME', 'test@example.com'),
            'password': os.getenv('SMTP_PASSWORD', 'test_password'),
            'use_tls': True,
            'from_address': os.getenv('FROM_ADDRESS', 'tqqq@example.com'),
            'from_name': 'TQQQ Integration Test'
        }
    }


# ============================================================================
# ERROR HANDLING FIXTURES
# ============================================================================

@pytest.fixture
def mock_network_error():
    """Provide mock network error."""
    return NetworkError("Connection timeout", component="API")


@pytest.fixture
def mock_api_error():
    """Provide mock API error."""
    return APIError("Invalid API call", component="API")


@pytest.fixture
def mock_rate_limit_error():
    """Provide mock rate limit error."""
    return RateLimitError("Rate limit exceeded", component="API")


# ============================================================================
# CLEANUP FIXTURES
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup_test_files():
    """Automatically cleanup test files after each test."""
    yield
    
    # Clean up any test files that might have been created
    test_files = [
        'test_config.ini',
        'integration_config.ini',
        '.test_api_usage',
        'test.log'
    ]
    
    for file in test_files:
        if os.path.exists(file):
            try:
                os.remove(file)
            except OSError:
                pass


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def create_mock_response(data: Dict[str, Any], status: int = 200):
    """Create a mock HTTP response."""
    response = Mock()
    response.status = status
    response.json = AsyncMock(return_value=data)
    response.__aenter__ = AsyncMock(return_value=response)
    response.__aexit__ = AsyncMock(return_value=None)
    return response


def assert_analysis_result_valid(result: Dict[str, Any]):
    """Assert that an analysis result has all required fields."""
    required_fields = [
        'analysis_date', 'current_price', 'sma_value', 'status',
        'percentage_difference', 'signal_strength'
    ]
    
    for field in required_fields:
        assert field in result, f"Missing required field: {field}"
    
    assert isinstance(result['current_price'], (int, float))
    assert isinstance(result['sma_value'], (int, float))
    assert result['status'] in ['above', 'below', 'equal']
    assert isinstance(result['percentage_difference'], (int, float))


def assert_email_content_valid(subject: str, body: str):
    """Assert that email content is valid."""
    assert subject is not None and len(subject) > 0
    assert body is not None and len(body) > 0
    assert "TQQQ" in subject or "TQQQ" in body