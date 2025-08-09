"""
Configuration settings management for TQQQ analysis application.

This module handles loading and managing application configuration
from INI files and environment variables with Pydantic validation.
"""

import os
import configparser
from typing import List, Optional
from pathlib import Path
import logging
from pydantic import BaseModel, Field, field_validator
from ..utils.exceptions import ConfigurationError


class APISettings(BaseModel):
    """API configuration settings."""
    
    provider: str = Field(default="yahoo_finance", description="Data provider (yahoo_finance or alpha_vantage)")
    fallback_provider: str = Field(default="alpha_vantage", description="Fallback data provider")
    api_key: str = Field(default="", description="Alpha Vantage API key (required for alpha_vantage provider)")
    base_url: str = Field(
        default="https://www.alphavantage.co/query",
        description="Alpha Vantage API base URL"
    )
    timeout: int = Field(default=30, ge=1, le=300, description="Request timeout in seconds")
    max_retries: int = Field(default=3, ge=0, le=10, description="Maximum retry attempts")
    
    @field_validator('api_key')
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        """Validate API key format, allowing empty for Yahoo Finance"""
        # API key is optional for Yahoo Finance
        if not v:
            return v
        
        # Special case: allow "demo" key for testing
        if v.lower() == "demo":
            return v
        
        # For production keys, validate length (Alpha Vantage keys are typically 16+ chars)
        if len(v) < 10:
            raise ValueError(f"API key appears to be invalid (too short): {len(v)} characters")
        
        # Alpha Vantage keys are typically alphanumeric with possible underscores
        if not all(c.isalnum() or c in ['_', '-'] for c in v):
            raise ValueError("API key contains invalid characters")
        
        return v
    
    @field_validator('provider')
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """Validate data provider."""
        valid_providers = ['yahoo_finance', 'alpha_vantage']
        if v not in valid_providers:
            raise ValueError(f"Invalid provider: {v}. Must be one of: {valid_providers}")
        return v
    
    @field_validator('base_url')
    @classmethod
    def validate_base_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError("Base URL must start with http:// or https://")
        return v.rstrip('/')


class EmailSettings(BaseModel):
    """Email configuration settings for Brevo SMTP."""
    
    smtp_server: str = Field(default="smtp-relay.brevo.com", description="SMTP server hostname")
    smtp_port: int = Field(default=587, ge=1, le=65535, description="SMTP server port")
    username: str = Field(default="no-reply@reliantrack.com", description="SMTP username")
    password: str = Field(default="your-smtp-password-here", description="SMTP password")
    use_tls: bool = Field(default=True, description="Use TLS for SMTP")
    from_name: str = Field(default="TQQQ Analysis System", description="Display name for sender")
    from_address: str = Field(default="no-reply@reliantrack.com", description="Email sender address")
    to_addresses: List[str] = Field(default=["user@example.com"], description="Email recipient addresses")
    
    @field_validator('to_addresses')
    @classmethod
    def validate_to_addresses(cls, v):
        if not v:
            raise ValueError("At least one recipient address is required")
        return v
    
    @field_validator('smtp_server')
    @classmethod
    def validate_smtp_server(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("SMTP server cannot be empty")
        return v.strip()
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("SMTP username cannot be empty")
        return v.strip()
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("SMTP password cannot be empty")
        return v.strip()


class AnalysisSettings(BaseModel):
    """Analysis configuration settings."""
    
    symbol: str = Field(default="TQQQ", description="Stock symbol to analyze")
    sma_period: int = Field(default=200, ge=1, le=1000, description="SMA period in days")
    max_data_age_days: int = Field(default=5, ge=1, le=30, description="Maximum data age in days")


class LoggingSettings(BaseModel):
    """Logging configuration settings."""
    
    level: str = Field(default="INFO", description="Logging level")
    log_file: str = Field(default="logs/tqqq_analysis.log", description="Log file path")
    max_file_size: str = Field(default="10MB", description="Maximum log file size")
    backup_count: int = Field(default=5, ge=0, le=100, description="Number of backup files")
    
    @field_validator('level')
    @classmethod
    def validate_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {', '.join(valid_levels)}")
        return v.upper()


class SystemSettings(BaseModel):
    """System configuration settings."""
    
    rate_limit_file: str = Field(default=".api_usage_count", description="Rate limit file path")
    timezone: str = Field(default="UTC", description="System timezone")


class AppSettings(BaseModel):
    """Complete application settings."""
    
    api: APISettings
    email: EmailSettings
    analysis: AnalysisSettings
    logging: LoggingSettings
    system: SystemSettings


class Settings:
    """
    Application settings manager.
    
    Loads configuration from INI files and environment variables,
    with environment variables taking precedence and Pydantic validation.
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize settings from configuration file.
        
        Args:
            config_file: Path to configuration file (defaults to config/config.ini)
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Default config file path
        if config_file is None:
            config_file = str(Path(__file__).parent.parent.parent.parent / "config" / "config.ini")
        
        self.config_file = Path(config_file)
        self.config = configparser.ConfigParser()
        
        # Load and validate configuration
        self._load_config()
        self._app_settings = self._create_app_settings()
    
    def _load_config(self):
        """Load configuration from file."""
        if self.config_file.exists():
            try:
                self.config.read(self.config_file)
                self.logger.info(f"Configuration loaded from {self.config_file}")
            except Exception as e:
                raise ConfigurationError(
                    f"Failed to load configuration file: {e}",
                    component="ConfigLoader"
                )
        else:
            self.logger.warning(f"Configuration file not found: {self.config_file}")
    
    def _get_env_or_config(self, env_var: str, section: str, key: str, default: Optional[str] = None) -> str:
        """
        Get value from environment variable or config file.
        
        Args:
            env_var: Environment variable name
            section: Config file section
            key: Config file key
            default: Default value if not found
            
        Returns:
            str: Configuration value
            
        Raises:
            ConfigurationError: If required configuration is missing
        """
        # Check environment variable first
        env_value = os.getenv(env_var)
        if env_value is not None:
            return env_value
        
        # Check config file
        try:
            return self.config.get(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            if default is not None:
                return default
            raise ConfigurationError(
                f"Configuration not found: {section}.{key} or environment variable {env_var}",
                config_section=section,
                config_key=key
            )
    
    def _create_app_settings(self) -> AppSettings:
        """Create validated application settings."""
        try:
            # API Settings
            api_settings = APISettings(
                provider=self._get_env_or_config('DATA_PROVIDER', 'api', 'provider', 'yahoo_finance'),
                fallback_provider=self._get_env_or_config('FALLBACK_PROVIDER', 'api', 'fallback_provider', 'alpha_vantage'),
                api_key=self._get_env_or_config('ALPHA_VANTAGE_KEY', 'api', 'alpha_vantage_key', ''),
                base_url=self._get_env_or_config('API_BASE_URL', 'api', 'base_url',
                                               'https://www.alphavantage.co/query'),
                timeout=int(self._get_env_or_config('API_TIMEOUT', 'api', 'timeout', '30')),
                max_retries=int(self._get_env_or_config('API_MAX_RETRIES', 'api', 'max_retries', '3'))
            )
            
            # Email Settings
            to_addresses_str = self._get_env_or_config('EMAIL_TO', 'email', 'to_addresses', 'user@example.com')
            to_addresses = [addr.strip() for addr in to_addresses_str.split(',')]
            
            email_settings = EmailSettings(
                smtp_server=self._get_env_or_config('SMTP_SERVER', 'email', 'smtp_server', 'smtp-relay.brevo.com'),
                smtp_port=int(self._get_env_or_config('SMTP_PORT', 'email', 'smtp_port', '587')),
                username=self._get_env_or_config('SMTP_USERNAME', 'email', 'username', 'no-reply@reliantrack.com'),
                password=self._get_env_or_config('SMTP_PASSWORD', 'email', 'password', 'your-smtp-password-here'),
                use_tls=self._get_env_or_config('SMTP_USE_TLS', 'email', 'use_tls', 'true').lower() in ('true', '1', 'yes', 'on'),
                from_name=self._get_env_or_config('EMAIL_FROM_NAME', 'email', 'from_name', 'TQQQ Analysis System'),
                from_address=self._get_env_or_config('EMAIL_FROM', 'email', 'from_address', 'no-reply@reliantrack.com'),
                to_addresses=to_addresses
            )
            
            # Analysis Settings
            analysis_settings = AnalysisSettings(
                symbol=self._get_env_or_config('STOCK_SYMBOL', 'analysis', 'symbol', 'TQQQ'),
                sma_period=int(self._get_env_or_config('SMA_PERIOD', 'analysis', 'sma_period', '200')),
                max_data_age_days=int(self._get_env_or_config('MAX_DATA_AGE_DAYS', 'analysis', 'max_data_age_days', '5'))
            )
            
            # Logging Settings
            logging_settings = LoggingSettings(
                level=self._get_env_or_config('LOG_LEVEL', 'logging', 'level', 'INFO'),
                log_file=self._get_env_or_config('LOG_FILE', 'logging', 'log_file', 'logs/tqqq_analysis.log'),
                max_file_size=self._get_env_or_config('LOG_MAX_SIZE', 'logging', 'max_file_size', '10MB'),
                backup_count=int(self._get_env_or_config('LOG_BACKUP_COUNT', 'logging', 'backup_count', '5'))
            )
            
            # System Settings
            system_settings = SystemSettings(
                rate_limit_file=self._get_env_or_config('RATE_LIMIT_FILE', 'system', 'rate_limit_file', '.api_usage_count'),
                timezone=self._get_env_or_config('TIMEZONE', 'system', 'timezone', 'UTC')
            )
            
            return AppSettings(
                api=api_settings,
                email=email_settings,
                analysis=analysis_settings,
                logging=logging_settings,
                system=system_settings
            )
            
        except Exception as e:
            if isinstance(e, ConfigurationError):
                raise
            raise ConfigurationError(f"Configuration validation failed: {e}")
    
    @property
    def app(self) -> AppSettings:
        """Get validated application settings."""
        return self._app_settings
    
    # API Configuration
    @property
    def alpha_vantage_key(self) -> str:
        """Alpha Vantage API key."""
        return self._get_env_or_config('ALPHA_VANTAGE_KEY', 'api', 'alpha_vantage_key')
    
    @property
    def api_base_url(self) -> str:
        """Alpha Vantage API base URL."""
        return self._get_env_or_config('API_BASE_URL', 'api', 'base_url', 
                                     'https://www.alphavantage.co/query')
    
    @property
    def api_timeout(self) -> int:
        """API request timeout in seconds."""
        return int(self._get_env_or_config('API_TIMEOUT', 'api', 'timeout', '30'))
    
    @property
    def api_max_retries(self) -> int:
        """Maximum API retry attempts."""
        return int(self._get_env_or_config('API_MAX_RETRIES', 'api', 'max_retries', '3'))
    
    # Email Configuration
    @property
    def smtp_server(self) -> str:
        """SMTP server hostname."""
        return self._get_env_or_config('SMTP_SERVER', 'email', 'smtp_server')
    
    @property
    def smtp_port(self) -> int:
        """SMTP server port."""
        return int(self._get_env_or_config('SMTP_PORT', 'email', 'smtp_port', '587'))
    
    @property
    def smtp_username(self) -> str:
        """SMTP username."""
        return self._get_env_or_config('SMTP_USERNAME', 'email', 'username')
    
    @property
    def smtp_password(self) -> str:
        """SMTP password."""
        return self._get_env_or_config('SMTP_PASSWORD', 'email', 'password')
    
    @property
    def smtp_use_tls(self) -> bool:
        """Whether to use TLS for SMTP."""
        value = self._get_env_or_config('SMTP_USE_TLS', 'email', 'use_tls', 'true')
        return value.lower() in ('true', '1', 'yes', 'on')
    
    @property
    def email_from_address(self) -> str:
        """Email sender address."""
        return self._get_env_or_config('EMAIL_FROM', 'email', 'from_address')
    
    @property
    def email_to_addresses(self) -> List[str]:
        """Email recipient addresses."""
        addresses = self._get_env_or_config('EMAIL_TO', 'email', 'to_addresses')
        return [addr.strip() for addr in addresses.split(',')]
    
    # Analysis Configuration
    @property
    def stock_symbol(self) -> str:
        """Stock symbol to analyze."""
        return self._get_env_or_config('STOCK_SYMBOL', 'analysis', 'symbol', 'TQQQ')
    
    @property
    def sma_period(self) -> int:
        """SMA period in days."""
        return int(self._get_env_or_config('SMA_PERIOD', 'analysis', 'sma_period', '200'))
    
    @property
    def max_data_age_days(self) -> int:
        """Maximum allowed data age in days."""
        return int(self._get_env_or_config('MAX_DATA_AGE_DAYS', 'analysis', 'max_data_age_days', '5'))
    
    # Logging Configuration
    @property
    def log_level(self) -> str:
        """Logging level."""
        return self._get_env_or_config('LOG_LEVEL', 'logging', 'level', 'INFO')
    
    @property
    def log_file(self) -> str:
        """Log file path."""
        return self._get_env_or_config('LOG_FILE', 'logging', 'log_file', 'logs/tqqq_analysis.log')
    
    @property
    def log_max_file_size(self) -> str:
        """Maximum log file size."""
        return self._get_env_or_config('LOG_MAX_SIZE', 'logging', 'max_file_size', '10MB')
    
    @property
    def log_backup_count(self) -> int:
        """Number of log backup files to keep."""
        return int(self._get_env_or_config('LOG_BACKUP_COUNT', 'logging', 'backup_count', '5'))
    
    # System Configuration
    @property
    def rate_limit_file(self) -> str:
        """Rate limit tracking file path."""
        return self._get_env_or_config('RATE_LIMIT_FILE', 'system', 'rate_limit_file', '.api_usage_count')
    
    @property
    def timezone(self) -> str:
        """System timezone."""
        return self._get_env_or_config('TIMEZONE', 'system', 'timezone', 'UTC')