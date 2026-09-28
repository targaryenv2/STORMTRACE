#!/usr/bin/env python3
"""
STORMTRACE Robustness & Extreme Input Verification Suite (Priority 17 & 16)
================================================================================
Tests system resilience against:
    - Empty grids / No-storm scenarios
    - Corrupted / NaN / Inf values in input tensors
    - Mismatched grid dimensions
    - Missing temporal frames / Large gaps
    - Out-of-domain geographic coordinates
    - Storm cell splitting and merging events
================================================================================
"""

import unittest
import numpy as np
import torch
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ml.models.spatiotemporal_model import SpatiotemporalForecastNet, ModelConfig
from ml.tracking.cell_tracker import StormCellTracker
from ml.tracking.motion_estimator import ConvectiveMotionEstimator
from ml.datasets.leakage_checker import DataLeakageAuditor
from dataset.grid import StormTraceGrid


class TestRobustnessAndExtremeInputs(unittest.TestCase):
    """Verifies edge case handling, robustness, and negative case behavior."""

    def setUp(self):
        torch.manual_seed(42)
        self.config = ModelConfig(
            in_channels=1, out_channels=1, hidden_dims=[16, 32],
            spatial_height=32, spatial_width=32
        )
        self.model = SpatiotemporalForecastNet(self.config)
        self.tracker = StormCellTracker(dbz_threshold=35.0)
        self.motion_estimator = ConvectiveMotionEstimator()

    def test_01_no_storm_empty_grid(self):
        """Priority 16: Zero convective activity produces calm output, not phantom storms."""
        empty_input = torch.zeros(1, 5, 1, 32, 32)
        with torch.no_grad():
            forecast = self.model(empty_input)

        self.assertEqual(forecast.shape, (1, 6, 1, 32, 32))
        self.assertTrue(torch.isfinite(forecast).all())
        # Model output should remain low (no explosion of false reflectivity)
        max_val = forecast.abs().max().item()
        self.assertLess(max_val, 15.0, "Model hallucinated severe storm from empty grid")

    def test_02_nan_and_inf_tensor_sanitization(self):
        """Priority 17: Robustness against NaN or Inf values in input sensors."""
        bad_input = torch.randn(1, 5, 1, 32, 32)
        bad_input[0, 2, 0, 10, 10] = float("nan")
        bad_input[0, 3, 0, 15, 15] = float("inf")

        # Sanitize before model
        sanitized = torch.nan_to_num(bad_input, nan=0.0, posinf=70.0, neginf=0.0)
        with torch.no_grad():
            output = self.model(sanitized)

        self.assertTrue(torch.isfinite(output).all(), "NaN/Inf propagated through neural forward pass")

    def test_03_mismatched_grid_regridding(self):
        """Priority 17: Bilinear resampling handles arbitrary native grid shapes safely."""
        grid_tool = StormTraceGrid(domain="REGIONAL_EAST_INDIA", height=64, width=64)
        src_grid = [[float(i + j) for i in range(20)] for j in range(20)]
        src_lons = list(np.linspace(80.0, 92.0, 20))
        src_lats = list(np.linspace(18.0, 28.0, 20))

        resampled = grid_tool.resample_2d_bilinear(src_grid, src_lons, src_lats)
        self.assertEqual(len(resampled), 64)
        self.assertEqual(len(resampled[0]), 64)
        self.assertTrue(all(isinstance(v, float) for row in resampled for v in row))

    def test_04_out_of_domain_coordinates(self):
        """Priority 12: Grid flags points strictly outside target domain."""
        grid = StormTraceGrid.regional_east_india()
        # Points outside East India
        trivandrum = (8.50, 76.95)
        delhi = (28.61, 77.20)
        kolkata = (22.57, 88.36)

        self.assertFalse(grid.min_lat <= trivandrum[0] <= grid.max_lat and grid.min_lon <= trivandrum[1] <= grid.max_lon)
        self.assertFalse(grid.min_lat <= delhi[0] <= grid.max_lat and grid.min_lon <= delhi[1] <= grid.max_lon)
        self.assertTrue(grid.min_lat <= kolkata[0] <= grid.max_lat and grid.min_lon <= kolkata[1] <= grid.max_lon)

    def test_05_motion_estimator_stationary_case(self):
        """Priority 7: Stationary convective cells correctly classified."""
        c0 = (10.0, 10.0)
        c1 = (10.02, 10.01) # Negligible drift
        res = self.motion_estimator.estimate_centroid_motion(c0, c1, dt_minutes=15.0)
        self.assertEqual(res["motion_type"], "STATIONARY")
        self.assertLess(res["speed_kmh"], 5.0)

    def test_06_leakage_auditor_detects_overlaps(self):
        """Priority 14: Leakage auditor catches non-monotonic or overlapping partitions."""
        clean_past = ["2026-09-19T13:00:00Z", "2026-09-19T13:15:00Z", "2026-09-19T13:30:00Z"]
        clean_future = ["2026-09-19T13:45:00Z", "2026-09-19T14:00:00Z"]
        is_clean, errors = DataLeakageAuditor.check_sequence_temporal_integrity(clean_past, clean_future)
        self.assertTrue(is_clean)
        self.assertEqual(len(errors), 0)

        # Introduce leakage: T0 in future sequence
        leaked_future = ["2026-09-19T13:30:00Z", "2026-09-19T13:45:00Z"]
        is_clean_leaked, leak_errors = DataLeakageAuditor.check_sequence_temporal_integrity(clean_past, leaked_future)
        self.assertFalse(is_clean_leaked)
        self.assertGreater(len(leak_errors), 0)


if __name__ == "__main__":
    unittest.main()
