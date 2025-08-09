"""
Alpha Vantage API client implementation.

This module provides the main client class for interacting with the Alpha Vantage API,
including async HTTP requests, retry logic, error handling, and response parsing.
"""

import aiohttp
import asyncio
import json
import time
from typing import Dict, Any, Optional
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    RetryError
)

from .endpoints import APIEndpoints
from ..utils.exceptions import (
    APIError,
    NetworkError,
    RateLimitError,
    DataValidationError,
    EnhancedTQQQAnalysisError
)
from ..utils.logging import APILogger, ErrorLogger
from ..utils.error_handler import ErrorHandler


class AlphaVantageClient:
    """
    Alpha Vantage API client with async support, retry logic, and comprehensive error handling.
    
    This class handles all HTTP communication with the Alpha Vantage API,
    including rate limiting, error handling, response validation, and session management.
    """
    
    def __init__(self, api_key: str, timeout: int = 30, base_url: Optional[str] = None):
        """
        Initialize the Alpha Vantage client.
        
        Args:
            api_key: Alpha Vantage API key
            timeout: Request timeout in seconds (default: 30)
            base_url: Custom base URL (optional)
            
        Raises:
            DataValidationError: If API key is invalid
        """
        if not api_key or not api_key.strip():
            raise DataValidationError("API key cannot be empty", field_name="api_key")
        
        self.api_key = api_key.strip()
        self.timeout = timeout
        self.base_url = base_url or APIEndpoints.BASE_URL
        self.session: Optional[aiohttp.ClientSession] = None
        self.logger = APILogger("client")
        self.error_logger = ErrorLogger("api_client")
        self.error_handler = ErrorHandler("api_client")
        
        # Request headers
        self.headers = {
            'User-Agent': 'TQQQ-Analysis/1.0.0 (Python/aiohttp)',
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate'
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit with proper cleanup."""
        await self.close()
    
    async def _ensure_session(self) -> None:
        """Ensure aiohttp session is created."""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers=self.headers,
                connector=aiohttp.TCPConnector(limit=10, limit_per_host=5)
            )
    
    async def close(self) -> None:
        """Close the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None
    
    async def fetch_daily_prices(self, symbol: str, output_size: str = "full") -> Dict[str, Any]:
        """
        Fetch daily price data for a symbol.
        
        Args:
            symbol: Stock symbol (e.g., 'TQQQ')
            output_size: Output size ('compact' or 'full') - defaults to 'full' for historical data
            
        Returns:
            Dict containing daily price data
            
        Raises:
            APIError: If API request fails
            NetworkError: If network request fails
            RateLimitError: If rate limit is exceeded
            DataValidationError: If response data is invalid
        """
        url = APIEndpoints.build_daily_prices_url(symbol, self.api_key, output_size)
        response_data = await self._make_request(url)
        
        # Validate response structure
        self._validate_daily_prices_response(response_data)
        
        return response_data
    
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        retry=retry_if_exception_type((NetworkError, aiohttp.ClientError, asyncio.TimeoutError)),
        reraise=True
    )
    async def _make_request(self, url: str) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic and comprehensive error handling.
        
        Args:
            url: Request URL
            
        Returns:
            Parsed JSON response
            
        Raises:
            APIError: If API returns an error
            NetworkError: If network request fails
            RateLimitError: If rate limit is exceeded
            DataValidationError: If response cannot be parsed
        """
        await self._ensure_session()
        
        if self.session is None:
            raise NetworkError("Failed to create HTTP session")
        
        start_time = time.time()
        
        # Log request
        self.logger.log_request("GET", url, headers=self.headers)
        
        try:
            async with self.session.get(url) as response:
                response_time = time.time() - start_time
                response_size = response.headers.get('Content-Length')
                
                # Handle rate limiting
                if response.status == 429:
                    retry_after = response.headers.get('Retry-After')
                    retry_after_int = int(retry_after) if retry_after else None
                    self.logger.log_rate_limit(retry_after_int)
                    raise RateLimitError(retry_after=retry_after_int)
                
                # Handle other HTTP errors
                if response.status >= 400:
                    error_text = await response.text()
                    self.logger.log_response(
                        response.status, 
                        response_time, 
                        int(response_size) if response_size else None,
                        error_text
                    )
                    
                    if response.status >= 500:
                        # Server errors should be retried
                        raise NetworkError(
                            f"Server error: HTTP {response.status}",
                            original_error=aiohttp.ClientResponseError(
                                request_info=response.request_info,
                                history=response.history,
                                status=response.status
                            )
                        )
                    else:
                        # Client errors should not be retried
                        raise APIError(
                            f"API error: HTTP {response.status}",
                            status_code=response.status,
                            response_data=error_text
                        )
                
                # Parse JSON response
                response_text = ""
                try:
                    response_text = await response.text()
                    response_data = json.loads(response_text)
                    
                    # Log successful response
                    self.logger.log_response(
                        response.status,
                        response_time,
                        len(response_text)
                    )
                    
                    # Check for API-level errors in response
                    self._check_api_errors(response_data)
                    
                    return response_data
                    
                except json.JSONDecodeError as e:
                    self.logger.log_response(
                        response.status,
                        response_time,
                        len(response_text) if response_text else None,
                        f"JSON decode error: {str(e)}"
                    )
                    raise DataValidationError(
                        f"Invalid JSON response: {str(e)}",
                        component="ResponseParser"
                    )
        
        except aiohttp.ClientError as e:
            response_time = time.time() - start_time
            self.logger.log_network_error(e, url)
            
            # Create enhanced network error with context
            context = {
                "url": url,
                "response_time": response_time,
                "timeout": self.timeout,
                "client_error_type": type(e).__name__
            }
            
            network_error = NetworkError(f"Network request failed: {str(e)}", original_error=e)
            self.error_logger.log_error_with_context(network_error, "APIClient", context)
            
            # Create enhanced error for better handling
            enhanced_error = self.error_handler.create_enhanced_error(network_error, context)
            raise enhanced_error
        
        except asyncio.TimeoutError as e:
            response_time = time.time() - start_time
            self.logger.log_network_error(e, url)
            
            # Create enhanced timeout error with context
            context = {
                "url": url,
                "response_time": response_time,
                "timeout": self.timeout,
                "error_type": "timeout"
            }
            
            timeout_error = NetworkError(f"Request timeout after {self.timeout}s", original_error=e)
            self.error_logger.log_error_with_context(timeout_error, "APIClient", context)
            
            # Create enhanced error for better handling
            enhanced_error = self.error_handler.create_enhanced_error(timeout_error, context)
            raise enhanced_error
    
    def _check_api_errors(self, response_data: Dict[str, Any]) -> None:
        """
        Check for API-level errors in response data.
        
        Args:
            response_data: Parsed response data
            
        Raises:
            APIError: If API returns an error
            RateLimitError: If rate limit is exceeded
        """
        # Check for error message
        if 'Error Message' in response_data:
            error_msg = response_data['Error Message']
            context = {
                "api_error_message": error_msg,
                "response_data": str(response_data)[:500]  # Limit size
            }
            
            api_error = APIError(f"API Error: {error_msg}", response_data=str(response_data))
            self.error_logger.log_error_with_context(api_error, "APIClient", context)
            
            # Use standard error message
            standard_message = self.error_handler.get_standard_error_message("API_ERROR")
            enhanced_error = self.error_handler.create_enhanced_error(api_error, context)
            raise enhanced_error
        
        # Check for information/note messages that might indicate errors
        if 'Information' in response_data:
            info_msg = response_data['Information']
            context = {
                "api_info_message": info_msg,
                "response_data": str(response_data)[:500]
            }
            
            if 'rate limit' in info_msg.lower() or 'call frequency' in info_msg.lower():
                rate_limit_error = RateLimitError(f"Rate limit exceeded: {info_msg}")
                self.error_logger.log_error_with_context(rate_limit_error, "APIClient", context)
                enhanced_error = self.error_handler.create_enhanced_error(rate_limit_error, context)
                raise enhanced_error
            else:
                api_error = APIError(f"API Information: {info_msg}", response_data=str(response_data))
                self.error_logger.log_error_with_context(api_error, "APIClient", context)
                enhanced_error = self.error_handler.create_enhanced_error(api_error, context)
                raise enhanced_error
        
        # Check for note messages
        if 'Note' in response_data:
            note_msg = response_data['Note']
            context = {
                "api_note_message": note_msg,
                "response_data": str(response_data)[:500]
            }
            
            if 'rate limit' in note_msg.lower() or 'call frequency' in note_msg.lower():
                rate_limit_error = RateLimitError(f"Rate limit exceeded: {note_msg}")
                self.error_logger.log_error_with_context(rate_limit_error, "APIClient", context)
                enhanced_error = self.error_handler.create_enhanced_error(rate_limit_error, context)
                raise enhanced_error
    
    def _validate_daily_prices_response(self, response_data: Dict[str, Any]) -> None:
        """
        Validate daily prices response structure.
        
        Args:
            response_data: Response data to validate
            
        Raises:
            DataValidationError: If response structure is invalid
        """
        required_keys = ['Meta Data', 'Time Series (Daily)']
        missing_keys = [key for key in required_keys if key not in response_data]
        
        if missing_keys:
            raise DataValidationError(
                f"Missing required keys in daily prices response: {', '.join(missing_keys)}",
                component="ResponseValidator"
            )
        
        # Validate that we have actual data
        time_series = response_data['Time Series (Daily)']
        if not time_series:
            raise DataValidationError(
                "Empty time series data in daily prices response",
                component="ResponseValidator"
            )
    
    
    async def health_check(self) -> bool:
        """
        Perform a health check by making a simple API request.
        
        Returns:
            True if API is accessible, False otherwise
        """
        try:
            # Make a simple request to check API availability
            await self.fetch_daily_prices("AAPL", "compact")
            return True
        except Exception as e:
            self.logger.logger.error(f"Health check failed: {str(e)}")
            return False
    
    def get_rate_limit_info(self) -> Dict[str, Any]:
        """
        Get rate limit information.
        
        Returns:
            Dict with rate limit information
        """
        return {
            "daily_limit": 25,
            "current_usage": "Unknown",  # Would need to track this
            "reset_time": "Unknown"      # Would need to track this
        }