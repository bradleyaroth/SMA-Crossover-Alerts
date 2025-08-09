"""
Email templates for TQQQ analysis notifications.

This module contains HTML and plain text email templates
for analysis results, errors, and system notifications.
"""

from typing import Dict, Any, Tuple
from datetime import datetime


class EmailTemplates:
    """
    Email template generator for various notification types.
    """
    
    def generate_success_email(self, result: dict, format: str = "html") -> Tuple[str, str]:
        """
        Generate success email with subject and body.
        
        Args:
            result: Analysis result data
            format: "html" or "text"
            
        Returns:
            tuple: (subject, body)
        """
        # Generate subject
        status = result.get('status', 'unknown').upper()
        date_str = result.get('analysis_date', datetime.now().strftime('%Y-%m-%d'))
        symbol = result.get('symbol', 'TQQQ').upper()
        subject = f"{symbol} Analysis: {status} 200-Day SMA - {date_str}"
        
        # Generate body based on format
        if format.lower() == "html":
            body = self.success_html_template(result)
        else:
            body = self.success_text_template(result)
            
        return subject, body
    
    def generate_error_email(self, error_info: dict, format: str = "html") -> Tuple[str, str]:
        """
        Generate error email with subject and body.
        
        Args:
            error_info: Error information
            format: "html" or "text"
            
        Returns:
            tuple: (subject, body)
        """
        # Generate subject
        error_type = error_info.get('error_type', 'Unknown Error')
        date_str = error_info.get('error_date', datetime.now().strftime('%Y-%m-%d'))
        symbol = error_info.get('symbol', 'TQQQ').upper()
        subject = f"{symbol} Analysis Error - {error_type} - {date_str}"
        
        # Generate body based on format
        if format.lower() == "html":
            body = self.error_html_template(error_info)
        else:
            body = self.error_text_template(error_info)
            
        return subject, body
    
    def success_html_template(self, data: Dict[str, Any]) -> str:
        """
        Generate HTML template for successful analysis results.
        
        Args:
            data: Analysis result data
            
        Returns:
            str: HTML email content
        """
        # Determine trend signal class for styling
        status = data.get('status', 'unknown').lower()
        if status == 'above':
            trend_class = 'trend-bullish'
            trend_signal = 'BULLISH'
        elif status == 'below':
            trend_class = 'trend-bearish'
            trend_signal = 'BEARISH'
        else:
            trend_class = 'trend-neutral'
            trend_signal = 'NEUTRAL'
        
        # Format data
        current_price = data.get('current_price', 0)
        sma_value = data.get('sma_value', 0)
        percentage_diff = data.get('percentage_difference', 0)
        message = data.get('message', 'No message available')
        analysis_date = data.get('analysis_date', datetime.now().strftime('%Y-%m-%d'))
        symbol = data.get('symbol', 'TQQQ').upper()
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
        
        # Create detailed message
        detailed_message = self.format_analysis_result(data)
        
        template = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{symbol} Stock Analysis Results</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f9f9f9; }}
        .container {{ max-width: 600px; margin: 0 auto; background-color: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .header {{ background-color: #2c3e50; color: white; padding: 20px; border-radius: 8px 8px 0 0; text-align: center; }}
        .content {{ padding: 20px; }}
        .result-box {{ background-color: #e8f5e8; padding: 15px; margin: 15px 0; border-radius: 5px; border-left: 4px solid #27ae60; }}
        .data-table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        .data-table th, .data-table td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
        .data-table th {{ background-color: #f8f9fa; font-weight: bold; }}
        .footer {{ background-color: #ecf0f1; padding: 15px; border-radius: 0 0 8px 8px; font-size: 12px; color: #7f8c8d; text-align: center; }}
        .trend-bullish {{ color: #27ae60; font-weight: bold; }}
        .trend-bearish {{ color: #e74c3c; font-weight: bold; }}
        .trend-neutral {{ color: #f39c12; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{symbol} Stock Analysis</h1>
            <p>Daily 200-Day SMA Comparison</p>
        </div>
        
        <div class="content">
            <div class="result-box">
                <h2>{message}</h2>
                <p><strong>Analysis Date:</strong> {analysis_date}</p>
            </div>
            
            <table class="data-table">
                <tr>
                    <th>Metric</th>
                    <th>Value</th>
                </tr>
                <tr>
                    <td>Current Closing Price</td>
                    <td>${current_price:.2f}</td>
                </tr>
                <tr>
                    <td>200-Day Simple Moving Average</td>
                    <td>${sma_value:.2f}</td>
                </tr>
                <tr>
                    <td>Percentage Difference</td>
                    <td>{percentage_diff:.2f}%</td>
                </tr>
                <tr>
                    <td>Trend Signal</td>
                    <td><span class="{trend_class}">{trend_signal}</span></td>
                </tr>
            </table>
            
            <p><strong>Analysis Summary:</strong></p>
            <p>{detailed_message}</p>
        </div>
        
        <div class="footer">
            <p>Generated by {symbol} Analysis System at {timestamp}</p>
            <p>This is an automated analysis for informational purposes only.</p>
        </div>
    </div>
</body>
</html>
        """
        return template.strip()
    
    def success_text_template(self, data: Dict[str, Any]) -> str:
        """
        Generate plain text template for successful analysis results.
        
        Args:
            data: Analysis result data
            
        Returns:
            str: Plain text email content
        """
        current_price = data.get('current_price', 0)
        sma_value = data.get('sma_value', 0)
        percentage_diff = data.get('percentage_difference', 0)
        status = data.get('status', 'unknown').upper()
        message = data.get('message', 'No message available')
        analysis_date = data.get('analysis_date', datetime.now().strftime('%Y-%m-%d'))
        symbol = data.get('symbol', 'TQQQ').upper()
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
        
        # Determine trend signal
        if status == 'ABOVE':
            trend_signal = 'BULLISH'
        elif status == 'BELOW':
            trend_signal = 'BEARISH'
        else:
            trend_signal = 'NEUTRAL'
        
        detailed_message = self.format_analysis_result(data)
        
        template = f"""
{symbol} STOCK ANALYSIS RESULTS
===========================

{message}

Analysis Date: {analysis_date}

MARKET DATA:
- Current Closing Price: ${current_price:.2f}
- 200-Day Simple Moving Average: ${sma_value:.2f}
- Percentage Difference: {percentage_diff:.2f}%
- Trend Signal: {trend_signal}

ANALYSIS SUMMARY:
{detailed_message}

TECHNICAL DETAILS:
- Data Source: Alpha Vantage API
- Analysis Time: {timestamp}
- Symbol: {symbol}
- SMA Period: 200 days

DISCLAIMER:
This is an automated analysis for informational purposes only.
Not financial advice. Please consult with a financial advisor.

---
Generated by {symbol} Analysis System
        """
        return template.strip()
    
    def error_html_template(self, error_data: Dict[str, Any]) -> str:
        """
        Generate HTML template for error notifications.
        
        Args:
            error_data: Error information
            
        Returns:
            str: HTML error email content
        """
        error_type = error_data.get('error_type', 'Unknown Error')
        error_message = error_data.get('error_message', 'No message available')
        error_timestamp = error_data.get('error_timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'))
        error_component = error_data.get('error_component', 'Unknown Component')
        stack_trace = error_data.get('stack_trace', 'No stack trace available')
        symbol = error_data.get('symbol', 'TQQQ').upper()
        
        template = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{symbol} Analysis Error Notification</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f9f9f9; }}
        .container {{ max-width: 600px; margin: 0 auto; background-color: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .header {{ background-color: #e74c3c; color: white; padding: 20px; border-radius: 8px 8px 0 0; text-align: center; }}
        .content {{ padding: 20px; }}
        .error-box {{ background-color: #fdf2f2; padding: 15px; margin: 15px 0; border-radius: 5px; border-left: 4px solid #e74c3c; }}
        .data-table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        .data-table th, .data-table td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
        .data-table th {{ background-color: #f8f9fa; font-weight: bold; }}
        .stack-trace {{ background-color: #f8f9fa; padding: 10px; border-radius: 5px; font-family: monospace; font-size: 12px; overflow-x: auto; }}
        .footer {{ background-color: #ecf0f1; padding: 15px; border-radius: 0 0 8px 8px; font-size: 12px; color: #7f8c8d; text-align: center; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚠️ {symbol} Analysis Error</h1>
            <p>System Error Notification</p>
        </div>
        
        <div class="content">
            <div class="error-box">
                <h2>Error Detected</h2>
                <p>The {symbol} analysis system encountered an error during execution.</p>
            </div>
            
            <table class="data-table">
                <tr>
                    <th>Error Details</th>
                    <th>Information</th>
                </tr>
                <tr>
                    <td>Error Type</td>
                    <td>{error_type}</td>
                </tr>
                <tr>
                    <td>Error Message</td>
                    <td>{error_message}</td>
                </tr>
                <tr>
                    <td>Timestamp</td>
                    <td>{error_timestamp}</td>
                </tr>
                <tr>
                    <td>Component</td>
                    <td>{error_component}</td>
                </tr>
            </table>
            
            <h3>Stack Trace:</h3>
            <div class="stack-trace">
                {stack_trace}
            </div>
            
            <p><strong>Next Steps:</strong></p>
            <ul>
                <li>Check the application logs for more detailed information</li>
                <li>Verify API connectivity and credentials</li>
                <li>Ensure all system dependencies are available</li>
                <li>Contact system administrator if the issue persists</li>
            </ul>
        </div>
        
        <div class="footer">
            <p>{symbol} Analysis System Error Notification</p>
            <p>This is an automated error report.</p>
        </div>
    </div>
</body>
</html>
        """
        return template.strip()
    
    def error_text_template(self, error_data: Dict[str, Any]) -> str:
        """
        Generate plain text template for error notifications.
        
        Args:
            error_data: Error information
            
        Returns:
            str: Plain text error email content
        """
        error_type = error_data.get('error_type', 'Unknown Error')
        error_message = error_data.get('error_message', 'No message available')
        error_timestamp = error_data.get('error_timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'))
        error_component = error_data.get('error_component', 'Unknown Component')
        stack_trace = error_data.get('stack_trace', 'No stack trace available')
        symbol = error_data.get('symbol', 'TQQQ').upper()
        
        template = f"""
{symbol} ANALYSIS ERROR NOTIFICATION
================================

⚠️  ERROR DETECTED

The {symbol} analysis system encountered an error during execution.

ERROR DETAILS:
- Error Type: {error_type}
- Error Message: {error_message}
- Timestamp: {error_timestamp}
- Component: {error_component}

STACK TRACE:
{stack_trace}

TROUBLESHOOTING STEPS:
1. Check the application logs for more detailed information
2. Verify API connectivity and credentials
3. Ensure all system dependencies are available
4. Contact system administrator if the issue persists

SYSTEM INFORMATION:
- Python Version: {error_data.get('python_version', 'Unknown')}
- Server: {error_data.get('hostname', 'Unknown')}
- Log File: {error_data.get('log_file_path', 'Unknown')}

Please check the logs for more detailed information.

---
{symbol} Analysis System Error Notification
This is an automated error report.
        """
        return template.strip()
    
    def format_analysis_result(self, result: dict) -> str:
        """
        Format analysis result into a readable summary.
        
        Args:
            result: Analysis result data
            
        Returns:
            str: Formatted analysis summary
        """
        current_price = result.get('current_price', 0)
        sma_value = result.get('sma_value', 0)
        percentage_diff = result.get('percentage_difference', 0)
        status = result.get('status', 'unknown')
        symbol = result.get('symbol', 'TQQQ').upper()
        
        if status == 'above':
            summary = f"{symbol} is currently trading ${current_price:.2f}, which is {abs(percentage_diff):.2f}% above its 200-day Simple Moving Average of ${sma_value:.2f}. This indicates a bullish trend and potential upward momentum."
        elif status == 'below':
            summary = f"{symbol} is currently trading ${current_price:.2f}, which is {abs(percentage_diff):.2f}% below its 200-day Simple Moving Average of ${sma_value:.2f}. This indicates a bearish trend and potential downward pressure."
        else:
            summary = f"{symbol} is currently trading ${current_price:.2f}, which is approximately equal to its 200-day Simple Moving Average of ${sma_value:.2f}. This indicates a neutral trend."
        
        return summary
    
    def format_error_details(self, error_info: dict) -> str:
        """
        Format error details into a readable summary.
        
        Args:
            error_info: Error information
            
        Returns:
            str: Formatted error summary
        """
        error_type = error_info.get('error_type', 'Unknown Error')
        error_message = error_info.get('error_message', 'No message available')
        error_component = error_info.get('error_component', 'Unknown Component')
        
        summary = f"A {error_type} occurred in the {error_component} component. Error details: {error_message}"
        
        return summary


# Legacy compatibility functions
def generate_success_html(data: Dict[str, Any]) -> str:
    """Legacy function for generating success HTML."""
    templates = EmailTemplates()
    return templates.success_html_template(data)


def generate_success_text(data: Dict[str, Any]) -> str:
    """Legacy function for generating success text."""
    templates = EmailTemplates()
    return templates.success_text_template(data)


def generate_error_text(error_data: Dict[str, Any]) -> str:
    """Legacy function for generating error text."""
    templates = EmailTemplates()
    return templates.error_text_template(error_data)