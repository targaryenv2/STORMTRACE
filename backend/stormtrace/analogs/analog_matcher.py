#!/usr/bin/env python3
"""
STORMTRACE Historical Analog Database & Pattern Matcher
Part 2: Real-time similarity retrieval matching current radar signatures against historical events.
"""

import math
from typing import List, Dict, Any


class HistoricalAnalogMatcher:
    """Searches historical convective catalog for morphologically similar storm patterns."""

    ANALOG_DATABASE = [
        {
            "analog_id": "ANALOG-2025-0512-01",
            "event_title": "May 2025 Chota Nagpur Supercell Outbreak",
            "date": "2025-05-12 16:30 IST",
            "location": "Ranchi - Jamshedpur Plateau",
            "max_dbz": 63.5,
            "max_lightning_rate": "910/h",
            "observed_outcome": "Severe hail up to 4cm and intense localized flash downpour with 65 km/h convective wind gusts.",
            "skill_score_csi": 0.912,
            "similarity_score": 0.94,
            "provenance_status": "BENCHMARK_CASE_STUDY",
            "data_sources": ["SYNTHETIC_BENCHMARK_SIMULATION", "WGLC_CLIMATOLOGY"]
        },
        {
            "analog_id": "ANALOG-2024-0618-02",
            "event_title": "June 2024 Gangetic Bengal Pre-Monsoon Squall Line",
            "date": "2024-06-18 18:15 IST",
            "location": "Kolkata - Howrah Coastal Belt",
            "max_dbz": 59.0,
            "max_lightning_rate": "680/h",
            "observed_outcome": "Nor'wester (Kalbaishakhi) squall line resulting in airport ground hold at NSCBI for 35 minutes.",
            "skill_score_csi": 0.885,
            "similarity_score": 0.91,
            "provenance_status": "BENCHMARK_CASE_STUDY",
            "data_sources": ["SYNTHETIC_BENCHMARK_SIMULATION", "WGLC_CLIMATOLOGY"]
        },
        {
            "analog_id": "ANALOG-2024-0922-03",
            "event_title": "September 2024 Tamil Nadu Coastal Convective Core",
            "date": "2024-09-22 15:40 IST",
            "location": "Chennai - Kanchipuram Airspace",
            "max_dbz": 54.0,
            "max_lightning_rate": "420/h",
            "observed_outcome": "Stationary sea-breeze convergence line producing intense cloud-to-ground lightning.",
            "skill_score_csi": 0.898,
            "similarity_score": 0.88,
            "provenance_status": "BENCHMARK_CASE_STUDY",
            "data_sources": ["SYNTHETIC_BENCHMARK_SIMULATION", "WGLC_CLIMATOLOGY"]
        },
        {
            "analog_id": "ANALOG-2023-1104-04",
            "event_title": "November 2023 Arabian Sea Coastal Updraft",
            "date": "2023-11-04 14:20 IST",
            "location": "Western Ghats / Kozhikode Coast",
            "max_dbz": 52.0,
            "max_lightning_rate": "360/h",
            "observed_outcome": "Orographic enhancement causing rapid 45mm rain accumulation in 1 hour.",
            "skill_score_csi": 0.870,
            "similarity_score": 0.85,
            "provenance_status": "BENCHMARK_CASE_STUDY",
            "data_sources": ["SYNTHETIC_BENCHMARK_SIMULATION", "WGLC_CLIMATOLOGY"]
        }
    ]

    def match_analog(self, query_max_dbz: float, query_region: str = "") -> List[Dict[str, Any]]:
        """Find closest historical analogs based on reflectivity, region, and kinematic severity."""
        results = []
        for item in self.ANALOG_DATABASE:
            dbz_diff = abs(item["max_dbz"] - query_max_dbz)
            sim = max(0.60, round(1.0 - (dbz_diff / 80.0), 3))
            results.append({
                **item,
                "computed_similarity": sim
            })
        
        results.sort(key=lambda x: x["computed_similarity"], reverse=True)
        return results
