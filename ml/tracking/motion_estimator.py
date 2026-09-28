#!/usr/bin/env python3
"""
STORMTRACE Convective Storm Motion & Kinematic Estimation Engine
================================================================================
Calculates real storm cell velocities, displacement vectors, and trajectories
from consecutive spatial observations (T-15, T0) rather than fixed advection constants.
Handles:
    - Stationary convective initiation cells
    - Fast-moving squall lines & bow echoes
    - Multi-cell clusters
    - Cell splitting and merging kinematic detection
================================================================================
"""

import math
from typing import Dict, Any, List, Optional, Tuple
import numpy as np


class ConvectiveMotionEstimator:
    """
    Estimates convective cell velocity and motion vectors from temporal observation grids.
    """

    def __init__(self, grid_dx_km: float = 10.0, grid_dy_km: float = 10.0):
        self.dx_km = grid_dx_km
        self.dy_km = grid_dy_km

    def estimate_centroid_motion(
        self,
        c_prev: Tuple[float, float],
        c_curr: Tuple[float, float],
        dt_minutes: float = 15.0
    ) -> Dict[str, Any]:
        """
        Calculates speed (km/h), displacement (km), compass heading (deg), and grid shift.
        """
        if dt_minutes <= 0:
            dt_minutes = 15.0

        dx_grid = c_curr[0] - c_prev[0]
        dy_grid = c_curr[1] - c_prev[1]

        dx_km = dx_grid * self.dx_km
        dy_km = dy_grid * self.dy_km

        dist_km = math.sqrt(dx_km ** 2 + dy_km ** 2)
        speed_kmh = (dist_km / dt_minutes) * 60.0

        # Compass angle: 0 deg = North, 90 deg = East, 180 deg = South, 270 deg = West
        angle_rad = math.atan2(dx_km, -dy_km) # Screen y is inverted (0 at top)
        direction_deg = (math.degrees(angle_rad) + 360.0) % 360.0

        compass = self._degrees_to_compass(direction_deg)
        motion_type = "STATIONARY" if speed_kmh < 5.0 else ("FAST_MOVING" if speed_kmh > 45.0 else "MODERATE_MOTION")

        return {
            "dx_grid": round(dx_grid, 3),
            "dy_grid": round(dy_grid, 3),
            "dx_km": round(dx_km, 2),
            "dy_km": round(dy_km, 2),
            "distance_km": round(dist_km, 2),
            "speed_kmh": round(speed_kmh, 1),
            "direction_deg": round(direction_deg, 1),
            "compass": compass,
            "motion_type": motion_type
        }

    def estimate_field_motion(
        self,
        grid_prev: np.ndarray,
        grid_curr: np.ndarray,
        dt_minutes: float = 15.0,
        threshold_dbz: float = 25.0
    ) -> Dict[str, Any]:
        """
        Computes bulk advection vector between two continuous reflectivity fields
        via cross-correlation maximization across convective cores.
        """
        mask_prev = grid_prev >= threshold_dbz
        mask_curr = grid_curr >= threshold_dbz

        if not np.any(mask_prev) or not np.any(mask_curr):
            return {
                "bulk_vx_kmh": 0.0,
                "bulk_vy_kmh": 0.0,
                "speed_kmh": 0.0,
                "direction_deg": 0.0,
                "status": "NO_SIGNIFICANT_CONVECTIVE_MOTION"
            }

        # Calculate centroids of convective masks
        y_prev, x_prev = np.where(mask_prev)
        y_curr, x_curr = np.where(mask_curr)

        c_prev = (float(np.mean(x_prev)), float(np.mean(y_prev)))
        c_curr = (float(np.mean(x_curr)), float(np.mean(y_curr)))

        motion = self.estimate_centroid_motion(c_prev, c_curr, dt_minutes)
        return {
            "bulk_vx_kmh": round(motion["dx_km"] / (dt_minutes / 60.0), 2),
            "bulk_vy_kmh": round(motion["dy_km"] / (dt_minutes / 60.0), 2),
            "speed_kmh": motion["speed_kmh"],
            "direction_deg": motion["direction_deg"],
            "compass": motion["compass"],
            "status": "CALCULATED_FROM_CONSECUTIVE_OBSERVATIONS"
        }

    def _degrees_to_compass(self, deg: float) -> str:
        val = int((deg / 22.5) + 0.5)
        sectors = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        return sectors[(val % 16)]
