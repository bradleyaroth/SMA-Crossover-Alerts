"""
Alpha Vantage API endpoint definitions and URL builders.

This module contains endpoint configurations and URL building utilities
for the Alpha Vantage API with parameter validation and error handling.
"""

from typing import Dict, Any, Optional
from urllib.parse import urlencode
from ..utils.exceptions import DataValidationError


class EndpointConfig:
    """Configuration for a specific API endpoint."""
    
    def __init__(self, function: str, required_params: list, optional_params: dict):
        """
        Initialize endpoint configuration.
        
        Args:
            function: API function name
            required_params: List of required parameter names
            optional_params: Dict of optional parameters with default values
        """
        self.function = function
        self.required_params = required_params
        self.optional_params = optional_params
    
    def validate_params(self, params: Dict[str, Any]) -> None:
        """
        Validate parameters for this endpoint.
        
        Args:
            params: Parameters to validate
            
        Raises:
            DataValidationError: If required parameters are missing
        """
        missing_params = [param for param in self.required_params if param not in params]
        if missing_params:
            raise DataValidationError(
                f"Missing required parameters: {', '.join(missing_params)}",
                component="EndpointValidation"
            )


class APIEndpoints:
    """
    Alpha Vantage API endpoint definitions and URL builders with validation.
    """
    
    # Base API URL
    BASE_URL = "https://www.alphavantage.co/query"
    
    # API Functions
    DAILY_PRICES = "TIME_SERIES_DAILY_ADJUSTED"
    
    # Endpoint configurations
    ENDPOINTS = {
        'daily_prices': EndpointConfig(
            function=DAILY_PRICES,
            required_params=['symbol', 'apikey'],
            optional_params={'outputsize': 'full'}  # Changed default to 'full' for historical data
        )
    }
    
    @classmethod
    def build_daily_prices_url(cls, symbol: str, api_key: str, output_size: str = "full") -> str:
        """
        Build URL for Alpha Vantage Daily Adjusted Time Series endpoint.
        
        Args:
            symbol: Stock symbol (e.g., 'IBM', 'TQQQ')
            api_key: Alpha Vantage API key
            output_size: Output size ('compact' or 'full')
            
        Returns:
            Complete URL for TIME_SERIES_DAILY_ADJUSTED API call
            
        Raises:
            DataValidationError: If parameters are invalid
        """
        # Validate symbol
        if not symbol or not symbol.strip():
            raise DataValidationError("Symbol cannot be empty", field_name="symbol")
        
        # Validate API key
        if not api_key or not api_key.strip():
            raise DataValidationError("API key cannot be empty", field_name="apikey")
        
        # Validate output size
        valid_sizes = ['compact', 'full']
        if output_size not in valid_sizes:
            raise DataValidationError(
                f"Output size must be one of: {', '.join(valid_sizes)}",
                field_name="outputsize",
                invalid_value=output_size
            )
        
        params = {
            'function': cls.DAILY_PRICES,
            'symbol': symbol.strip().upper(),
            'outputsize': output_size,
            'apikey': api_key.strip()
        }
        
        # Validate using endpoint configuration
        endpoint_config = cls.ENDPOINTS['daily_prices']
        endpoint_config.validate_params(params)
        
        return cls._build_url(params)
    
    
    @classmethod
    def _build_url(cls, params: Dict[str, Any]) -> str:
        """
        Build complete URL from parameters.
        
        Args:
            params: Dictionary of URL parameters
            
        Returns:
            Complete URL string
        """
        param_string = "&".join([f"{key}={value}" for key, value in params.items()])
        return f"{cls.BASE_URL}?{param_string}"