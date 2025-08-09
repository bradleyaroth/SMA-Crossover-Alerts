"""
Unit tests for analysis module.

Tests for data processors, stock comparators, and analysis logic.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from typing import Dict, Any

# Import will be available once dependencies are installed
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from sma_crossover_alerts.analysis.processor import StockDataProcessor, DataProcessor
from sma_crossover_alerts.analysis.comparator import StockComparator, PriceComparator
from sma_crossover_alerts.utils.exceptions import DataValidationError, TQQQAnalyzerError
from tests.fixtures.mock_data import MockAPIResponses, MockAnalysisData


class TestDataProcessor:
    """Test cases for DataProcessor."""
    
    def test_initialization(self):
        """Test DataProcessor initialization."""
        processor = DataProcessor()
        assert processor is not None
    
    def test_find_latest_synchronized_date_success(self):
        """Test finding latest synchronized date with matching data."""
        processor = DataProcessor()
        
        price_data = {
            "Time Series (Daily)": {
                "2024-01-15": {"5. adjusted close": "46.23"},
                "2024-01-12": {"5. adjusted close": "45.34"},
                "2024-01-11": {"5. adjusted close": "44.23"}
            }
        }
        
        sma_data = {
            "Technical Analysis: SMA": {
                "2024-01-15": {"SMA": "42.15"},
                "2024-01-12": {"SMA": "42.08"},
                "2024-01-10": {"SMA": "42.01"}  # Different date
            }
        }
        
        result = processor.find_latest_synchronized_date(price_data, sma_data)
        assert result == "2024-01-12"  # Latest common date
    
    def test_find_latest_synchronized_date_no_match(self):
        """Test finding synchronized date with no matching dates."""
        processor = DataProcessor()
        
        price_data = {
            "Time Series (Daily)": {
                "2024-01-15": {"5. adjusted close": "46.23"}
            }
        }
        
        sma_data = {
            "Technical Analysis: SMA": {
                "2024-01-10": {"SMA": "42.15"}
            }
        }
        
        with pytest.raises(DataValidationError) as exc_info:
            processor.find_latest_synchronized_date(price_data, sma_data)
        
        assert "No synchronized dates found" in str(exc_info.value)
    
    def test_extract_latest_values_success(self):
        """Test extracting latest values from synchronized data."""
        processor = DataProcessor()
        
        price_data = {
            "Time Series (Daily)": {
                "2024-01-15": {"5. adjusted close": "46.23"},
                "2024-01-12": {"5. adjusted close": "45.34"}
            }
        }
        
        sma_data = {
            "Technical Analysis: SMA": {
                "2024-01-15": {"SMA": "42.15"},
                "2024-01-12": {"SMA": "42.08"}
            }
        }
        
        date, price, sma = processor.extract_latest_values(price_data, sma_data, "2024-01-15")
        
        assert date == "2024-01-15"
        assert price == 46.23
        assert sma == 42.15
    
    def test_extract_latest_values_missing_date(self):
        """Test extracting values with missing date."""
        processor = DataProcessor()
        
        price_data = {"Time Series (Daily)": {}}
        sma_data = {"Technical Analysis: SMA": {}}
        
        with pytest.raises(DataValidationError) as exc_info:
            processor.extract_latest_values(price_data, sma_data, "2024-01-15")
        
        assert "Date 2024-01-15 not found in price data" in str(exc_info.value)
    
    def test_validate_data_freshness_fresh(self):
        """Test data freshness validation with fresh data."""
        processor = DataProcessor()
        
        today = datetime.now().strftime('%Y-%m-%d')
        result = processor.validate_data_freshness(today, max_age_days=5)
        
        assert result is True
    
    def test_validate_data_freshness_stale(self):
        """Test data freshness validation with stale data."""
        processor = DataProcessor()
        
        old_date = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
        result = processor.validate_data_freshness(old_date, max_age_days=5)
        
        assert result is False
    
    def test_validate_data_freshness_invalid_date(self):
        """Test data freshness validation with invalid date."""
        processor = DataProcessor()
        
        with pytest.raises(DataValidationError) as exc_info:
            processor.validate_data_freshness("invalid-date")
        
        assert "Invalid date format" in str(exc_info.value)


class TestStockDataProcessor:
    """Test cases for StockDataProcessor."""
    
    def test_initialization(self):
        """Test StockDataProcessor initialization."""
        processor = StockDataProcessor()
        assert processor is not None
    
    def test_extract_daily_price_data_success(self, mock_daily_response):
        """Test successful daily price data extraction."""
        processor = StockDataProcessor()
        
        date, price = processor.extract_daily_price_data(mock_daily_response)
        
        assert date == "2024-01-15"
        assert price == 46.23
    
    def test_extract_daily_price_data_missing_meta(self):
        """Test daily price extraction with missing metadata."""
        processor = StockDataProcessor()
        
        invalid_response = {
            "Time Series (Daily)": {
                "2024-01-15": {"5. adjusted close": "46.23"}
            }
        }
        
        with pytest.raises(DataValidationError) as exc_info:
            processor.extract_daily_price_data(invalid_response)
        
        assert "Missing Meta Data" in str(exc_info.value)
    
    def test_extract_daily_price_data_missing_time_series(self):
        """Test daily price extraction with missing time series."""
        processor = StockDataProcessor()
        
        invalid_response = {
            "Meta Data": {
                "3. Last Refreshed": "2024-01-15"
            }
        }
        
        with pytest.raises(DataValidationError) as exc_info:
            processor.extract_daily_price_data(invalid_response)
        
        assert "Missing Time Series data" in str(exc_info.value)
    
    def test_extract_daily_price_data_invalid_price(self):
        """Test daily price extraction with invalid price."""
        processor = StockDataProcessor()
        
        invalid_response = {
            "Meta Data": {
                "3. Last Refreshed": "2024-01-15"
            },
            "Time Series (Daily)": {
                "2024-01-15": {"5. adjusted close": "invalid_price"}
            }
        }
        
        with pytest.raises(DataValidationError) as exc_info:
            processor.extract_daily_price_data(invalid_response)
        
        assert "Invalid price value" in str(exc_info.value)
    
    def test_calculate_sma_success(self):
        """Test successful manual SMA calculation."""
        processor = StockDataProcessor()
        
        # Create test data with 5 days for 3-day SMA
        test_data = {
            "Time Series (Daily)": {
                "2024-01-15": {"5. adjusted close": "46.00"},
                "2024-01-14": {"5. adjusted close": "44.00"},
                "2024-01-13": {"5. adjusted close": "42.00"},
                "2024-01-12": {"5. adjusted close": "40.00"},
                "2024-01-11": {"5. adjusted close": "38.00"}
            }
        }

        date, sma = processor.calculate_sma(test_data, period=3)

        assert date == "2024-01-15"  # Most recent date
        expected_sma = (46.00 + 44.00 + 42.00) / 3  # 44.00
        assert abs(sma - expected_sma) < 0.01
    
    def test_extract_sma_data_missing_meta(self):
        """Test SMA extraction with missing metadata."""
        processor = StockDataProcessor()
        
        invalid_response = {
            "Technical Analysis: SMA": {
                "2024-01-15": {"SMA": "42.15"}
            }
        }
        
        with pytest.raises(DataValidationError) as exc_info:
            processor.extract_sma_data(invalid_response)
        
        assert "Missing Meta Data" in str(exc_info.value)
    
    def test_calculate_sma_missing_time_series(self):
        """Test SMA calculation with missing time series data."""
        processor = StockDataProcessor()

        invalid_response = {
            "Meta Data": {
                "3. Last Refreshed": "2024-01-15"
            }
        }

        with pytest.raises(DataValidationError) as exc_info:
            processor.calculate_sma(invalid_response)

        assert "Missing 'Time Series (Daily)'" in str(exc_info.value)
    
    def test_calculate_sma_invalid_price(self):
        """Test SMA calculation with invalid closing price."""
        processor = StockDataProcessor()

        test_data = {
            "Time Series (Daily)": {
                "2024-01-15": {"5. adjusted close": "invalid_price"},
                "2024-01-14": {"5. adjusted close": "44.00"},
                "2024-01-13": {"5. adjusted close": "42.00"}
            }
        }

        with pytest.raises(DataValidationError) as exc_info:
            processor.calculate_sma(test_data, period=3)

        assert "Invalid closing price" in str(exc_info.value)
    
    def test_validate_price_value_valid(self):
        """Test price validation with valid values."""
        processor = StockDataProcessor()
        
        assert processor.validate_price_value(46.23) is True
        assert processor.validate_price_value(0.01) is True
        assert processor.validate_price_value(1000.0) is True
    
    def test_validate_price_value_invalid(self):
        """Test price validation with invalid values."""
        processor = StockDataProcessor()
        
        assert processor.validate_price_value(0.0) is False
        assert processor.validate_price_value(-10.0) is False
        assert processor.validate_price_value(float('inf')) is False
        assert processor.validate_price_value(float('nan')) is False
    
    def test_validate_sma_value_valid(self):
        """Test SMA validation with valid values."""
        processor = StockDataProcessor()
        
        assert processor.validate_sma_value(42.15) is True
        assert processor.validate_sma_value(0.01) is True
        assert processor.validate_sma_value(500.0) is True
    
    def test_validate_sma_value_invalid(self):
        """Test SMA validation with invalid values."""
        processor = StockDataProcessor()
        
        assert processor.validate_sma_value(0.0) is False
        assert processor.validate_sma_value(-5.0) is False
        assert processor.validate_sma_value(float('inf')) is False
        assert processor.validate_sma_value(float('nan')) is False
    
    def test_extract_date_from_daily_response_success(self, mock_daily_response):
        """Test date extraction from daily response."""
        processor = StockDataProcessor()
        
        date = processor._extract_date_from_daily_response(mock_daily_response)
        assert date == "2024-01-15"
    
    def test_extract_date_from_sma_response_success(self, mock_sma_response):
        """Test date extraction from SMA response."""
        processor = StockDataProcessor()
        
        date = processor._extract_date_from_sma_response(mock_sma_response)
        assert date == "2024-01-15"
    
    def test_validate_date_format_valid(self):
        """Test date format validation with valid dates."""
        processor = StockDataProcessor()
        
        assert processor._validate_date_format("2024-01-15") == "2024-01-15"
        assert processor._validate_date_format("2023-12-31") == "2023-12-31"
    
    def test_validate_date_format_invalid(self):
        """Test date format validation with invalid dates."""
        processor = StockDataProcessor()
        
        with pytest.raises(DataValidationError):
            processor._validate_date_format("invalid-date")
        
        with pytest.raises(DataValidationError):
            processor._validate_date_format("2024/01/15")
        
        with pytest.raises(DataValidationError):
            processor._validate_date_format("15-01-2024")


class TestPriceComparator:
    """Test cases for PriceComparator."""
    
    def test_initialization(self):
        """Test PriceComparator initialization."""
        comparator = PriceComparator()
        assert comparator is not None
    
    def test_analyze_price_vs_sma_above(self):
        """Test price analysis when price is above SMA."""
        comparator = PriceComparator()
        
        result = comparator.analyze_price_vs_sma(88.84, 74.08)
        
        assert result['status'] == 'above'
        assert result['percentage_difference'] > 0
        assert result['signal_strength'] in ['weak', 'moderate', 'strong']
        assert 'absolute_difference' in result
    
    def test_analyze_price_vs_sma_below(self):
        """Test price analysis when price is below SMA."""
        comparator = PriceComparator()
        
        result = comparator.analyze_price_vs_sma(65.50, 74.08)
        
        assert result['status'] == 'below'
        assert result['percentage_difference'] < 0
        assert result['signal_strength'] in ['weak', 'moderate', 'strong']
    
    def test_analyze_price_vs_sma_equal(self):
        """Test price analysis when price equals SMA."""
        comparator = PriceComparator()
        
        result = comparator.analyze_price_vs_sma(74.08, 74.08)
        
        assert result['status'] == 'equal'
        assert result['percentage_difference'] == 0.0
        assert result['signal_strength'] == 'neutral'
    
    def test_generate_recommendation_bullish(self):
        """Test recommendation generation for bullish signal."""
        comparator = PriceComparator()
        
        analysis_result = {
            'status': 'above',
            'percentage_difference': 15.5,
            'signal_strength': 'strong'
        }
        
        recommendation = comparator.generate_recommendation(analysis_result)
        
        assert 'BULLISH' in recommendation or 'POSITIVE' in recommendation
        assert '15.5%' in recommendation
        assert 'above' in recommendation.lower()
    
    def test_generate_recommendation_bearish(self):
        """Test recommendation generation for bearish signal."""
        comparator = PriceComparator()
        
        analysis_result = {
            'status': 'below',
            'percentage_difference': -12.3,
            'signal_strength': 'moderate'
        }
        
        recommendation = comparator.generate_recommendation(analysis_result)
        
        assert 'BEARISH' in recommendation or 'NEGATIVE' in recommendation
        assert '12.3%' in recommendation
        assert 'below' in recommendation.lower()
    
    def test_generate_recommendation_neutral(self):
        """Test recommendation generation for neutral signal."""
        comparator = PriceComparator()
        
        analysis_result = {
            'status': 'equal',
            'percentage_difference': 0.0,
            'signal_strength': 'neutral'
        }
        
        recommendation = comparator.generate_recommendation(analysis_result)
        
        assert 'NEUTRAL' in recommendation
        assert 'equal' in recommendation.lower() or 'at' in recommendation.lower()


class TestStockComparator:
    """Test cases for StockComparator."""
    
    def test_initialization(self):
        """Test StockComparator initialization."""
        comparator = StockComparator()
        assert comparator is not None
    
    def test_compare_price_to_sma_above(self):
        """Test price comparison when above SMA."""
        comparator = StockComparator()
        
        result = comparator.compare_price_to_sma(88.84, 74.08)
        assert result == "ABOVE"
    
    def test_compare_price_to_sma_below(self):
        """Test price comparison when below SMA."""
        comparator = StockComparator()
        
        result = comparator.compare_price_to_sma(65.50, 74.08)
        assert result == "BELOW"
    
    def test_compare_price_to_sma_equal(self):
        """Test price comparison when equal to SMA."""
        comparator = StockComparator()
        
        result = comparator.compare_price_to_sma(74.08, 74.08)
        assert result == "EQUAL"
    
    def test_compare_price_to_sma_invalid_price(self):
        """Test price comparison with invalid price."""
        comparator = StockComparator()
        
        with pytest.raises(DataValidationError):
            comparator.compare_price_to_sma(-10.0, 74.08)
        
        with pytest.raises(DataValidationError):
            comparator.compare_price_to_sma(0.0, 74.08)
    
    def test_compare_price_to_sma_invalid_sma(self):
        """Test price comparison with invalid SMA."""
        comparator = StockComparator()
        
        with pytest.raises(DataValidationError):
            comparator.compare_price_to_sma(88.84, -5.0)
        
        with pytest.raises(DataValidationError):
            comparator.compare_price_to_sma(88.84, 0.0)
    
    def test_format_comparison_message_above(self):
        """Test message formatting for above comparison."""
        comparator = StockComparator()
        
        message = comparator.format_comparison_message("ABOVE", 88.84, 74.08)
        expected = "The stock price is above the 200-day moving average."
        
        assert message == expected
    
    def test_format_comparison_message_below(self):
        """Test message formatting for below comparison."""
        comparator = StockComparator()
        
        message = comparator.format_comparison_message("BELOW", 65.50, 74.08)
        expected = "The stock price is below the 200-day moving average."
        
        assert message == expected
    
    def test_format_comparison_message_equal(self):
        """Test message formatting for equal comparison."""
        comparator = StockComparator()
        
        message = comparator.format_comparison_message("EQUAL", 74.08, 74.08)
        expected = "The stock price equals the 200-day moving average."
        
        assert message == expected
    
    def test_calculate_percentage_difference_above(self):
        """Test percentage calculation when price is above SMA."""
        comparator = StockComparator()
        
        result = comparator.calculate_percentage_difference(88.84, 74.08)
        expected = ((88.84 - 74.08) / 74.08) * 100
        
        assert abs(result - expected) < 0.01
        assert result > 0
    
    def test_calculate_percentage_difference_below(self):
        """Test percentage calculation when price is below SMA."""
        comparator = StockComparator()
        
        result = comparator.calculate_percentage_difference(65.50, 74.08)
        expected = ((65.50 - 74.08) / 74.08) * 100
        
        assert abs(result - expected) < 0.01
        assert result < 0
    
    def test_calculate_percentage_difference_equal(self):
        """Test percentage calculation when price equals SMA."""
        comparator = StockComparator()
        
        result = comparator.calculate_percentage_difference(74.08, 74.08)
        assert result == 0.0
    
    def test_calculate_percentage_difference_zero_sma(self):
        """Test percentage calculation with zero SMA."""
        comparator = StockComparator()
        
        with pytest.raises(DataValidationError):
            comparator.calculate_percentage_difference(88.84, 0.0)
    
    def test_determine_trend_signal_bullish(self):
        """Test trend signal determination for bullish trend."""
        comparator = StockComparator()
        
        signal = comparator.determine_trend_signal(88.84, 74.08)
        assert signal == "BULLISH"
    
    def test_determine_trend_signal_bearish(self):
        """Test trend signal determination for bearish trend."""
        comparator = StockComparator()
        
        signal = comparator.determine_trend_signal(65.50, 74.08)
        assert signal == "BEARISH"
    
    def test_determine_trend_signal_neutral(self):
        """Test trend signal determination for neutral trend."""
        comparator = StockComparator()
        
        signal = comparator.determine_trend_signal(74.08, 74.08)
        assert signal == "NEUTRAL"
    
    def test_generate_comparison_result_complete(self):
        """Test complete comparison result generation."""
        comparator = StockComparator()
        
        result = comparator.generate_comparison_result(88.84, 74.08, "2024-01-15")
        
        # Check all required fields
        required_fields = [
            'date', 'closing_price', 'sma_value', 'comparison',
            'percentage_difference', 'trend_signal', 'message', 'detailed_message'
        ]
        
        for field in required_fields:
            assert field in result
        
        # Check specific values
        assert result['date'] == "2024-01-15"
        assert result['closing_price'] == 88.84
        assert result['sma_value'] == 74.08
        assert result['comparison'] == "ABOVE"
        assert result['trend_signal'] == "BULLISH"
        assert result['percentage_difference'] > 0
    
    def test_generate_comparison_result_invalid_date(self):
        """Test comparison result generation with invalid date."""
        comparator = StockComparator()
        
        with pytest.raises(DataValidationError):
            comparator.generate_comparison_result(88.84, 74.08, "invalid-date")
    
    def test_get_error_messages(self):
        """Test error messages retrieval."""
        comparator = StockComparator()
        
        messages = comparator.get_error_messages()
        
        assert isinstance(messages, dict)
        assert "api_failure" in messages
        assert "data_error" in messages
        assert "network_error" in messages
        assert "rate_limit" in messages
        
        # Check message content
        assert "API data" in messages["api_failure"]
        assert "validation failed" in messages["data_error"]
        assert "Network connection" in messages["network_error"]
        assert "rate limit" in messages["rate_limit"]


if __name__ == "__main__":
    pytest.main([__file__])