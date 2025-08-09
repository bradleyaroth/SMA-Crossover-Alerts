"""
Unit tests for notification module.

Tests for email sender, templates, and notification logic.
"""

import pytest
import smtplib
from unittest.mock import Mock, patch, MagicMock
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List

# Import will be available once dependencies are installed
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from sma_crossover_alerts.notification.email_sender import EmailSender, send_analysis_email, send_error_email
from sma_crossover_alerts.notification.templates import EmailTemplates, generate_success_html, generate_success_text, generate_error_text
from sma_crossover_alerts.utils.exceptions import EmailError
from tests.fixtures.mock_data import MockEmailData, MockAnalysisData


class TestEmailTemplates:
    """Test cases for EmailTemplates."""
    
    def test_initialization(self):
        """Test EmailTemplates initialization."""
        templates = EmailTemplates()
        assert templates is not None
    
    def test_generate_success_email_html(self, sample_analysis_result):
        """Test success email generation in HTML format."""
        templates = EmailTemplates()
        
        subject, body = templates.generate_success_email(sample_analysis_result, format="html")
        
        assert subject is not None
        assert len(subject) > 0
        assert "TQQQ" in subject
        assert "2024-01-15" in subject
        
        assert body is not None
        assert len(body) > 0
        assert "<html>" in body
        assert "$46.23" in body
        assert "$42.15" in body
        assert "above" in body.lower()
    
    def test_generate_success_email_text(self, sample_analysis_result):
        """Test success email generation in text format."""
        templates = EmailTemplates()
        
        subject, body = templates.generate_success_email(sample_analysis_result, format="text")
        
        assert subject is not None
        assert len(subject) > 0
        assert "TQQQ" in subject
        
        assert body is not None
        assert len(body) > 0
        assert "<html>" not in body
        assert "$46.23" in body
        assert "$42.15" in body
        assert "above" in body.lower()
    
    def test_generate_error_email_html(self):
        """Test error email generation in HTML format."""
        templates = EmailTemplates()
        error_info = MockEmailData.get_sample_error_email_data()
        
        subject, body = templates.generate_error_email(error_info, format="html")
        
        assert subject is not None
        assert "Error" in subject
        assert "2024-01-15" in subject
        
        assert body is not None
        assert "<html>" in body
        assert "APIError" in body
        assert "Failed to fetch data" in body
    
    def test_generate_error_email_text(self):
        """Test error email generation in text format."""
        templates = EmailTemplates()
        error_info = MockEmailData.get_sample_error_email_data()
        
        subject, body = templates.generate_error_email(error_info, format="text")
        
        assert subject is not None
        assert "Error" in subject
        
        assert body is not None
        assert "<html>" not in body
        assert "APIError" in body
        assert "Failed to fetch data" in body
    
    def test_success_html_template(self, sample_analysis_result):
        """Test HTML template generation for success."""
        templates = EmailTemplates()
        
        html = templates.success_html_template(sample_analysis_result)
        
        assert html is not None
        assert "<html>" in html
        assert "<head>" in html
        assert "<body>" in html
        assert "TQQQ Analysis Report" in html
        assert "$46.23" in html
        assert "$42.15" in html
    
    def test_success_text_template(self, sample_analysis_result):
        """Test text template generation for success."""
        templates = EmailTemplates()
        
        text = templates.success_text_template(sample_analysis_result)
        
        assert text is not None
        assert "TQQQ STOCK ANALYSIS RESULTS" in text
        assert "$46.23" in text
        assert "$42.15" in text
        assert "Analysis Date: 2024-01-15" in text
    
    def test_error_html_template(self):
        """Test HTML template generation for errors."""
        templates = EmailTemplates()
        error_data = MockEmailData.get_sample_error_email_data()
        
        html = templates.error_html_template(error_data)
        
        assert html is not None
        assert "<html>" in html
        assert "TQQQ Analysis Error Report" in html
        assert "APIError" in html
        assert "Failed to fetch data" in html
    
    def test_error_text_template(self):
        """Test text template generation for errors."""
        templates = EmailTemplates()
        error_data = MockEmailData.get_sample_error_email_data()
        
        text = templates.error_text_template(error_data)
        
        assert text is not None
        assert "TQQQ ANALYSIS ERROR REPORT" in text
        assert "APIError" in text
        assert "Failed to fetch data" in text
    
    def test_format_analysis_result(self, sample_analysis_result):
        """Test analysis result formatting."""
        templates = EmailTemplates()
        
        formatted = templates.format_analysis_result(sample_analysis_result)
        
        assert formatted is not None
        assert "Current Price: $46.23" in formatted
        assert "200-day SMA: $42.15" in formatted
        assert "Status: ABOVE" in formatted
    
    def test_format_error_details(self):
        """Test error details formatting."""
        templates = EmailTemplates()
        error_info = MockEmailData.get_sample_error_email_data()
        
        formatted = templates.format_error_details(error_info)
        
        assert formatted is not None
        assert "Error Type: APIError" in formatted
        assert "Component: API" in formatted
        assert "Timestamp: 2024-01-15 18:00:00 UTC" in formatted


class TestEmailSender:
    """Test cases for EmailSender."""
    
    def test_initialization_valid_config(self):
        """Test EmailSender initialization with valid config."""
        config = {
            'smtp_server': 'smtp.test.com',
            'smtp_port': 587,
            'username': 'test@example.com',
            'password': 'test_password',
            'use_tls': True,
            'from_address': 'sender@example.com',
            'from_name': 'Test Sender'
        }
        
        sender = EmailSender(config)
        
        assert sender.smtp_server == 'smtp.test.com'
        assert sender.smtp_port == 587
        assert sender.username == 'test@example.com'
        assert sender.password == 'test_password'
        assert sender.use_tls is True
        assert sender.from_address == 'sender@example.com'
        assert sender.from_name == 'Test Sender'
    
    def test_initialization_missing_config(self):
        """Test EmailSender initialization with missing config."""
        config = {
            'smtp_server': 'smtp.test.com'
            # Missing required fields
        }
        
        with pytest.raises(KeyError):
            EmailSender(config)
    
    @patch('smtplib.SMTP')
    def test_create_smtp_connection_success(self, mock_smtp):
        """Test successful SMTP connection creation."""
        config = {
            'smtp_server': 'smtp.test.com',
            'smtp_port': 587,
            'username': 'test@example.com',
            'password': 'test_password',
            'use_tls': True,
            'from_address': 'sender@example.com',
            'from_name': 'Test Sender'
        }
        
        mock_server = Mock()
        mock_smtp.return_value = mock_server
        
        sender = EmailSender(config)
        connection = sender._create_smtp_connection()
        
        assert connection is mock_server
        mock_smtp.assert_called_once_with('smtp.test.com', 587)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with('test@example.com', 'test_password')
    
    @patch('smtplib.SMTP')
    def test_create_smtp_connection_no_tls(self, mock_smtp):
        """Test SMTP connection creation without TLS."""
        config = {
            'smtp_server': 'smtp.test.com',
            'smtp_port': 25,
            'username': 'test@example.com',
            'password': 'test_password',
            'use_tls': False,
            'from_address': 'sender@example.com',
            'from_name': 'Test Sender'
        }
        
        mock_server = Mock()
        mock_smtp.return_value = mock_server
        
        sender = EmailSender(config)
        connection = sender._create_smtp_connection()
        
        mock_server.starttls.assert_not_called()
        mock_server.login.assert_called_once_with('test@example.com', 'test_password')
    
    @patch('smtplib.SMTP')
    def test_create_smtp_connection_failure(self, mock_smtp):
        """Test SMTP connection creation failure."""
        config = {
            'smtp_server': 'smtp.test.com',
            'smtp_port': 587,
            'username': 'test@example.com',
            'password': 'test_password',
            'use_tls': True,
            'from_address': 'sender@example.com',
            'from_name': 'Test Sender'
        }
        
        mock_smtp.side_effect = smtplib.SMTPException("Connection failed")
        
        sender = EmailSender(config)
        
        with pytest.raises(EmailError) as exc_info:
            sender._create_smtp_connection()
        
        assert "Failed to create SMTP connection" in str(exc_info.value)
    
    @patch('smtplib.SMTP')
    def test_test_connection_success(self, mock_smtp):
        """Test successful connection test."""
        config = {
            'smtp_server': 'smtp.test.com',
            'smtp_port': 587,
            'username': 'test@example.com',
            'password': 'test_password',
            'use_tls': True,
            'from_address': 'sender@example.com',
            'from_name': 'Test Sender'
        }
        
        mock_server = Mock()
        mock_smtp.return_value = mock_server
        
        sender = EmailSender(config)
        result = sender.test_connection()
        
        assert result is True
        mock_server.quit.assert_called_once()
    
    @patch('smtplib.SMTP')
    def test_test_connection_failure(self, mock_smtp):
        """Test connection test failure."""
        config = {
            'smtp_server': 'smtp.test.com',
            'smtp_port': 587,
            'username': 'test@example.com',
            'password': 'test_password',
            'use_tls': True,
            'from_address': 'sender@example.com',
            'from_name': 'Test Sender'
        }
        
        mock_smtp.side_effect = smtplib.SMTPException("Connection failed")
        
        sender = EmailSender(config)
        result = sender.test_connection()
        
        assert result is False
    
    @patch('smtplib.SMTP')
    def test_send_email_success(self, mock_smtp):
        """Test successful email sending."""
        config = {
            'smtp_server': 'smtp.test.com',
            'smtp_port': 587,
            'username': 'test@example.com',
            'password': 'test_password',
            'use_tls': True,
            'from_address': 'sender@example.com',
            'from_name': 'Test Sender'
        }
        
        mock_server = Mock()
        mock_smtp.return_value = mock_server
        
        sender = EmailSender(config)
        result = sender.send_email(
            subject="Test Subject",
            body="Test Body",
            recipients=["recipient@example.com"],
            is_html=False
        )
        
        assert result is True
        mock_server.send_message.assert_called_once()
        mock_server.quit.assert_called_once()
    
    @patch('smtplib.SMTP')
    def test_send_email_html(self, mock_smtp):
        """Test HTML email sending."""
        config = {
            'smtp_server': 'smtp.test.com',
            'smtp_port': 587,
            'username': 'test@example.com',
            'password': 'test_password',
            'use_tls': True,
            'from_address': 'sender@example.com',
            'from_name': 'Test Sender'
        }
        
        mock_server = Mock()
        mock_smtp.return_value = mock_server
        
        sender = EmailSender(config)
        result = sender.send_email(
            subject="Test Subject",
            body="<html><body>Test HTML Body</body></html>",
            recipients=["recipient@example.com"],
            is_html=True
        )
        
        assert result is True
        
        # Verify HTML email was created
        call_args = mock_server.send_message.call_args[0][0]
        assert call_args.is_multipart()
    
    @patch('smtplib.SMTP')
    def test_send_email_failure(self, mock_smtp):
        """Test email sending failure."""
        config = {
            'smtp_server': 'smtp.test.com',
            'smtp_port': 587,
            'username': 'test@example.com',
            'password': 'test_password',
            'use_tls': True,
            'from_address': 'sender@example.com',
            'from_name': 'Test Sender'
        }
        
        mock_server = Mock()
        mock_server.send_message.side_effect = smtplib.SMTPException("Send failed")
        mock_smtp.return_value = mock_server
        
        sender = EmailSender(config)
        result = sender.send_email(
            subject="Test Subject",
            body="Test Body",
            recipients=["recipient@example.com"]
        )
        
        assert result is False
    
    @patch('smtplib.SMTP')
    def test_send_analysis_result_success(self, mock_smtp, sample_analysis_result):
        """Test successful analysis result email sending."""
        config = {
            'smtp_server': 'smtp.test.com',
            'smtp_port': 587,
            'username': 'test@example.com',
            'password': 'test_password',
            'use_tls': True,
            'from_address': 'sender@example.com',
            'from_name': 'Test Sender'
        }
        
        mock_server = Mock()
        mock_smtp.return_value = mock_server
        
        sender = EmailSender(config)
        result = sender.send_analysis_result(
            sample_analysis_result,
            ["recipient@example.com"]
        )
        
        assert result is True
        mock_server.send_message.assert_called()
    
    @patch('smtplib.SMTP')
    def test_send_error_notification_success(self, mock_smtp):
        """Test successful error notification sending."""
        config = {
            'smtp_server': 'smtp.test.com',
            'smtp_port': 587,
            'username': 'test@example.com',
            'password': 'test_password',
            'use_tls': True,
            'from_address': 'sender@example.com',
            'from_name': 'Test Sender'
        }
        
        mock_server = Mock()
        mock_smtp.return_value = mock_server
        
        error_info = MockEmailData.get_sample_error_email_data()
        
        sender = EmailSender(config)
        result = sender.send_error_notification(
            error_info,
            ["recipient@example.com"]
        )
        
        assert result is True
        mock_server.send_message.assert_called()
    
    def test_html_to_text_conversion(self):
        """Test HTML to text conversion."""
        config = {
            'smtp_server': 'smtp.test.com',
            'smtp_port': 587,
            'username': 'test@example.com',
            'password': 'test_password',
            'use_tls': True,
            'from_address': 'sender@example.com',
            'from_name': 'Test Sender'
        }
        
        sender = EmailSender(config)
        
        html_content = "<html><body><h1>Title</h1><p>Paragraph text</p></body></html>"
        text_content = sender._html_to_text(html_content)
        
        assert "Title" in text_content
        assert "Paragraph text" in text_content
        assert "<html>" not in text_content
        assert "<body>" not in text_content


class TestEmailUtilityFunctions:
    """Test cases for email utility functions."""
    
    @patch('smtplib.SMTP')
    def test_send_analysis_email_function(self, mock_smtp, sample_analysis_result):
        """Test send_analysis_email utility function."""
        smtp_config = {
            'smtp_server': 'smtp.test.com',
            'smtp_port': 587,
            'username': 'test@example.com',
            'password': 'test_password',
            'use_tls': True,
            'from_address': 'sender@example.com',
            'from_name': 'Test Sender'
        }
        
        mock_server = Mock()
        mock_smtp.return_value = mock_server
        
        result = send_analysis_email(
            smtp_config,
            sample_analysis_result,
            ["recipient@example.com"]
        )
        
        assert result is True
        mock_server.send_message.assert_called()
    
    @patch('smtplib.SMTP')
    def test_send_error_email_function(self, mock_smtp):
        """Test send_error_email utility function."""
        smtp_config = {
            'smtp_server': 'smtp.test.com',
            'smtp_port': 587,
            'username': 'test@example.com',
            'password': 'test_password',
            'use_tls': True,
            'from_address': 'sender@example.com',
            'from_name': 'Test Sender'
        }
        
        mock_server = Mock()
        mock_smtp.return_value = mock_server
        
        error_data = MockEmailData.get_sample_error_email_data()
        
        result = send_error_email(
            smtp_config,
            error_data,
            ["recipient@example.com"]
        )
        
        assert result is True
        mock_server.send_message.assert_called()


class TestEmailTemplateUtilityFunctions:
    """Test cases for email template utility functions."""
    
    def test_generate_success_html_function(self, sample_analysis_result):
        """Test generate_success_html utility function."""
        html = generate_success_html(sample_analysis_result)
        
        assert html is not None
        assert "<html>" in html
        assert "TQQQ Analysis Report" in html
        assert "$46.23" in html
    
    def test_generate_success_text_function(self, sample_analysis_result):
        """Test generate_success_text utility function."""
        text = generate_success_text(sample_analysis_result)
        
        assert text is not None
        assert "TQQQ STOCK ANALYSIS RESULTS" in text
        assert "$46.23" in text
        assert "<html>" not in text
    
    def test_generate_error_text_function(self):
        """Test generate_error_text utility function."""
        error_data = MockEmailData.get_sample_error_email_data()
        
        text = generate_error_text(error_data)
        
        assert text is not None
        assert "TQQQ ANALYSIS ERROR REPORT" in text
        assert "APIError" in text
        assert "<html>" not in text


if __name__ == "__main__":
    pytest.main([__file__])