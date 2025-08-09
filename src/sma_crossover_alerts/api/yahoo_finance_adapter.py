"""
Yahoo Finance API adapter for TQQQ analysis.

This module provides a Yahoo Finance adapter that mimics the Alpha Vantage API structure,
allowing seamless integration with the existing TQQQ analysis system.
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import asyncio
import time

from ..utils.exceptions import (
    APIError,
    NetworkError,
    DataValidationError,
    EnhancedTQQQAnalysisError
)
from ..utils.logging import APILogger, ErrorLogger
from ..utils.error_handler import ErrorHandler


class YahooFinanceAdapter:
    """
    Yahoo Finance adapter that provides Alpha Vantage compatible interface.
    
    This adapter converts Yahoo Finance data to Alpha Vantage format,
    allowing drop-in replacement without changing existing code.
    """
    
    def __init__(self, timeout: int = 30):
        """
        Initialize the Yahoo Finance adapter.
        
        Args:
            timeout: Request timeout in seconds (default: 30)
        """
        self.timeout = timeout
        self.logger = APILogger("yahoo_finance_adapter")
        self.error_logger = ErrorLogger("yahoo_finance_adapter")
        self.error_handler = ErrorHandler("yahoo_finance_adapter")
        
        # Cache for ticker objects to improve performance
        self._ticker_cache: Dict[str, yf.Ticker] = {}
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def close(self) -> None:
        """Close adapter (no-op for Yahoo Finance)."""
        self._ticker_cache.clear()
    
    def _get_ticker(self, symbol: str) -> yf.Ticker:
        """
        Get or create ticker object with caching.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            yfinance Ticker object
        """
        if symbol not in self._ticker_cache:
            self._ticker_cache[symbol] = yf.Ticker(symbol)
        return self._ticker_cache[symbol]
    
    async def fetch_daily_prices(self, symbol: str, output_size: str = "full") -> Dict[str, Any]:
        """
        Fetch daily price data in Alpha Vantage format.
        
        Args:
            symbol: Stock symbol (e.g., 'TQQQ')
            output_size: Output size ('compact' or 'full') - determines data range
            
        Returns:
            Dict containing daily price data in Alpha Vantage format
            
        Raises:
            APIError: If API request fails
            NetworkError: If network request fails
            DataValidationError: If response data is invalid
        """
        start_time = time.time()
        
        try:
            # Log request
            self.logger.log_request("GET", f"Yahoo Finance API for {symbol}", {})
            
            # Determine date range based on output_size
            if output_size == "compact":
                # Compact: last 100 trading days (roughly 4-5 months)
                period = "6mo"
            else:
                # Full: get enough data for 200+ day SMA (roughly 1 year)
                period = "1y"
            
            # Run in thread pool to avoid blocking
            ticker = self._get_ticker(symbol)
            hist = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: ticker.history(period=period)
            )
            
            response_time = time.time() - start_time
            
            # Validate data
            if hist.empty:
                raise DataValidationError(
                    f"No historical data available for symbol {symbol}",
                    field_name="historical_data",
                    component="YahooFinanceAdapter"
                )
            
            # Convert to Alpha Vantage format
            alpha_vantage_data = self._convert_to_alpha_vantage_format(symbol, hist)
            
            # Log successful response
            self.logger.log_response(200, response_time, len(str(alpha_vantage_data)))
            
            return alpha_vantage_data
            
        except Exception as e:
            response_time = time.time() - start_time
            
            if isinstance(e, (DataValidationError, APIError, NetworkError)):
                # Re-raise our custom exceptions
                raise
            
            # Handle other exceptions
            context = {
                "symbol": symbol,
                "output_size": output_size,
                "response_time": response_time,
                "error_type": type(e).__name__
            }
            
            if "network" in str(e).lower() or "connection" in str(e).lower():
                network_error = NetworkError(f"Yahoo Finance network error: {str(e)}", original_error=e)
                self.error_logger.log_error_with_context(network_error, "YahooFinanceAdapter", context)
                enhanced_error = self.error_handler.create_enhanced_error(network_error, context)
                raise enhanced_error
            else:
                api_error = APIError(f"Yahoo Finance API error: {str(e)}", response_data=str(e))
                self.error_logger.log_error_with_context(api_error, "YahooFinanceAdapter", context)
                enhanced_error = self.error_handler.create_enhanced_error(api_error, context)
                raise enhanced_error
    
    def _convert_to_alpha_vantage_format(self, symbol: str, hist: pd.DataFrame) -> Dict[str, Any]:
        """
        Convert Yahoo Finance data to Alpha Vantage TIME_SERIES_DAILY_ADJUSTED format.
        
        Args:
            symbol: Stock symbol
            hist: Yahoo Finance historical data DataFrame
            
        Returns:
            Dict in Alpha Vantage format
        """
        # Create metadata
        meta_data = {
            "1. Information": "Daily Prices (open, high, low, close) and Volumes",
            "2. Symbol": symbol.upper(),
            "3. Last Refreshed": hist.index[-1].strftime('%Y-%m-%d'),
            "4. Output Size": "Full" if len(hist) > 100 else "Compact",
            "5. Time Zone": "US/Eastern"
        }
        
        # Convert time series data
        time_series = {}
        for date, row in hist.iterrows():
            # Convert date index to string format
            date_str = str(date)[:10]  # Extract YYYY-MM-DD from timestamp
            
            # Yahoo Finance Close prices are already adjusted for splits/dividends
            time_series[date_str] = {
                "1. open": f"{row['Open']:.4f}",
                "2. high": f"{row['High']:.4f}",
                "3. low": f"{row['Low']:.4f}",
                "4. close": f"{row['Close']:.4f}",
                "5. adjusted close": f"{row['Close']:.4f}",  # Already adjusted
                "6. volume": str(int(row['Volume'])),
                "7. dividend amount": f"{row.get('Dividends', 0.0):.4f}",
                "8. split coefficient": "1.0000"  # Would need separate split data
            }
        
        return {
            "Meta Data": meta_data,
            "Time Series (Daily)": time_series
        }
    
    async def health_check(self) -> bool:
        """
        Perform a health check by making a simple API request.
        
        Returns:
            True if API is accessible, False otherwise
        """
        try:
            # Test with a reliable symbol
            await self.fetch_daily_prices("AAPL", "compact")
            return True
        except Exception as e:
            self.logger.logger.error(f"Health check failed: {str(e)}")
            return False
    
    def get_rate_limit_info(self) -> Dict[str, Any]:
        """
        Get rate limit information for Yahoo Finance.
        
        Returns:
            Dict with rate limit information
        """
        return {
            "daily_limit": "Unlimited",
            "current_usage": "N/A",
            "reset_time": "N/A",
            "provider": "Yahoo Finance",
            "notes": "No API key required, generally unlimited for reasonable usage"
        }
    
    def get_provider_info(self) -> Dict[str, Any]:
        """
        Get information about the data provider.
        
        Returns:
            Dict with provider information
        """
        return {
            "provider": "Yahoo Finance",
            "api_key_required": False,
            "cost": "Free",
            "data_quality": "High",
            "real_time": True,
            "adjusted_prices": True,
            "historical_range": "20+ years",
            "update_frequency": "Real-time during market hours"
        }


class YahooFinanceClientFactory:
    """
    Factory class to create Yahoo Finance clients that are compatible with Alpha Vantage clients.
    """
    
    @staticmethod
    def create_client(api_key: Optional[str] = None, timeout: int = 30, 
                     base_url: Optional[str] = None) -> YahooFinanceAdapter:
        """
        Create a Yahoo Finance adapter client.
        
        Args:
            api_key: Not used for Yahoo Finance (kept for compatibility)
            timeout: Request timeout in seconds
            base_url: Not used for Yahoo Finance (kept for compatibility)
            
        Returns:
            YahooFinanceAdapter instance
        """
        # Ignore api_key and base_url for Yahoo Finance
        return YahooFinanceAdapter(timeout=timeout)
    
    @staticmethod
    def is_yahoo_finance_available() -> bool:
        """
        Check if Yahoo Finance is available.
        
        Returns:
            True if yfinance is installed and working
        """
        try:
            import yfinance as yf
            # Quick test
            ticker = yf.Ticker("AAPL")
            info = ticker.info
            return bool(info.get('symbol'))
        except Exception:
            return False


# Compatibility alias for drop-in replacement
AlphaVantageClient = YahooFinanceAdapter