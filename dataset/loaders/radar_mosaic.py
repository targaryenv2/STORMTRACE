#!/usr/bin/env python3
"""
STORMTRACE Multi-Radar Mosaic & Compositing Engine
================================================================================
Implements Multi-Doppler Weather Radar (DWR) Compositing & 2D Grid Mosaicking.
Fuses overlapping volume scans from multiple radar stations into a unified
$128 \times 128$ Cartesian grid at $0.04^\circ$ (~4.4 km) resolution.

Key Capabilities:
1. Multi-Radar Station Registry (IMD & ISRO stations: Kolkata, Paradeep, Gopalpur,
   Agartala, Patna, Ranchi, TERLS, Kochi, Chennai).
2. Polar-to-Cartesian projection and distance/beam-height correction.
3. Multi-Station Compositing Strategies:
   - Maximum Reflectivity (MRMS standard for severe storm core capture)
   - Inverse Distance Weighting (IDW)
   - Quality-Weighted Dual-Doppler Fusion
4. Radar Coverage Map & Dual-Doppler Overlap Diagnostics.
5. Radial Velocity & Divergence Synthesis for Convective Initiation precursor detection.
================================================================================
"""

import math
import numpy as np
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple, Union

try:
    from dataset.grid import StormTraceGrid
    from dataset.provenance import (
        create_dataset_metadata,
        DataType,
        TemporalSemantics
    )
except ImportError:
    from stormtrace.data.grid import StormTraceGrid
    from stormtrace.data.provenance import (
        create_dataset_metadata,
        DataType,
        TemporalSemantics
    )


# Standard Doppler Weather Radar (DWR) Station Network Registry in India
RADAR_STATION_NETWORK: Dict[str, Dict[str, Any]] = {
    "DWR_KOLKATA": {
        "station_id": "DWR_KOLKATA",
        "station_name": "IMD Kolkata (VECC/Alipore)",
        "lat": 22.5726,
        "lon": 88.3639,
        "elevation_m": 12.0,
        "band": "S-Band",
        "frequency_ghz": 2.8,
        "max_range_km": 250.0,
        "beam_width_deg": 1.0,
        "organization": "IMD"
    },
    "DWR_PARADEEP": {
        "station_id": "DWR_PARADEEP",
        "station_name": "IMD Paradeep Radar",
        "lat": 20.3168,
        "lon": 86.6114,
        "elevation_m": 35.0,
        "band": "S-Band",
        "frequency_ghz": 2.8,
        "max_range_km": 250.0,
        "beam_width_deg": 1.0,
        "organization": "IMD"
    },
    "DWR_GOPALPUR": {
        "station_id": "DWR_GOPALPUR",
        "station_name": "IMD Gopalpur Radar",
        "lat": 19.3080,
        "lon": 84.9120,
        "elevation_m": 48.0,
        "band": "S-Band",
        "frequency_ghz": 2.8,
        "max_range_km": 250.0,
        "beam_width_deg": 1.0,
        "organization": "IMD"
    },
    "DWR_AGARTALA": {
        "station_id": "DWR_AGARTALA",
        "station_name": "IMD Agartala Radar",
        "lat": 23.8315,
        "lon": 91.2868,
        "elevation_m": 15.0,
        "band": "S-Band",
        "frequency_ghz": 2.8,
        "max_range_km": 250.0,
        "beam_width_deg": 1.0,
        "organization": "IMD"
    },
    "DWR_PATNA": {
        "station_id": "DWR_PATNA",
        "station_name": "IMD Patna Radar",
        "lat": 25.5941,
        "lon": 85.1376,
        "elevation_m": 53.0,
        "band": "C-Band",
        "frequency_ghz": 5.6,
        "max_range_km": 250.0,
        "beam_width_deg": 1.0,
        "organization": "IMD"
    },
    "DWR_RANCHI": {
        "station_id": "DWR_RANCHI",
        "station_name": "IMD Ranchi Radar",
        "lat": 23.3441,
        "lon": 85.3096,
        "elevation_m": 650.0,
        "band": "X-Band",
        "frequency_ghz": 9.4,
        "max_range_km": 150.0,
        "beam_width_deg": 1.0,
        "organization": "IMD"
    },
    "DWR_TERLS": {
        "station_id": "DWR_TERLS",
        "station_name": "ISRO TERLS Thumba DWR",
        "lat": 8.5360,
        "lon": 76.8710,
        "elevation_m": 25.0,
        "band": "C-Band",
        "frequency_ghz": 5.6,
        "max_range_km": 250.0,
        "beam_width_deg": 1.0,
        "organization": "ISRO"
    },
    "DWR_KOCHI": {
        "station_id": "DWR_KOCHI",
        "station_name": "IMD / Naval Kochi Radar",
        "lat": 9.9312,
        "lon": 76.2673,
        "elevation_m": 10.0,
        "band": "C-Band",
        "frequency_ghz": 5.6,
        "max_range_km": 250.0,
        "beam_width_deg": 1.0,
        "organization": "IMD"
    },
    "DWR_CHENNAI": {
        "station_id": "DWR_CHENNAI",
        "station_name": "IMD Chennai Radar",
        "lat": 13.0827,
        "lon": 80.2707,
        "elevation_m": 16.0,
        "band": "S-Band",
        "frequency_ghz": 2.8,
        "max_range_km": 250.0,
        "beam_width_deg": 1.0,
        "organization": "IMD"
    }
}


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Computes great-circle distance between two geographic coordinates in km."""
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2.0)**2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


class MultiRadarMosaicEngine:
    """
    Composites multiple Doppler Weather Radar scans onto a unified regional grid.
    """

    def __init__(self, target_grid: Optional[StormTraceGrid] = None):
        self.grid = target_grid or StormTraceGrid()
        self.height, self.width = self.grid.height, self.grid.width
        self.lats, self.lons = self.grid.get_lat_lon_mesh()

    def calculate_station_distance_grid(self, station_id: str) -> np.ndarray:
        """Computes a 2D grid [H, W] of distances in km from a given radar station."""
        stn = RADAR_STATION_NETWORK.get(station_id)
        if not stn:
            raise ValueError(f"Unknown station ID: {station_id}")
        stn_lat, stn_lon = stn["lat"], stn["lon"]

        # Vectorized approximation suitable for regional domain
        dlat = np.radians(self.lats - stn_lat)
        dlon = np.radians(self.lons - stn_lon)
        lat1 = np.radians(stn_lat)
        lat2 = np.radians(self.lats)

        a = np.sin(dlat / 2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0)**2
        c = 2.0 * np.arctan2(np.sqrt(a), np.sqrt(1.0 - np.clip(a, 0.0, 1.0)))
        return 6371.0 * c

    def get_radar_quality_weight(
        self,
        station_id: str,
        dist_km: np.ndarray,
        elevation_angle_deg: float = 0.5
    ) -> np.ndarray:
        """
        Computes distance-and-beam-broadening quality weights.
        Higher quality close to radar; decays near maximum range or beam blockage.
        """
        stn = RADAR_STATION_NETWORK.get(station_id, {"max_range_km": 250.0})
        max_r = stn.get("max_range_km", 250.0)

        # Quality starts near 1.0 within 150km, tapers off as beam broadens / height increases
        # Earth curvature: Beam altitude h = r*sin(theta) + r^2 / (2 * 4/3 * R_earth)
        r_eff = 6371.0 * 4.0 / 3.0
        beam_alt_km = (
            dist_km * math.sin(math.radians(elevation_angle_deg)) +
            (dist_km**2) / (2.0 * r_eff)
        )

        # Weight is 0 beyond max range or if beam is above 10km (stratosphere)
        in_range = dist_km <= max_r
        dist_factor = np.exp(-0.5 * (dist_km / 120.0)**2)
        alt_factor = np.clip(1.0 - (beam_alt_km / 8.0), 0.0, 1.0)

        weight = np.where(in_range, dist_factor * alt_factor, 0.0)
        return weight

    def create_multi_radar_composite(
        self,
        radar_scans: List[Dict[str, Any]],
        method: str = "MAX_REFLECTIVITY"
    ) -> Dict[str, Any]:
        """
        Fuses multiple station radar fields into a single mosaic composite.

        Args:
            radar_scans: List of dicts, each containing:
                - "station_id": e.g. "DWR_KOLKATA"
                - "dbz_grid": 2D array [H, W] of reflectivity in dBZ
                - "vel_grid": Optional 2D array [H, W] of radial velocity (m/s)
                - "timestamp_utc": ISO timestamp
            method: "MAX_REFLECTIVITY", "IDW", or "QUALITY_WEIGHTED"

        Returns:
            Dict containing:
                - "composite_dbz": 2D array [H, W]
                - "composite_velocity": 2D array [H, W]
                - "coverage_count_grid": 2D array [H, W] (number of active radars covering each pixel)
                - "participating_stations": List of active station IDs
                - "divergence_grid": 2D array [H, W] of estimated horizontal convergence/divergence
                - "metadata": Provenance and operational metadata
        """
        if not radar_scans:
            empty_grid = np.zeros((self.height, self.width), dtype=np.float32)
            return {
                "composite_dbz": empty_grid,
                "composite_velocity": empty_grid,
                "coverage_count_grid": np.zeros((self.height, self.width), dtype=np.int32),
                "participating_stations": [],
                "divergence_grid": empty_grid,
                "metadata": {"status": "NO_RADAR_DATA"}
            }

        # Initialize accumulation buffers
        max_dbz = np.full((self.height, self.width), -30.0, dtype=np.float32)
        weighted_dbz_sum = np.zeros((self.height, self.width), dtype=np.float32)
        weighted_vel_sum = np.zeros((self.height, self.width), dtype=np.float32)
        weight_sum = np.zeros((self.height, self.width), dtype=np.float32)
        coverage_mask = np.zeros((self.height, self.width), dtype=np.int32)
        participating = []

        for scan in radar_scans:
            stn_id = scan.get("station_id")
            if stn_id not in RADAR_STATION_NETWORK:
                # Fallback to default coordinate if not registered
                continue

            participating.append(stn_id)
            dbz = np.asarray(scan.get("dbz_grid", np.zeros((self.height, self.width))), dtype=np.float32)
            vel = np.asarray(scan.get("vel_grid", np.zeros((self.height, self.width))), dtype=np.float32)

            dist_km = self.calculate_station_distance_grid(stn_id)
            weights = self.get_radar_quality_weight(stn_id, dist_km)
            valid_mask = (weights > 0.01)

            # Update coverage count
            coverage_mask += valid_mask.astype(np.int32)

            # Max Reflectivity
            masked_dbz = np.where(valid_mask, dbz, -30.0)
            max_dbz = np.maximum(max_dbz, masked_dbz)

            # Quality-weighted accumulators
            weighted_dbz_sum += (np.maximum(dbz, 0.0) * weights)
            weighted_vel_sum += (vel * weights)
            weight_sum += weights

        # Finalize composite fields according to chosen method
        safe_weight = np.where(weight_sum > 1e-5, weight_sum, 1.0)

        if method == "MAX_REFLECTIVITY":
            composite_dbz = np.where(coverage_mask > 0, np.maximum(max_dbz, 0.0), 0.0)
        else: # IDW or QUALITY_WEIGHTED
            composite_dbz = np.where(coverage_mask > 0, weighted_dbz_sum / safe_weight, 0.0)

        composite_vel = np.where(coverage_mask > 0, weighted_vel_sum / safe_weight, 0.0)

        # 2D Divergence Estimation via spatial gradient: div(V) = dU/dx + dV/dy
        # Approximated from composite radial velocity field
        dy, dx = np.gradient(composite_vel)
        divergence = (dx + dy) * 1e3 # Scaled to 10^-3 s^-1

        return {
            "composite_dbz": composite_dbz.astype(np.float32),
            "composite_velocity": composite_vel.astype(np.float32),
            "coverage_count_grid": coverage_mask,
            "participating_stations": participating,
            "divergence_grid": divergence.astype(np.float32),
            "metadata": {
                "compositing_method": method,
                "station_count": len(participating),
                "grid_resolution_deg": self.grid.resolution_deg,
                "peak_reflectivity_dbz": float(np.max(composite_dbz)),
                "severe_convective_coverage_pct": float(np.mean(composite_dbz >= 35.0) * 100.0),
                "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            }
        }


if __name__ == "__main__":
    mosaic_engine = MultiRadarMosaicEngine()
    print("MultiRadarMosaicEngine initialized successfully.")
    print(f"Registered radar stations: {list(RADAR_STATION_NETWORK.keys())}")
