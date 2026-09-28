#!/usr/bin/env python3
"""
STORMTRACE OASIS Common Alerting Protocol (CAP 1.2) Serializer
================================================================================
Compliant with OASIS CAP v1.2 and National Disaster Management Authority (NDMA)
Common Alerting Protocol specifications for severe thunderstorm & lightning nowcasts.
================================================================================
"""

import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional


def serialize_cap_xml(alert_data: Dict[str, Any]) -> str:
    """
    Serializes a STORMTRACE alert dictionary into standard OASIS CAP 1.2 XML format.
    """
    now_utc = datetime.now(timezone.utc)
    sent_iso = now_utc.strftime("%Y-%m-%dT%H:%M:%S+00:00")
    expires_dt = now_utc + timedelta(minutes=int(alert_data.get("lead_time_min", 60)))
    expires_iso = expires_dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")

    identifier = alert_data.get("identifier", f"STR-CAP-{now_utc.strftime('%Y%m%d%H%M%S')}")
    sender = alert_data.get("sender", "imd-nowcasting@stormtrace.gov.in")
    status = alert_data.get("status", "Actual")
    msg_type = alert_data.get("msgType", "Alert")
    scope = alert_data.get("scope", "Public")
    event = alert_data.get("event", "Severe Thunderstorm & Lightning Warning")
    urgency = alert_data.get("urgency", "Immediate")
    severity = alert_data.get("severity", "Severe")
    certainty = alert_data.get("certainty", "Observed")
    headline = alert_data.get("headline", "Severe Thunderstorm Approaching Impact Zone")
    description = alert_data.get("description", "High-reflectivity convective storm core detected with rapid lightning intensification.")
    instruction = alert_data.get("instruction", "Seek immediate safe shelter indoors. Avoid open fields, tall trees, and metal structures.")
    area_desc = alert_data.get("area", {}).get("areaDesc", "Gangetic West Bengal & Coastal Odisha")
    polygon = alert_data.get("area", {}).get("polygon", "22.50,88.30 22.70,88.35 22.65,88.55 22.45,88.45 22.50,88.30")

    # Build XML Tree
    root = ET.Element("alert", xmlns="urn:oasis:names:tc:emergency:cap:1.2")
    
    ET.SubElement(root, "identifier").text = identifier
    ET.SubElement(root, "sender").text = sender
    ET.SubElement(root, "sent").text = sent_iso
    ET.SubElement(root, "status").text = status
    ET.SubElement(root, "msgType").text = msg_type
    ET.SubElement(root, "scope").text = scope
    ET.SubElement(root, "code").text = "IMD-NOWCAST-26072"

    info = ET.SubElement(root, "info")
    ET.SubElement(info, "language").text = "en-IN"
    ET.SubElement(info, "category").text = "Met"
    ET.SubElement(info, "event").text = event
    ET.SubElement(info, "urgency").text = urgency
    ET.SubElement(info, "severity").text = severity
    ET.SubElement(info, "certainty").text = certainty
    ET.SubElement(info, "eventCode").text = "SVR-THUNDERSTORM"
    ET.SubElement(info, "expires").text = expires_iso
    ET.SubElement(info, "senderName").text = "STORMTRACE Convective Nowcasting System (MoES/IMD)"
    ET.SubElement(info, "headline").text = headline
    ET.SubElement(info, "description").text = description
    ET.SubElement(info, "instruction").text = instruction

    area = ET.SubElement(info, "area")
    ET.SubElement(area, "areaDesc").text = area_desc
    if polygon:
        ET.SubElement(area, "polygon").text = polygon

    # Parameter blocks for scientific telemetry
    param_dbz = ET.SubElement(info, "parameter")
    ET.SubElement(param_dbz, "valueName").text = "MaxReflectivity_dBZ"
    ET.SubElement(param_dbz, "value").text = str(alert_data.get("peak_dbz", 52.5))

    param_lgt = ET.SubElement(info, "parameter")
    ET.SubElement(param_lgt, "valueName").text = "PeakLightningProbability"
    ET.SubElement(param_lgt, "value").text = str(alert_data.get("lightning_prob", 0.88))

    return ET.tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8")
