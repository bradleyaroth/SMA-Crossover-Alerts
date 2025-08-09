"""
Notification module for email delivery.

This module handles email notifications for analysis results,
errors, and system alerts.
"""

from .email_sender import EmailSender
from .templates import EmailTemplates

__all__ = ['EmailSender', 'EmailTemplates']