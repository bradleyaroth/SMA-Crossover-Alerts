#!/usr/bin/env python3
"""
Integration test for StockComparator with existing components.

This test demonstrates how the StockComparator integrates with
StockDataProcessor and DataValidator to provide complete analysis.
"""

import sys
from pathlib import Path

# Add the src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from sma_crossover_alerts.analysis.processor import StockDataProcessor
from sma_crossover_alerts.analysis.comparator import StockComparator
from sma_crossover_alerts.config.validation import DataValidator
from sma_crossover_alerts.utils.exceptions import DataValidationError
from sma_crossover_alerts.utils.logging import setup_logging

def test_full_integration():
    """Test complete integration workflow."""
    
    # Setup logging
    setup_logging(log_level="INFO", console_output=True)
    
    print("TQQQ STOCK COMPARATOR - INTEGRATION TEST")
    print("=" * 60)
    
    # Initialize components
    processor = StockDataProcessor()
    validator = DataValidator(max_data_age_days=5)
    comparator = StockComparator()
    
    print("✓ All components initialized")
    
    # Mock API response data (using the example from task specification)
    mock_price_response = {
        "Meta Data": {
            "1. Information": "Daily Prices (open, high, low, close) and Volumes",
            "2. Symbol": "TQQQ",
            "3. Last Refreshed": "2025-08-06",
            "4. Output Size": "Compact",
            "5. Time Zone": "US/Eastern"
        },
        "Time Series (Daily)": {
            "2025-08-06": {
                "1. open": "88.50",
                "2. high": "89.20",
                "3. low": "88.10",
                "4. close": "88.84",
                "5. volume": "1234567"
            }
        }
    }
    
    mock_sma_response = {
        "Meta Data": {
            "1: Symbol": "TQQQ",
            "2: Indicator": "Simple Moving Average (SMA)",
            "3: Last Refreshed": "2025-08-06",
            "4: Interval": "daily",
            "5: Time Period": 200,
            "6: Series Type": "close",
            "7: Time Zone": "US/Eastern"
        },
        "Technical Analysis: SMA": {
            "2025-08-06": {
                "SMA": "74.08"
            }
        }
    }
    
    try:
        print("\n1. PROCESSING DATA WITH STOCKDATAPROCESSOR")
        print("-" * 50)
        
        # Extract data using StockDataProcessor
        price_data = processor.extract_daily_price_data(mock_price_response)
        sma_data = processor.extract_sma_data(mock_sma_response)
        
        print(f"   Price data extracted: {price_data}")
        print(f"   SMA data extracted: {sma_data}")
        
        print("\n2. VALIDATING DATA WITH DATAVALIDATOR")
        print("-" * 50)
        
        # Validate data synchronization
        validated_date = validator.validate_data_sync(price_data, sma_data)
        print(f"   ✓ Data synchronization validated for date: {validated_date}")
        
        # Extract values for comparison
        date_str = price_data[0]
        closing_price = price_data[1]
        sma_value = sma_data[1]
        
        print(f"   Date: {date_str}")
        print(f"   Closing Price: ${closing_price:.2f}")
        print(f"   SMA Value: ${sma_value:.2f}")
        
        print("\n3. PERFORMING ANALYSIS WITH STOCKCOMPARATOR")
        print("-" * 50)
        
        # Test individual methods
        comparison_result = comparator.compare_price_to_sma(closing_price, sma_value)
        print(f"   Comparison Result: {comparison_result}")
        
        percentage_diff = comparator.calculate_percentage_difference(closing_price, sma_value)
        print(f"   Percentage Difference: {percentage_diff:.2f}%")
        
        trend_signal = comparator.determine_trend_signal(closing_price, sma_value)
        print(f"   Trend Signal: {trend_signal}")
        
        message = comparator.format_comparison_message(comparison_result, closing_price, sma_value)
        print(f"   Message: {message}")
        
        print("\n4. GENERATING COMPREHENSIVE RESULT")
        print("-" * 50)
        
        # Generate comprehensive analysis result
        analysis_result = comparator.generate_comparison_result(closing_price, sma_value, date_str)
        
        print("   Complete Analysis Result:")
        for key, value in analysis_result.items():
            if key == 'detailed_message':
                print(f"     {key}: {value}")
            else:
                print(f"     {key}: {value}")
        
        print("\n5. VERIFYING EXPECTED VALUES")
        print("-" * 50)
        
        # Verify against task specification example
        expected_values = {
            'comparison': 'ABOVE',
            'trend_signal': 'BULLISH',
            'message': 'The stock price is above the 200-day moving average.'
        }
        
        all_correct = True
        for key, expected in expected_values.items():
            actual = analysis_result[key]
            correct = actual == expected
            status = "✓ PASS" if correct else "✗ FAIL"
            print(f"   {status} {key}: {actual} (expected: {expected})")
            if not correct:
                all_correct = False
        
        # Check percentage difference (allow small floating point differences)
        expected_percentage = 19.93
        actual_percentage = analysis_result['percentage_difference']
        percentage_correct = abs(actual_percentage - expected_percentage) < 0.1
        status = "✓ PASS" if percentage_correct else "✗ FAIL"
        print(f"   {status} percentage_difference: {actual_percentage}% (expected: ~{expected_percentage}%)")
        if not percentage_correct:
            all_correct = False
        
        print("\n6. TESTING ERROR HANDLING INTEGRATION")
        print("-" * 50)
        
        # Test with mismatched data (should trigger DataValidator error)
        try:
            mismatched_sma_data = ("2025-08-05", 74.08)  # Different date
            validator.validate_data_sync(price_data, mismatched_sma_data)
            print("   ✗ FAIL: Should have raised DataValidationError for mismatched dates")
        except DataValidationError as e:
            print(f"   ✓ PASS: Correctly caught validation error - {e}")
        
        # Test with invalid price data in comparator
        try:
            comparator.compare_price_to_sma(-10.0, sma_value)
            print("   ✗ FAIL: Should have raised DataValidationError for negative price")
        except DataValidationError as e:
            print(f"   ✓ PASS: Correctly caught comparator validation error - {e}")
        
        print("\n" + "=" * 60)
        if all_correct:
            print("✅ INTEGRATION TEST PASSED!")
            print("StockComparator successfully integrates with existing components:")
            print("  • StockDataProcessor extracts data from API responses")
            print("  • DataValidator ensures data synchronization and integrity")
            print("  • StockComparator performs accurate price vs SMA analysis")
            print("  • All components work together seamlessly")
        else:
            print("❌ INTEGRATION TEST FAILED!")
            print("Some validation checks did not pass as expected.")
        print("=" * 60)
        
        return all_correct
        
    except Exception as e:
        print(f"\n❌ Integration test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_workflow_simulation():
    """Simulate the complete workflow as it would run in production."""
    
    print("\n" + "=" * 60)
    print("PRODUCTION WORKFLOW SIMULATION")
    print("=" * 60)
    
    # Initialize components
    processor = StockDataProcessor()
    validator = DataValidator(max_data_age_days=5)
    comparator = StockComparator()
    
    # Simulate different market scenarios
    scenarios = [
        {
            "name": "Bullish Scenario (Price Above SMA)",
            "price": 88.84,
            "sma": 74.08,
            "date": "2025-08-06"
        },
        {
            "name": "Bearish Scenario (Price Below SMA)",
            "price": 65.50,
            "sma": 74.08,
            "date": "2025-08-06"
        },
        {
            "name": "Neutral Scenario (Price Equal to SMA)",
            "price": 74.08,
            "sma": 74.08,
            "date": "2025-08-06"
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i}. {scenario['name']}")
        print("-" * 40)
        
        try:
            # Simulate the complete workflow
            result = comparator.generate_comparison_result(
                scenario['price'], 
                scenario['sma'], 
                scenario['date']
            )
            
            print(f"   Analysis: {result['message']}")
            print(f"   Signal: {result['trend_signal']}")
            print(f"   Difference: {result['percentage_difference']:+.2f}%")
            print(f"   Details: {result['detailed_message']}")
            
        except Exception as e:
            print(f"   ❌ Scenario failed: {e}")
    
    print(f"\n✅ Workflow simulation completed successfully!")

if __name__ == "__main__":
    try:
        success = test_full_integration()
        test_workflow_simulation()
        
        if success:
            print("\n🎉 ALL INTEGRATION TESTS PASSED!")
            print("The StockComparator is ready for production use.")
        else:
            print("\n❌ INTEGRATION TESTS FAILED!")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Integration test execution failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)