"""
Email notification system for TQQQ analysis results.

This module handles SMTP email delivery with retry logic and
support for both HTML and plain text messages using Brevo SMTP.
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional, Dict, Any, Tuple
from tenacity import retry, stop_after_attempt, wait_exponential
from datetime import datetime
from .templates import EmailTemplates


class EmailSender:
    """
    SMTP email sender with retry logic and error handling for Brevo.
    
    This class handles email delivery for analysis results,
    errors, and system notifications using Brevo SMTP service.
    """
    
    def __init__(self, smtp_config: dict):
        """
        Initialize the email sender with Brevo SMTP configuration.
        
        Args:
            smtp_config: Dictionary containing SMTP configuration:
                - smtp_server: SMTP server hostname (smtp-relay.brevo.com)
                - smtp_port: SMTP server port (587)
                - username: SMTP username (no-reply@reliantrack.com)
                - password: SMTP password
                - use_tls: Whether to use TLS encryption (True)
                - from_name: Display name for sender
                - from_address: Sender email address
        """
        self.smtp_config = smtp_config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.templates = EmailTemplates()
        
        # Validate required configuration
        required_keys = ['smtp_server', 'smtp_port', 'username', 'password', 'from_address']
        for key in required_keys:
            if key not in smtp_config:
                raise ValueError(f"Missing required SMTP configuration: {key}")
    
    def _create_smtp_connection(self) -> smtplib.SMTP:
        """
        Create SMTP connection to Brevo server.
        
        Returns:
            smtplib.SMTP: Authenticated SMTP connection
            
        Raises:
            Exception: If connection or authentication fails
        """
        try:
            self.logger.debug(f"Connecting to SMTP server: {self.smtp_config['smtp_server']}:{self.smtp_config['smtp_port']}")
            
            smtp = smtplib.SMTP(self.smtp_config['smtp_server'], self.smtp_config['smtp_port'])
            
            # Enable TLS encryption
            if self.smtp_config.get('use_tls', True):
                smtp.starttls()
                self.logger.debug("TLS encryption enabled")
            
            # Authenticate with Brevo
            smtp.login(self.smtp_config['username'], self.smtp_config['password'])
            self.logger.debug("SMTP authentication successful")
            
            return smtp
            
        except Exception as e:
            self.logger.error(f"Failed to create SMTP connection: {e}")
            raise
    
    def test_connection(self) -> bool:
        """
        Test SMTP connection to Brevo server.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            with self._create_smtp_connection() as smtp:
                # Test the connection by sending NOOP command
                smtp.noop()
            self.logger.info("SMTP connection test successful")
            return True
            
        except Exception as e:
            self.logger.error(f"SMTP connection test failed: {e}")
            return False
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=60),
        reraise=True
    )
    def send_email(self, subject: str, body: str, recipients: List[str], 
                   is_html: bool = False) -> bool:
        """
        Send email with retry logic.
        
        Args:
            subject: Email subject
            body: Email body content
            recipients: List of recipient email addresses
            is_html: Whether body contains HTML content
            
        Returns:
            bool: True if email sent successfully
            
        Raises:
            Exception: If email sending fails after retries
        """
        try:
            # Create message
            if is_html:
                msg = MIMEMultipart('alternative')
                # Add plain text version (simplified HTML)
                text_part = MIMEText(self._html_to_text(body), 'plain')
                html_part = MIMEText(body, 'html')
                msg.attach(text_part)
                msg.attach(html_part)
            else:
                msg = MIMEText(body, 'plain')
            
            # Set headers
            msg['Subject'] = subject
            from_name = self.smtp_config.get('from_name', 'Stock Analysis System')
            msg['From'] = f"{from_name} <{self.smtp_config['from_address']}>"
            msg['To'] = ', '.join(recipients)
            
            # Send email using Brevo SMTP
            with self._create_smtp_connection() as smtp:
                smtp.send_message(msg)
            
            self.logger.info(f"Email sent successfully to {len(recipients)} recipients: {', '.join(recipients)}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send email: {str(e)}")
            raise
    
    def send_analysis_result(self, result: dict, recipients: List[str]) -> bool:
        """
        Send analysis result email with professional formatting.
        
        Args:
            result: Analysis result data containing:
                - current_price: Current TQQQ price
                - sma_value: 200-day SMA value
                - percentage_difference: Percentage difference
                - status: 'above', 'below', or 'equal'
                - message: Comparison message
                - analysis_date: Date of analysis
            recipients: List of recipient email addresses
            
        Returns:
            bool: True if email sent successfully
        """
        try:
            # Generate email content using templates
            subject, html_body = self.templates.generate_success_email(result, format="html")
            
            # Send HTML email
            return self.send_email(subject, html_body, recipients, is_html=True)
            
        except Exception as e:
            self.logger.error(f"Failed to send analysis result email: {e}")
            # Fallback to plain text
            try:
                subject, text_body = self.templates.generate_success_email(result, format="text")
                return self.send_email(subject, text_body, recipients, is_html=False)
            except Exception as fallback_error:
                self.logger.error(f"Fallback email also failed: {fallback_error}")
                raise
    
    def send_error_notification(self, error_info: dict, recipients: List[str]) -> bool:
        """
        Send error notification email.
        
        Args:
            error_info: Error information containing:
                - error_type: Type of error
                - error_message: Error message
                - error_timestamp: When error occurred
                - error_component: Component that failed
                - stack_trace: Stack trace (optional)
            recipients: List of recipient email addresses
            
        Returns:
            bool: True if email sent successfully
        """
        try:
            # Generate error email content
            subject, html_body = self.templates.generate_error_email(error_info, format="html")
            
            # Send HTML email
            return self.send_email(subject, html_body, recipients, is_html=True)
            
        except Exception as e:
            self.logger.error(f"Failed to send error notification email: {e}")
            # Fallback to plain text
            try:
                subject, text_body = self.templates.generate_error_email(error_info, format="text")
                return self.send_email(subject, text_body, recipients, is_html=False)
            except Exception as fallback_error:
                self.logger.error(f"Fallback error email also failed: {fallback_error}")
                raise
    
    def _html_to_text(self, html_content: str) -> str:
        """
        Convert HTML content to plain text for multipart emails.
        
        Args:
            html_content: HTML content
            
        Returns:
            str: Plain text version
        """
        # Simple HTML to text conversion
        import re
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html_content)
        
        # Replace HTML entities
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text


# Legacy compatibility - maintain existing interface
def send_analysis_email(smtp_config: dict, analysis_data: dict, recipients: List[str]) -> bool:
    """
    Legacy function for sending analysis emails.
    
    Args:
        smtp_config: SMTP configuration dictionary
        analysis_data: Analysis result data
        recipients: List of recipient email addresses
        
    Returns:
        bool: True if email sent successfully
    """
    sender = EmailSender(smtp_config)
    return sender.send_analysis_result(analysis_data, recipients)


def send_error_email(smtp_config: dict, error_data: dict, recipients: List[str]) -> bool:
    """
    Legacy function for sending error emails.
    
    Args:
        smtp_config: SMTP configuration dictionary
        error_data: Error information
        recipients: List of recipient email addresses
        
    Returns:
        bool: True if email sent successfully
    """
    sender = EmailSender(smtp_config)
    return sender.send_error_notification(error_data, recipients)