"""
Configuration validation module.

This module provides validation for application configuration
using Pydantic models for type safety and validation, as well as
data validation and synchronization for stock price and SMA data.
"""

from pydantic import BaseModel, EmailStr, validator
from typing import List, Optional, Tuple
import re
from datetime import datetime, timedelta
import logging

from ..utils.exceptions import DataValidationError, ConfigurationError, EnhancedTQQQAnalysisError
from ..utils.logging import get_logger, ErrorLogger
from ..utils.error_handler import ErrorHandler


class APIConfig(BaseModel):
    """API configuration validation model."""
    
    alpha_vantage_key: str
    base_url: str = "https://www.alphavantage.co/query"
    timeout: int = 30
    max_retries: int = 3
    
    @validator('alpha_vantage_key')
    def validate_api_key(cls, v):
        """Validate API key format, allowing 'demo' for testing"""
        if not v:
            raise ValueError("API key cannot be empty")
        
        # Special case: allow "demo" key for testing
        if v.lower() == "demo":
            return v
        
        # For production keys, validate length and format
        if len(v) < 10:
            raise ValueError('API key appears to be invalid (too short)')
        if not re.match(r'^[A-Z0-9]+$', v):
            raise ValueError('API key should contain only uppercase letters and numbers')
        return v
    
    @validator('timeout')
    def validate_timeout(cls, v):
        """Validate timeout value."""
        if not 1 <= v <= 300:
            raise ValueError('Timeout must be between 1 and 300 seconds')
        return v
    
    @validator('max_retries')
    def validate_max_retries(cls, v):
        """Validate max retries value."""
        if not 0 <= v <= 10:
            raise ValueError('Max retries must be between 0 and 10')
        return v


class EmailConfig(BaseModel):
    """Email configuration validation model."""
    
    smtp_server: str
    smtp_port: int = 587
    username: str
    password: str
    use_tls: bool = True
    from_address: EmailStr
    to_addresses: List[EmailStr]
    
    @validator('smtp_server')
    def validate_smtp_server(cls, v):
        """Validate SMTP server hostname."""
        if not v or len(v.strip()) == 0:
            raise ValueError('SMTP server cannot be empty')
        return v.strip()
    
    @validator('smtp_port')
    def validate_smtp_port(cls, v):
        """Validate SMTP port."""
        if not 1 <= v <= 65535:
            raise ValueError('Invalid SMTP port (must be 1-65535)')
        return v
    
    @validator('username')
    def validate_username(cls, v):
        """Validate SMTP username."""
        if not v or len(v.strip()) == 0:
            raise ValueError('SMTP username cannot be empty')
        return v.strip()
    
    @validator('password')
    def validate_password(cls, v):
        """Validate SMTP password."""
        if not v or len(v.strip()) == 0:
            raise ValueError('SMTP password cannot be empty')
        return v
    
    @validator('to_addresses')
    def validate_to_addresses(cls, v):
        """Validate recipient addresses."""
        if not v or len(v) == 0:
            raise ValueError('At least one recipient email address is required')
        return v


class AnalysisConfig(BaseModel):
    """Analysis configuration validation model."""
    
    symbol: str = "TQQQ"
    sma_period: int = 200
    max_data_age_days: int = 5
    
    @validator('symbol')
    def validate_symbol(cls, v):
        """Validate stock symbol."""
        if not v or not v.isalpha() or len(v) > 10:
            raise ValueError('Invalid stock symbol (must be alphabetic, max 10 chars)')
        return v.upper()
    
    @validator('sma_period')
    def validate_sma_period(cls, v):
        """Validate SMA period."""
        if not 1 <= v <= 500:
            raise ValueError('SMA period must be between 1 and 500 days')
        return v
    
    @validator('max_data_age_days')
    def validate_max_data_age(cls, v):
        """Validate maximum data age."""
        if not 1 <= v <= 30:
            raise ValueError('Max data age must be between 1 and 30 days')
        return v


class LoggingConfig(BaseModel):
    """Logging configuration validation model."""
    
    level: str = "INFO"
    log_file: str = "logs/tqqq_analysis.log"
    max_file_size: str = "10MB"
    backup_count: int = 5
    
    @validator('level')
    def validate_log_level(cls, v):
        """Validate logging level."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Invalid log level. Must be one of: {valid_levels}')
        return v.upper()
    
    @validator('max_file_size')
    def validate_max_file_size(cls, v):
        """Validate max file size format."""
        if not re.match(r'^\d+[KMGT]?B$', v.upper()):
            raise ValueError('Invalid file size format (e.g., 10MB, 1GB)')
        return v.upper()
    
    @validator('backup_count')
    def validate_backup_count(cls, v):
        """Validate backup count."""
        if not 0 <= v <= 50:
            raise ValueError('Backup count must be between 0 and 50')
        return v


class SystemConfig(BaseModel):
    """System configuration validation model."""
    
    rate_limit_file: str = ".api_usage_count"
    timezone: str = "UTC"
    
    @validator('timezone')
    def validate_timezone(cls, v):
        """Validate timezone format."""
        # Basic validation - could be enhanced with pytz
        if not v or len(v.strip()) == 0:
            raise ValueError('Timezone cannot be empty')
        return v.strip()


class ConfigValidator:
    """
    Main configuration validator.
    
    Validates all configuration sections using Pydantic models.
    """
    
    def __init__(self):
        """Initialize configuration validator."""
        self.error_logger = ErrorLogger("config_validator")
        self.error_handler = ErrorHandler("config_validator")
    
    def validate_api_config(self, config_dict: dict) -> APIConfig:
        """Validate API configuration with enhanced error handling."""
        try:
            return APIConfig(**config_dict)
        except ValueError as e:
            context = {
                "config_section": "api",
                "provided_keys": list(config_dict.keys()),
                "validation_error": str(e)
            }
            
            config_error = ConfigurationError(
                f"API configuration validation failed: {str(e)}",
                config_section="api",
                component="ConfigValidator"
            )
            
            self.error_logger.log_error_with_context(config_error, "ConfigValidator", context)
            
            # Create enhanced error with standard message
            enhanced_error = self.error_handler.create_enhanced_error(config_error, context)
            raise enhanced_error from e
    
    @staticmethod
    def validate_email_config(config_dict: dict) -> EmailConfig:
        """Validate email configuration."""
        return EmailConfig(**config_dict)
    
    @staticmethod
    def validate_analysis_config(config_dict: dict) -> AnalysisConfig:
        """Validate analysis configuration."""
        return AnalysisConfig(**config_dict)
    
    @staticmethod
    def validate_logging_config(config_dict: dict) -> LoggingConfig:
        """Validate logging configuration."""
        return LoggingConfig(**config_dict)
    
    @staticmethod
    def validate_system_config(config_dict: dict) -> SystemConfig:
        """Validate system configuration."""
        return SystemConfig(**config_dict)
    
    def validate_all_config(self, settings) -> dict:
        """
        Validate all configuration sections.
        
        Args:
            settings: Settings instance
            
        Returns:
            dict: Validated configuration data
        """
        validated_config = {}
        
        # Validate API config
        api_config = {
            'alpha_vantage_key': settings.alpha_vantage_key,
            'base_url': settings.api_base_url,
            'timeout': settings.api_timeout,
            'max_retries': settings.api_max_retries
        }
        validated_config['api'] = self.validate_api_config(api_config)
        
        # Validate email config
        email_config = {
            'smtp_server': settings.smtp_server,
            'smtp_port': settings.smtp_port,
            'username': settings.smtp_username,
            'password': settings.smtp_password,
            'use_tls': settings.smtp_use_tls,
            'from_address': settings.email_from_address,
            'to_addresses': settings.email_to_addresses
        }
        validated_config['email'] = ConfigValidator.validate_email_config(email_config)
        
        # Validate analysis config
        analysis_config = {
            'symbol': settings.stock_symbol,
            'sma_period': settings.sma_period,
            'max_data_age_days': settings.max_data_age_days
        }
        validated_config['analysis'] = ConfigValidator.validate_analysis_config(analysis_config)
        
        # Validate logging config
        logging_config = {
            'level': settings.log_level,
            'log_file': settings.log_file,
            'max_file_size': settings.log_max_file_size,
            'backup_count': settings.log_backup_count
        }
        validated_config['logging'] = ConfigValidator.validate_logging_config(logging_config)
        
        # Validate system config
        system_config = {
            'rate_limit_file': settings.rate_limit_file,
            'timezone': settings.timezone
        }
        validated_config['system'] = ConfigValidator.validate_system_config(system_config)
        
        return validated_config


class DataValidator:
    """
    Data validation and synchronization for stock price and SMA data.
    
    This class implements the data validation and synchronization logic to ensure
    data integrity and temporal alignment between price and SMA datasets as
    specified in the original requirements and architecture documents.
    """
    
    def __init__(self, max_data_age_days: int = 5):
        """
        Initialize the data validator.
        
        Args:
            max_data_age_days: Maximum allowed data age in days
        """
        self.logger = get_logger(__name__)
        self.max_data_age_days = max_data_age_days
        self.MIN_PRICE = 0.01
        self.MAX_PRICE = 10000.0
        self.MIN_SMA = 0.01
        self.MAX_SMA = 10000.0
    
    def validate_data_sync(self, price_data: Tuple[str, float], sma_data: Tuple[str, float]) -> str:
        """
        Validate data synchronization between price and SMA datasets.
        
        This method implements the exact validation logic from the original requirements:
        - Compare dates extracted from price and SMA data
        - Validate date format consistency
        - Ensure both datasets represent the same trading day
        
        Args:
            price_data: Tuple of (date, price_value) from processor
            sma_data: Tuple of (date, sma_value) from processor
            
        Returns:
            str: Validated date if successful
            
        Raises:
            DataValidationError: If dates don't match or are invalid
        """
        price_date, price_value = price_data
        sma_date, sma_value = sma_data
        
        self.logger.debug(f"Validating data sync: price_date={price_date}, sma_date={sma_date}")
        
        # Validate date synchronization
        if price_date != sma_date:
            self.logger.error(f"Data dates don't match: price={price_date}, sma={sma_date}")
            raise DataValidationError(
                f"Data dates don't match: price={price_date}, sma={sma_date}",
                field_name="date_sync",
                invalid_value=f"price:{price_date}, sma:{sma_date}",
                component="DataValidator"
            )
        
        # Validate date format consistency
        if not self.validate_date_consistency(price_date):
            self.logger.error(f"Invalid date format: {price_date}")
            raise DataValidationError(
                f"Invalid date format: {price_date}",
                field_name="date_format",
                invalid_value=price_date,
                component="DataValidator"
            )
        
        # Validate data integrity
        if not self.validate_data_integrity(price_value, sma_value):
            self.logger.error(f"Data integrity validation failed for price={price_value}, sma={sma_value}")
            raise DataValidationError(
                f"Data integrity validation failed",
                field_name="data_integrity",
                invalid_value=f"price:{price_value}, sma:{sma_value}",
                component="DataValidator"
            )
        
        self.logger.info(f"Data synchronization validated successfully for date: {price_date}")
        return price_date
    
    def validate_temporal_alignment(self, price_date: str, sma_date: str) -> bool:
        """
        Validate temporal alignment between price and SMA data dates.
        
        Args:
            price_date: Date from price data (YYYY-MM-DD format)
            sma_date: Date from SMA data (YYYY-MM-DD format)
            
        Returns:
            bool: True if dates match, False otherwise
        """
        self.logger.debug(f"Validating temporal alignment: price={price_date}, sma={sma_date}")
        
        # Direct date comparison
        dates_match = price_date == sma_date
        
        if dates_match:
            self.logger.debug("Temporal alignment validated: dates match")
        else:
            self.logger.warning(f"Temporal alignment failed: price_date={price_date}, sma_date={sma_date}")
        
        return dates_match
    
    def validate_data_integrity(self, price: float, sma: float) -> bool:
        """
        Validate data integrity for price and SMA values.
        
        Performs comprehensive validation including:
        - Value range validation (0.01 to 10,000 as specified)
        - Data type validation
        - Cross-validation of price vs SMA relationship
        
        Args:
            price: Price value to validate
            sma: SMA value to validate
            
        Returns:
            bool: True if all integrity checks pass, False otherwise
        """
        self.logger.debug(f"Validating data integrity: price={price}, sma={sma}")
        
        # Validate price value
        if not self._validate_price_range(price):
            self.logger.warning(f"Price value {price} failed range validation")
            return False
        
        # Validate SMA value
        if not self._validate_sma_range(sma):
            self.logger.warning(f"SMA value {sma} failed range validation")
            return False
        
        # Cross-validate values
        if not self.cross_validate_values(price, sma):
            self.logger.warning(f"Cross-validation failed for price={price}, sma={sma}")
            return False
        
        self.logger.debug("Data integrity validation passed")
        return True
    
    def validate_date_consistency(self, date_str: str) -> bool:
        """
        Validate date format and consistency.
        
        Validates:
        - YYYY-MM-DD format
        - Date is not in the future
        - Date is not too old (configurable threshold)
        - Date is a valid calendar date
        
        Args:
            date_str: Date string to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        self.logger.debug(f"Validating date consistency: {date_str}")
        
        if not date_str or not isinstance(date_str, str):
            self.logger.warning(f"Invalid date string type: {type(date_str)}")
            return False
        
        # Check YYYY-MM-DD format
        date_pattern = r'^\d{4}-\d{2}-\d{2}$'
        if not re.match(date_pattern, date_str):
            self.logger.warning(f"Date format validation failed: {date_str}")
            return False
        
        try:
            # Parse date to validate it's a real date
            parsed_date = datetime.strptime(date_str, "%Y-%m-%d")
            current_date = datetime.now()
            
            # Check if date is not in the future
            if parsed_date > current_date:
                self.logger.warning(f"Date is in the future: {date_str}")
                return False
            
            # Check if date is not too old
            max_age = timedelta(days=self.max_data_age_days)
            if current_date - parsed_date > max_age:
                self.logger.warning(f"Date is too old: {date_str} (max age: {self.max_data_age_days} days)")
                return False
            
            self.logger.debug(f"Date consistency validation passed: {date_str}")
            return True
            
        except ValueError as e:
            self.logger.warning(f"Date parsing failed: {date_str} - {str(e)}")
            return False
    
    def cross_validate_values(self, price: float, sma: float) -> bool:
        """
        Perform cross-validation of price and SMA values.
        
        Validates that price and SMA values are reasonable relative to each other:
        - Both values should be positive
        - Values should be within reasonable relationship bounds
        - SMA should be reasonable relative to current price
        
        Args:
            price: Current price value
            sma: SMA value
            
        Returns:
            bool: True if cross-validation passes, False otherwise
        """
        self.logger.debug(f"Cross-validating values: price={price}, sma={sma}")
        
        # Basic sanity checks
        if price <= 0 or sma <= 0:
            self.logger.warning("Cross-validation failed: negative or zero values")
            return False
        
        # Check if values are reasonable relative to each other
        # SMA should not be more than 10x or less than 0.1x the current price
        ratio = price / sma if sma != 0 else float('inf')
        
        if ratio > 10.0 or ratio < 0.1:
            self.logger.warning(f"Cross-validation failed: unreasonable price/SMA ratio: {ratio:.2f}")
            return False
        
        # Additional validation: values should be in similar magnitude
        magnitude_diff = abs(price - sma) / max(price, sma)
        if magnitude_diff > 5.0:  # Allow up to 500% difference
            self.logger.warning(f"Cross-validation failed: excessive magnitude difference: {magnitude_diff:.2f}")
            return False
        
        self.logger.debug("Cross-validation passed")
        return True
    
    def _validate_price_range(self, price: float) -> bool:
        """
        Validate price value is within acceptable range.
        
        Args:
            price: Price value to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not isinstance(price, (int, float)):
            return False
        
        if price <= 0:
            return False
        
        return self.MIN_PRICE <= price <= self.MAX_PRICE
    
    def _validate_sma_range(self, sma: float) -> bool:
        """
        Validate SMA value is within acceptable range.
        
        Args:
            sma: SMA value to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not isinstance(sma, (int, float)):
            return False
        
        if sma <= 0:
            return False
        
        return self.MIN_SMA <= sma <= self.MAX_SMA
    
    def validate_data_freshness(self, date_str: str) -> bool:
        """
        Validate that data is not stale.
        
        Args:
            date_str: Date string to check freshness
            
        Returns:
            bool: True if data is fresh, False if stale
        """
        try:
            data_date = datetime.strptime(date_str, "%Y-%m-%d")
            current_date = datetime.now()
            age_days = (current_date - data_date).days
            
            is_fresh = age_days <= self.max_data_age_days
            
            if not is_fresh:
                self.logger.warning(f"Data is stale: {age_days} days old (max: {self.max_data_age_days})")
            else:
                self.logger.debug(f"Data is fresh: {age_days} days old")
            
            return is_fresh
            
        except ValueError:
            self.logger.error(f"Invalid date format for freshness check: {date_str}")
            return False
    
    def log_validation_summary(self, price_data: Tuple[str, float], sma_data: Tuple[str, float],
                             validation_result: bool) -> None:
        """
        Log comprehensive validation summary.
        
        Args:
            price_data: Price data tuple
            sma_data: SMA data tuple
            validation_result: Overall validation result
        """
        price_date, price_value = price_data
        sma_date, sma_value = sma_data
        
        summary = {
            "validation_result": validation_result,
            "price_date": price_date,
            "sma_date": sma_date,
            "price_value": price_value,
            "sma_value": sma_value,
            "dates_match": price_date == sma_date,
            "price_in_range": self._validate_price_range(price_value),
            "sma_in_range": self._validate_sma_range(sma_value),
            "cross_validation": self.cross_validate_values(price_value, sma_value),
            "date_fresh": self.validate_data_freshness(price_date)
        }
        
        if validation_result:
            self.logger.info(f"Validation Summary - SUCCESS: {summary}")
        else:
            self.logger.error(f"Validation Summary - FAILED: {summary}")