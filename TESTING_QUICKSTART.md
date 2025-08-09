# TQQQ Analysis - Testing Quick Start Guide

This guide helps you quickly set up and run the comprehensive test suite for the TQQQ Analysis application.

## 🚀 Quick Setup (3 Steps)

### Step 1: Setup Test Environment
```bash
# Run the automated setup script
python3 setup_tests.py
```

### Step 2: Validate Installation
```bash
# Verify everything is working
python3 validate_tests.py
```

### Step 3: Run Tests
```bash
# Run unit tests (fast)
python3 run_unit_tests.py

# Or run all tests
python3 run_tests.py --all
```

## 🔧 Manual Setup (If Automated Setup Fails)

### Install Test Dependencies
```bash
# Install required packages
pip3 install pytest pytest-asyncio pytest-cov pytest-mock

# Or install all test dependencies
pip3 install -r requirements-test.txt
```

### Set Python Path
```bash
# Add source directory to Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Or for permanent setup, add to ~/.bashrc:
echo 'export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"' >> ~/.bashrc
```

### Create Required Directories
```bash
mkdir -p logs htmlcov
```

## 🧪 Running Tests

### Unit Tests (Recommended for Development)
```bash
# Fast unit tests with basic output
python3 run_unit_tests.py

# Unit tests with coverage
python3 run_unit_tests.py --coverage

# Quiet output
python3 run_unit_tests.py --quiet
```

### Integration Tests
```bash
# Integration tests with mocked services (safe)
python3 run_tests.py --integration

# Integration tests with real API (may be rate limited)
python3 run_tests.py --integration --real-api

# Integration tests with real SMTP
python3 run_tests.py --integration --real-smtp
```

### All Tests
```bash
# All tests with coverage report
python3 run_tests.py --all --coverage

# All tests, verbose output
python3 run_tests.py --all --verbose

# All tests with real services (use carefully)
python3 run_tests.py --all --real-api --real-smtp
```

### Direct Pytest (Alternative)
```bash
# Set Python path first
export PYTHONPATH="$(pwd)/src"

# Run specific test categories
python3 -m pytest tests/unit -v                    # Unit tests
python3 -m pytest tests/integration -v             # Integration tests
python3 -m pytest -m "unit" -v                     # Unit tests by marker
python3 -m pytest -m "not slow" -v                 # Skip slow tests

# Run with coverage
python3 -m pytest --cov=tqqq_analysis --cov-report=html tests/
```

## 🐛 Troubleshooting

### Common Issues and Solutions

#### "No module named 'tqqq_analysis'"
```bash
# Solution: Set Python path
export PYTHONPATH="$(pwd)/src"

# Or run from project root with:
cd /path/to/tqqq_analysis
python3 run_tests.py --all
```

#### "python: command not found"
```bash
# Use python3 instead
python3 run_tests.py --all

# Or create alias
alias python=python3
```

#### "pytest: command not found"
```bash
# Install pytest
pip3 install pytest

# Or use python module syntax
python3 -m pytest tests/
```

#### Import errors in tests
```bash
# Validate test structure
python3 validate_tests.py

# Check if all source files exist
ls -la src/tqqq_analysis/
```

#### Permission denied
```bash
# Make scripts executable
chmod +x run_tests.py run_unit_tests.py setup_tests.py validate_tests.py
```

### Environment Variables for Integration Tests

```bash
# For real API testing (optional)
export USE_REAL_API=true
export ALPHA_VANTAGE_API_KEY=your_actual_api_key

# For real SMTP testing (optional)
export USE_REAL_SMTP=true
export SMTP_SERVER=smtp-relay.brevo.com
export SMTP_USERNAME=your_username
export SMTP_PASSWORD=your_password
export FROM_ADDRESS=your_email@domain.com
export TEST_RECIPIENT=test@domain.com
```

## 📊 Understanding Test Output

### Successful Test Run
```
TQQQ Analysis - Unit Tests
========================================
Running: python3 -m pytest tests/unit -v -m unit --tb=short --no-header --disable-warnings
✓ Success

tests/unit/test_api.py::TestAlphaVantageClient::test_initialization ✓ PASSED
tests/unit/test_analysis.py::TestStockComparator::test_compare_price_to_sma ✓ PASSED
...

========== 45 passed in 2.34s ==========
```

### Test Failure Example
```
tests/unit/test_api.py::TestAlphaVantageClient::test_fetch_data ✗ FAILED

FAILURES:
test_api.py:123: AssertionError: Expected 'TQQQ' but got 'None'
```

### Coverage Report
```
Name                                 Stmts   Miss  Cover   Missing
------------------------------------------------------------------
src/tqqq_analysis/api/client.py        156      8    95%   45-52
src/tqqq_analysis/analysis/processor.py 98      2    98%   67, 89
------------------------------------------------------------------
TOTAL                                  892     23    97%
```

## 🎯 Test Categories

### Unit Tests (`-m unit`)
- **Fast**: < 1 second per test
- **Isolated**: No external dependencies
- **Comprehensive**: 95%+ code coverage
- **Safe**: Can run anywhere, anytime

### Integration Tests (`-m integration`)
- **Realistic**: Tests component interactions
- **Optional External Services**: Can use real API/SMTP
- **Slower**: 1-30 seconds per test
- **Careful**: May hit rate limits with real services

### Performance Tests (`-m performance`)
- **Benchmarking**: Validates response times
- **Load Testing**: Tests under concurrent load
- **Regression Detection**: Catches performance issues
- **Resource Monitoring**: Memory and CPU usage

## 📈 Coverage Goals

- **Overall Coverage**: ≥ 90%
- **Unit Test Coverage**: ≥ 95%
- **Critical Paths**: 100%
- **Error Handling**: ≥ 90%

## 🔄 Continuous Integration

### GitHub Actions
```yaml
- name: Run Tests
  run: |
    python3 setup_tests.py
    python3 run_tests.py --all --coverage
```

### Local CI Simulation
```bash
# Simulate CI environment
python3 setup_tests.py
python3 validate_tests.py
python3 run_tests.py --all --coverage --lint
```

## 📝 Next Steps

1. **Start with validation**: `python3 validate_tests.py`
2. **Run unit tests**: `python3 run_unit_tests.py`
3. **Check coverage**: `python3 run_tests.py --coverage-only`
4. **View coverage report**: `open htmlcov/index.html`
5. **Run integration tests**: `python3 run_tests.py --integration`

## 🆘 Getting Help

If tests still don't work:

1. **Check Python version**: `python3 --version` (requires 3.8+)
2. **Verify project structure**: `ls -la src/tqqq_analysis/`
3. **Check dependencies**: `pip3 list | grep pytest`
4. **Run validation**: `python3 validate_tests.py`
5. **Check logs**: `cat logs/pytest.log`

## 📚 Full Documentation

For complete documentation, see [`tests/README.md`](tests/README.md).