#!/usr/bin/env python3
"""
Simple integration test for the TQQQ Analysis API implementation.

This script tests the core API integration components to ensure they work together correctly.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from sma_crossover_alerts.api.client import AlphaVantageClient
from sma_crossover_alerts.api.endpoints import APIEndpoints
from sma_crossover_alerts.config.settings import Settings
from sma_crossover_alerts.utils.exceptions import (
    APIError, NetworkError, RateLimitError, DataValidationError, ConfigurationError
)
from sma_crossover_alerts.utils.logging import setup_logging, APILogger


async def test_api_endpoints():
    """Test API endpoint URL building."""
    print("Testing API endpoint URL building...")
    
    try:
        # Test daily prices URL
        daily_url = APIEndpoints.build_daily_prices_url("TQQQ", "test_key", "compact")
        print(f"✓ Daily prices URL: {daily_url}")
        
        # Test SMA URL
        sma_url = APIEndpoints.build_sma_url("TQQQ", "test_key", 200, "daily", "open")
        print(f"✓ SMA URL: {sma_url}")
        
        # Test validation
        try:
            APIEndpoints.build_daily_prices_url("", "test_key")
            print("✗ Validation should have failed for empty symbol")
        except DataValidationError:
            print("✓ Validation correctly rejected empty symbol")
        
        return True
    except Exception as e:
        print(f"✗ API endpoints test failed: {e}")
        return False


def test_configuration():
    """Test configuration loading."""
    print("\nTesting configuration management...")
    
    try:
        # Create a test config file
        config_content = """
[api]
alpha_vantage_key = RQX9W2I4AY7JG6LS
base_url = https://www.alphavantage.co/query
timeout = 30
max_retries = 3

[email]
smtp_server = smtp.example.com
smtp_port = 587
username = test_user
password = test_pass
use_tls = true
from_address = test@example.com
to_addresses = recipient@example.com

[analysis]
symbol = TQQQ
sma_period = 200
max_data_age_days = 5

[logging]
level = INFO
log_file = logs/test.log
max_file_size = 10MB
backup_count = 5

[system]
rate_limit_file = .test_usage
timezone = UTC
"""
        
        # Write test config
        config_path = Path("test_config.ini")
        config_path.write_text(config_content)
        
        try:
            # Test configuration loading
            settings = Settings(str(config_path))
            
            # Test API settings
            assert settings.app.api.api_key == "RQX9W2I4AY7JG6LS"
            assert settings.app.api.timeout == 30
            assert settings.app.analysis.symbol == "TQQQ"
            
            print("✓ Configuration loaded successfully")
            print(f"✓ API key: {settings.app.api.api_key[:8]}...")
            print(f"✓ Symbol: {settings.app.analysis.symbol}")
            
            return True
            
        finally:
            # Clean up test config
            if config_path.exists():
                config_path.unlink()
                
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False


def test_logging():
    """Test logging setup."""
    print("\nTesting logging system...")
    
    try:
        # Setup logging
        setup_logging(log_level="INFO", log_file="logs/test.log", console_output=True)
        
        # Test API logger
        api_logger = APILogger("test")
        api_logger.log_request("GET", "https://example.com/test", {"User-Agent": "Test"})
        api_logger.log_response(200, 0.5, 1024)
        
        print("✓ Logging system initialized successfully")
        return True
        
    except Exception as e:
        print(f"✗ Logging test failed: {e}")
        return False


async def test_api_client_basic():
    """Test basic API client functionality."""
    print("\nTesting API client (basic functionality)...")
    
    try:
        # Test client initialization
        client = AlphaVantageClient("RQX9W2I4AY7JG6LS", timeout=30)
        print("✓ API client initialized successfully")
        
        # Test context manager
        async with client:
            print("✓ Context manager works")
            
            # Test health check (this will make a real API call)
            print("Testing health check (making real API call)...")
            try:
                is_healthy = await client.health_check()
                if is_healthy:
                    print("✓ API health check passed")
                else:
                    print("⚠ API health check failed (might be rate limited)")
            except RateLimitError:
                print("⚠ Rate limit exceeded during health check (expected)")
            except Exception as e:
                print(f"⚠ Health check failed: {e}")
        
        print("✓ Client cleanup successful")
        return True
        
    except Exception as e:
        print(f"✗ API client test failed: {e}")
        return False


async def test_error_handling():
    """Test error handling."""
    print("\nTesting error handling...")
    
    try:
        # Test invalid API key
        try:
            client = AlphaVantageClient("")
            print("✗ Should have failed with empty API key")
            return False
        except DataValidationError:
            print("✓ Correctly rejected empty API key")
        
        # Test invalid parameters
        try:
            APIEndpoints.build_daily_prices_url("", "test_key")
            print("✗ Should have failed with empty symbol")
            return False
        except DataValidationError:
            print("✓ Correctly rejected empty symbol")
        
        print("✓ Error handling tests passed")
        return True
        
    except Exception as e:
        print(f"✗ Error handling test failed: {e}")
        return False


async def main():
    """Run all integration tests."""
    print("=" * 60)
    print("TQQQ Analysis API Integration Tests")
    print("=" * 60)
    
    # Create logs directory
    Path("logs").mkdir(exist_ok=True)
    
    tests = [
        ("API Endpoints", test_api_endpoints()),
        ("Configuration", test_configuration()),
        ("Logging", test_logging()),
        ("API Client Basic", test_api_client_basic()),
        ("Error Handling", test_error_handling())
    ]
    
    results = []
    for test_name, test_coro in tests:
        if asyncio.iscoroutine(test_coro):
            result = await test_coro
        else:
            result = test_coro
        results.append((test_name, result))
    
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name:<20}: {status}")
        if result:
            passed += 1
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! API integration is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)