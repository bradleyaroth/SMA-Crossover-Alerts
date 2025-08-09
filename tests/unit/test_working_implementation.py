"""
Working validation tests that match actual implementation
"""
import pytest
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

class TestActualImplementation:
    """Tests that validate actual working functionality"""
    
    def test_can_import_core_modules(self):
        """Test that core modules can be imported"""
        try:
            from sma_crossover_alerts.analysis.processor import DataProcessor, StockDataProcessor
            from sma_crossover_alerts.analysis.comparator import PriceComparator, StockComparator
            from sma_crossover_alerts.api.client import AlphaVantageClient
            from sma_crossover_alerts.notification.email_sender import EmailSender
            assert True
        except ImportError as e:
            pytest.fail(f"Failed to import core modules: {e}")
    
    def test_data_processor_initialization(self):
        """Test DataProcessor can be initialized"""
        from sma_crossover_alerts.analysis.processor import DataProcessor
        processor = DataProcessor()
        assert processor is not None
    
    def test_stock_data_processor_initialization(self):
        """Test StockDataProcessor can be initialized"""
        from sma_crossover_alerts.analysis.processor import StockDataProcessor
        processor = StockDataProcessor()
        assert processor is not None
    
    def test_price_comparator_initialization(self):
        """Test PriceComparator can be initialized"""
        from sma_crossover_alerts.analysis.comparator import PriceComparator
        comparator = PriceComparator()
        assert comparator is not None
    
    def test_stock_comparator_initialization(self):
        """Test StockComparator can be initialized"""
        from sma_crossover_alerts.analysis.comparator import StockComparator
        comparator = StockComparator()
        assert comparator is not None
    
    def test_email_sender_with_valid_config(self):
        """Test EmailSender with minimal valid config"""
        from sma_crossover_alerts.notification.email_sender import EmailSender
        
        config = {
            'smtp_server': 'smtp.test.com',
            'smtp_port': 587,
            'username': 'test@test.com',
            'password': 'testpass',
            'from_address': 'test@test.com'
        }
        
        sender = EmailSender(config)
        assert sender is not None
    
    def test_api_client_initialization(self):
        """Test AlphaVantageClient can be initialized"""
        from sma_crossover_alerts.api.client import AlphaVantageClient
        
        client = AlphaVantageClient(api_key="test_key")
        assert client is not None
        assert client.api_key == "test_key"
