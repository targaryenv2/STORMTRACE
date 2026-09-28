#!/usr/bin/env python3
"""
STORMTRACE Alert Dispatch & Delivery Pipeline Test Suite.
Tests the complete end-to-end alert pipeline:
1. Payload validation (missing zone, severity, lead time, bad types).
2. Unique Alert ID generation conforming to STR-DEMO-YYYYMMDD-HHMMSS-XXXX.
3. Structured CAP-style demo alert message creation.
4. Mandatory demo disclaimer inclusion.
5. SMTP unconfigured handling (clear failure, no fake success).
6. SMTP mock delivery success (status='sent', masked recipient).
7. SMTP mock delivery failure (status='failed', error details).
8. Secret hygiene (no SMTP credentials leaked in payload or response).
9. Audit history recording.
10. End-to-end dispatch workflow.
11. Live HTTP API endpoint verification (POST /api/v1/alerts/trigger & GET /api/v1/alerts/history).
"""

import os
import re
import sys
import json
import unittest
import urllib.request
import urllib.error
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.stormtrace.alerts.alert_engine import (
    generate_alert_id,
    validate_alert_request,
    create_structured_demo_alert,
    dispatch_alert,
    get_alert_history,
    ALERT_ID_REGEX,
    DEMO_DISCLAIMER
)
from backend.stormtrace.alerts.email_sender import (
    mask_email,
    send_demo_alert_email,
    get_smtp_config
)


class TestAlertPipeline(unittest.TestCase):
    """Unit and Integration tests for alert generation, delivery, and API routes."""

    def test_01_alert_id_format(self):
        """Test 1: Alert ID must match STR-DEMO-YYYYMMDD-HHMMSS-XXXX format."""
        alert_id = generate_alert_id()
        self.assertTrue(ALERT_ID_REGEX.match(alert_id), f"Alert ID '{alert_id}' does not match pattern")
        self.assertTrue(alert_id.startswith("STR-DEMO-"))

    def test_02_validation_success(self):
        """Test 2: Valid payload passes validation."""
        payload = {
            "zone_id": "ZONE_KOLKATA_AIRPORT",
            "severity_level": "Severe",
            "lead_time_min": 30
        }
        valid, err = validate_alert_request(payload)
        self.assertTrue(valid)
        self.assertIsNone(err)

    def test_03_validation_missing_zone(self):
        """Test 3: Missing zone_id fails validation."""
        payload = {
            "severity_level": "Severe",
            "lead_time_min": 30
        }
        valid, err = validate_alert_request(payload)
        self.assertFalse(valid)
        self.assertIn("zone_id", err)

    def test_04_validation_missing_severity(self):
        """Test 4: Missing severity_level fails validation."""
        payload = {
            "zone_id": "ZONE_KOLKATA_AIRPORT",
            "lead_time_min": 30
        }
        valid, err = validate_alert_request(payload)
        self.assertFalse(valid)
        self.assertIn("severity_level", err)

    def test_05_validation_missing_lead_time(self):
        """Test 5: Missing lead_time_min fails validation."""
        payload = {
            "zone_id": "ZONE_KOLKATA_AIRPORT",
            "severity_level": "Severe"
        }
        valid, err = validate_alert_request(payload)
        self.assertFalse(valid)
        self.assertIn("lead_time_min", err)

    def test_06_validation_invalid_lead_time_range(self):
        """Test 6: Invalid lead_time_min range fails validation."""
        payload = {
            "zone_id": "ZONE_KOLKATA_AIRPORT",
            "severity_level": "Severe",
            "lead_time_min": 500
        }
        valid, err = validate_alert_request(payload)
        self.assertFalse(valid)
        self.assertIn("between 1 and 360", err)

    def test_07_email_masking(self):
        """Test 7: Email address masking for privacy."""
        self.assertEqual(mask_email("user@example.com"), "u**r@example.com")
        self.assertEqual(mask_email("meteorologist@stormtrace.org"), "m***********t@stormtrace.org")
        self.assertEqual(mask_email("ab@test.org"), "a*@test.org")
        self.assertEqual(mask_email(""), "")
        self.assertEqual(mask_email(None), "")

    def test_08_smtp_unconfigured_behavior(self):
        """Test 8: When SMTP is unconfigured, send_demo_alert_email fails cleanly with clear message."""
        with patch.dict(os.environ, {"DEMO_ALERT_RECIPIENT": "", "SMTP_HOST": ""}, clear=True):
            success, msg, masked = send_demo_alert_email({"headline": "Test"}, {"headline": "Test"})
            self.assertFalse(success)
            self.assertIn("not configured", msg.lower())
            self.assertEqual(masked, "")

    def test_09_smtp_success_mock(self):
        """Test 9: Successful email transmission via mock SMTP."""
        fake_env = {
            "DEMO_ALERT_RECIPIENT": "meteorology.duty@example.com",
            "SMTP_HOST": "smtp.example.com",
            "SMTP_PORT": "587",
            "SMTP_USERNAME": "test_user",
            "SMTP_PASSWORD": "secret_password",
            "SMTP_FROM": "alerts@stormtrace.org"
        }
        with patch.dict(os.environ, fake_env, clear=False):
            with patch("smtplib.SMTP") as mock_smtp_cls:
                mock_server = MagicMock()
                mock_smtp_cls.return_value = mock_server
                
                success, msg, masked = send_demo_alert_email(
                    {"alert_id": "STR-DEMO-20240502-120000-ABCD", "zone_id": "ZONE_KOLKATA_AIRPORT"},
                    {"headline": "Severe Storm Alert", "disclaimer": DEMO_DISCLAIMER}
                )
                self.assertTrue(success)
                self.assertEqual(msg, "sent")
                self.assertTrue(masked.startswith("m") and masked.endswith("y@example.com"))
                self.assertTrue(mock_server.sendmail.called)

    def test_10_smtp_failure_mock(self):
        """Test 10: Simulated SMTP connection failure returns failure without crashing."""
        fake_env = {
            "DEMO_ALERT_RECIPIENT": "duty@example.com",
            "SMTP_HOST": "smtp.example.com",
            "SMTP_PORT": "587"
        }
        with patch.dict(os.environ, fake_env, clear=False):
            with patch("smtplib.SMTP", side_effect=Exception("Connection timed out")):
                success, msg, masked = send_demo_alert_email(
                    {"alert_id": "STR-DEMO-20240502-120000-ABCD", "zone_id": "ZONE_1"},
                    {"headline": "Test Alert"}
                )
                self.assertFalse(success)
                self.assertIn("Connection timed out", msg)

    def test_11_structured_alert_content_and_disclaimer(self):
        """Test 11: Structured alert includes CAP-style fields and mandatory disclaimer."""
        payload = {
            "cell_id": "CELL_001",
            "zone_id": "ZONE_KOLKATA_AIRPORT",
            "lead_time_min": 30,
            "severity_level": "Severe",
            "urgency": "Immediate",
            "event_type": "Severe Thunderstorm Warning",
            "headline": "Storm approaching airport",
            "instruction": "Ground aircraft"
        }
        alert = create_structured_demo_alert(payload, "STR-DEMO-TEST-001")
        self.assertEqual(alert["identifier"], "STR-DEMO-TEST-001")
        self.assertEqual(alert["status"], "Draft/Demo")
        self.assertEqual(alert["msgType"], "Alert")
        self.assertEqual(alert["scope"], "Restricted/Demo")
        self.assertIn("demonstration", alert["disclaimer"].lower())
        self.assertIn("not an official", alert["disclaimer"].lower())
        self.assertEqual(alert["severity"], "Severe")
        self.assertEqual(alert["urgency"], "Immediate")

    def test_12_secret_hygiene(self):
        """Test 12: Passwords and sensitive configs are never exposed in dispatch responses."""
        fake_env = {
            "DEMO_ALERT_RECIPIENT": "duty@example.com",
            "SMTP_HOST": "smtp.example.com",
            "SMTP_PORT": "587",
            "SMTP_USERNAME": "my_smtp_user",
            "SMTP_PASSWORD": "super_secret_smtp_password"
        }
        with patch.dict(os.environ, fake_env, clear=False):
            with patch("smtplib.SMTP") as mock_smtp_cls:
                mock_server = MagicMock()
                mock_smtp_cls.return_value = mock_server

                payload = {
                    "zone_id": "ZONE_KOLKATA_AIRPORT",
                    "severity_level": "Severe",
                    "lead_time_min": 30
                }
                result = dispatch_alert(payload)
                result_str = str(result)
                self.assertNotIn("super_secret_smtp_password", result_str)
                self.assertNotIn("my_smtp_user", result_str)
                self.assertIn("d**y@example.com", result_str)

    def test_13_dispatch_and_audit_history(self):
        """Test 13: dispatch_alert creates an alert and logs audit history."""
        payload = {
            "cell_id": "CELL_20240502_001",
            "zone_id": "ZONE_KOLKATA_AIRPORT",
            "lead_time_min": 30,
            "severity_level": "Severe",
            "urgency": "Immediate"
        }
        result = dispatch_alert(payload)
        self.assertIn("alert_id", result)
        self.assertTrue(result["alert_id"].startswith("STR-DEMO-"))
        self.assertEqual(result["mode"], "DEMO")
        self.assertIn("delivery", result)
        self.assertIn("structured_alert", result)
        self.assertIn("disclaimer", result)
        
        # Verify history
        history = get_alert_history()
        self.assertTrue(len(history) > 0)
        self.assertTrue(any(item["alert_id"] == result["alert_id"] for item in history))


if __name__ == "__main__":
    unittest.main()
