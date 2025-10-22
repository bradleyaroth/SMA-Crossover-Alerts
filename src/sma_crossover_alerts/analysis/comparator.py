"""
Price comparison module for multi-ticker investment strategy analysis.

This module handles the comparison logic for SPY-based TQQQ investment strategy
with QQQ bubble protection monitoring.
"""

from typing import Dict, Any, Optional, Tuple
import logging
from datetime import datetime
from ..utils.exceptions import DataValidationError, TQQQAnalyzerError, EnhancedTQQQAnalysisError
from ..utils.logging import get_logger, ErrorLogger
from ..utils.error_handler import ErrorHandler

logger = logging.getLogger(__name__)


class InvestmentRecommendation:
    """Investment recommendation constants."""
    BUY_HOLD_TQQQ = "BUY/HOLD TQQQ"
    SELL_DCA_QQQ = "SELL TQQQ, DCA INTO QQQ"
    DELEVERAGE_QQQ = "DELEVERAGE TO QQQ"
    EXIT_TO_CASH = "EXIT TO CASH"
    MAINTAIN_POSITION = "MAINTAIN CURRENT POSITION"


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


class MultiTickerAnalyzer:
    """
    Multi-ticker investment strategy analyzer.
    
    Implements SPY-based buy/sell signals with QQQ bubble protection.
    """
    
    def __init__(self, thresholds: Optional[Dict[str, float]] = None):
        """
        Initialize the multi-ticker analyzer.
        
        Args:
            thresholds: Dictionary of threshold values (optional)
        """
        self.logger = get_logger(__name__)
        self.error_logger = ErrorLogger("multi_ticker_analyzer")
        self.error_handler = ErrorHandler("multi_ticker_analyzer")
        
        # Set default thresholds if not provided
        self.thresholds = thresholds or {
            'spy_buy': 4.0,
            'spy_sell': -3.0,
            'qqq_warning': 30.0,
            'qqq_danger': 40.0
        }
    
    def analyze_multi_ticker(
        self,
        spy_data: Dict[str, Any],
        qqq_data: Dict[str, Any],
        tqqq_data: Optional[Dict[str, Any]] = None,
        date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform complete multi-ticker analysis.
        
        Args:
            spy_data: SPY price and SMA data {'price': float, 'sma': float}
            qqq_data: QQQ price and SMA data {'price': float, 'sma': float}
            tqqq_data: Optional TQQQ price and SMA data for reference
            date: Analysis date
            
        Returns:
            dict: Complete analysis with recommendation
        """
        try:
            if date is None:
                date = datetime.now().strftime('%Y-%m-%d')
            
            # Calculate percentage differences
            spy_pct = self._calculate_percentage_diff(spy_data['price'], spy_data['sma'])
            qqq_pct = self._calculate_percentage_diff(qqq_data['price'], qqq_data['sma'])
            
            # Determine investment recommendation
            recommendation, priority, explanation = self._determine_recommendation(spy_pct, qqq_pct)
            
            # Check if this is a signal crossing event
            signal_event = self._detect_signal_crossing(spy_pct, qqq_pct)
            
            # Build comprehensive result
            result = {
                'date': date,
                'recommendation': recommendation,
                'priority': priority,
                'explanation': explanation,
                'signal_event': signal_event,
                'spy': {
                    'symbol': 'SPY',
                    'price': spy_data['price'],
                    'sma': spy_data['sma'],
                    'percentage_diff': round(spy_pct, 2),
                    'status': self._get_spy_status(spy_pct),
                    'color': self._get_spy_color(spy_pct)
                },
                'qqq': {
                    'symbol': 'QQQ',
                    'price': qqq_data['price'],
                    'sma': qqq_data['sma'],
                    'percentage_diff': round(qqq_pct, 2),
                    'status': self._get_qqq_status(qqq_pct),
                    'color': self._get_qqq_color(qqq_pct)
                }
            }
            
            # Add TQQQ data if provided
            if tqqq_data:
                tqqq_pct = self._calculate_percentage_diff(tqqq_data['price'], tqqq_data['sma'])
                result['tqqq'] = {
                    'symbol': 'TQQQ',
                    'price': tqqq_data['price'],
                    'sma': tqqq_data['sma'],
                    'percentage_diff': round(tqqq_pct, 2)
                }
            
            self.logger.info(
                f"Multi-ticker analysis complete: {recommendation} | "
                f"SPY: {spy_pct:+.2f}% | QQQ: {qqq_pct:+.2f}%"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Multi-ticker analysis failed: {str(e)}")
            raise TQQQAnalyzerError(
                f"Failed to perform multi-ticker analysis: {str(e)}",
                component="MultiTickerAnalyzer"
            ) from e
    
    def _calculate_percentage_diff(self, price: float, sma: float) -> float:
        """Calculate percentage difference from SMA."""
        if sma == 0:
            raise DataValidationError(
                "SMA value cannot be zero",
                field_name="sma",
                invalid_value="0",
                component="MultiTickerAnalyzer"
            )
        return ((price - sma) / sma) * 100
    
    def _determine_recommendation(
        self,
        spy_pct: float,
        qqq_pct: float
    ) -> Tuple[str, int, str]:
        """
        Determine investment recommendation based on priority logic.
        
        Returns:
            tuple: (recommendation, priority_level, explanation)
        """
        # Priority 1: QQQ Danger Level (40%+)
        if qqq_pct >= self.thresholds['qqq_danger']:
            return (
                InvestmentRecommendation.EXIT_TO_CASH,
                1,
                f"QQQ is {qqq_pct:.2f}% above its 200-day SMA, exceeding the {self.thresholds['qqq_danger']:.0f}% danger threshold. "
                "This indicates extreme bubble conditions. Exit all positions to cash immediately."
            )
        
        # Priority 2: QQQ Warning Level (30-40%)
        if qqq_pct >= self.thresholds['qqq_warning']:
            return (
                InvestmentRecommendation.DELEVERAGE_QQQ,
                2,
                f"QQQ is {qqq_pct:.2f}% above its 200-day SMA, exceeding the {self.thresholds['qqq_warning']:.0f}% warning threshold. "
                "This indicates elevated bubble risk. Deleverage from TQQQ to QQQ for safety."
            )
        
        # Priority 3: SPY Sell Signal (below -3%)
        if spy_pct <= self.thresholds['spy_sell']:
            return (
                InvestmentRecommendation.SELL_DCA_QQQ,
                3,
                f"SPY is {spy_pct:.2f}% below its 200-day SMA, triggering the {self.thresholds['spy_sell']:.0f}% sell threshold. "
                "Sell TQQQ and dollar-cost average into QQQ over the next 6-12 months."
            )
        
        # Priority 4: SPY Buy Signal (above +4%)
        if spy_pct >= self.thresholds['spy_buy']:
            return (
                InvestmentRecommendation.BUY_HOLD_TQQQ,
                4,
                f"SPY is {spy_pct:.2f}% above its 200-day SMA, exceeding the {self.thresholds['spy_buy']:.0f}% buy threshold. "
                f"QQQ is at {qqq_pct:.2f}% (below {self.thresholds['qqq_warning']:.0f}% warning level). "
                "Market conditions are favorable for holding TQQQ."
            )
        
        # Default: Neutral Zone
        return (
            InvestmentRecommendation.MAINTAIN_POSITION,
            5,
            f"SPY is at {spy_pct:.2f}% (between {self.thresholds['spy_sell']:.0f}% and {self.thresholds['spy_buy']:.0f}% thresholds). "
            f"QQQ is at {qqq_pct:.2f}% (below {self.thresholds['qqq_warning']:.0f}% warning level). "
            "No action required. Maintain current position."
        )
    
    def _detect_signal_crossing(self, spy_pct: float, qqq_pct: float) -> Optional[str]:
        """
        Detect if we're at or near a threshold crossing.
        
        Returns:
            str: Signal event description or None
        """
        # Check for threshold crossings (within 0.5% of threshold)
        tolerance = 0.5
        
        if abs(qqq_pct - self.thresholds['qqq_danger']) <= tolerance:
            return f"⚠️ QQQ APPROACHING {self.thresholds['qqq_danger']:.0f}% DANGER LEVEL"
        
        if abs(qqq_pct - self.thresholds['qqq_warning']) <= tolerance:
            return f"⚠️ QQQ APPROACHING {self.thresholds['qqq_warning']:.0f}% WARNING LEVEL"
        
        if abs(spy_pct - self.thresholds['spy_buy']) <= tolerance:
            return f"📈 SPY NEAR {self.thresholds['spy_buy']:.0f}% BUY THRESHOLD"
        
        if abs(spy_pct - self.thresholds['spy_sell']) <= tolerance:
            return f"📉 SPY NEAR {self.thresholds['spy_sell']:.0f}% SELL THRESHOLD"
        
        return None
    
    def _get_spy_status(self, spy_pct: float) -> str:
        """Get SPY status description."""
        if spy_pct >= self.thresholds['spy_buy']:
            return f"ABOVE BUY THRESHOLD (+{self.thresholds['spy_buy']:.0f}%)"
        elif spy_pct <= self.thresholds['spy_sell']:
            return f"BELOW SELL THRESHOLD ({self.thresholds['spy_sell']:.0f}%)"
        else:
            return "IN NEUTRAL ZONE"
    
    def _get_spy_color(self, spy_pct: float) -> str:
        """Get color indicator for SPY."""
        if spy_pct >= self.thresholds['spy_buy']:
            return "green"
        elif spy_pct <= self.thresholds['spy_sell']:
            return "red"
        else:
            return "yellow"
    
    def _get_qqq_status(self, qqq_pct: float) -> str:
        """Get QQQ status description."""
        if qqq_pct >= self.thresholds['qqq_danger']:
            return f"DANGER ZONE (>{self.thresholds['qqq_danger']:.0f}%)"
        elif qqq_pct >= self.thresholds['qqq_warning']:
            return f"WARNING ZONE ({self.thresholds['qqq_warning']:.0f}-{self.thresholds['qqq_danger']:.0f}%)"
        else:
            return "SAFE ZONE"
    
    def _get_qqq_color(self, qqq_pct: float) -> str:
        """Get color indicator for QQQ."""
        if qqq_pct >= self.thresholds['qqq_danger']:
            return "red"
        elif qqq_pct >= self.thresholds['qqq_warning']:
            return "orange"
        else:
            return "green"