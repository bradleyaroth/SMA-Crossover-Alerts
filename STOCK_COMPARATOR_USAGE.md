# StockComparator Usage Guide

## Overview

The `StockComparator` class implements the core comparison engine and business logic for the TQQQ stock analysis application. It compares TQQQ closing prices against the 200-day Simple Moving Average as specified in the original requirements.

## Features

- **Exact Comparison Logic**: Implements the precise comparison logic from original requirements
- **Standard Message Generation**: Generates exact response messages as specified
- **Comprehensive Analysis**: Provides detailed analysis results with percentage differences and trend signals
- **Robust Error Handling**: Handles edge cases and validates input data
- **Integrated Logging**: Uses the existing logging infrastructure
- **Seamless Integration**: Works with existing `StockDataProcessor` and `DataValidator` components

## Basic Usage

### Import and Initialize

```python
from tqqq_analysis.analysis.comparator import StockComparator

# Initialize the comparator
comparator = StockComparator()
```

### Core Methods

#### 1. Basic Price Comparison

```python
# Compare price to SMA
result = comparator.compare_price_to_sma(88.84, 74.08)
print(result)  # Output: "ABOVE"
```

**Returns**: `"ABOVE"`, `"BELOW"`, or `"EQUAL"`

#### 2. Generate Standard Messages

```python
# Generate exact messages from requirements
message = comparator.format_comparison_message("ABOVE", 88.84, 74.08)
print(message)  # Output: "The stock price is above the 200-day moving average."
```

**Standard Messages**:
- Above SMA: "The stock price is above the 200-day moving average."
- Below SMA: "The stock price is below the 200-day moving average."
- Equal SMA: "The stock price equals the 200-day moving average."

#### 3. Calculate Percentage Difference

```python
# Calculate percentage difference
percentage = comparator.calculate_percentage_difference(88.84, 74.08)
print(f"{percentage:.2f}%")  # Output: "19.92%"
```

**Formula**: `((closing_price - sma_value) / sma_value) * 100`

#### 4. Determine Trend Signal

```python
# Get trend signal
signal = comparator.determine_trend_signal(88.84, 74.08)
print(signal)  # Output: "BULLISH"
```

**Signals**: `"BULLISH"`, `"BEARISH"`, or `"NEUTRAL"`

#### 5. Comprehensive Analysis

```python
# Generate complete analysis result
result = comparator.generate_comparison_result(88.84, 74.08, "2025-08-06")

print(result)
# Output:
# {
#     "date": "2025-08-06",
#     "closing_price": 88.84,
#     "sma_value": 74.08,
#     "comparison": "ABOVE",
#     "percentage_difference": 19.92,
#     "trend_signal": "BULLISH",
#     "message": "The stock price is above the 200-day moving average.",
#     "detailed_message": "TQQQ closed at $88.84 on 2025-08-06, which is 19.92% above its 200-day SMA of $74.08."
# }
```

## Integration with Existing Components

### Complete Workflow Example

```python
from tqqq_analysis.analysis.processor import StockDataProcessor
from tqqq_analysis.analysis.comparator import StockComparator
from tqqq_analysis.config.validation import DataValidator

# Initialize components
processor = StockDataProcessor()
validator = DataValidator()
comparator = StockComparator()

# Process API data
price_data = processor.extract_daily_price_data(daily_response)
sma_data = processor.calculate_sma(daily_response, period=200)

# Validate data synchronization
validated_date = validator.validate_data_sync(price_data, sma_data)

# Perform analysis
date_str, closing_price = price_data
_, sma_value = sma_data

analysis_result = comparator.generate_comparison_result(
    closing_price, sma_value, date_str
)

# Use results for email notifications, logging, etc.
print(f"Analysis: {analysis_result['message']}")
print(f"Signal: {analysis_result['trend_signal']}")
print(f"Details: {analysis_result['detailed_message']}")
```

## Error Handling

### Standard Error Messages

```python
# Get standard error messages for different scenarios
error_messages = comparator.get_error_messages()

print(error_messages['api_failure'])    # "No API data available."
print(error_messages['data_error'])     # "Data validation failed - please try again."
print(error_messages['network_error'])  # "Network connection failed - please check connectivity."
print(error_messages['rate_limit'])     # "API rate limit exceeded - please try again later."
```

### Exception Handling

```python
from tqqq_analysis.utils.exceptions import DataValidationError

try:
    result = comparator.compare_price_to_sma(-10.0, 74.08)  # Invalid negative price
except DataValidationError as e:
    print(f"Validation error: {e}")
    # Handle validation failure appropriately
```

## Test Examples

### Example Test Cases

```python
# Test different market scenarios
test_cases = [
    {
        "name": "Bullish Market",
        "price": 88.84,
        "sma": 74.08,
        "expected_comparison": "ABOVE",
        "expected_signal": "BULLISH"
    },
    {
        "name": "Bearish Market", 
        "price": 65.50,
        "sma": 74.08,
        "expected_comparison": "BELOW",
        "expected_signal": "BEARISH"
    },
    {
        "name": "Neutral Market",
        "price": 74.08,
        "sma": 74.08,
        "expected_comparison": "EQUAL",
        "expected_signal": "NEUTRAL"
    }
]

for case in test_cases:
    result = comparator.generate_comparison_result(
        case["price"], case["sma"], "2025-08-06"
    )
    
    print(f"{case['name']}: {result['comparison']} ({result['trend_signal']})")
    print(f"  Message: {result['message']}")
    print(f"  Difference: {result['percentage_difference']:+.2f}%")
```

## Production Usage

### Email Notification Integration

```python
# Use with email notification system
analysis_result = comparator.generate_comparison_result(price, sma, date)

# Data for email templates
email_data = {
    'analysis_date': analysis_result['date'],
    'current_price': analysis_result['closing_price'],
    'sma_value': analysis_result['sma_value'],
    'status': 'above' if analysis_result['comparison'] == 'ABOVE' else 'below',
    'percentage_difference': abs(analysis_result['percentage_difference']),
    'status_class': 'above' if analysis_result['comparison'] == 'ABOVE' else 'below',
    'signal_strength': 'strong',  # Can be enhanced based on percentage
    'recommendation': analysis_result['detailed_message']
}

# Send email with analysis results
email_sender.send_analysis_email(email_data)
```

### Logging Integration

```python
# The StockComparator automatically logs analysis steps
# Logs include:
# - Comparison inputs and results
# - Percentage calculations  
# - Trend determinations
# - Validation errors
# - Analysis completion summaries

# Example log output:
# DEBUG - Price comparison: $88.84 vs SMA $74.08 = ABOVE
# DEBUG - Percentage difference: ($88.84 - $74.08) / $74.08 * 100 = 19.92%
# DEBUG - Trend signal: BULLISH
# INFO - Comparison analysis complete for 2025-08-06: Price $88.84 is ABOVE SMA $74.08 (+19.92%, BULLISH)
```

## Implementation Details

### Exact Comparison Logic

The comparison logic implements the exact requirements from the original specification:

```python
def compare_price_to_sma(self, closing_price: float, sma_value: float) -> str:
    if closing_price > sma_value:
        return "ABOVE"
    elif closing_price < sma_value:
        return "BELOW"
    else:
        return "EQUAL"  # Edge case: exactly equal
```

### Validation and Error Handling

- Input validation for all parameters
- Proper exception handling with custom exception types
- Edge case handling (zero values, floating-point precision)
- Integration with existing exception hierarchy

### Performance Considerations

- Efficient calculations with minimal overhead
- Proper logging without performance impact
- Memory-efficient result generation
- Fast comparison operations

## Testing

Run the comprehensive test suite:

```bash
# Test StockComparator implementation
python3 test_stock_comparator.py

# Test integration with existing components  
python3 test_integration_comparator.py

# Run existing unit tests
python3 -m pytest tests/unit/test_analysis.py -v
```

All tests should pass, confirming the implementation meets requirements and integrates properly with existing components.