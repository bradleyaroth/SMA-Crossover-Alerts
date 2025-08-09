"""
Unit tests for API module.

Tests for Alpha Vantage API client, endpoints, and data models.
"""

import pytest
import asyncio
import aiohttp
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime
import json

# Import will be available once dependencies are installed
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from sma_crossover_alerts.api.client import AlphaVantageClient
from sma_crossover_alerts.api.endpoints import APIEndpoints, EndpointConfig
from sma_crossover_alerts.utils.exceptions import (
    APIError, NetworkError, RateLimitError, DataValidationError
)
from tests.fixtures.mock_data import MockAPIResponses, MockErrorScenarios


class TestEndpointConfig:
    """Test cases for EndpointConfig."""
    
    def test_endpoint_config_initialization(self):
        """Test EndpointConfig initialization."""
        config = EndpointConfig(
            function="TIME_SERIES_DAILY_ADJUSTED_ADJUSTED",
            required_params=["symbol", "apikey"],
            optional_params={"outputsize": "compact"}
        )
        
        assert config.function == "TIME_SERIES_DAILY_ADJUSTED_ADJUSTED"
        assert config.required_params == ["symbol", "apikey"]
        assert config.optional_params == {"outputsize": "compact"}
    
    def test_validate_params_success(self):
        """Test successful parameter validation."""
        config = EndpointConfig(
            function="TIME_SERIES_DAILY_ADJUSTED",
            required_params=["symbol", "apikey"],
            optional_params={"outputsize": "compact"}
        )
        
        params = {"symbol": "TQQQ", "apikey": "test_key", "outputsize": "full"}
        # Should not raise exception
        config.validate_params(params)
    
    def test_validate_params_missing_required(self):
        """Test parameter validation with missing required params."""
        config = EndpointConfig(
            function="TIME_SERIES_DAILY_ADJUSTED",
            required_params=["symbol", "apikey"],
            optional_params={"outputsize": "compact"}
        )
        
        params = {"symbol": "TQQQ"}  # Missing apikey
        
        with pytest.raises(DataValidationError) as exc_info:
            config.validate_params(params)
        
        assert "Missing required parameter: apikey" in str(exc_info.value)
    
    def test_validate_params_empty_required(self):
        """Test parameter validation with empty required params."""
        config = EndpointConfig(
            function="TIME_SERIES_DAILY_ADJUSTED",
            required_params=["symbol", "apikey"],
            optional_params={}
        )
        
        params = {"symbol": "", "apikey": "test_key"}  # Empty symbol
        
        with pytest.raises(DataValidationError) as exc_info:
            config.validate_params(params)
        
        assert "Parameter 'symbol' cannot be empty" in str(exc_info.value)


class TestAPIEndpoints:
    """Test cases for APIEndpoints."""
    
    def test_build_daily_prices_url_default(self):
        """Test daily prices URL building with defaults."""
        url = APIEndpoints.build_daily_prices_url("TQQQ", "test_key")
        
        expected_params = [
            "function=TIME_SERIES_DAILY_ADJUSTED",
            "symbol=TQQQ",
            "apikey=test_key",
            "outputsize=full"
        ]
        
        assert url.startswith("https://www.alphavantage.co/query?")
        for param in expected_params:
            assert param in url
    
    def test_build_daily_prices_url_custom_size(self):
        """Test daily prices URL building with custom output size."""
        url = APIEndpoints.build_daily_prices_url("TQQQ", "test_key", "full")
        
        assert "outputsize=full" in url
        assert "outputsize=compact" not in url
    
    def test_build_daily_prices_url_validation_error(self):
        """Test daily prices URL building with validation error."""
        with pytest.raises(DataValidationError):
            APIEndpoints.build_daily_prices_url("", "test_key")
        
        with pytest.raises(DataValidationError):
            APIEndpoints.build_daily_prices_url("TQQQ", "")
    
    def test_build_daily_prices_url_full_output(self):
        """Test daily prices URL building with full output size."""
        url = APIEndpoints.build_daily_prices_url("TQQQ", "test_key", "full")
        
        expected_params = [
            "function=TIME_SERIES_DAILY_ADJUSTED",
            "symbol=TQQQ",
            "apikey=test_key",
            "outputsize=full"
        ]
        
        assert url.startswith("https://www.alphavantage.co/query?")
        for param in expected_params:
            assert param in url
    
    def test_build_sma_url_custom_params(self):
        """Test SMA URL building with custom parameters."""
        url = APIEndpoints.build_sma_url(
            "TQQQ", "test_key", period=50, interval="weekly", series_type="close"
        )
        
        assert "time_period=50" in url
        assert "interval=weekly" in url
        assert "series_type=close" in url
    
        
        with pytest.raises(DataValidationError):
            APIEndpoints.build_sma_url("TQQQ", "")
        
        with pytest.raises(DataValidationError):
            APIEndpoints.build_sma_url("TQQQ", "test_key", period=0)
    
    def test_build_url_internal(self):
        """Test internal URL building method."""
        params = {
            "function": "TIME_SERIES_DAILY_ADJUSTED",
            "symbol": "TQQQ",
            "apikey": "test_key"
        }
        
        url = APIEndpoints._build_url(params)
        
        assert url.startswith("https://www.alphavantage.co/query?")
        assert "function=TIME_SERIES_DAILY_ADJUSTED" in url
        assert "symbol=TQQQ" in url
        assert "apikey=test_key" in url


class TestAlphaVantageClient:
    """Test cases for AlphaVantageClient."""
    
    def test_client_initialization_valid(self):
        """Test client initialization with valid parameters."""
        client = AlphaVantageClient("test_api_key_123456789")
        
        assert client.api_key == "test_api_key_123456789"
        assert client.timeout == 30  # default
        assert client.base_url == "https://www.alphavantage.co/query"
        assert client.session is None  # Not created yet
    
    def test_client_initialization_custom_params(self):
        """Test client initialization with custom parameters."""
        client = AlphaVantageClient(
            "test_key", 
            timeout=60, 
            base_url="https://custom.api.com"
        )
        
        assert client.api_key == "test_key"
        assert client.timeout == 60
        assert client.base_url == "https://custom.api.com"
    
    def test_client_initialization_invalid_key(self):
        """Test client initialization with invalid API key."""
        with pytest.raises(DataValidationError) as exc_info:
            AlphaVantageClient("")
        
        assert "API key cannot be empty" in str(exc_info.value)
        
        with pytest.raises(DataValidationError) as exc_info:
            AlphaVantageClient("short")
        
        assert "API key must be at least 8 characters" in str(exc_info.value)
    
    def test_client_initialization_invalid_timeout(self):
        """Test client initialization with invalid timeout."""
        with pytest.raises(DataValidationError) as exc_info:
            AlphaVantageClient("test_key_123456789", timeout=0)
        
        assert "Timeout must be positive" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test client as async context manager."""
        client = AlphaVantageClient("test_key_123456789")
        
        async with client as c:
            assert c is client
            assert client.session is not None
            assert isinstance(client.session, aiohttp.ClientSession)
        
        # Session should be closed after context exit
        assert client.session.closed
    
    @pytest.mark.asyncio
    async def test_ensure_session(self):
        """Test session creation."""
        client = AlphaVantageClient("test_key_123456789")
        
        assert client.session is None
        
        await client._ensure_session()
        
        assert client.session is not None
        assert isinstance(client.session, aiohttp.ClientSession)
        
        # Calling again should not create new session
        old_session = client.session
        await client._ensure_session()
        assert client.session is old_session
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_close(self):
        """Test client close method."""
        client = AlphaVantageClient("test_key_123456789")
        
        # Close without session should not error
        await client.close()
        
        # Create session and close
        await client._ensure_session()
        session = client.session
        
        await client.close()
        
        assert session.closed
        assert client.session is None
    
    @pytest.mark.asyncio
    async def test_fetch_daily_prices_success(self, mock_daily_response):
        """Test successful daily prices fetch."""
        client = AlphaVantageClient("test_key_123456789")
        
        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_daily_response
            
            result = await client.fetch_daily_prices("TQQQ")
            
            assert result == mock_daily_response
            mock_request.assert_called_once()
            
            # Verify URL contains correct parameters
            call_args = mock_request.call_args[0][0]
            assert "function=TIME_SERIES_DAILY_ADJUSTED" in call_args
            assert "symbol=TQQQ" in call_args
    
    @pytest.mark.asyncio
    async def test_fetch_daily_prices_validation_error(self):
        """Test daily prices fetch with validation error."""
        client = AlphaVantageClient("test_key_123456789")
        
        with pytest.raises(DataValidationError):
            await client.fetch_daily_prices("")
    
    
    @pytest.mark.asyncio
    async def test_fetch_daily_prices_full_output(self, mock_daily_response):
        """Test daily prices fetch with full output size."""
        client = AlphaVantageClient("test_key_123456789")
        
        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_daily_response
            
            result = await client.fetch_daily_prices("TQQQ", "full")
            
            assert result == mock_daily_response
            mock_request.assert_called_once()
            
            # Verify URL contains correct parameters
            call_args = mock_request.call_args[0][0]
            assert "function=TIME_SERIES_DAILY_ADJUSTED" in call_args
            assert "symbol=TQQQ" in call_args
            assert "outputsize=full" in call_args
    
    @pytest.mark.asyncio
    async def test_make_request_success(self):
        """Test successful HTTP request."""
        client = AlphaVantageClient("test_key_123456789")
        mock_response_data = {"test": "data"}
        
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_response_data)
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = Mock()
        mock_session.get.return_value = mock_response
        
        with patch.object(client, '_ensure_session', new_callable=AsyncMock):
            client.session = mock_session
            
            result = await client._make_request("http://test.com")
            
            assert result == mock_response_data
            mock_session.get.assert_called_once_with("http://test.com")
    
    @pytest.mark.asyncio
    async def test_make_request_http_error(self):
        """Test HTTP request with error status."""
        client = AlphaVantageClient("test_key_123456789")
        
        mock_response = Mock()
        mock_response.status = 500
        mock_response.text = AsyncMock(return_value="Internal Server Error")
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = Mock()
        mock_session.get.return_value = mock_response
        
        with patch.object(client, '_ensure_session', new_callable=AsyncMock):
            client.session = mock_session
            
            with pytest.raises(APIError) as exc_info:
                await client._make_request("http://test.com")
            
            assert "HTTP 500" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_make_request_timeout(self):
        """Test HTTP request timeout."""
        client = AlphaVantageClient("test_key_123456789")
        
        mock_session = Mock()
        mock_session.get.side_effect = asyncio.TimeoutError()
        
        with patch.object(client, '_ensure_session', new_callable=AsyncMock):
            client.session = mock_session
            
            with pytest.raises(NetworkError) as exc_info:
                await client._make_request("http://test.com")
            
            assert "Request timeout" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_make_request_connection_error(self):
        """Test HTTP request connection error."""
        client = AlphaVantageClient("test_key_123456789")
        
        mock_session = Mock()
        mock_session.get.side_effect = aiohttp.ClientConnectorError(
            connection_key=Mock(), os_error=OSError("Connection refused")
        )
        
        with patch.object(client, '_ensure_session', new_callable=AsyncMock):
            client.session = mock_session
            
            with pytest.raises(NetworkError) as exc_info:
                await client._make_request("http://test.com")
            
            assert "Connection error" in str(exc_info.value)
    
    def test_check_api_errors_rate_limit(self, mock_rate_limit_response):
        """Test API error checking for rate limit."""
        client = AlphaVantageClient("test_key_123456789")
        
        with pytest.raises(RateLimitError) as exc_info:
            client._check_api_errors(mock_rate_limit_response)
        
        assert "Rate limit exceeded" in str(exc_info.value)
    
    def test_check_api_errors_general_error(self, mock_error_response):
        """Test API error checking for general error."""
        client = AlphaVantageClient("test_key_123456789")
        
        with pytest.raises(APIError) as exc_info:
            client._check_api_errors(mock_error_response)
        
        assert "Invalid API call" in str(exc_info.value)
    
    def test_check_api_errors_no_error(self, mock_daily_response):
        """Test API error checking with valid response."""
        client = AlphaVantageClient("test_key_123456789")
        
        # Should not raise exception
        client._check_api_errors(mock_daily_response)
    
    def test_validate_daily_prices_response_valid(self, mock_daily_response):
        """Test daily prices response validation with valid data."""
        client = AlphaVantageClient("test_key_123456789")
        
        # Should not raise exception
        client._validate_daily_prices_response(mock_daily_response)
    
    def test_validate_daily_prices_response_invalid(self):
        """Test daily prices response validation with invalid data."""
        client = AlphaVantageClient("test_key_123456789")
        
        invalid_response = {"Meta Data": {}}  # Missing Time Series
        
        with pytest.raises(DataValidationError) as exc_info:
            client._validate_daily_prices_response(invalid_response)
        
        assert "Missing Time Series data" in str(exc_info.value)
    
    
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, mock_daily_response):
        """Test successful health check."""
        client = AlphaVantageClient("test_key_123456789")
        
        with patch.object(client, 'fetch_daily_prices', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_daily_response
            
            result = await client.health_check()
            
            assert result is True
            mock_fetch.assert_called_once_with("AAPL", "compact")
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Test health check failure."""
        client = AlphaVantageClient("test_key_123456789")
        
        with patch.object(client, 'fetch_daily_prices', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = APIError("API Error", component="API")
            
            result = await client.health_check()
            
            assert result is False
    
    def test_get_rate_limit_info(self):
        """Test rate limit info retrieval."""
        client = AlphaVantageClient("test_key_123456789")
        
        info = client.get_rate_limit_info()
        
        assert isinstance(info, dict)
        assert "calls_per_minute" in info
        assert "calls_per_day" in info
        assert info["calls_per_minute"] == 5
        assert info["calls_per_day"] == 500


if __name__ == "__main__":
    pytest.main([__file__])