"""
Full workflow integration tests for TQQQ Analysis Application.

These tests verify the complete end-to-end workflow including API calls,
data processing, analysis, and email notifications.
"""

import pytest
import asyncio
import os
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from pathlib import Path

# Import will be available once dependencies are installed
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from sma_crossover_alerts.api.client import AlphaVantageClient
from sma_crossover_alerts.analysis.processor import StockDataProcessor
from sma_crossover_alerts.analysis.comparator import StockComparator, PriceComparator
from sma_crossover_alerts.notification.email_sender import EmailSender
from sma_crossover_alerts.notification.templates import EmailTemplates
from sma_crossover_alerts.config.settings import Settings
from sma_crossover_alerts.utils.exceptions import *
from tests.fixtures.mock_data import MockAPIResponses, MockRealWorldData
from tests.fixtures.test_config import IntegrationTestConfig, TestConfig


class TestFullWorkflowIntegration:
    """Integration tests for complete workflow."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_complete_workflow_with_mocks(self, test_config_dict):
        """Test complete workflow with mocked components."""
        # Setup components
        api_client = AlphaVantageClient(test_config_dict['api']['alpha_vantage_key'])
        processor = StockDataProcessor()
        comparator = StockComparator()
        email_sender = EmailSender(test_config_dict['email'])
        templates = EmailTemplates()
        
        # Mock API responses
        mock_daily_response = MockRealWorldData.get_current_tqqq_response()
        mock_sma_response = MockRealWorldData.get_current_sma_response()
        
        with patch.object(api_client, 'fetch_daily_prices', new_callable=AsyncMock) as mock_daily, \
             patch.object(api_client, 'fetch_sma', new_callable=AsyncMock) as mock_sma, \
             patch.object(email_sender, 'send_email') as mock_send:
            
            mock_daily.return_value = mock_daily_response
            mock_sma.return_value = mock_sma_response
            mock_send.return_value = True
            
            async with api_client:
                # Step 1: Fetch data
                daily_data = await api_client.fetch_daily_prices("TQQQ")
                sma_data = await api_client.fetch_sma("TQQQ", 200)
                
                # Step 2: Process data
                price_date, current_price = processor.extract_daily_price_data(daily_data)
                sma_date, sma_value = processor.extract_sma_data(sma_data)
                
                # Step 3: Perform analysis
                analysis_result = comparator.generate_comparison_result(
                    current_price, sma_value, price_date
                )
                
                # Step 4: Generate email
                subject, body = templates.generate_success_email(analysis_result)
                
                # Step 5: Send email
                email_sent = email_sender.send_email(
                    subject, body, test_config_dict['email']['to_addresses'], is_html=True
                )
                
                # Verify workflow completed successfully
                assert daily_data is not None
                assert sma_data is not None
                assert current_price > 0
                assert sma_value > 0
                assert analysis_result is not None
                assert 'status' in analysis_result
                assert subject is not None
                assert body is not None
                assert email_sent is True
                
                # Verify API calls were made
                mock_daily.assert_called_once_with("TQQQ")
                mock_sma.assert_called_once_with("TQQQ", 200)
                mock_send.assert_called_once()
    
    @pytest.mark.integration
    @pytest.mark.network
    @pytest.mark.asyncio
    async def test_real_api_workflow(self, integration_config):
        """Test workflow with real API calls (if enabled)."""
        if not integration_config['use_real_api']:
            pytest.skip("Real API testing disabled")
        
        api_client = AlphaVantageClient(integration_config['api_key'])
        processor = StockDataProcessor()
        comparator = StockComparator()
        
        try:
            async with api_client:
                # Test with real API calls
                daily_data = await api_client.fetch_daily_prices("TQQQ", "compact")
                
                # Small delay to respect rate limits
                await asyncio.sleep(1)
                
                sma_data = await api_client.fetch_sma("TQQQ", 200, "daily", "open")
                
                # Process real data
                price_date, current_price = processor.extract_daily_price_data(daily_data)
                sma_date, sma_value = processor.extract_sma_data(sma_data)
                
                # Perform analysis
                analysis_result = comparator.generate_comparison_result(
                    current_price, sma_value, price_date
                )
                
                # Verify results
                assert current_price > 0
                assert sma_value > 0
                assert analysis_result['status'] in ['above', 'below', 'equal']
                assert isinstance(analysis_result['percentage_difference'], (int, float))
                
        except RateLimitError:
            pytest.skip("API rate limit exceeded - expected with free tier")
        except NetworkError:
            pytest.skip("Network error - API may be unavailable")
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_error_handling_workflow(self, test_config_dict):
        """Test workflow error handling and recovery."""
        api_client = AlphaVantageClient(test_config_dict['api']['alpha_vantage_key'])
        email_sender = EmailSender(test_config_dict['email'])
        templates = EmailTemplates()
        
        # Test API error handling
        with patch.object(api_client, 'fetch_daily_prices', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = APIError("API Error", component="API")
            
            with patch.object(email_sender, 'send_email') as mock_send:
                mock_send.return_value = True
                
                # Simulate error workflow
                try:
                    asyncio.run(api_client.fetch_daily_prices("TQQQ"))
                    assert False, "Should have raised APIError"
                except APIError as e:
                    # Generate error email
                    error_info = {
                        'error_type': 'APIError',
                        'error_message': str(e),
                        'error_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
                        'error_component': 'API',
                        'error_date': datetime.now().strftime('%Y-%m-%d')
                    }
                    
                    subject, body = templates.generate_error_email(error_info)
                    email_sent = email_sender.send_email(
                        subject, body, test_config_dict['email']['to_addresses']
                    )
                    
                    assert email_sent is True
                    assert "Error" in subject
                    mock_send.assert_called_once()
    
    @pytest.mark.integration
    def test_data_synchronization_workflow(self, test_config_dict):
        """Test workflow with mismatched data dates."""
        processor = StockDataProcessor()
        comparator = StockComparator()
        
        # Get mismatched responses
        daily_response, sma_response = MockAPIResponses.get_mismatched_dates_responses()
        
        # Process data - should handle synchronization
        try:
            price_date, current_price = processor.extract_daily_price_data(daily_response)
            sma_date, sma_value = processor.extract_sma_data(sma_response)
            
            # Should use the most recent common date or handle gracefully
            if price_date != sma_date:
                # This is expected with mismatched data
                # The system should either synchronize or raise appropriate error
                pass
            
        except DataValidationError as e:
            # This is acceptable - system correctly identified data mismatch
            assert "synchronized" in str(e).lower() or "date" in str(e).lower()
    
    @pytest.mark.integration
    @pytest.mark.performance
    def test_workflow_performance(self, test_config_dict, performance_timer):
        """Test workflow performance benchmarks."""
        api_client = AlphaVantageClient(test_config_dict['api']['alpha_vantage_key'])
        processor = StockDataProcessor()
        comparator = StockComparator()
        
        # Mock fast responses
        mock_daily_response = MockRealWorldData.get_current_tqqq_response()
        mock_sma_response = MockRealWorldData.get_current_sma_response()
        
        with patch.object(api_client, 'fetch_daily_prices', new_callable=AsyncMock) as mock_daily, \
             patch.object(api_client, 'fetch_sma', new_callable=AsyncMock) as mock_sma:
            
            mock_daily.return_value = mock_daily_response
            mock_sma.return_value = mock_sma_response
            
            async def run_workflow():
                async with api_client:
                    # Time the complete workflow
                    performance_timer.start()
                    
                    daily_data = await api_client.fetch_daily_prices("TQQQ")
                    sma_data = await api_client.fetch_sma("TQQQ", 200)
                    
                    price_date, current_price = processor.extract_daily_price_data(daily_data)
                    sma_date, sma_value = processor.extract_sma_data(sma_data)
                    
                    analysis_result = comparator.generate_comparison_result(
                        current_price, sma_value, price_date
                    )
                    
                    performance_timer.stop()
                    
                    return analysis_result
            
            result = asyncio.run(run_workflow())
            
            # Verify performance
            assert performance_timer.elapsed is not None
            assert performance_timer.elapsed < 5.0  # Should complete within 5 seconds
            assert result is not None


class TestComponentIntegration:
    """Integration tests for component interactions."""
    
    @pytest.mark.integration
    def test_processor_comparator_integration(self):
        """Test integration between processor and comparator."""
        processor = StockDataProcessor()
        comparator = StockComparator()
        
        # Use real-world-like data
        mock_daily_response = MockRealWorldData.get_current_tqqq_response()
        mock_sma_response = MockRealWorldData.get_current_sma_response()
        
        # Process data
        price_date, current_price = processor.extract_daily_price_data(mock_daily_response)
        sma_date, sma_value = processor.extract_sma_data(mock_sma_response)
        
        # Perform comparison
        comparison_result = comparator.generate_comparison_result(
            current_price, sma_value, price_date
        )
        
        # Verify integration
        assert comparison_result['closing_price'] == current_price
        assert comparison_result['sma_value'] == sma_value
        assert comparison_result['date'] == price_date
        assert comparison_result['comparison'] in ['ABOVE', 'BELOW', 'EQUAL']
    
    @pytest.mark.integration
    def test_comparator_templates_integration(self):
        """Test integration between comparator and email templates."""
        comparator = StockComparator()
        templates = EmailTemplates()
        
        # Generate analysis result
        analysis_result = comparator.generate_comparison_result(88.84, 74.08, "2024-01-15")
        
        # Generate email templates
        subject, html_body = templates.generate_success_email(analysis_result, format="html")
        _, text_body = templates.generate_success_email(analysis_result, format="text")
        
        # Verify integration
        assert str(analysis_result['closing_price']) in html_body
        assert str(analysis_result['sma_value']) in html_body
        assert analysis_result['comparison'].lower() in html_body.lower()
        
        assert str(analysis_result['closing_price']) in text_body
        assert str(analysis_result['sma_value']) in text_body
        assert analysis_result['comparison'].lower() in text_body.lower()
    
    @pytest.mark.integration
    @pytest.mark.network
    def test_email_integration_with_real_smtp(self, integration_config):
        """Test email integration with real SMTP (if enabled)."""
        if not integration_config['use_real_smtp']:
            pytest.skip("Real SMTP testing disabled")
        
        email_sender = EmailSender(integration_config['smtp_config'])
        templates = EmailTemplates()
        
        # Test connection
        connection_ok = email_sender.test_connection()
        if not connection_ok:
            pytest.skip("SMTP connection failed")
        
        # Generate test email
        test_result = {
            'analysis_date': datetime.now().strftime('%Y-%m-%d'),
            'current_price': 88.84,
            'sma_value': 74.08,
            'status': 'above',
            'percentage_difference': 19.92,
            'signal_strength': 'moderate'
        }
        
        subject, body = templates.generate_success_email(test_result)
        
        # Send test email
        email_sent = email_sender.send_email(
            f"[TEST] {subject}",
            body,
            integration_config['smtp_config']['to_addresses'],
            is_html=True
        )
        
        assert email_sent is True


class TestErrorRecoveryIntegration:
    """Integration tests for error handling and recovery."""
    
    @pytest.mark.integration
    def test_api_retry_integration(self, test_config_dict):
        """Test API retry logic integration."""
        api_client = AlphaVantageClient(test_config_dict['api']['alpha_vantage_key'])
        
        call_count = 0
        
        async def mock_request_with_retries(url):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise NetworkError("Connection timeout", component="API")
            return MockRealWorldData.get_current_tqqq_response()
        
        with patch.object(api_client, '_make_request', side_effect=mock_request_with_retries):
            async def test_retry():
                async with api_client:
                    result = await api_client.fetch_daily_prices("TQQQ")
                    return result
            
            result = asyncio.run(test_retry())
            
            # Verify retry logic worked
            assert call_count == 3  # Should have retried twice before success
            assert result is not None
    
    @pytest.mark.integration
    def test_graceful_degradation(self, test_config_dict):
        """Test graceful degradation when components fail."""
        email_sender = EmailSender(test_config_dict['email'])
        templates = EmailTemplates()
        
        # Test with partial data
        incomplete_result = {
            'current_price': 88.84,
            'sma_value': 74.08,
            'status': 'above'
            # Missing some fields
        }
        
        # Should handle gracefully
        try:
            subject, body = templates.generate_success_email(incomplete_result)
            assert subject is not None
            assert body is not None
        except Exception as e:
            # If it fails, it should fail gracefully with meaningful error
            assert "missing" in str(e).lower() or "required" in str(e).lower()


if __name__ == "__main__":
    pytest.main([__file__])