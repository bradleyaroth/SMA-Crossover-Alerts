# TQQQ Analysis - Test Suite Documentation

This document provides comprehensive documentation for the TQQQ Analysis application test suite, including test organization, execution instructions, and coverage requirements.

## Table of Contents

- [Test Suite Overview](#test-suite-overview)
- [Test Organization](#test-organization)
- [Test Execution](#test-execution)
- [Test Categories](#test-categories)
- [Coverage Requirements](#coverage-requirements)
- [Configuration](#configuration)
- [Continuous Integration](#continuous-integration)
- [Troubleshooting](#troubleshooting)

## Test Suite Overview

The TQQQ Analysis test suite provides comprehensive coverage of all application components with over 90% code coverage. The suite includes unit tests, integration tests, performance tests, and end-to-end workflow validation.

### Key Features

- **Comprehensive Coverage**: 90%+ code coverage across all modules
- **Multiple Test Types**: Unit, integration, performance, and end-to-end tests
- **Real Service Testing**: Optional testing with real Alpha Vantage API and SMTP servers
- **Performance Benchmarks**: Automated performance validation and regression detection
- **CI/CD Ready**: Full automation support with detailed reporting

## Test Organization

```
tests/
├── __init__.py                 # Test package initialization
├── conftest.py                 # Shared fixtures and configuration
├── unit/                       # Unit tests (fast, isolated)
│   ├── __init__.py
│   ├── test_api.py            # API client and endpoints tests
│   ├── test_analysis.py       # Data processing and analysis tests
│   ├── test_config.py         # Configuration management tests
│   ├── test_error_handling.py # Error handling and exceptions tests
│   ├── test_notification.py   # Email notification tests
│   └── test_utils.py          # Utility function tests
├── integration/                # Integration tests (slower, external deps)
│   ├── __init__.py
│   ├── test_api_integration.py      # Real API integration tests
│   ├── test_email_integration.py    # Real SMTP integration tests
│   └── test_full_workflow.py        # End-to-end workflow tests
└── fixtures/                   # Test data and utilities
    ├── __init__.py
    ├── mock_data.py           # Mock API responses and test data
    └── test_config.py         # Test configuration utilities
```

## Test Execution

### Quick Start

```bash
# Run all tests
python run_tests.py --all

# Run unit tests only (fast)
python run_unit_tests.py

# Run with coverage report
python run_tests.py --all --coverage

# Run integration tests with real services
python run_tests.py --integration --real-api --real-smtp
```

### Test Runner Scripts

#### Main Test Runner (`run_tests.py`)

The primary test execution interface with comprehensive options:

```bash
# Basic usage
python run_tests.py [OPTIONS]

# Examples
python run_tests.py --unit                    # Unit tests only
python run_tests.py --integration             # Integration tests only
python run_tests.py --performance             # Performance tests only
python run_tests.py --all --coverage          # All tests with coverage
python run_tests.py --coverage-only           # Generate coverage report only
python run_tests.py --clean                   # Clean test artifacts
python run_tests.py --lint                    # Run code linting
```

#### Unit Test Runner (`run_unit_tests.py`)

Optimized for fast development feedback:

```bash
python run_unit_tests.py [--coverage] [--quiet]
```

### Direct Pytest Execution

```bash
# Run all tests
pytest

# Run specific test categories
pytest -m unit                 # Unit tests only
pytest -m integration          # Integration tests only
pytest -m "not slow"           # Skip slow tests
pytest -m "unit and not network"  # Unit tests without network

# Run specific test files
pytest tests/unit/test_api.py
pytest tests/integration/test_full_workflow.py

# Run with coverage
pytest --cov=tqqq_analysis --cov-report=html
```

## Test Categories

### Unit Tests (`-m unit`)

Fast, isolated tests that verify individual components without external dependencies.

**Characteristics:**
- Execution time: < 1 second per test
- No network calls or external services
- Extensive use of mocks and fixtures
- High coverage of edge cases and error conditions

**Components Tested:**
- API client logic and error handling
- Data processing and validation
- Analysis algorithms and comparisons
- Email template generation
- Configuration management
- Utility functions

### Integration Tests (`-m integration`)

Tests that verify component interactions and external service integration.

**Characteristics:**
- Execution time: 1-30 seconds per test
- May use real external services (optional)
- Tests complete workflows
- Validates data flow between components

**Components Tested:**
- End-to-end analysis workflow
- Real Alpha Vantage API integration
- Real SMTP server integration
- Component interaction patterns
- Error recovery and retry logic

### Performance Tests (`-m performance`)

Tests that validate performance requirements and detect regressions.

**Characteristics:**
- Execution time: Variable (up to 60 seconds)
- Measures response times and resource usage
- Validates against performance benchmarks
- Load testing capabilities

**Benchmarks:**
- API calls: < 10 seconds
- Email sending: < 5 seconds
- Full workflow: < 30 seconds
- Data processing: < 2 seconds
- Analysis computation: < 1 second

### Network Tests (`-m network`)

Tests requiring network access (subset of integration tests).

**Characteristics:**
- Requires internet connectivity
- May be rate-limited by external services
- Can be skipped in offline environments
- Used for real-world validation

## Coverage Requirements

### Coverage Targets

- **Overall Coverage**: ≥ 90%
- **Unit Test Coverage**: ≥ 95%
- **Critical Path Coverage**: 100%
- **Error Handling Coverage**: ≥ 90%

### Coverage Reporting

```bash
# Generate HTML coverage report
python run_tests.py --coverage-only

# View coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Coverage Configuration

Coverage settings are defined in `.coveragerc`:

- **Source**: `src/tqqq_analysis/`
- **Exclusions**: Test files, `__pycache__`, build artifacts
- **Branch Coverage**: Enabled
- **Report Formats**: HTML, XML, JSON, Terminal

## Configuration

### Pytest Configuration (`pytest.ini`)

Key settings:
- Test discovery patterns
- Marker definitions
- Output formatting
- Timeout settings
- Logging configuration

### Environment Variables

```bash
# Integration test configuration
export USE_REAL_API=true              # Enable real API calls
export USE_REAL_SMTP=true             # Enable real SMTP testing
export ALPHA_VANTAGE_API_KEY=your_key # Real API key
export SMTP_SERVER=smtp.example.com   # Real SMTP server
export SMTP_USERNAME=your_username    # SMTP credentials
export SMTP_PASSWORD=your_password    # SMTP credentials

# Test environment
export TESTING=true                   # Enable test mode
export PYTHONPATH=src                 # Python path for imports
```

### Test Data Configuration

Test configuration is managed through:
- `tests/fixtures/test_config.py`: Test-specific configuration
- `tests/fixtures/mock_data.py`: Mock API responses and test data
- `tests/conftest.py`: Shared fixtures and utilities

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, '3.10', '3.11']
    
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v3
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-asyncio
    
    - name: Run tests
      run: python run_tests.py --all --coverage
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

### Jenkins Pipeline Example

```groovy
pipeline {
    agent any
    stages {
        stage('Setup') {
            steps {
                sh 'python -m pip install -r requirements.txt'
                sh 'python -m pip install pytest pytest-cov'
            }
        }
        stage('Unit Tests') {
            steps {
                sh 'python run_tests.py --unit --coverage'
            }
        }
        stage('Integration Tests') {
            steps {
                sh 'python run_tests.py --integration'
            }
        }
    }
    post {
        always {
            publishHTML([
                allowMissing: false,
                alwaysLinkToLastBuild: true,
                keepAll: true,
                reportDir: 'htmlcov',
                reportFiles: 'index.html',
                reportName: 'Coverage Report'
            ])
        }
    }
}
```

## Troubleshooting

### Common Issues

#### Import Errors

```bash
# Error: ModuleNotFoundError: No module named 'tqqq_analysis'
# Solution: Set PYTHONPATH
export PYTHONPATH=src
```

#### API Rate Limiting

```bash
# Error: RateLimitError during integration tests
# Solution: Use mock tests or wait between runs
python run_tests.py --integration  # Uses mocks by default
```

#### SMTP Connection Errors

```bash
# Error: SMTPConnectError during email tests
# Solution: Check SMTP configuration or use mocks
python run_tests.py --unit  # Uses mocks for email tests
```

#### Coverage Issues

```bash
# Error: Coverage below threshold
# Solution: Check excluded files and add tests
python run_tests.py --coverage-only
open htmlcov/index.html  # Review uncovered code
```

### Debug Mode

```bash
# Run tests with debug output
pytest -v -s --tb=long

# Run specific test with debugging
pytest -v -s tests/unit/test_api.py::TestAlphaVantageClient::test_fetch_daily_prices_success
```

### Performance Issues

```bash
# Profile test execution
pytest --durations=10  # Show 10 slowest tests

# Run only fast tests
pytest -m "not slow"
```

### Test Data Issues

```bash
# Clean test artifacts
python run_tests.py --clean

# Regenerate test data
rm -rf tests/fixtures/__pycache__
python -c "from tests.fixtures.mock_data import *; print('Test data loaded')"
```

## Best Practices

### Writing Tests

1. **Use descriptive test names**: `test_fetch_daily_prices_with_invalid_symbol`
2. **Follow AAA pattern**: Arrange, Act, Assert
3. **Use appropriate fixtures**: Leverage `conftest.py` fixtures
4. **Mock external dependencies**: Use `unittest.mock` for external services
5. **Test edge cases**: Include error conditions and boundary values

### Test Organization

1. **Group related tests**: Use test classes for logical grouping
2. **Use appropriate markers**: Mark tests with `@pytest.mark.unit`, etc.
3. **Keep tests independent**: Each test should be able to run in isolation
4. **Use meaningful assertions**: Provide clear failure messages

### Performance Considerations

1. **Keep unit tests fast**: < 1 second execution time
2. **Use mocks for external services**: Avoid network calls in unit tests
3. **Parallelize when possible**: Use `pytest-xdist` for parallel execution
4. **Profile slow tests**: Identify and optimize bottlenecks

## Contributing

When adding new tests:

1. Follow the existing test organization structure
2. Add appropriate markers (`@pytest.mark.unit`, etc.)
3. Update this documentation if adding new test categories
4. Ensure new tests maintain coverage requirements
5. Add fixtures to `conftest.py` for reusable test data

## Support

For test-related issues:

1. Check this documentation first
2. Review existing test examples
3. Check the troubleshooting section
4. Consult the main project documentation
5. Create an issue with detailed error information