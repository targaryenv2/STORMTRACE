#!/usr/bin/env python3
"""
Unit and Integration Tests for Sprint 3:
- OASIS CAP 1.2 XML Serializer
- Incident Situation Report (SitRep) Generator & HTML Exporter
"""

import unittest
import xml.etree.ElementTree as ET

from backend.stormtrace.alerts.cap_serializer import serialize_cap_xml
from backend.stormtrace.alerts.report_generator import generate_incident_situation_report, render_situation_report_html


class TestCAPAndIncidentReport(unittest.TestCase):

    def test_cap_12_xml_serialization(self):
        """Verify generation of valid OASIS CAP 1.2 XML alert tree."""
        alert_payload = {
            "identifier": "STR-LIVE-20260928-120000-E9A1",
            "sender": "imd-nowcasting@stormtrace.gov.in",
            "event": "Severe Thunderstorm & Lightning Warning",
            "severity": "Extreme",
            "urgency": "Immediate",
            "lead_time_min": 45,
            "peak_dbz": 56.4,
            "lightning_prob": 0.94,
            "area": {
                "areaDesc": "Kolkata Metropolitan Area & Hooghly",
                "polygon": "22.50,88.30 22.70,88.35 22.65,88.55 22.45,88.45 22.50,88.30"
            }
        }

        xml_str = serialize_cap_xml(alert_payload)
        self.assertIn("<?xml", xml_str)
        self.assertIn("urn:oasis:names:tc:emergency:cap:1.2", xml_str)
        
        # Parse XML tree to guarantee structural validity
        root = ET.fromstring(xml_str)
        self.assertEqual(root.tag, "{urn:oasis:names:tc:emergency:cap:1.2}alert")
        
        info = root.find("{urn:oasis:names:tc:emergency:cap:1.2}info")
        self.assertIsNotNone(info)
        severity = info.find("{urn:oasis:names:tc:emergency:cap:1.2}severity").text
        self.assertEqual(severity, "Extreme")

    def test_incident_situation_report_generation(self):
        """Verify structured SitRep generation and HTML rendering."""
        report = generate_incident_situation_report(cell_id="SC-2026-0928-01")
        self.assertEqual(report["target_cell"]["cell_id"], "SC-2026-0928-01")
        self.assertEqual(len(report["horizon_trajectories"]), 6)
        self.assertGreaterEqual(len(report["critical_infrastructure_impacts"]), 1)

        html = render_situation_report_html(report)
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("CONVECTIVE STORM & LIGHTNING INCIDENT SITUATION REPORT", html)
        self.assertIn("SC-2026-0928-01", html)


if __name__ == "__main__":
    unittest.main()
