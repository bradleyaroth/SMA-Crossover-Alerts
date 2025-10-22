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
        # Generate subject - use date from result or current date
        date_str = result.get('date', result.get('analysis_date', datetime.now().strftime('%Y-%m-%d')))
        subject = f"TQQQ Strategy: {date_str}"
        
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
        # Extract data
        recommendation = data.get('recommendation', 'NO RECOMMENDATION')
        explanation = data.get('explanation', 'No explanation available')
        signal_event = data.get('signal_event')
        date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
        
        spy = data.get('spy', {})
        qqq = data.get('qqq', {})
        tqqq = data.get('tqqq')
        
        # Determine recommendation box color
        if 'BUY' in recommendation or 'HOLD' in recommendation:
            rec_color = '#27ae60'
            rec_bg = '#e8f5e8'
        elif 'EXIT' in recommendation or 'SELL' in recommendation:
            rec_color = '#e74c3c'
            rec_bg = '#fdf2f2'
        else:
            rec_color = '#f39c12'
            rec_bg = '#fff8e1'
        
        # Build signal event alert if present
        signal_alert = ''
        if signal_event:
            signal_alert = f"""
            <div style="background-color: #fff3cd; padding: 12px; margin: 15px 0; border-radius: 5px; border-left: 4px solid #ffc107; font-weight: bold;">
                {signal_event}
            </div>
            """
        
        # Build TQQQ section if data is available
        tqqq_section = ''
        if tqqq:
            tqqq_section = f"""
            <div style="background-color: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #6c757d;">
                <h3 style="margin-top: 0; color: #2c3e50;">TQQQ (Reference)</h3>
                <p style="margin: 5px 0;"><strong>Current Price:</strong> ${tqqq.get('price', 0):.2f}</p>
            </div>
            """
        
        template = f"""
<!DOCTYPE html>
<html>
<head>
    <title>TQQQ Strategy Analysis</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f9f9f9; }}
        .container {{ max-width: 700px; margin: 0 auto; background-color: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .header {{ background-color: #2c3e50; color: white; padding: 20px; border-radius: 8px 8px 0 0; text-align: center; }}
        .content {{ padding: 20px; }}
        .recommendation-box {{ background-color: {rec_bg}; padding: 20px; margin: 15px 0; border-radius: 5px; border-left: 6px solid {rec_color}; text-align: center; }}
        .recommendation-box h2 {{ margin: 0 0 10px 0; color: {rec_color}; font-size: 24px; }}
        .ticker-card {{ background-color: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; }}
        .ticker-header {{ font-size: 18px; font-weight: bold; margin-bottom: 10px; color: #2c3e50; }}
        .ticker-data {{ margin: 5px 0; }}
        .explanation-box {{ background-color: #e3f2fd; padding: 15px; margin: 15px 0; border-radius: 5px; border-left: 4px solid #2196f3; }}
        .footer {{ background-color: #ecf0f1; padding: 15px; border-radius: 0 0 8px 8px; font-size: 12px; color: #7f8c8d; text-align: center; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 TQQQ Investment Strategy</h1>
            <p>Multi-Ticker Analysis Report</p>
        </div>
        
        <div class="content">
            <div class="recommendation-box">
                <h2>📊 CURRENT RECOMMENDATION</h2>
                <p style="font-size: 20px; font-weight: bold; margin: 10px 0;">{recommendation}</p>
                <p style="font-size: 14px; color: #666; margin: 5px 0;">Analysis Date: {date}</p>
            </div>
            
            {signal_alert}
            
            <h3 style="color: #2c3e50; border-bottom: 2px solid #2c3e50; padding-bottom: 5px;">Multi-Ticker Dashboard</h3>
            
            <div class="ticker-card">
                <div class="ticker-header">SPY (Primary Signal)</div>
                <div class="ticker-data"><strong>Price:</strong> ${spy.get('price', 0):.2f}</div>
                <div class="ticker-data"><strong>200-day SMA:</strong> ${spy.get('sma', 0):.2f}</div>
                <div class="ticker-data"><strong>Difference:</strong> <span style="color: {self._get_color_hex(spy.get('color'))}; font-weight: bold;">{spy.get('percentage_diff', 0):+.2f}%</span></div>
                <div class="ticker-data"><strong>Status:</strong> <span style="color: {self._get_color_hex(spy.get('color'))}; font-weight: bold;">{spy.get('status', 'UNKNOWN')}</span></div>
            </div>
            
            <div class="ticker-card">
                <div class="ticker-header">QQQ (Bubble Protection)</div>
                <div class="ticker-data"><strong>Price:</strong> ${qqq.get('price', 0):.2f}</div>
                <div class="ticker-data"><strong>200-day SMA:</strong> ${qqq.get('sma', 0):.2f}</div>
                <div class="ticker-data"><strong>Difference:</strong> <span style="color: {self._get_color_hex(qqq.get('color'))}; font-weight: bold;">{qqq.get('percentage_diff', 0):+.2f}%</span></div>
                <div class="ticker-data"><strong>Status:</strong> <span style="color: {self._get_color_hex(qqq.get('color'))}; font-weight: bold;">{qqq.get('status', 'UNKNOWN')}</span></div>
            </div>
            
            {tqqq_section}
            
            <div class="explanation-box">
                <h3 style="margin-top: 0; color: #1976d2;">📋 Explanation</h3>
                <p style="margin: 0; line-height: 1.6;">{explanation}</p>
            </div>
        </div>
        
        <div class="footer">
            <p>Generated by TQQQ Strategy Analysis System at {timestamp}</p>
            <p>This is an automated analysis for informational purposes only. Not financial advice.</p>
        </div>
    </div>
</body>
</html>
        """
        return template.strip()
    
    def _get_color_hex(self, color: str) -> str:
        """Convert color name to hex code."""
        color_map = {
            'green': '#27ae60',
            'red': '#e74c3c',
            'yellow': '#f39c12',
            'orange': '#fd7e14'
        }
        return color_map.get(color, '#6c757d')
    
    def success_text_template(self, data: Dict[str, Any]) -> str:
        """
        Generate plain text template for successful analysis results.
        
        Args:
            data: Analysis result data
            
        Returns:
            str: Plain text email content
        """
        # Extract data
        recommendation = data.get('recommendation', 'NO RECOMMENDATION')
        explanation = data.get('explanation', 'No explanation available')
        signal_event = data.get('signal_event')
        date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
        
        spy = data.get('spy', {})
        qqq = data.get('qqq', {})
        tqqq = data.get('tqqq')
        
        # Build signal event alert if present
        signal_alert = ''
        if signal_event:
            signal_alert = f"""
{signal_event}
{'=' * 60}

"""
        
        # Build TQQQ section if data is available
        tqqq_section = ''
        if tqqq:
            tqqq_section = f"""
TQQQ (Reference):
- Current Price: ${tqqq.get('price', 0):.2f}

"""
        
        template = f"""
TQQQ INVESTMENT STRATEGY ANALYSIS
{'=' * 60}

📊 CURRENT RECOMMENDATION: {recommendation}

Analysis Date: {date}

{signal_alert}
MULTI-TICKER DASHBOARD
{'=' * 60}

SPY (Primary Signal):
- Price: ${spy.get('price', 0):.2f} | 200-day SMA: ${spy.get('sma', 0):.2f}
- Difference: {spy.get('percentage_diff', 0):+.2f}%
- Status: {spy.get('status', 'UNKNOWN')}

QQQ (Bubble Protection):
- Price: ${qqq.get('price', 0):.2f} | 200-day SMA: ${qqq.get('sma', 0):.2f}
- Difference: {qqq.get('percentage_diff', 0):+.2f}%
- Status: {qqq.get('status', 'UNKNOWN')}

{tqqq_section}
EXPLANATION
{'=' * 60}
{explanation}

TECHNICAL DETAILS
{'=' * 60}
- Analysis Time: {timestamp}
- Strategy: SPY-based TQQQ with QQQ bubble protection
- SPY Thresholds: Buy +4%, Sell -3%
- QQQ Thresholds: Warning 30%, Danger 40%

DISCLAIMER
{'=' * 60}
This is an automated analysis for informational purposes only.
Not financial advice. Please consult with a financial advisor.

---
Generated by TQQQ Strategy Analysis System
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