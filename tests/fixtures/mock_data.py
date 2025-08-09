"""
Mock data and sample responses for testing.

This module contains sample API responses, test data, and mock objects
used throughout the test suite.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List


class MockAPIResponses:
    """Mock Alpha Vantage API responses for testing."""
    
    @staticmethod
    def get_sample_daily_response() -> Dict[str, Any]:
        """Get sample daily time series response (now returns adjusted data)."""
        return MockAPIResponses.get_sample_daily_adjusted_response()
    
    @staticmethod
    def get_sample_daily_adjusted_response() -> Dict[str, Any]:
        """
        Get sample Alpha Vantage TIME_SERIES_DAILY_ADJUSTED response.
        
        Returns:
            dict: Sample adjusted daily response
        """
        return {
            "Meta Data": {
                "1. Information": "Daily Time Series with Splits and Dividend Events",
                "2. Symbol": "IBM",
                "3. Last Refreshed": "2025-08-07",
                "4. Output Size": "Full size",
                "5. Time Zone": "US/Eastern"
            },
            "Time Series (Daily)": {
                "2025-08-07": {
                    "1. open": "252.81",
                    "2. high": "255.0",
                    "3. low": "248.875",
                    "4. close": "250.16",
                    "5. adjusted close": "250.16",
                    "6. volume": "6251285",
                    "7. dividend amount": "0.0000",
                    "8. split coefficient": "1.0"
                },
                "2025-08-06": {
                    "1. open": "251.53",
                    "2. high": "254.32",
                    "3. low": "249.28",
                    "4. close": "252.28",
                    "5. adjusted close": "252.28",
                    "6. volume": "3692105",
                    "7. dividend amount": "0.0000",
                    "8. split coefficient": "1.0"
                },
                "2025-08-05": {
                    "1. open": "252.0",
                    "2. high": "252.8",
                    "3. low": "248.995",
                    "4. close": "250.67",
                    "5. adjusted close": "250.67",
                    "6. volume": "5823016",
                    "7. dividend amount": "0.0000",
                    "8. split coefficient": "1.0"
                }
            }
        }
    
    @staticmethod
    def get_full_historical_daily_response() -> Dict[str, Any]:
        """Get full historical daily adjusted response (now returns adjusted data)."""
        return MockAPIResponses.get_full_historical_daily_adjusted_response(250)
    
    @staticmethod
    def get_full_historical_daily_adjusted_response(days: int = 250) -> Dict[str, Any]:
        """
        Generate full historical daily adjusted response with specified number of days.
        
        Args:
            days: Number of historical days to generate (default: 250)
        
        Returns:
            dict: Alpha Vantage TIME_SERIES_DAILY_ADJUSTED response with full historical data
        """
        from datetime import datetime, timedelta
        
        # Start from current date and go backwards
        end_date = datetime.now()
        time_series = {}
        
        # Generate historical data
        base_price = 250.0  # Starting price for IBM-like data
        for i in range(days):
            date = end_date - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            
            # Generate realistic price data with some variation
            price_variation = (i % 10 - 5) * 2.0  # Daily variations
            current_price = base_price + price_variation + (i * 0.05)  # Slight trend
            
            # For adjusted data, close and adjusted close are usually the same unless there are splits/dividends
            adjusted_close = current_price
            regular_close = current_price
            
            time_series[date_str] = {
                "1. open": f"{current_price - 1.0:.2f}",
                "2. high": f"{current_price + 2.0:.2f}",
                "3. low": f"{current_price - 2.0:.2f}",
                "4. close": f"{regular_close:.2f}",
                "5. adjusted close": f"{adjusted_close:.2f}",
                "6. volume": str(1000000 + (i * 1000)),
                "7. dividend amount": "0.0000",
                "8. split coefficient": "1.0"
            }
        
        return {
            "Meta Data": {
                "1. Information": "Daily Time Series with Splits and Dividend Events",
                "2. Symbol": "IBM",
                "3. Last Refreshed": end_date.strftime("%Y-%m-%d"),
                "4. Output Size": "Full size",
                "5. Time Zone": "US/Eastern"
            },
            "Time Series (Daily)": time_series
        }
    
    @staticmethod
    def get_error_response() -> Dict[str, Any]:
        """Get sample error response."""
        return {
            "Error Message": "Invalid API call. Please retry or visit the documentation (https://www.alphavantage.co/documentation/) for TIME_SERIES_DAILY_ADJUSTED."
        }
    
    @staticmethod
    def get_rate_limit_response() -> Dict[str, Any]:
        """Get sample rate limit response."""
        return {
            "Note": "Thank you for using Alpha Vantage! Our standard API call frequency is 5 calls per minute and 500 calls per day."
        }
    
    @staticmethod
    def get_malformed_daily_response() -> Dict[str, Any]:
        """Get malformed daily adjusted response for error testing."""
        return {
            "Meta Data": {
                "1. Information": "Daily Time Series with Splits and Dividend Events",
                "2. Symbol": "IBM"
                # Missing required fields
            },
            "Time Series (Daily)": {
                "2025-08-07": {
                    "1. open": "invalid_number",  # Invalid data
                    "2. high": "255.0",
                    # Missing required fields including adjusted close
                }
            }
        }
    
    @staticmethod
    def get_empty_response() -> Dict[str, Any]:
        """Get empty response for testing."""
        return {}
    
    @staticmethod
    def get_mismatched_dates_responses() -> tuple:
        """Get responses with mismatched dates for testing synchronization."""
        daily_response = {
            "Meta Data": {
                "1. Information": "Daily Time Series with Splits and Dividend Events",
                "2. Symbol": "IBM",
                "3. Last Refreshed": "2025-08-07",
                "4. Output Size": "Full size",
                "5. Time Zone": "US/Eastern"
            },
            "Time Series (Daily)": {
                "2025-08-07": {
                    "1. open": "252.81",
                    "2. high": "255.0",
                    "3. low": "248.875",
                    "4. close": "250.16",
                    "5. adjusted close": "250.16",
                    "6. volume": "6251285",
                    "7. dividend amount": "0.0000",
                    "8. split coefficient": "1.0"
                },
                "2025-08-06": {
                    "1. open": "251.53",
                    "2. high": "254.32",
                    "3. low": "249.28",
                    "4. close": "252.28",
                    "5. adjusted close": "252.28",
                    "6. volume": "3692105",
                    "7. dividend amount": "0.0000",
                    "8. split coefficient": "1.0"
                }
            }
        }
        
        sma_response = {
            "Meta Data": {
                "1: Symbol": "TQQQ",
                "2: Indicator": "Simple Moving Average (SMA)",
                "3: Last Refreshed": "2024-01-10",
                "4: Interval": "daily",
                "5: Time Period": 200,
                "6: Series Type": "open",
                "7: Time Zone": "US/Eastern"
            },
            "Technical Analysis: SMA": {
                "2024-01-10": {"SMA": "41.95"},  # Different dates
                "2024-01-09": {"SMA": "41.88"}
            }
        }
        
        return daily_response, sma_response


class MockAnalysisData:
    """Mock analysis data for testing."""
    
    @staticmethod
    def get_sample_analysis_result() -> Dict[str, Any]:
        """Get sample analysis result."""
        return {
            'analysis_date': '2024-01-15',
            'current_price': 46.23,
            'sma_value': 42.15,
            'status': 'above',
            'percentage_difference': 9.68,
            'signal_strength': 'moderate',
            'absolute_difference': 4.08,
            'recommendation': 'POSITIVE SIGNAL: Price is 9.68% above 200-day SMA. Moderate upward trend.'
        }
    
    @staticmethod
    def get_bearish_analysis_result() -> Dict[str, Any]:
        """Get bearish analysis result."""
        return {
            'analysis_date': '2024-01-15',
            'current_price': 38.50,
            'sma_value': 42.15,
            'status': 'below',
            'percentage_difference': -8.66,
            'signal_strength': 'moderate',
            'absolute_difference': 3.65,
            'recommendation': 'NEGATIVE SIGNAL: Price is 8.66% below 200-day SMA. Moderate downward trend.'
        }
    
    @staticmethod
    def get_strong_bullish_result() -> Dict[str, Any]:
        """Get strong bullish analysis result."""
        return {
            'analysis_date': '2024-01-15',
            'current_price': 50.00,
            'sma_value': 42.15,
            'status': 'above',
            'percentage_difference': 18.63,
            'signal_strength': 'strong',
            'absolute_difference': 7.85,
            'recommendation': 'BULLISH SIGNAL: Price is 18.63% above 200-day SMA. Strong upward momentum indicated.'
        }
    
    @staticmethod
    def get_weak_signal_result() -> Dict[str, Any]:
        """Get weak signal analysis result."""
        return {
            'analysis_date': '2024-01-15',
            'current_price': 43.50,
            'sma_value': 42.15,
            'status': 'above',
            'percentage_difference': 3.20,
            'signal_strength': 'weak',
            'absolute_difference': 1.35,
            'recommendation': 'NEUTRAL-POSITIVE: Price is 3.20% above 200-day SMA. Weak signal, monitor for trend confirmation.'
        }


class MockEmailData:
    """Mock email data for testing."""
    
    @staticmethod
    def get_sample_success_email_data() -> Dict[str, Any]:
        """Get sample success email data."""
        return {
            'analysis_date': '2024-01-15',
            'current_price': 46.23,
            'sma_value': 42.15,
            'status': 'above',
            'percentage_difference': 9.68,
            'signal_strength': 'moderate',
            'recommendation': 'POSITIVE SIGNAL: Price is 9.68% above 200-day SMA.',
            'next_run_time': '2024-01-16 18:00:00 EST'
        }
    
    @staticmethod
    def get_sample_error_email_data() -> Dict[str, Any]:
        """Get sample error email data."""
        return {
            'error_date': '2024-01-15',
            'error_type': 'APIError',
            'error_message': 'Failed to fetch data from Alpha Vantage API',
            'error_timestamp': '2024-01-15 18:00:00 UTC',
            'error_component': 'API',
            'stack_trace': '''Traceback (most recent call last):
  File "/opt/tqqq-analyzer/src/tqqq_analysis/api/client.py", line 45, in fetch_daily_prices
    response = await session.get(url)
  File "/opt/tqqq-analyzer/venv/lib/python3.9/site-packages/aiohttp/client.py", line 1138, in __aenter__
    self._resp = await self._coro
aiohttp.client_exceptions.ClientConnectorError: Cannot connect to host www.alphavantage.co:443 ssl:default''',
            'python_version': '3.9.0',
            'hostname': 'tqqq-server-01',
            'log_file_path': '/opt/tqqq-analyzer/logs/tqqq_analysis.log'
        }
    
    @staticmethod
    def get_sample_warning_email_data() -> Dict[str, Any]:
        """Get sample warning email data."""
        return {
            'warning_date': '2024-01-15',
            'warning_type': 'DataFreshness',
            'warning_message': 'Data is 3 days old, exceeds recommended freshness',
            'warning_timestamp': '2024-01-15 18:00:00 UTC',
            'warning_component': 'DataProcessor',
            'additional_info': 'Last data update: 2024-01-12. Market may have been closed due to holiday.'
        }


class MockConfigurationData:
    """Mock configuration data for testing."""
    
    @staticmethod
    def get_valid_config_dict() -> Dict[str, Any]:
        """Get valid configuration dictionary."""
        return {
            'api': {
                'alpha_vantage_key': 'VALID_TEST_API_KEY_123',
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
                'to_addresses': ['recipient1@example.com', 'recipient2@example.com']
            },
            'analysis': {
                'symbol': 'TQQQ',
                'sma_period': 200,
                'max_data_age_days': 5
            },
            'logging': {
                'level': 'INFO',
                'log_file': 'logs/tqqq_analysis.log',
                'max_file_size': '10MB',
                'backup_count': 5
            },
            'system': {
                'rate_limit_file': '.api_usage_count',
                'timezone': 'UTC'
            }
        }
    
    @staticmethod
    def get_invalid_config_dict() -> Dict[str, Any]:
        """Get invalid configuration dictionary for testing validation."""
        return {
            'api': {
                'alpha_vantage_key': 'SHORT',  # Too short
                'base_url': 'invalid-url',  # Invalid URL
                'timeout': -1,  # Invalid timeout
                'max_retries': 100  # Too many retries
            },
            'email': {
                'smtp_server': '',  # Empty server
                'smtp_port': 99999,  # Invalid port
                'username': 'invalid-email',  # Invalid email
                'password': '',  # Empty password
                'use_tls': 'maybe',  # Invalid boolean
                'from_address': 'not-an-email',  # Invalid email
                'to_addresses': []  # Empty recipients
            }
        }


class MockLogData:
    """Mock log data for testing."""
    
    @staticmethod
    def get_sample_log_entries() -> List[str]:
        """Get sample log entries."""
        return [
            "2024-01-15 18:00:00 - tqqq_analysis.main - INFO - TQQQ Analysis Application Starting",
            "2024-01-15 18:00:01 - tqqq_analysis.config - INFO - Configuration loaded successfully",
            "2024-01-15 18:00:02 - tqqq_analysis.api - INFO - Fetching daily prices for TQQQ",
            "2024-01-15 18:00:03 - tqqq_analysis.api - INFO - Fetching SMA data for TQQQ",
            "2024-01-15 18:00:05 - tqqq_analysis.analysis - INFO - Processing data for 2024-01-15",
            "2024-01-15 18:00:06 - tqqq_analysis.analysis - INFO - Analysis complete: Price $46.23 is 9.68% above SMA $42.15",
            "2024-01-15 18:00:07 - tqqq_analysis.notification - INFO - Sending analysis result email",
            "2024-01-15 18:00:08 - tqqq_analysis.main - INFO - Analysis completed successfully in 8.45 seconds"
        ]
    
    @staticmethod
    def get_error_log_entries() -> List[str]:
        """Get sample error log entries."""
        return [
            "2024-01-15 18:00:00 - tqqq_analysis.main - INFO - TQQQ Analysis Application Starting",
            "2024-01-15 18:00:01 - tqqq_analysis.config - INFO - Configuration loaded successfully",
            "2024-01-15 18:00:02 - tqqq_analysis.api - INFO - Fetching daily prices for TQQQ",
            "2024-01-15 18:00:05 - tqqq_analysis.api - ERROR - API request failed: Connection timeout",
            "2024-01-15 18:00:06 - tqqq_analysis.api - INFO - Retrying API request (attempt 2/3)",
            "2024-01-15 18:00:09 - tqqq_analysis.api - ERROR - API request failed: Connection timeout",
            "2024-01-15 18:00:10 - tqqq_analysis.api - INFO - Retrying API request (attempt 3/3)",
            "2024-01-15 18:00:13 - tqqq_analysis.api - ERROR - API request failed: Connection timeout",
            "2024-01-15 18:00:14 - tqqq_analysis.main - CRITICAL - Analysis failed: API Error",
            "2024-01-15 18:00:15 - tqqq_analysis.notification - INFO - Sending error notification email"
        ]


class MockPerformanceData:
    """Mock performance test data."""
    
    @staticmethod
    def get_performance_benchmarks() -> Dict[str, float]:
        """Get performance benchmarks in seconds."""
        return {
            'api_call_max': 10.0,
            'email_send_max': 5.0,
            'full_workflow_max': 30.0,
            'data_processing_max': 2.0,
            'analysis_max': 1.0
        }
    
    @staticmethod
    def get_load_test_scenarios() -> List[Dict[str, Any]]:
        """Get load test scenarios."""
        return [
            {
                'name': 'light_load',
                'concurrent_users': 5,
                'total_requests': 25,
                'duration': 30
            },
            {
                'name': 'moderate_load',
                'concurrent_users': 10,
                'total_requests': 100,
                'duration': 60
            },
            {
                'name': 'heavy_load',
                'concurrent_users': 20,
                'total_requests': 200,
                'duration': 120
            }
        ]


class MockRealWorldData:
    """Mock real-world data scenarios for comprehensive testing."""
    
    @staticmethod
    def get_current_tqqq_response() -> Dict[str, Any]:
        """Get current TQQQ-like response with recent data."""
        today = datetime.now()
        dates = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(5)]
        
        return {
            "Meta Data": {
                "1. Information": "Daily Prices (open, high, low, close) and Volumes",
                "2. Symbol": "TQQQ",
                "3. Last Refreshed": dates[0],
                "4. Output Size": "Compact",
                "5. Time Zone": "US/Eastern"
            },
            "Time Series (Daily)": {
                dates[0]: {
                    "1. open": "88.50",
                    "2. high": "89.20",
                    "3. low": "88.10",
                    "4. close": "88.84",
                    "5. volume": "12345678"
                },
                dates[1]: {
                    "1. open": "87.80",
                    "2. high": "88.60",
                    "3. low": "87.40",
                    "4. close": "88.25",
                    "5. volume": "11234567"
                },
                dates[2]: {
                    "1. open": "87.20",
                    "2. high": "88.00",
                    "3. low": "86.90",
                    "4. close": "87.65",
                    "5. volume": "10987654"
                },
                dates[3]: {
                    "1. open": "86.90",
                    "2. high": "87.50",
                    "3. low": "86.60",
                    "4. close": "87.15",
                    "5. volume": "9876543"
                },
                dates[4]: {
                    "1. open": "86.50",
                    "2. high": "87.10",
                    "3. low": "86.20",
                    "4. close": "86.80",
                    "5. volume": "8765432"
                }
            }
        }
    
    @staticmethod
    def get_current_sma_response() -> Dict[str, Any]:
        """Get current SMA response with recent data."""
        today = datetime.now()
        dates = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(5)]
        
        return {
            "Meta Data": {
                "1: Symbol": "TQQQ",
                "2: Indicator": "Simple Moving Average (SMA)",
                "3: Last Refreshed": dates[0],
                "4: Interval": "daily",
                "5: Time Period": 200,
                "6: Series Type": "open",
                "7: Time Zone": "US/Eastern"
            },
            "Technical Analysis: SMA": {
                dates[0]: {"SMA": "74.08"},
                dates[1]: {"SMA": "74.05"},
                dates[2]: {"SMA": "74.02"},
                dates[3]: {"SMA": "73.99"},
                dates[4]: {"SMA": "73.96"}
            }
        }
    
    @staticmethod
    def get_weekend_response() -> Dict[str, Any]:
        """Get response for weekend/holiday scenario."""
        # Last Friday's data
        last_friday = datetime.now()
        while last_friday.weekday() != 4:  # Friday is 4
            last_friday -= timedelta(days=1)
        
        return {
            "Meta Data": {
                "1. Information": "Daily Prices (open, high, low, close) and Volumes",
                "2. Symbol": "TQQQ",
                "3. Last Refreshed": last_friday.strftime('%Y-%m-%d'),
                "4. Output Size": "Compact",
                "5. Time Zone": "US/Eastern"
            },
            "Time Series (Daily)": {
                last_friday.strftime('%Y-%m-%d'): {
                    "1. open": "88.50",
                    "2. high": "89.20",
                    "3. low": "88.10",
                    "4. close": "88.84",
                    "5. volume": "12345678"
                }
            }
        }


class MockErrorScenarios:
    """Mock error scenarios for comprehensive error testing."""
    
    @staticmethod
    def get_timeout_scenario():
        """Get timeout error scenario."""
        import asyncio
        return asyncio.TimeoutError("Request timed out")
    
    @staticmethod
    def get_connection_error_scenario():
        """Get connection error scenario."""
        import aiohttp
        return aiohttp.ClientConnectorError(
            connection_key=None,
            os_error=OSError("Connection refused")
        )
    
    @staticmethod
    def get_invalid_json_response() -> str:
        """Get invalid JSON response."""
        return "This is not valid JSON content"
    
    @staticmethod
    def get_partial_response() -> Dict[str, Any]:
        """Get partial/incomplete response."""
        return {
            "Meta Data": {
                "1. Information": "Daily Prices (open, high, low, close) and Volumes",
                "2. Symbol": "TQQQ"
                # Missing required fields
            }
            # Missing Time Series data
        }
    
    @staticmethod
    def get_corrupted_data_response() -> Dict[str, Any]:
        """Get response with corrupted data."""
        return {
            "Meta Data": {
                "1. Information": "Daily Prices (open, high, low, close) and Volumes",
                "2. Symbol": "TQQQ",
                "3. Last Refreshed": "2024-01-15",
                "4. Output Size": "Compact",
                "5. Time Zone": "US/Eastern"
            },
            "Time Series (Daily)": {
                "2024-01-15": {
                    "1. open": "not_a_number",
                    "2. high": "89.20",
                    "3. low": "-999.99",  # Invalid negative price
                    "4. close": "",  # Empty value
                    "5. volume": "invalid_volume"
                }
            }
        }


# Utility functions for test data generation
def generate_time_series_data(start_date: str, days: int, base_price: float = 45.0) -> Dict[str, Dict[str, str]]:
    """Generate time series data for testing."""
    data = {}
    current_date = datetime.strptime(start_date, "%Y-%m-%d")
    
    for i in range(days):
        date_str = current_date.strftime("%Y-%m-%d")
        
        # Generate realistic price variations
        variation = (i % 5 - 2) * 0.5  # Simple price variation
        open_price = base_price + variation
        high_price = open_price + abs(variation) + 0.5
        low_price = open_price - abs(variation) - 0.3
        close_price = open_price + (variation * 0.8)
        volume = 10000000 + (i * 100000)
        
        data[date_str] = {
            "1. open": f"{open_price:.2f}",
            "2. high": f"{high_price:.2f}",
            "3. low": f"{low_price:.2f}",
            "4. close": f"{close_price:.2f}",
            "5. volume": str(volume)
        }
        
        current_date -= timedelta(days=1)
    
    return data


def generate_sma_data(start_date: str, days: int, base_sma: float = 42.0) -> Dict[str, Dict[str, str]]:
    """Generate SMA data for testing."""
    data = {}
    current_date = datetime.strptime(start_date, "%Y-%m-%d")
    
    for i in range(days):
        date_str = current_date.strftime("%Y-%m-%d")
        
        # Generate slowly changing SMA values
        sma_variation = (i * 0.01)  # Slow SMA change
        sma_value = base_sma + sma_variation
        
        data[date_str] = {
            "SMA": f"{sma_value:.2f}"
        }
        
        current_date -= timedelta(days=1)
    
    return data


def generate_extended_time_series(start_date: str, days: int, trend: str = "neutral") -> Dict[str, Any]:
    """Generate extended time series data with trends."""
    base_price = 45.0
    data = {}
    current_date = datetime.strptime(start_date, "%Y-%m-%d")
    
    for i in range(days):
        date_str = current_date.strftime("%Y-%m-%d")
        
        # Apply trend
        if trend == "bullish":
            trend_factor = i * 0.1
        elif trend == "bearish":
            trend_factor = -i * 0.1
        else:
            trend_factor = 0
        
        # Add some randomness
        import random
        random_factor = random.uniform(-0.5, 0.5)
        
        price = base_price + trend_factor + random_factor
        
        data[date_str] = {
            "1. open": f"{price:.2f}",
            "2. high": f"{price + 0.5:.2f}",
            "3. low": f"{price - 0.3:.2f}",
            "4. close": f"{price + random_factor * 0.5:.2f}",
            "5. volume": str(10000000 + i * 100000)
        }
        
        current_date -= timedelta(days=1)
    
    return {
        "Meta Data": {
            "1. Information": "Daily Prices (open, high, low, close) and Volumes",
            "2. Symbol": "TQQQ",
            "3. Last Refreshed": start_date,
            "4. Output Size": "Full",
            "5. Time Zone": "US/Eastern"
        },
        "Time Series (Daily)": data
    }


def create_synchronized_responses(date: str, price: float, sma: float) -> tuple:
    """Create synchronized daily and SMA responses for testing."""
    daily_response = {
        "Meta Data": {
            "1. Information": "Daily Prices (open, high, low, close) and Volumes",
            "2. Symbol": "TQQQ",
            "3. Last Refreshed": date,
            "4. Output Size": "Compact",
            "5. Time Zone": "US/Eastern"
        },
        "Time Series (Daily)": {
            date: {
                "1. open": f"{price:.2f}",
                "2. high": f"{price + 0.5:.2f}",
                "3. low": f"{price - 0.3:.2f}",
                "4. close": f"{price:.2f}",
                "5. volume": "12345678"
            }
        }
    }
    
    sma_response = {
        "Meta Data": {
            "1: Symbol": "TQQQ",
            "2: Indicator": "Simple Moving Average (SMA)",
            "3: Last Refreshed": date,
            "4: Interval": "daily",
            "5: Time Period": 200,
            "6: Series Type": "open",
            "7: Time Zone": "US/Eastern"
        },
        "Technical Analysis: SMA": {
            date: {"SMA": f"{sma:.2f}"}
        }
    }
    
    return daily_response, sma_response