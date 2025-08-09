#!/usr/bin/env python3
"""
SMA Crossover Alerts - Main Entry Point

This is the main entry point for the SMA Crossover Alerts application.
It orchestrates the entire analysis workflow including data fetching,
processing, analysis, and notification delivery.
"""

import sys
import asyncio
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from sma_crossover_alerts.config.settings import Settings
from sma_crossover_alerts.config.validation import ConfigValidator
from sma_crossover_alerts.utils.logging import setup_logging
from sma_crossover_alerts.utils.exceptions import (
    TQQQAnalyzerError,
    APIError,
    DataValidationError,
    EmailError,
    ConfigurationError,
    DataSynchronizationError
)
from sma_crossover_alerts.api.client import AlphaVantageClient
from sma_crossover_alerts.analysis.processor import StockDataProcessor
from sma_crossover_alerts.analysis.comparator import StockComparator
from sma_crossover_alerts.notification.email_sender import EmailSender
from sma_crossover_alerts.utils.error_handler import ErrorHandler


class SMAAnalyzer:
    """
    Main application class for SMA Crossover Alerts.
    
    Coordinates all components of the analysis workflow including
    API data fetching, analysis processing, and email notifications.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the SMA analyzer.
        
        Args:
            config_path: Optional path to configuration file
        """
        self.config_path = config_path
        self.settings = None
        self.logger = None
        self.start_time = datetime.now()
        
        # Component instances
        self.api_client = None
        self.processor = None
        self.comparator = None
        self.email_sender = None
        self.error_handler = None
    
    def initialize(self):
        """
        Initialize the application components.
        
        Loads configuration, sets up logging, and validates settings.
        """
        try:
            # Load settings
            self.settings = Settings(self.config_path)
            
            # Set up logging
            setup_logging(
                log_level=self.settings.log_level,
                log_file=self.settings.log_file,
                max_file_size=self.settings.log_max_file_size,
                backup_count=self.settings.log_backup_count
            )
            
            self.logger = logging.getLogger('sma_crossover_alerts.main')
            self.logger.info("SMA Crossover Alerts Application Starting")
            self.logger.info(f"Start time: {self.start_time}")
            self.logger.info(f"Configuration loaded from: {self.config_path or 'default location'}")
            
            # Validate configuration
            config_validator = ConfigValidator()
            validated_config = config_validator.validate_all_config(self.settings)
            self.logger.info("Configuration validation completed successfully")
            
            # Initialize components
            self._initialize_components()
            
        except Exception as e:
            if self.logger:
                self.logger.critical(f"Initialization failed: {str(e)}")
            else:
                print(f"CRITICAL: Initialization failed: {str(e)}")
            raise ConfigurationError(f"Application initialization failed: {str(e)}")
    
    def _initialize_components(self):
        """Initialize all application components."""
        try:
            # Initialize API client using data provider factory
            from src.sma_crossover_alerts.api.data_provider_factory import DataProviderFactory
            
            factory = DataProviderFactory()
            self.api_client = factory.create_client(
                provider=self.settings.app.api.provider,
                api_key=self.settings.app.api.api_key if self.settings.app.api.api_key else None,
                timeout=self.settings.app.api.timeout,
                base_url=self.settings.app.api.base_url
            )
            
            self.logger.info(f"Initialized {self.settings.app.api.provider} data provider")
            
            # Initialize data processor
            self.processor = StockDataProcessor()
            
            # Initialize stock comparator
            self.comparator = StockComparator()
            
            # Initialize email sender
            email_config = {
                'smtp_server': self.settings.smtp_server,
                'smtp_port': self.settings.smtp_port,
                'username': self.settings.smtp_username,
                'password': self.settings.smtp_password,
                'use_tls': self.settings.smtp_use_tls,
                'from_name': self.settings.app.email.from_name,
                'from_address': self.settings.email_from_address,
                'to_addresses': self.settings.email_to_addresses
            }
            self.email_sender = EmailSender(email_config)
            
            # Initialize error handler
            self.error_handler = ErrorHandler("main_application")
            
            self.logger.info("All components initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Component initialization failed: {str(e)}")
            raise
    
    async def run_analysis(self, dry_run: bool = False) -> bool:
        """
        Run the complete SMA crossover analysis workflow.
        
        Args:
            dry_run: If True, run analysis without sending email
            
        Returns:
            bool: True if analysis completed successfully
        """
        try:
            self.logger.info("Starting SMA crossover analysis workflow")
            
            # Step 1: Fetch historical data from API
            self.logger.info("Fetching historical data from API...")
            daily_data = await self.fetch_data()
            
            # Step 2: Process data and calculate SMA
            self.logger.info("Processing data and calculating SMA...")
            processed_data = self.process_data(daily_data)
            
            # Step 3: Validate data synchronization
            self.logger.info("Validating data synchronization...")
            validated_date = self.validate_data(
                (processed_data['date'], processed_data['price']),
                (processed_data['date'], processed_data['sma'])
            )
            
            # Step 4: Compare price to SMA
            self.logger.info("Performing price vs SMA analysis...")
            comparison_result = self.compare_data(
                processed_data['price'],
                processed_data['sma'],
                validated_date
            )
            
            # Step 5: Send email notification (unless dry run)
            if not dry_run:
                self.logger.info("Sending email notification...")
                success = await self.send_notification(comparison_result)
                if not success:
                    self.logger.warning("Email notification failed, but analysis completed")
            else:
                self.logger.info("Dry run mode: Skipping email notification")
                success = True
            
            end_time = datetime.now()
            duration = end_time - self.start_time
            self.logger.info(f"Analysis completed successfully in {duration.total_seconds():.2f} seconds")
            
            return True
            
        except Exception as e:
            return self.handle_error(e, "main_workflow")
    
    async def fetch_data(self) -> Dict[str, Any]:
        """
        Fetch historical daily price data from configured API provider.
        
        Returns:
            Dict: Full historical daily price data for manual SMA calculation
        """
        try:
            async with self.api_client:
                # Single API call with full historical data for SMA calculation
                daily_data = await self.api_client.fetch_daily_prices(
                    self.settings.stock_symbol,
                    output_size="full"  # Changed from "compact" to get full historical data
                )
                
                self.logger.info(f"Successfully fetched full historical data for {self.settings.stock_symbol}")
                return daily_data
                
        except Exception as e:
            self.logger.error(f"Data fetching failed: {str(e)}")
            raise
    
    def process_data(self, daily_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process and extract price data and calculate SMA manually.
        
        Args:
            daily_data: Full historical daily price data from API
            
        Returns:
            Dict: Processed data with date, price, and calculated sma
        """
        try:
            # Extract current price data
            price_date, price_value = self.processor.extract_daily_price_data(daily_data)
            
            # Calculate SMA manually from historical data
            sma_date, sma_value = self.processor.calculate_sma(daily_data, self.settings.sma_period)
            
            # Dates should match since both come from the same dataset
            if price_date != sma_date:
                self.logger.warning(f"Date mismatch: price_date={price_date}, sma_date={sma_date}")
                # This should not happen with single data source, but handle gracefully
                # Use the price date as primary since it's the most recent data point
            
            processed_data = {
                'date': price_date,  # Use price date as primary
                'price': price_value,
                'sma': sma_value,
                'symbol': self.settings.stock_symbol
            }
            
            self.logger.info(f"Processed data for {price_date}: Price=${price_value:.2f}, {self.settings.sma_period}-day SMA=${sma_value:.2f}")
            return processed_data
            
        except Exception as e:
            self.logger.error(f"Data processing failed: {str(e)}")
            raise
    
    def validate_data(self, price_result: Tuple[str, float], sma_result: Tuple[str, float]) -> str:
        """
        Validate data synchronization and integrity.
        
        Args:
            price_result: (date, price) tuple
            sma_result: (date, sma) tuple
            
        Returns:
            str: Validated date
        """
        try:
            price_date, price_value = price_result
            sma_date, sma_value = sma_result
            
            # Validate dates match
            if price_date != sma_date:
                raise DataSynchronizationError(
                    f"Date mismatch between price ({price_date}) and SMA ({sma_date}) data"
                )
            
            # Validate data freshness
            from datetime import datetime, timedelta
            data_date = datetime.strptime(price_date, "%Y-%m-%d")
            current_date = datetime.now()
            age_days = (current_date - data_date).days
            
            if age_days > self.settings.max_data_age_days:
                self.logger.warning(f"Data is {age_days} days old, exceeds maximum of {self.settings.max_data_age_days} days")
            
            # Validate price and SMA values are reasonable
            if price_value <= 0 or sma_value <= 0:
                raise DataValidationError("Price and SMA values must be positive")
            
            if price_value > 10000 or sma_value > 10000:
                raise DataValidationError("Price and SMA values seem unreasonably high")
            
            self.logger.info(f"Data validation successful for {price_date}")
            return price_date
            
        except Exception as e:
            self.logger.error(f"Data validation failed: {str(e)}")
            raise
    
    def compare_data(self, price: float, sma: float, date: str) -> Dict[str, Any]:
        """
        Compare price against SMA using business logic.
        
        Args:
            price: Current stock price
            sma: Simple Moving Average value
            date: Analysis date
            
        Returns:
            Dict: Comparison result with analysis
        """
        try:
            # Generate comparison result
            comparison_result = self.comparator.generate_comparison_result(price, sma, date)
            
            # Add additional metadata
            comparison_result.update({
                'symbol': self.settings.stock_symbol,
                'sma_period': self.settings.sma_period,
                'analysis_timestamp': datetime.now().isoformat(),
                'data_age_days': (datetime.now() - datetime.strptime(date, "%Y-%m-%d")).days
            })
            
            self.logger.info(f"Analysis complete: {comparison_result['comparison']} SMA by {abs(comparison_result['percentage_difference']):.2f}%")
            return comparison_result
            
        except Exception as e:
            self.logger.error(f"Data comparison failed: {str(e)}")
            raise
    
    async def send_notification(self, result: Dict[str, Any]) -> bool:
        """
        Send email notification with analysis results.
        
        Args:
            result: Analysis result dictionary
            
        Returns:
            bool: True if email sent successfully
        """
        try:
            # Map comparator result to email template format
            email_data = {
                'current_price': result['closing_price'],  # Map closing_price to current_price
                'sma_value': result['sma_value'],
                'status': result['comparison'].lower(),  # Map comparison to status
                'percentage_difference': result['percentage_difference'],
                'message': result['message'],
                'analysis_date': result['date'],
                'detailed_message': result['detailed_message'],
                'trend_signal': result['trend_signal'],
                'symbol': result.get('symbol', 'TQQQ'),
                'sma_period': result.get('sma_period', 200)
            }
            
            # Send analysis result email
            success = self.email_sender.send_analysis_result(
                email_data,
                self.settings.email_to_addresses
            )
            
            if success:
                self.logger.info("Email notification sent successfully")
            else:
                self.logger.error("Email notification failed")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Email notification failed: {str(e)}")
            return False
    
    def handle_error(self, error: Exception, component: str) -> bool:
        """
        Handle errors with comprehensive logging and recovery.
        
        Args:
            error: Exception that occurred
            component: Component where error occurred
            
        Returns:
            bool: False (indicating failure)
        """
        try:
            # Log the error with context
            context = {
                'component': component,
                'error_type': type(error).__name__,
                'timestamp': datetime.now().isoformat(),
                'runtime_seconds': (datetime.now() - self.start_time).total_seconds()
            }
            
            if isinstance(error, (APIError, DataValidationError, EmailError)):
                self.logger.error(f"{component} error: {str(error)}")
            else:
                self.logger.critical(f"Unexpected error in {component}: {str(error)}")
            
            # Try to send error notification (but don't fail if this fails)
            try:
                import asyncio
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self._send_error_notification(type(error).__name__, str(error)))
                else:
                    asyncio.run(self._send_error_notification(type(error).__name__, str(error)))
            except Exception as notify_error:
                self.logger.error(f"Failed to send error notification: {str(notify_error)}")
            
            return False
            
        except Exception as handle_error:
            self.logger.critical(f"Error handling failed: {str(handle_error)}")
            return False
    
    async def _send_error_notification(self, error_type: str, error_message: str):
        """
        Send error notification email.
        
        Args:
            error_type: Type of error that occurred
            error_message: Detailed error message
        """
        try:
            if self.email_sender:
                error_data = {
                    'error_type': error_type,
                    'error_message': error_message,
                    'timestamp': datetime.now().isoformat(),
                    'symbol': self.settings.stock_symbol if self.settings else 'TQQQ',
                    'runtime_seconds': (datetime.now() - self.start_time).total_seconds()
                }
                
                self.email_sender.send_error_notification(
                    error_data,
                    self.settings.email_to_addresses if self.settings else []
                )
            else:
                self.logger.warning("Email sender not available for error notification")
                
        except Exception as e:
            self.logger.error(f"Failed to send error notification: {str(e)}")
    
    async def test_api_connectivity(self) -> bool:
        """Test API connectivity."""
        try:
            if not self.api_client:
                self._initialize_components()
            
            async with self.api_client:
                return await self.api_client.health_check()
                
        except Exception as e:
            self.logger.error(f"API connectivity test failed: {str(e)}")
            return False
    
    async def test_email_configuration(self) -> bool:
        """Test email configuration."""
        try:
            if not self.email_sender:
                self._initialize_components()
            
            return self.email_sender.test_connection()
            
        except Exception as e:
            self.logger.error(f"Email configuration test failed: {str(e)}")
            return False
    
    def cleanup(self):
        """Clean up resources and log final status."""
        try:
            if self.logger:
                end_time = datetime.now()
                total_duration = end_time - self.start_time
                self.logger.info(f"Application shutdown - Total runtime: {total_duration.total_seconds():.2f} seconds")
            
            # Close API client if needed
            if self.api_client:
                try:
                    asyncio.create_task(self.api_client.close())
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"Error closing API client: {str(e)}")
                        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Cleanup error: {str(e)}")


def create_argument_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser."""
    parser = argparse.ArgumentParser(
        description='SMA Crossover Alerts Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                          # Run with default configuration
  python main.py --config custom.ini     # Use custom configuration file
  python main.py --dry-run               # Run without sending email
  python main.py --test-email            # Test email configuration only
  python main.py --test-api              # Test API connectivity only
  python main.py --verbose               # Enable verbose logging
        """
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='Configuration file path (default: config/config.ini)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run analysis without sending email notification'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging output'
    )
    
    parser.add_argument(
        '--test-email',
        action='store_true',
        help='Test email configuration and connectivity only'
    )
    
    parser.add_argument(
        '--test-api',
        action='store_true',
        help='Test API connectivity and authentication only'
    )
    
    return parser


async def main():
    """
    Main application entry point with command-line interface.
    
    Initializes the application, runs the analysis, and handles cleanup.
    """
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Override log level if verbose
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    analyzer = SMAAnalyzer(config_path=args.config)
    exit_code = 0
    
    try:
        # Initialize application
        analyzer.initialize()
        
        # Handle test modes
        if args.test_email:
            print("Testing email configuration...")
            success = await analyzer.test_email_configuration()
            if success:
                print("✓ Email configuration test successful")
                exit_code = 0
            else:
                print("✗ Email configuration test failed")
                exit_code = 1
            return exit_code
        
        if args.test_api:
            print("Testing API connectivity...")
            success = await analyzer.test_api_connectivity()
            if success:
                print("✓ API connectivity test successful")
                exit_code = 0
            else:
                print("✗ API connectivity test failed")
                exit_code = 1
            return exit_code
        
        # Run main analysis
        success = await analyzer.run_analysis(dry_run=args.dry_run)
        
        if success:
            print("✓ SMA crossover analysis completed successfully")
            exit_code = 0
        else:
            print("✗ SMA crossover analysis failed")
            exit_code = 1
        
    except ConfigurationError as e:
        print(f"CONFIGURATION ERROR: {str(e)}")
        exit_code = 1
        
    except APIError as e:
        print(f"API ERROR: {str(e)}")
        exit_code = 2
        
    except DataValidationError as e:
        print(f"DATA ERROR: {str(e)}")
        exit_code = 3
        
    except EmailError as e:
        print(f"EMAIL ERROR: {str(e)}")
        exit_code = 4
        
    except TQQQAnalyzerError as e:
        print(f"APPLICATION ERROR: {str(e)}")
        exit_code = 5
        
    except Exception as e:
        print(f"UNEXPECTED ERROR: {str(e)}")
        exit_code = 99
        
    finally:
        # Clean up
        analyzer.cleanup()
    
    return exit_code


if __name__ == "__main__":
    # Run the async main function
    exit_code = asyncio.run(main())
    sys.exit(exit_code)