#!/usr/bin/env python3
"""
STORMTRACE Temporal Alignment & Modality Matching Engine
Phase 8: Manages timestamp semantics, configurable alignment tolerances,
and explicit distinction between real-time observations, reanalysis, and monthly climatology.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple


class TemporalToleranceConfig:
    """Configurable temporal tolerance windows in seconds for each modality."""
    def __init__(
        self,
        radar_tolerance_sec: int = 600,       # 10 minutes
        satellite_tolerance_sec: int = 1800,   # 30 minutes
        imerg_tolerance_sec: int = 1800,       # 30 minutes
        era5_tolerance_sec: int = 3600         # 60 minutes
    ):
        self.radar_tolerance_sec = radar_tolerance_sec
        self.satellite_tolerance_sec = satellite_tolerance_sec
        self.imerg_tolerance_sec = imerg_tolerance_sec
        self.era5_tolerance_sec = era5_tolerance_sec

    def to_dict(self) -> Dict[str, int]:
        return {
            "radar_tolerance_sec": self.radar_tolerance_sec,
            "satellite_tolerance_sec": self.satellite_tolerance_sec,
            "imerg_tolerance_sec": self.imerg_tolerance_sec,
            "era5_tolerance_sec": self.era5_tolerance_sec
        }


def parse_iso_timestamp(ts_str: str) -> datetime:
    """Parses standard ISO 8601 strings into timezone-aware UTC datetime."""
    # Normalize Z and format
    clean = ts_str.replace("Z", "+00:00")
    if "T" in clean:
        dt = datetime.fromisoformat(clean)
    else:
        # Format: YYYY-MM-DD HH:MM:SS
        dt = datetime.strptime(clean, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def format_iso_timestamp(dt: datetime) -> str:
    """Formats datetime to standard ISO 8601 UTC string."""
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class MultimodalTemporalAligner:
    """
    Aligns multimodal data streams to a common forecast initialization timestamp T0.
    Explicitly tracks time deltas, availability flags, and climatological baseline month.
    """

    def __init__(self, tolerances: Optional[TemporalToleranceConfig] = None):
        self.tolerances = tolerances or TemporalToleranceConfig()

    def match_modalities(
        self,
        t0_iso: str,
        available_radar_timestamps: List[str],
        available_satellite_timestamps: List[str],
        available_imerg_timestamps: List[str],
        available_era5_timestamps: List[str]
    ) -> Dict[str, Any]:
        """
        For a target T0 timestamp, finds the closest matching timestamp in each modality
        within its configurable tolerance.
        """
        t0_dt = parse_iso_timestamp(t0_iso)
        t0_epoch = t0_dt.timestamp()

        result = {
            "target_initialization_time_utc": format_iso_timestamp(t0_dt),
            "target_calendar_month": t0_dt.month,
            "modalities": {}
        }

        # 1. Radar Matching
        radar_match = self._find_closest(t0_epoch, available_radar_timestamps, self.tolerances.radar_tolerance_sec)
        result["modalities"]["radar"] = {
            "available": radar_match is not None,
            "matched_timestamp_utc": radar_match["matched_iso"] if radar_match else None,
            "delta_seconds": radar_match["delta_sec"] if radar_match else None,
            "data_type": "REAL_OBSERVATION" if radar_match else "UNAVAILABLE",
            "temporal_semantics": "INSTANTANEOUS_OBSERVATION"
        }

        # 2. Satellite (INSAT-3DS) Matching
        sat_match = self._find_closest(t0_epoch, available_satellite_timestamps, self.tolerances.satellite_tolerance_sec)
        result["modalities"]["satellite_insat3ds"] = {
            "available": sat_match is not None,
            "matched_timestamp_utc": sat_match["matched_iso"] if sat_match else None,
            "delta_seconds": sat_match["delta_sec"] if sat_match else None,
            "data_type": "REAL_OBSERVATION" if sat_match else "UNAVAILABLE",
            "temporal_semantics": "INSTANTANEOUS_OBSERVATION"
        }

        # 3. IMERG Precipitation Matching
        imerg_match = self._find_closest(t0_epoch, available_imerg_timestamps, self.tolerances.imerg_tolerance_sec)
        result["modalities"]["imerg_precipitation"] = {
            "available": imerg_match is not None,
            "matched_timestamp_utc": imerg_match["matched_iso"] if imerg_match else None,
            "delta_seconds": imerg_match["delta_sec"] if imerg_match else None,
            "data_type": "REAL_OBSERVATION" if imerg_match else "UNAVAILABLE",
            "temporal_semantics": "TIME_WINDOW_AGGREGATE"
        }

        # 4. ERA5 NWP Matching
        era5_match = self._find_closest(t0_epoch, available_era5_timestamps, self.tolerances.era5_tolerance_sec)
        result["modalities"]["nwp_era5"] = {
            "available": era5_match is not None,
            "matched_timestamp_utc": era5_match["matched_iso"] if era5_match else None,
            "delta_seconds": era5_match["delta_sec"] if era5_match else None,
            "data_type": "REAL_REANALYSIS" if era5_match else "UNAVAILABLE",
            "temporal_semantics": "REANALYSIS_STEP"
        }

        # 5. Lightning (WGLC Climatology)
        # CRITICAL: WGLC is monthly climatology; it does NOT match instantaneous timestamps!
        result["modalities"]["lightning_wglc"] = {
            "available": True,
            "climatological_month": t0_dt.month,
            "matched_timestamp_utc": None,  # Intentionally None: NOT an instantaneous observation
            "delta_seconds": 0,
            "data_type": "REAL_CLIMATOLOGY",
            "temporal_semantics": "MONTHLY_CLIMATOLOGY_AVERAGE",
            "observation_period": "2010-2020",
            "role": "auxiliary_climatological_baseline",
            "caveat": "Monthly average lightning propensity (2010-2020), not real-time lightning strikes."
        }

        return result

    def _find_closest(self, target_epoch: float, candidate_iso_list: List[str], max_tolerance_sec: int) -> Optional[Dict[str, Any]]:
        """Finds closest ISO timestamp within max_tolerance_sec."""
        if not candidate_iso_list:
            return None

        best_match = None
        min_diff = float("inf")

        for iso_str in candidate_iso_list:
            try:
                cand_dt = parse_iso_timestamp(iso_str)
                cand_epoch = cand_dt.timestamp()
                diff = abs(cand_epoch - target_epoch)
                if diff <= max_tolerance_sec and diff < min_diff:
                    min_diff = diff
                    best_match = {
                        "matched_iso": format_iso_timestamp(cand_dt),
                        "delta_sec": int(cand_epoch - target_epoch)
                    }
            except Exception:
                continue

        return best_match
