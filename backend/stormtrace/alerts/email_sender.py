"""STORMTRACE Demo Alert Email Delivery Module.

Provides secure SMTP email transmission for demonstration alerts,
masking recipient details and preventing credential leakage.
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Tuple, Dict, Any, Optional


def mask_email(email: str) -> str:
    """Masks an email address for privacy in logs and UI responses (e.g., u***r@example.com)."""
    if not email:
        return ""
    if "@" not in email:
        return email
    user, domain = email.split("@", 1)
    if len(user) <= 2:
        masked_user = user[0] + "*"
    else:
        masked_user = user[0] + "*" * (len(user) - 2) + user[-1]
    return f"{masked_user}@{domain}"


def get_smtp_config() -> Dict[str, Any]:
    """Loads SMTP and recipient configuration from environment variables."""
    # Ensure .env is loaded if present
    env_file = os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env")
    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())

    return {
        "recipient": os.getenv("DEMO_ALERT_RECIPIENT", "").strip(),
        "host": os.getenv("SMTP_HOST", "").strip(),
        "port": int(os.getenv("SMTP_PORT", "587")),
        "username": os.getenv("SMTP_USERNAME", "").strip(),
        "password": os.getenv("SMTP_PASSWORD", "").strip(),
        "from_addr": os.getenv("SMTP_FROM", "stormtrace-alerts@demo.local").strip(),
    }


def send_demo_alert_email(
    alert_payload: Dict[str, Any],
    structured_alert: Dict[str, Any],
    config_override: Optional[Dict[str, Any]] = None
) -> Tuple[bool, str, str]:
    """Sends real demo alert email using configured SMTP parameters.
    
    Returns:
        (success, status_or_error, masked_recipient)
    """
    config = config_override or get_smtp_config()
    recipient = config.get("recipient", "")
    host = config.get("host", "")
    port = config.get("port", 587)
    username = config.get("username", "")
    password = config.get("password", "")
    from_addr = config.get("from_addr", "stormtrace-alerts@demo.local")

    if not host or not recipient:
        return False, "Demo notification channel is not configured. (Configure SMTP_HOST and DEMO_ALERT_RECIPIENT in .env)", ""

    masked_recip = mask_email(recipient)
    alert_id = alert_payload.get("alert_id", "STR-DEMO-ALERT")
    zone_id = alert_payload.get("zone_id", "ZONE_UNKNOWN")
    event_type = alert_payload.get("event_type", "Severe Thunderstorm Warning")
    headline = alert_payload.get("headline", f"Convective Storm Approaching {zone_id}")
    lead_time = alert_payload.get("lead_time_min", 30)
    severity = alert_payload.get("severity_level", "Severe")
    urgency = alert_payload.get("urgency", "Immediate")
    instruction = alert_payload.get("instruction", "Initiate safety protocols.")

    subject = f"[STORMTRACE DEMO] {event_type} — {zone_id}"

    body_text = f"""STORMTRACE DEMONSTRATION ALERT
======================================================================
Alert ID:     {alert_id}
Target Zone:  {zone_id}
Lead Time:    +{lead_time} minutes
Severity:     {severity}
Urgency:      {urgency}
Event:        {event_type}
Headline:     {headline}
Instruction:  {instruction}

DATA STATUS:
Demo / synthetic data (Generated from STORMTRACE Nowcasting Engine)

DISCLAIMER:
This is an AI decision-support demonstration alert.
It is not an official IMD warning and does not constitute
an official public safety notification.
======================================================================

STRUCTURED ALERT PAYLOAD (CAP-STYLE):
Identifier:   {structured_alert.get('identifier')}
Status:       {structured_alert.get('status')}
Scope:        {structured_alert.get('scope')}
Sent UTC:     {structured_alert.get('sent')}
Certainty:    {structured_alert.get('certainty')}
"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = recipient
    msg.attach(MIMEText(body_text, "plain", "utf-8"))

    try:
        if port == 465:
            server = smtplib.SMTP_SSL(host, port, timeout=10)
        else:
            server = smtplib.SMTP(host, port, timeout=10)
            server.ehlo()
            server.starttls()
            server.ehlo()

        if username and password:
            server.login(username, password)

        server.sendmail(from_addr, [recipient], msg.as_string())
        server.quit()
        return True, "sent", masked_recip

    except smtplib.SMTPAuthenticationError:
        return False, "SMTP authentication failed. Check SMTP_USERNAME and SMTP_PASSWORD.", masked_recip
    except smtplib.SMTPConnectError:
        return False, f"Failed to connect to SMTP host {host}:{port}.", masked_recip
    except Exception as e:
        err_detail = str(e) if str(e) else type(e).__name__
        return False, f"Delivery failed: {err_detail}", masked_recip
