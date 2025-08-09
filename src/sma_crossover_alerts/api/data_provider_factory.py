"""
Data provider factory for switching between Alpha Vantage and Yahoo Finance.

This module provides a factory pattern to create the appropriate data provider
based on configuration, allowing seamless switching between providers.
"""

from typing import Optional, Union
from enum import Enum

from .client import AlphaVantageClient
from .yahoo_finance_adapter import YahooFinanceAdapter, YahooFinanceClientFactory
from ..utils.exceptions import DataValidationError
from ..utils.logging import APILogger


class DataProvider(Enum):
    """Supported data providers."""
    ALPHA_VANTAGE = "alpha_vantage"
    YAHOO_FINANCE = "yahoo_finance"


class DataProviderFactory:
    """
    Factory class for creating data provider clients.
    
    This factory allows switching between different data providers
    (Alpha Vantage, Yahoo Finance) based on configuration.
    """
    
    def __init__(self):
        self.logger = APILogger("data_provider_factory")
    
    def create_client(
        self, 
        provider: Union[DataProvider, str],
        api_key: Optional[str] = None,
        timeout: int = 30,
        base_url: Optional[str] = None
    ) -> Union[AlphaVantageClient, YahooFinanceAdapter]:
        """
        Create a data provider client based on the specified provider.
        
        Args:
            provider: Data provider to use (DataProvider enum or string)
            api_key: API key (required for Alpha Vantage, ignored for Yahoo Finance)
            timeout: Request timeout in seconds
            base_url: Base URL (used for Alpha Vantage, ignored for Yahoo Finance)
            
        Returns:
            Configured data provider client
            
        Raises:
            DataValidationError: If provider is invalid or configuration is missing
        """
        # Convert string to enum if needed
        if isinstance(provider, str):
            try:
                provider = DataProvider(provider.lower())
            except ValueError:
                raise DataValidationError(
                    f"Invalid data provider: {provider}. "
                    f"Supported providers: {[p.value for p in DataProvider]}",
                    field_name="provider"
                )
        
        self.logger.logger.info(f"Creating client for provider: {provider.value}")
        
        if provider == DataProvider.ALPHA_VANTAGE:
            return self._create_alpha_vantage_client(api_key, timeout, base_url)
        elif provider == DataProvider.YAHOO_FINANCE:
            return self._create_yahoo_finance_client(timeout)
        else:
            raise DataValidationError(
                f"Unsupported data provider: {provider}",
                field_name="provider"
            )
    
    def _create_alpha_vantage_client(
        self, 
        api_key: Optional[str], 
        timeout: int, 
        base_url: Optional[str]
    ) -> AlphaVantageClient:
        """Create Alpha Vantage client."""
        if not api_key:
            raise DataValidationError(
                "API key is required for Alpha Vantage provider",
                field_name="api_key"
            )
        
        self.logger.logger.info("Creating Alpha Vantage client")
        return AlphaVantageClient(api_key=api_key, timeout=timeout, base_url=base_url)
    
    def _create_yahoo_finance_client(self, timeout: int) -> YahooFinanceAdapter:
        """Create Yahoo Finance client."""
        if not YahooFinanceClientFactory.is_yahoo_finance_available():
            raise DataValidationError(
                "Yahoo Finance is not available. Please install yfinance: pip install yfinance",
                component="YahooFinanceAdapter"
            )
        
        self.logger.logger.info("Creating Yahoo Finance client")
        return YahooFinanceClientFactory.create_client(timeout=timeout)
    
    def get_available_providers(self) -> list[str]:
        """
        Get list of available data providers.
        
        Returns:
            List of available provider names
        """
        available = []
        
        # Alpha Vantage is always available (just needs API key)
        available.append(DataProvider.ALPHA_VANTAGE.value)
        
        # Check if Yahoo Finance is available
        if YahooFinanceClientFactory.is_yahoo_finance_available():
            available.append(DataProvider.YAHOO_FINANCE.value)
        
        return available
    
    def get_provider_info(self, provider: Union[DataProvider, str]) -> dict:
        """
        Get information about a specific provider.
        
        Args:
            provider: Provider to get info for
            
        Returns:
            Dict with provider information
        """
        if isinstance(provider, str):
            provider = DataProvider(provider.lower())
        
        if provider == DataProvider.ALPHA_VANTAGE:
            return {
                "name": "Alpha Vantage",
                "api_key_required": True,
                "cost": "Free tier available, premium features require subscription",
                "rate_limits": "25 requests per day (free tier)",
                "data_quality": "High",
                "real_time": True,
                "historical_range": "20+ years",
                "adjusted_prices": True,
                "notes": "Premium endpoint TIME_SERIES_DAILY_ADJUSTED requires subscription"
            }
        elif provider == DataProvider.YAHOO_FINANCE:
            return {
                "name": "Yahoo Finance",
                "api_key_required": False,
                "cost": "Free",
                "rate_limits": "Generally unlimited for reasonable usage",
                "data_quality": "High",
                "real_time": True,
                "historical_range": "20+ years",
                "adjusted_prices": True,
                "notes": "No API key required, data automatically adjusted for splits/dividends"
            }
        else:
            return {"error": f"Unknown provider: {provider}"}
    
    def recommend_provider(self, api_key_available: bool = False) -> DataProvider:
        """
        Recommend the best provider based on current conditions.
        
        Args:
            api_key_available: Whether Alpha Vantage API key is available
            
        Returns:
            Recommended provider
        """
        # If Yahoo Finance is available, prefer it (free, no API key needed)
        if YahooFinanceClientFactory.is_yahoo_finance_available():
            self.logger.logger.info("Recommending Yahoo Finance (free, no API key required)")
            return DataProvider.YAHOO_FINANCE
        
        # Fall back to Alpha Vantage if API key is available
        if api_key_available:
            self.logger.logger.info("Recommending Alpha Vantage (API key available)")
            return DataProvider.ALPHA_VANTAGE
        
        # Default to Yahoo Finance even if not confirmed available
        self.logger.logger.warning("No optimal provider found, defaulting to Yahoo Finance")
        return DataProvider.YAHOO_FINANCE


# Convenience function for quick client creation
def create_data_client(
    provider: Union[DataProvider, str] = "yahoo_finance",
    api_key: Optional[str] = None,
    timeout: int = 30,
    base_url: Optional[str] = None
) -> Union[AlphaVantageClient, YahooFinanceAdapter]:
    """
    Convenience function to create a data provider client.
    
    Args:
        provider: Data provider to use (defaults to Yahoo Finance)
        api_key: API key (required for Alpha Vantage)
        timeout: Request timeout in seconds
        base_url: Base URL (for Alpha Vantage)
        
    Returns:
        Configured data provider client
    """
    factory = DataProviderFactory()
    return factory.create_client(provider, api_key, timeout, base_url)