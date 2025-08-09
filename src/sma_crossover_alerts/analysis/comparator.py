"""
Price comparison module for TQQQ stock analysis.

This module handles the comparison logic between current stock price
and the 200-day Simple Moving Average, providing analysis results.
"""

from typing import Dict, Any
import logging
from ..utils.exceptions import DataValidationError, TQQQAnalyzerError, EnhancedTQQQAnalysisError
from ..utils.logging import get_logger, ErrorLogger
from ..utils.error_handler import ErrorHandler

logger = logging.getLogger(__name__)


class PriceComparator:
    """
    Compares stock prices against Simple Moving Average.
    
    This class implements the core analysis logic for comparing
    current TQQQ price against its 200-day SMA.
    """
    
    def __init__(self):
        """Initialize the price comparator."""
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def analyze_price_vs_sma(self, current_price: float, sma_value: float) -> Dict[str, Any]:
        """
        Analyze current price against 200-day SMA.
        
        Args:
            current_price: Current stock price
            sma_value: 200-day Simple Moving Average value
            
        Returns:
            dict: Analysis results with status and percentage difference
        """
        # Calculate percentage difference
        percentage_diff = ((current_price - sma_value) / sma_value) * 100
        
        # Determine status (above or below)
        status = "above" if current_price > sma_value else "below"
        
        # Determine signal strength based on percentage difference
        abs_diff = abs(percentage_diff)
        if abs_diff > 10:
            signal_strength = "strong"
        elif abs_diff > 5:
            signal_strength = "moderate"
        else:
            signal_strength = "weak"
        
        # Create analysis result
        result = {
            'status': status,
            'percentage_difference': round(percentage_diff, 2),
            'signal_strength': signal_strength,
            'current_price': current_price,
            'sma_value': sma_value,
            'absolute_difference': round(abs(current_price - sma_value), 2)
        }
        
        self.logger.info(
            f"Analysis complete: Price ${current_price:.2f} is {abs(percentage_diff):.2f}% "
            f"{status} SMA ${sma_value:.2f} ({signal_strength} signal)"
        )
        
        return result
    
    def generate_recommendation(self, analysis_result: Dict[str, Any]) -> str:
        """
        Generate trading recommendation based on analysis.
        
        Args:
            analysis_result: Result from analyze_price_vs_sma method
            
        Returns:
            str: Trading recommendation text
        """
        status = analysis_result['status']
        signal_strength = analysis_result['signal_strength']
        percentage_diff = abs(analysis_result['percentage_difference'])
        
        if status == "above":
            if signal_strength == "strong":
                recommendation = (
                    f"BULLISH SIGNAL: Price is {percentage_diff:.2f}% above 200-day SMA. "
                    "Strong upward momentum indicated."
                )
            elif signal_strength == "moderate":
                recommendation = (
                    f"POSITIVE SIGNAL: Price is {percentage_diff:.2f}% above 200-day SMA. "
                    "Moderate upward trend."
                )
            else:
                recommendation = (
                    f"NEUTRAL-POSITIVE: Price is {percentage_diff:.2f}% above 200-day SMA. "
                    "Weak signal, monitor for trend confirmation."
                )
        else:  # below
            if signal_strength == "strong":
                recommendation = (
                    f"BEARISH SIGNAL: Price is {percentage_diff:.2f}% below 200-day SMA. "
                    "Strong downward momentum indicated."
                )
            elif signal_strength == "moderate":
                recommendation = (
                    f"NEGATIVE SIGNAL: Price is {percentage_diff:.2f}% below 200-day SMA. "
                    "Moderate downward trend."
                )
            else:
                recommendation = (
                    f"NEUTRAL-NEGATIVE: Price is {percentage_diff:.2f}% below 200-day SMA. "
                    "Weak signal, monitor for trend confirmation."
                )
        
        self.logger.info(f"Generated recommendation: {recommendation}")
        return recommendation


class StockComparator:
    """
    Compares stock prices against Simple Moving Average.
    
    This class implements the core analysis logic for comparing
    current TQQQ price against its 200-day SMA as specified in the
    original requirements.
    """
    
    def __init__(self):
        """Initialize the stock comparator."""
        self.logger = get_logger(__name__)
        self.error_logger = ErrorLogger("stock_comparator")
        self.error_handler = ErrorHandler("stock_comparator")
    
    def compare_price_to_sma(self, closing_price: float, sma_value: float) -> str:
        """
        Compare closing price to SMA value.
        
        Args:
            closing_price: Current stock closing price
            sma_value: 200-day Simple Moving Average value
            
        Returns:
            str: Comparison result - "ABOVE", "BELOW", or "EQUAL"
            
        Raises:
            DataValidationError: If input values are invalid
        """
        # Validate inputs
        if not isinstance(closing_price, (int, float)) or closing_price <= 0:
            raise DataValidationError(
                f"Invalid closing price: {closing_price}",
                field_name="closing_price",
                invalid_value=str(closing_price),
                component="StockComparator"
            )
        
        if not isinstance(sma_value, (int, float)) or sma_value <= 0:
            raise DataValidationError(
                f"Invalid SMA value: {sma_value}",
                field_name="sma_value",
                invalid_value=str(sma_value),
                component="StockComparator"
            )
        
        # Perform comparison with exact logic from requirements
        if closing_price > sma_value:
            result = "ABOVE"
        elif closing_price < sma_value:
            result = "BELOW"
        else:
            result = "EQUAL"  # Edge case: exactly equal
        
        self.logger.debug(
            f"Price comparison: ${closing_price:.2f} vs SMA ${sma_value:.2f} = {result}"
        )
        
        return result
    
    def format_comparison_message(self, comparison_result: str, price: float, sma: float) -> str:
        """
        Generate the exact messages specified in requirements.
        
        Args:
            comparison_result: Result from compare_price_to_sma ("ABOVE", "BELOW", "EQUAL")
            price: Current stock price
            sma: SMA value
            
        Returns:
            str: Formatted comparison message
        """
        if comparison_result == "ABOVE":
            message = "The stock price is above the 200-day moving average."
        elif comparison_result == "BELOW":
            message = "The stock price is below the 200-day moving average."
        else:  # EQUAL
            message = "The stock price equals the 200-day moving average."
        
        self.logger.debug(f"Generated message: {message}")
        return message
    
    def calculate_percentage_difference(self, closing_price: float, sma_value: float) -> float:
        """
        Calculate percentage difference: ((price - sma) / sma) * 100.
        
        Args:
            closing_price: Current stock closing price
            sma_value: 200-day Simple Moving Average value
            
        Returns:
            float: Percentage difference (positive = above SMA, negative = below SMA)
            
        Raises:
            DataValidationError: If SMA value is zero or invalid
        """
        if sma_value == 0:
            raise DataValidationError(
                "SMA value cannot be zero for percentage calculation",
                field_name="sma_value",
                invalid_value="0",
                component="StockComparator"
            )
        
        percentage_diff = ((closing_price - sma_value) / sma_value) * 100
        
        self.logger.debug(
            f"Percentage difference: (${closing_price:.2f} - ${sma_value:.2f}) / ${sma_value:.2f} * 100 = {percentage_diff:.2f}%"
        )
        
        return percentage_diff
    
    def determine_trend_signal(self, closing_price: float, sma_value: float) -> str:
        """
        Determine trend signal based on price vs SMA comparison.
        
        Args:
            closing_price: Current stock closing price
            sma_value: 200-day Simple Moving Average value
            
        Returns:
            str: Trend signal - "BULLISH", "BEARISH", or "NEUTRAL"
        """
        if closing_price > sma_value:
            signal = "BULLISH"
        elif closing_price < sma_value:
            signal = "BEARISH"
        else:
            signal = "NEUTRAL"
        
        self.logger.debug(f"Trend signal: {signal}")
        return signal
    
    def generate_comparison_result(self, closing_price: float, sma_value: float, date: str) -> Dict[str, Any]:
        """
        Generate complete comparison analysis.
        
        Args:
            closing_price: Current stock closing price
            sma_value: 200-day Simple Moving Average value
            date: Analysis date in YYYY-MM-DD format
            
        Returns:
            dict: Comprehensive comparison result
            
        Raises:
            DataValidationError: If input validation fails
            TQQQAnalyzerError: If analysis fails
        """
        try:
            # Validate date format
            if not isinstance(date, str) or len(date) != 10:
                raise DataValidationError(
                    f"Invalid date format: {date}. Expected YYYY-MM-DD",
                    field_name="date",
                    invalid_value=str(date),
                    component="StockComparator"
                )
            
            # Perform core analysis
            comparison = self.compare_price_to_sma(closing_price, sma_value)
            percentage_diff = self.calculate_percentage_difference(closing_price, sma_value)
            trend_signal = self.determine_trend_signal(closing_price, sma_value)
            message = self.format_comparison_message(comparison, closing_price, sma_value)
            
            # Create detailed message
            direction = "above" if percentage_diff >= 0 else "below"
            detailed_message = (
                f"TQQQ closed at ${closing_price:.2f} on {date}, which is "
                f"{abs(percentage_diff):.2f}% {direction} its 200-day SMA of ${sma_value:.2f}."
            )
            
            # Compile comprehensive result
            result = {
                "date": date,
                "closing_price": closing_price,
                "sma_value": sma_value,
                "comparison": comparison,
                "percentage_difference": round(percentage_diff, 2),
                "trend_signal": trend_signal,
                "message": message,
                "detailed_message": detailed_message
            }
            
            self.logger.info(
                f"Comparison analysis complete for {date}: "
                f"Price ${closing_price:.2f} is {comparison} SMA ${sma_value:.2f} "
                f"({percentage_diff:+.2f}%, {trend_signal})"
            )
            
            return result
            
        except DataValidationError:
            # Re-raise validation errors
            raise
        except Exception as e:
            # Wrap unexpected errors
            raise TQQQAnalyzerError(
                f"Failed to generate comparison result: {str(e)}",
                component="StockComparator"
            ) from e
    
    def get_error_messages(self) -> Dict[str, str]:
        """
        Get standard error messages for different scenarios.
        
        Returns:
            dict: Standard error messages
        """
        return {
            "api_failure": "No API data available.",
            "data_error": "Data validation failed - please try again.",
            "network_error": "Network connection failed - please check connectivity.",
            "rate_limit": "API rate limit exceeded - please try again later."
        }