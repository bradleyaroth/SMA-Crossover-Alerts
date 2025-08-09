"""
Data processing module for TQQQ stock analysis.

This module handles data synchronization, validation, and processing
of stock price and SMA data from the Alpha Vantage API.
"""

from datetime import datetime
from typing import Dict, Any, Tuple, Optional
import logging
import re

from ..utils.exceptions import DataValidationError, DataSynchronizationError, EnhancedTQQQAnalysisError
from ..utils.logging import get_logger, ErrorLogger
from ..utils.error_handler import ErrorHandler

logger = logging.getLogger(__name__)


class DataProcessor:
    """
    Processes and synchronizes stock price and SMA data.
    
    This class handles the synchronization of price data and SMA data,
    ensuring that both datasets have matching dates for accurate analysis.
    """
    
    def __init__(self):
        """Initialize the data processor."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.error_logger = ErrorLogger("data_processor")
        self.error_handler = ErrorHandler("data_processor")
    
    def find_latest_synchronized_date(self, price_data: Dict[str, Any], 
                                    sma_data: Dict[str, Any]) -> str:
        """
        Find the most recent date where both price and SMA data exist.
        
        Args:
            price_data: Daily price time series data
            sma_data: SMA time series data
            
        Returns:
            str: Latest synchronized date in YYYY-MM-DD format
            
        Raises:
            ValueError: If no synchronized dates are found
        """
        # Extract time series data
        price_series = price_data.get("Time Series (Daily)", {})
        sma_series = sma_data.get("Technical Analysis: SMA", {})
        
        price_dates = set(price_series.keys())
        sma_dates = set(sma_series.keys())
        
        # Find intersection of dates
        common_dates = price_dates.intersection(sma_dates)
        
        if not common_dates:
            context = {
                "price_dates_count": len(price_dates),
                "sma_dates_count": len(sma_dates),
                "price_date_range": f"{min(price_dates) if price_dates else 'None'} to {max(price_dates) if price_dates else 'None'}",
                "sma_date_range": f"{min(sma_dates) if sma_dates else 'None'} to {max(sma_dates) if sma_dates else 'None'}"
            }
            
            sync_error = DataSynchronizationError(
                "No synchronized dates found between price and SMA data",
                price_dates=list(price_dates),
                sma_dates=list(sma_dates)
            )
            
            self.error_logger.log_error_with_context(sync_error, "DataProcessor", context)
            
            # Create enhanced error with standard message
            enhanced_error = self.error_handler.create_enhanced_error(sync_error, context)
            raise enhanced_error
        
        # Return most recent date
        latest_date = max(common_dates)
        self.logger.info(f"Latest synchronized date found: {latest_date}")
        return latest_date
    
    def extract_latest_values(self, price_data: Dict[str, Any], 
                            sma_data: Dict[str, Any]) -> Tuple[float, float, str]:
        """
        Extract the latest price and SMA values from synchronized data.
        
        Args:
            price_data: Daily price time series data
            sma_data: SMA time series data
            
        Returns:
            Tuple[float, float, str]: (current_price, sma_value, analysis_date)
        """
        # Find latest synchronized date
        latest_date = self.find_latest_synchronized_date(price_data, sma_data)
        
        # Extract price data for the latest date
        price_series = price_data["Time Series (Daily)"]
        latest_price_data = price_series[latest_date]
        current_price = float(latest_price_data["5. adjusted close"])
        
        # Extract SMA data for the latest date
        sma_series = sma_data["Technical Analysis: SMA"]
        latest_sma_data = sma_series[latest_date]
        sma_value = float(latest_sma_data["SMA"])
        
        self.logger.info(f"Extracted values for {latest_date}: Price=${current_price:.2f}, SMA=${sma_value:.2f}")
        
        return current_price, sma_value, latest_date
    
    def validate_data_freshness(self, analysis_date: str, max_age_days: int = 5) -> bool:
        """
        Validate that the analysis data is not too old.
        
        Args:
            analysis_date: Date of the analysis data (YYYY-MM-DD format)
            max_age_days: Maximum allowed age in days
            
        Returns:
            bool: True if data is fresh, False otherwise
        """
        try:
            data_date = datetime.strptime(analysis_date, "%Y-%m-%d")
            current_date = datetime.now()
            age_days = (current_date - data_date).days
            
            is_fresh = age_days <= max_age_days
            
            if not is_fresh:
                self.logger.warning(f"Data is {age_days} days old, exceeds maximum of {max_age_days} days")
            else:
                self.logger.info(f"Data is {age_days} days old, within acceptable range")
                
            return is_fresh
            
        except ValueError as e:
            self.logger.error(f"Invalid date format: {analysis_date}")
            return False


class StockDataProcessor:
    """
    Processes and extracts stock price and SMA data from Alpha Vantage API responses.
    
    This class handles the extraction of closing price and SMA values from the specific
    JSON structures returned by Alpha Vantage API, with comprehensive validation and
    error handling.
    """
    
    def __init__(self):
        """Initialize the stock data processor."""
        self.logger = get_logger(__name__)
        self.error_logger = ErrorLogger("stock_data_processor")
        self.error_handler = ErrorHandler("stock_data_processor")
        self.MIN_PRICE = 0.01
        self.MAX_PRICE = 10000.0
        self.MIN_SMA = 0.01
        self.MAX_SMA = 10000.0
    
    def extract_daily_price_data(self, response: Dict[str, Any]) -> Tuple[str, float]:
        """
        Extract current closing price from Alpha Vantage daily adjusted response.
        
        Args:
            response: Alpha Vantage TIME_SERIES_DAILY_ADJUSTED response
            
        Returns:
            Tuple[str, float]: (date, adjusted_closing_price)
            
        Raises:
            DataValidationError: If response is malformed or data is invalid
        """
        try:
            # Extract date from metadata
            date = self._extract_date_from_daily_response(response)
            self.logger.debug(f"Extracted date from daily response: {date}")
            
            # Extract time series data
            time_series = response.get("Time Series (Daily)")
            if not time_series:
                raise DataValidationError(
                    "Missing 'Time Series (Daily)' key in response",
                    field_name="Time Series (Daily)",
                    component="StockDataProcessor"
                )
            
            # Get data for the extracted date
            daily_data = time_series.get(date)
            if not daily_data:
                raise DataValidationError(
                    f"No data found for date {date} in time series",
                    field_name="Time Series (Daily)",
                    invalid_value=date,
                    component="StockDataProcessor"
                )
            
            # Extract ADJUSTED closing price (CRITICAL CHANGE!)
            adjusted_close_str = daily_data.get("5. adjusted close")
            if adjusted_close_str is None:
                raise DataValidationError(
                    "Missing '5. adjusted close' field in daily data",
                    field_name="5. adjusted close",
                    component="StockDataProcessor"
                )
            
            # Convert to float
            try:
                adjusted_close = float(adjusted_close_str)
            except (ValueError, TypeError) as e:
                raise DataValidationError(
                    f"Invalid adjusted close price value: {adjusted_close_str}",
                    field_name="5. adjusted close",
                    invalid_value=str(adjusted_close_str),
                    component="StockDataProcessor"
                ) from e
            
            # Validate price value
            if not self.validate_price_value(adjusted_close):
                raise DataValidationError(
                    f"Adjusted close price {adjusted_close} is outside valid range ({self.MIN_PRICE}-{self.MAX_PRICE})",
                    field_name="5. adjusted close",
                    invalid_value=str(adjusted_close),
                    component="StockDataProcessor"
                )
            
            self.logger.info(f"Successfully extracted adjusted closing price: ${adjusted_close:.2f} for {date}")
            return date, adjusted_close
            
        except DataValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error extracting daily price data: {str(e)}")
            raise DataValidationError(
                f"Failed to extract daily price data: {str(e)}",
                component="StockDataProcessor"
            ) from e
    
    def calculate_sma(self, daily_data: Dict[str, Any], period: int = 200) -> Tuple[str, float]:
        """
        Calculate Simple Moving Average from daily adjusted price data.
        
        Args:
            daily_data: Alpha Vantage TIME_SERIES_DAILY_ADJUSTED response
            period: Number of days for SMA calculation (default: 200)
            
        Returns:
            Tuple[str, float]: (latest_date, sma_value)
            
        Raises:
            DataValidationError: If insufficient data or invalid format
        """
        try:
            # Extract time series data
            time_series = daily_data.get("Time Series (Daily)")
            if not time_series:
                raise DataValidationError(
                    "Missing 'Time Series (Daily)' key in response",
                    field_name="Time Series (Daily)",
                    component="StockDataProcessor"
                )
            
            # Sort dates in descending order (most recent first)
            sorted_dates = sorted(time_series.keys(), reverse=True)
            
            # Validate sufficient historical data
            if len(sorted_dates) < period:
                raise DataValidationError(
                    f"Insufficient historical data: {len(sorted_dates)} days available, "
                    f"{period} days required for SMA calculation"
                )
            
            # Extract ADJUSTED closing prices for the last {period} days (CRITICAL CHANGE!)
            adjusted_closing_prices = []
            for date in sorted_dates[:period]:
                adjusted_close_str = time_series[date].get("5. adjusted close")
                if not adjusted_close_str:
                    raise DataValidationError(f"Missing adjusted close price for date {date}")
                
                try:
                    adjusted_close = float(adjusted_close_str)
                    if not self.validate_price_value(adjusted_close):
                        raise DataValidationError(f"Invalid adjusted close price: {adjusted_close}")
                    adjusted_closing_prices.append(adjusted_close)
                except ValueError as e:
                    raise DataValidationError(f"Invalid adjusted close price format for {date}: {adjusted_close_str}") from e
            
            # Calculate Simple Moving Average using adjusted prices
            sma_value = sum(adjusted_closing_prices) / period
            latest_date = sorted_dates[0]  # Most recent date
            
            # Validate calculated SMA value
            if not self.validate_sma_value(sma_value):
                raise DataValidationError(
                    f"Calculated SMA value {sma_value} is outside valid range ({self.MIN_SMA}-{self.MAX_SMA})",
                    field_name="calculated_sma",
                    invalid_value=str(sma_value),
                    component="StockDataProcessor"
                )
            
            self.logger.info(f"Calculated {period}-day SMA using adjusted prices: {sma_value:.4f} for date {latest_date}")
            self.logger.debug(f"Used {len(adjusted_closing_prices)} adjusted closing prices for calculation")
            self.logger.debug(f"Price range: ${min(adjusted_closing_prices):.2f} - ${max(adjusted_closing_prices):.2f}")
            
            return latest_date, sma_value
            
        except DataValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error calculating SMA: {str(e)}")
            raise DataValidationError(
                f"Failed to calculate SMA: {str(e)}",
                component="StockDataProcessor"
            ) from e
    
    def validate_price_value(self, price: float) -> bool:
        """
        Validate that a price value is within reasonable bounds.
        
        Args:
            price: Price value to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not isinstance(price, (int, float)):
            self.logger.warning(f"Price value is not numeric: {type(price)}")
            return False
        
        if price <= 0:
            self.logger.warning(f"Price value is not positive: {price}")
            return False
        
        if price < self.MIN_PRICE or price > self.MAX_PRICE:
            self.logger.warning(f"Price value {price} is outside valid range ({self.MIN_PRICE}-{self.MAX_PRICE})")
            return False
        
        return True
    
    def validate_sma_value(self, sma: float) -> bool:
        """
        Validate that an SMA value is within reasonable bounds.
        
        Args:
            sma: SMA value to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not isinstance(sma, (int, float)):
            self.logger.warning(f"SMA value is not numeric: {type(sma)}")
            return False
        
        if sma <= 0:
            self.logger.warning(f"SMA value is not positive: {sma}")
            return False
        
        if sma < self.MIN_SMA or sma > self.MAX_SMA:
            self.logger.warning(f"SMA value {sma} is outside valid range ({self.MIN_SMA}-{self.MAX_SMA})")
            return False
        
        return True
    
    def _extract_date_from_daily_response(self, response: Dict[str, Any]) -> str:
        """
        Extract the last refreshed date from daily prices response.
        
        Args:
            response: Alpha Vantage daily prices response
            
        Returns:
            str: Date in YYYY-MM-DD format
            
        Raises:
            DataValidationError: If date cannot be extracted or is invalid
        """
        try:
            meta_data = response.get("Meta Data")
            if not meta_data:
                raise DataValidationError(
                    "Missing 'Meta Data' section in daily response",
                    field_name="Meta Data",
                    component="StockDataProcessor"
                )
            
            # Extract date using the correct key (note: period, not colon)
            last_refreshed = meta_data.get("3. Last Refreshed")
            if not last_refreshed:
                raise DataValidationError(
                    "Missing '3. Last Refreshed' field in Meta Data",
                    field_name="3. Last Refreshed",
                    component="StockDataProcessor"
                )
            
            # Validate date format
            date = self._validate_date_format(last_refreshed)
            return date
            
        except DataValidationError:
            raise
        except Exception as e:
            raise DataValidationError(
                f"Failed to extract date from daily response: {str(e)}",
                field_name="Meta Data",
                component="StockDataProcessor"
            ) from e
    
    def _extract_date_from_sma_response(self, response: Dict[str, Any]) -> str:
        """
        Extract the last refreshed date from SMA response.
        
        Args:
            response: Alpha Vantage SMA response
            
        Returns:
            str: Date in YYYY-MM-DD format
            
        Raises:
            DataValidationError: If date cannot be extracted or is invalid
        """
        try:
            meta_data = response.get("Meta Data")
            if not meta_data:
                raise DataValidationError(
                    "Missing 'Meta Data' section in SMA response",
                    field_name="Meta Data",
                    component="StockDataProcessor"
                )
            
            # Extract date using the correct key (note: colon, not period)
            last_refreshed = meta_data.get("3: Last Refreshed")
            if not last_refreshed:
                raise DataValidationError(
                    "Missing '3: Last Refreshed' field in Meta Data",
                    field_name="3: Last Refreshed",
                    component="StockDataProcessor"
                )
            
            # Validate date format
            date = self._validate_date_format(last_refreshed)
            return date
            
        except DataValidationError:
            raise
        except Exception as e:
            raise DataValidationError(
                f"Failed to extract date from SMA response: {str(e)}",
                field_name="Meta Data",
                component="StockDataProcessor"
            ) from e
    
    def _validate_date_format(self, date_str: str) -> str:
        """
        Validate and normalize date format.
        
        Args:
            date_str: Date string to validate
            
        Returns:
            str: Validated date in YYYY-MM-DD format
            
        Raises:
            DataValidationError: If date format is invalid
        """
        if not date_str or not isinstance(date_str, str):
            raise DataValidationError(
                f"Invalid date string: {date_str}",
                field_name="date",
                invalid_value=str(date_str),
                component="StockDataProcessor"
            )
        
        # Check if date matches YYYY-MM-DD format
        date_pattern = r'^\d{4}-\d{2}-\d{2}$'
        if not re.match(date_pattern, date_str):
            raise DataValidationError(
                f"Date format must be YYYY-MM-DD, got: {date_str}",
                field_name="date",
                invalid_value=date_str,
                component="StockDataProcessor"
            )
        
        # Validate that it's a real date
        try:
            parsed_date = datetime.strptime(date_str, "%Y-%m-%d")
            
            # Check if date is not in the future
            current_date = datetime.now()
            if parsed_date > current_date:
                raise DataValidationError(
                    f"Date cannot be in the future: {date_str}",
                    field_name="date",
                    invalid_value=date_str,
                    component="StockDataProcessor"
                )
            
            # Check if date is not too old (more than 10 years)
            ten_years_ago = current_date.replace(year=current_date.year - 10)
            if parsed_date < ten_years_ago:
                self.logger.warning(f"Date is more than 10 years old: {date_str}")
            
            return date_str
            
        except ValueError as e:
            raise DataValidationError(
                f"Invalid date value: {date_str}",
                field_name="date",
                invalid_value=date_str,
                component="StockDataProcessor"
            ) from e