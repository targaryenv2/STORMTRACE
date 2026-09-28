"""STORMTRACE Demonstration Alert Engine.

Manages alert validation, unique ID generation (STR-DEMO-...),
structured CAP-style demo message construction, audit logging,
and delivery dispatching.
"""

import os
import re
import json
import time
import secrets
from datetime import datetime, timezone
from typing import Dict, Any, Tuple, Optional, List

from .email_sender import send_demo_alert_email, mask_email

ALERT_ID_REGEX = re.compile(r"^STR-DEMO-\d{8}-\d{6}-[A-F0-9]{4}$")
DEMO_DISCLAIMER = (
    "DEMONSTRATION ALERT: This is a prototype nowcast demonstration and NOT an official government CAP alert. "
    "Refer to IMD/NDMA for official advisories."
)

_ALERT_HISTORY: List[Dict[str, Any]] = []


def generate_alert_id() -> str:
    """Generates a standardized STORMTRACE demo alert identifier.
    
    Format: STR-DEMO-YYYYMMDD-HHMMSS-XXXX (e.g. STR-DEMO-20260922-214530-A8F2)
    Explicitly marked as STR-DEMO to prevent misrepresentation as official government CAP.
    """
    now_utc = datetime.now(timezone.utc)
    date_str = now_utc.strftime("%Y%m%d")
    time_str = now_utc.strftime("%H%M%S")
    rand_suffix = secrets.token_hex(2).upper()
    return f"STR-DEMO-{date_str}-{time_str}-{rand_suffix}"


def validate_alert_request(payload: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validates the mandatory parameters in an alert trigger request.
    
    Returns:
        (is_valid, error_message)
    """
    if not isinstance(payload, dict):
        return False, "Invalid payload: must be a JSON object."

    required_fields = ["zone_id", "severity_level", "lead_time_min"]
    for field in required_fields:
        if field not in payload or payload[field] is None or payload[field] == "":
            return False, f"Missing mandatory parameter: '{field}' is required."

    try:
        lead_time = int(payload["lead_time_min"])
        if lead_time <= 0 or lead_time > 360:
            return False, "Parameter 'lead_time_min' must be an integer between 1 and 360 minutes."
    except (ValueError, TypeError):
        return False, "Parameter 'lead_time_min' must be a valid integer."

    valid_severities = ["Moderate", "Severe", "Extreme", "High", "Low"]
    if str(payload["severity_level"]).capitalize() not in [s.capitalize() for s in valid_severities]:
        return False, f"Parameter 'severity_level' must be one of: {', '.join(valid_severities)}"

    return True, None


def create_structured_demo_alert(payload: Dict[str, Any], alert_id: str) -> Dict[str, Any]:
    """Generates a structured CAP-style demonstration alert object."""
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    zone_id = payload.get("zone_id", "ZONE_GENERAL")
    lead_time = int(payload.get("lead_time_min", 30))
    severity = str(payload.get("severity_level", "Severe")).capitalize()
    urgency = str(payload.get("urgency", "Immediate")).capitalize()
    event_type = payload.get("event_type", "Severe Thunderstorm & Lightning Warning")
    headline = payload.get("headline", f"Convective Storm Approaching {zone_id}")
    instruction = payload.get("instruction", "Initiate safety protocols and seek enclosed shelter.")

    return {
        "identifier": alert_id,
        "sender": "STORMTRACE-ENGINE@localhost",
        "sent": now_iso,
        "status": "Draft/Demo",
        "msgType": "Alert",
        "scope": "Restricted/Demo",
        "event": event_type,
        "urgency": urgency,
        "severity": severity,
        "certainty": "Observed",
        "headline": headline,
        "description": "Convective nowcasting alert based on live radar and meteorological telemetry.",
        "instruction": instruction,
        "area": {
            "areaDesc": zone_id,
            "lead_time_min": lead_time
        },
        "disclaimer": DEMO_DISCLAIMER
    }


def dispatch_alert(
    payload: Dict[str, Any],
    config_override: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Processes validation, alert generation, delivery, and audit logging."""
    # 1. Validation
    is_valid, err_msg = validate_alert_request(payload)
    if not is_valid:
        return {
            "success": False,
            "error": err_msg,
            "status": "validation_failed"
        }

    # 2. Alert Generation
    alert_id = generate_alert_id()
    payload["alert_id"] = alert_id
    structured_alert = create_structured_demo_alert(payload, alert_id)

    # 3. Email Delivery
    email_success, email_status, masked_recip = send_demo_alert_email(
        alert_payload=payload,
        structured_alert=structured_alert,
        config_override=config_override
    )

    # Webhook Delivery
    webhook_success = False
    webhook_url = os.getenv("ALERT_WEBHOOK_URL")
    if "webhook" in payload.get("channels", []) and webhook_url and not payload.get("dry_run", False):
        try:
            import urllib.request
            req = urllib.request.Request(
                webhook_url,
                data=json.dumps({"content": payload.get("message", "STORMTRACE Alert")}).encode("utf-8"),
                headers={'Content-Type': 'application/json', 'User-Agent': 'StormTrace/1.0'}
            )
            urllib.request.urlopen(req, timeout=5)
            webhook_success = True
        except Exception as e:
            print(f"Webhook delivery failed: {e}")

    # 4. Audit History Logging (No secrets stored)
    audit_entry = {
        "alert_id": alert_id,
        "timestamp_utc": structured_alert["sent"],
        "zone_id": payload.get("zone_id"),
        "severity": payload.get("severity_level"),
        "urgency": payload.get("urgency"),
        "lead_time_min": payload.get("lead_time_min"),
        "channel": "webhook" if webhook_success else "email",
        "delivery_status": "sent" if (email_success or webhook_success) else "failed",
        "mode": "DEMO" if payload.get("dry_run", False) or not os.getenv("ALERT_LIVE_MODE") else "LIVE",
        "recipient_masked": "Discord/Webhook" if webhook_success else masked_recip,
        "error": None if (email_success or webhook_success) else email_status
    }
    _ALERT_HISTORY.append(audit_entry)

    # 5. Build Response
    success = email_success or webhook_success or payload.get("dry_run", False)
    return {
        "success": success,
        "alert_id": alert_id,
        "mode": "DEMO" if payload.get("dry_run", False) or not os.getenv("ALERT_LIVE_MODE") else "LIVE",
        "delivery": {
            "channel": "webhook" if webhook_success else "email",
            "status": "sent" if success else "failed",
            "recipient": "Discord/Webhook" if webhook_success else masked_recip
        },
        "structured_alert": structured_alert,
        "disclaimer": structured_alert["disclaimer"]
    }


def get_alert_history() -> List[Dict[str, Any]]:
    """Returns stored alert history records."""
    return list(_ALERT_HISTORY)
