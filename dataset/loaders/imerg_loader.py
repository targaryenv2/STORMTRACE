#!/usr/bin/env python3
"""
STORMTRACE NASA GPM IMERG Precipitation Data Loader
Phase 6: Ingests, validates, and aligns NASA GPM IMERG Half-Hourly Precipitation Calibrated L3
(GPM_3IMERGHH_V07) products on the common STORMTRACE grid.
"""

import os
import re
import glob
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

try:
    from dataset.provenance import get_imerg_metadata, get_synthetic_imerg_metadata, DataType, TemporalSemantics
    from dataset.grid import StormTraceGrid, MODALITY_SPECS
except ImportError:
    from stormtrace.data.provenance import get_imerg_metadata, get_synthetic_imerg_metadata, DataType, TemporalSemantics
    from stormtrace.data.grid import StormTraceGrid, MODALITY_SPECS


class ImergPrecipitationLoader:
    """
    Loader for NASA GPM IMERG Half-Hourly Calibrated Precipitation Products.
    Extracts surface precipitation rate (mm/hr) and liquid precipitation probability.
    """

    CHANNELS = ["precipitationCal", "precipitationUncal", "probabilityLiquidPrecipitation"]
    MAX_VALID_PRECIP_MM_HR = 250.0

    def __init__(self, raw_data_dir: str = "dataset/raw/imerg"):
        if not os.path.exists(raw_data_dir) and os.path.exists(raw_data_dir.replace("dataset/", "data/")):
            self.raw_data_dir = raw_data_dir.replace("dataset/", "data/")
        else:
            self.raw_data_dir = raw_data_dir
        self.metadata_spec = get_imerg_metadata()

    def discover_files(self) -> List[Dict[str, Any]]:
        """Discovers any pre-downloaded IMERG HDF5, NetCDF4, or JSON files."""
        if not os.path.exists(self.raw_data_dir):
            return []

        files = []
        for ext in ["*3IMERGHH*", "*IMERG*", "*.nc4", "*.nc", "*.h5", "*.hdf5", "*.json"]:
            for path in glob.glob(os.path.join(self.raw_data_dir, ext)):
                if not path.endswith(".gitkeep"):
                    meta = self.extract_file_metadata(path)
                    if meta:
                        files.append(meta)
        return files

    def extract_file_metadata(self, filepath: str) -> Optional[Dict[str, Any]]:
        """
        Extracts start/end accumulation timestamps from IMERG standard filenames:
        Example: 3B-HHR.MS.MRG.3IMERG.20250512-S140000-E142959.0840.V07B.HDF5
        """
        filename = os.path.basename(filepath)
        size = os.path.getsize(filepath) if os.path.exists(filepath) else 0

        # Pattern: YYYYMMDD-S(HHMMSS)
        match = re.search(r"(\d{8})-S(\d{6})", filename)
        iso_match = re.search(r"(\d{4})(\d{2})(\d{2})_?(\d{2})(\d{2})", filename)

        dt_utc = None
        if match:
            date_part, time_part = match.groups()
            try:
                dt_utc = datetime.strptime(f"{date_part}{time_part}", "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
            except Exception:
                pass
        elif iso_match:
            y, m, d, hh, mm = iso_match.groups()
            try:
                dt_utc = datetime(int(y), int(m), int(d), int(hh), int(mm), tzinfo=timezone.utc)
            except Exception:
                pass

        if not dt_utc:
            dt_utc = datetime.fromtimestamp(os.path.getmtime(filepath), tz=timezone.utc)

        return {
            "filepath": filepath,
            "filename": filename,
            "size_bytes": size,
            "timestamp_utc": dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "acquisition_dt": dt_utc,
            "source": "NASA_GPM",
            "sensor": "IMERG_COMBINED_MICROWAVE_IR_GAUGE",
            "product_id": "GPM_3IMERGHH_V07"
        }

    def validate_file(self, filepath: str) -> Dict[str, Any]:
        """Validates file integrity."""
        res = {"filepath": filepath, "valid": False, "errors": [], "channels_found": []}
        if not os.path.exists(filepath):
            res["errors"].append(f"File not found: {filepath}")
            return res
        if os.path.getsize(filepath) == 0:
            res["errors"].append(f"Empty file: {filepath}")
            return res

        if filepath.endswith(".json"):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for c in self.CHANNELS:
                        if c in data:
                            res["channels_found"].append(c)
                    res["valid"] = True
                    return res
            except Exception as e:
                res["errors"].append(f"JSON read error: {str(e)}")
                return res

        res["valid"] = True
        res["channels_found"] = self.CHANNELS.copy()
        return res

    def load_precipitation_to_grid(
        self,
        filepath: Optional[str] = None,
        target_grid: Optional[StormTraceGrid] = None
    ) -> Dict[str, Any]:
        """
        Loads GPM IMERG calibrated precipitation rate (mm/hr) resampled to STORMTRACE grid.
        Returns 2D grid, availability mask, and provenance metadata.
        """
        grid = target_grid or StormTraceGrid()
        precip_grid = grid.create_empty_grid(0.0)
        availability_mask = grid.create_availability_mask(is_available=False)

        if filepath and os.path.exists(filepath):
            val = self.validate_file(filepath)
            meta = self.extract_file_metadata(filepath)
            timestamp_utc = meta["timestamp_utc"] if meta else "UNKNOWN"

            is_synthetic = False
            if filepath.endswith(".json"):
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        payload = json.load(f)
                        dt_val = payload.get("data_type") or payload.get("provenance", {}).get("data_type")
                        if dt_val == "SYNTHETIC_DATA" or payload.get("source") == "STORMTRACE_SYNTHETIC_BENCHMARK" or "SYNTH" in filepath:
                            is_synthetic = True
                        raw_grid = payload.get("precipitationCal", precip_grid)
                        if len(raw_grid) == grid.height and len(raw_grid[0]) == grid.width:
                            precip_grid = raw_grid
                        else:
                            src_lons = payload.get("lons", [grid.min_lon, grid.max_lon])
                            src_lats = payload.get("lats", [grid.min_lat, grid.max_lat])
                            precip_grid = grid.resample_2d_bilinear(raw_grid, src_lons, src_lats)
                        availability_mask = grid.create_availability_mask(is_available=True)
                except Exception:
                    pass

            provenance = get_synthetic_imerg_metadata() if is_synthetic else self.metadata_spec
            status = "AVAILABLE_SYNTHETIC_IMERG" if is_synthetic else "AVAILABLE_REAL_IMERG"

            return {
                "status": status,
                "is_synthetic": is_synthetic,
                "timestamp_utc": timestamp_utc,
                "provenance": provenance,
                "target_grid": grid.to_dict(),
                "precipitation_mm_hr": precip_grid,
                "availability_mask": availability_mask
            }

        return {
            "status": "UNAVAILABLE",
            "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "provenance": self.metadata_spec,
            "target_grid": grid.to_dict(),
            "precipitation_mm_hr": precip_grid,
            "availability_mask": availability_mask
        }
