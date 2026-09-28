"""STORMTRACE Alerts Module."""

from .alert_engine import (
    generate_alert_id,
    validate_alert_request,
    create_structured_demo_alert,
    dispatch_alert,
    get_alert_history
)
from .email_sender import send_demo_alert_email, mask_email, get_smtp_config

__all__ = [
    "generate_alert_id",
    "validate_alert_request",
    "create_structured_demo_alert",
    "dispatch_alert",
    "get_alert_history",
    "send_demo_alert_email",
    "mask_email",
    "get_smtp_config"
]
