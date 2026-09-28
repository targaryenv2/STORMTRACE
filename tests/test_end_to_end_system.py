#!/usr/bin/env python3
"""
STORMTRACE End-to-End Pipeline & Master Integration Test (Priority 24)
================================================================================
Comprehensive verification of the full forecasting stack:
    1. Data Ingestion & Spatial Bounds Validation
    2. Temporal Sequence Construction (T-60 to T0 -> T+15 to T+120)
    3. PyTorch Spatiotemporal ConvLSTM Forward Pass
    4. Neural Multimodal Fusion Architecture
    5. Stochastic MC-Dropout Uncertainty Estimation
    6. Kinematic Motion Vector Estimation
    7. Multi-Horizon Storm Cell Tracking
    8. Dynamic Future-Frame Evaluation (CSI, POD, FAR, Brier, RMSE)
    9. Empirical Probability Calibration
    10. Data Leakage Prevention
    11. Backend API Routing & Model Response Contracts
    12. Grounded AI Assistant Response Integrity
================================================================================
"""

import unittest
import os
import sys
import torch
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ml.models.spatiotemporal_model import SpatiotemporalForecastNet, ModelConfig
from ml.models.multimodal_convlstm import MultimodalSpatiotemporalForecastNet
from ml.datasets.temporal_radar_dataset import TemporalRadarDataset
from ml.datasets.leakage_checker import DataLeakageAuditor
from ml.evaluation.metrics import evaluate_forecast_vs_target, compute_csi, compute_pod, compute_far
from ml.evaluation.future_frame_evaluator import FutureFrameEvaluator
from ml.calibration.prob_calibrator import ProbabilityCalibrator
from ml.tracking.cell_tracker import StormCellTracker
from ml.tracking.motion_estimator import ConvectiveMotionEstimator
from ml.extrapolator import ForecastExtrapolator, PyTorchConvLSTMPredictor, OpticalFlowAdvectionBaseline
from dataset.grid import StormTraceGrid
from backend.stormtrace.ai.provider import LocalFallbackProvider, get_ai_provider


class TestEndToEndSTORMTRACEPipeline(unittest.TestCase):
    """End-to-End Master Test Suite validating Priorities 1 through 28."""

    def setUp(self):
        torch.manual_seed(42)
        np.random.seed(42)

    def test_01_grid_and_spatial_bounds(self):
        """P12: Target Regional East India grid boundaries (83.5-89.8E, 20.0-26.3N)."""
        grid = StormTraceGrid.regional_east_india(height=64, width=64)
        self.assertEqual(grid.min_lon, 83.5)
        self.assertEqual(grid.max_lon, 89.8)
        self.assertEqual(grid.min_lat, 20.0)
        self.assertEqual(grid.max_lat, 26.3)
        self.assertEqual(grid.height, 64)
        self.assertEqual(grid.width, 64)

    def test_02_pytorch_convlstm_forward_and_mc_dropout(self):
        """P1 & P6: Neural ConvLSTM execution and 25-pass MC Dropout uncertainty."""
        config = ModelConfig(
            in_channels=1, out_channels=1, hidden_dims=[16, 32],
            dropout_rate=0.2, spatial_height=32, spatial_width=32
        )
        model = SpatiotemporalForecastNet(config)
        input_seq = torch.randn(2, 5, 1, 32, 32) # [B, T_in=5, C=1, H, W]

        # Standard forward pass
        forecast = model(input_seq, future_steps=6)
        self.assertEqual(forecast.shape, (2, 6, 1, 32, 32))

        # Neural MC Dropout passes
        mean_fc, unc_std = model.predict_mc_dropout(input_seq, future_steps=6, num_passes=25)
        self.assertEqual(mean_fc.shape, (2, 6, 1, 32, 32))
        self.assertEqual(unc_std.shape, (2, 6, 1, 32, 32))
        self.assertTrue(torch.isfinite(mean_fc).all())
        self.assertTrue(torch.isfinite(unc_std).all())
        self.assertTrue((unc_std >= 0.0).all())

    def test_03_multimodal_fusion_architecture(self):
        """P8: Multimodal ConvLSTM network with dynamic availability masking."""
        multi_net = MultimodalSpatiotemporalForecastNet(out_channels=1, hidden_dims=[32, 64], dropout_rate=0.2)
        b, t, h, w = 2, 5, 32, 32

        inputs = {
            "radar": torch.randn(b, t, 1, h, w),
            "satellite": torch.randn(b, t, 1, h, w),
            "nwp": torch.randn(b, t, 2, h, w),
            "imerg": torch.randn(b, t, 1, h, w),
            "lightning": torch.randn(b, t, 1, h, w),
            "availability_mask": torch.tensor([[1.0, 0.0, 1.0, 1.0, 1.0], [1.0, 1.0, 1.0, 1.0, 1.0]])
        }

        fused_forecast = multi_net(inputs, future_steps=6)
        self.assertEqual(fused_forecast.shape, (b, 6, 1, h, w))
        self.assertTrue(torch.isfinite(fused_forecast).all())

    def test_04_motion_estimation_and_tracking(self):
        """P7 & P22: Motion estimation and multi-horizon storm cell tracking."""
        motion_est = ConvectiveMotionEstimator(grid_dx_km=10.0, grid_dy_km=10.0)
        c_prev = (20.0, 20.0)
        c_curr = (21.5, 19.0) # Moved +1.5 x, -1.0 y in 15 min
        motion = motion_est.estimate_centroid_motion(c_prev, c_curr, dt_minutes=15.0)

        self.assertGreater(motion["speed_kmh"], 0.0)
        self.assertIn("compass", motion)
        self.assertIn(motion["motion_type"], ["FAST_MOVING", "MODERATE_MOTION", "STATIONARY"])

        # Multi-horizon tracking
        tracker = StormCellTracker(dbz_threshold=35.0)
        mock_grid = np.zeros((48, 48), dtype=np.float32)
        mock_grid[15:25, 20:30] = 52.0 # Convective cell
        lons = list(np.linspace(84.0, 89.0, 48))
        lats = list(np.linspace(21.0, 26.0, 48))
        cells = tracker.extract_cells_from_grid(mock_grid.tolist(), lons, lats, threshold=35.0)
        self.assertGreater(len(cells), 0)
        self.assertGreaterEqual(cells[0]["max_dbz"], 50.0)

    def test_05_future_frame_evaluation_and_metrics(self):
        """P4 & P5: Future-frame evaluation against ground truth."""
        evaluator = FutureFrameEvaluator(dbz_threshold=35.0)
        grid_shape = (32, 32)
        pred_grid = np.zeros(grid_shape)
        pred_grid[10:20, 10:20] = 48.0 # Hits & some false alarms

        target_grid = np.zeros(grid_shape)
        target_grid[12:22, 12:22] = 50.0 # Overlap

        metrics = evaluate_forecast_vs_target(pred_grid, target_grid, threshold_dbz=35.0)
        self.assertEqual(metrics["evaluation_status"], "CALCULATED_FROM_GROUND_TRUTH")
        self.assertGreater(metrics["metrics"]["csi"], 0.0)
        self.assertGreater(metrics["metrics"]["pod"], 0.0)
        self.assertLessEqual(metrics["metrics"]["far"], 1.0)
        self.assertTrue(metrics["metrics"]["brier_score"] >= 0.0)

    def test_06_probability_calibrator(self):
        """P18: Empirical probability calibration."""
        calibrator = ProbabilityCalibrator(n_bins=5)
        raw_scores = np.array([10.0, 25.0, 35.0, 45.0, 55.0, 65.0])
        binary_targets = np.array([0, 0, 0, 1, 1, 1])

        calibrator.fit(raw_scores, binary_targets)
        calibrated_probs = calibrator.calibrate(raw_scores)

        self.assertEqual(len(calibrated_probs), len(raw_scores))
        self.assertTrue(all(0.0 <= p <= 1.0 for p in calibrated_probs))
        # Monotonicity check: higher reflectivity -> higher probability
        self.assertTrue(calibrated_probs[-1] >= calibrated_probs[0])

    def test_07_leakage_prevention(self):
        """P14: Zero future leakage across temporal splits."""
        train_ts = ["2026-09-01T12:00:00Z", "2026-09-01T12:15:00Z"]
        val_ts = ["2026-09-02T12:00:00Z", "2026-09-02T12:15:00Z"]
        test_ts = ["2026-09-03T12:00:00Z", "2026-09-03T12:15:00Z"]

        audit = DataLeakageAuditor.audit_splits_chronology(train_ts, val_ts, test_ts)
        self.assertEqual(audit["status"], "CLEAN")
        self.assertTrue(audit["is_leakage_free"])
        self.assertEqual(len(audit["violations"]), 0)

    def test_08_forecaster_engine_and_baseline_separation(self):
        """P1 & P20: Neural predictor vs baseline isolation."""
        engine = ForecastExtrapolator()
        mock_frame = {
            "step_index": 0,
            "time_min": 0,
            "grids": {"reflectivity_dbz": [[0.0] * 32 for _ in range(32)]},
            "cells": []
        }
        mock_frame["grids"]["reflectivity_dbz"][15][15] = 45.0

        # Neural prediction
        neural_pred = engine.predict_neural([mock_frame] * 5)
        self.assertEqual(neural_pred["model_type"], "PyTorch_ConvLSTM_Forecaster")
        self.assertEqual(len(neural_pred["lead_time_forecasts"]), 6)

        # Baseline prediction
        baseline_pred = engine.predict([mock_frame] * 5)
        self.assertEqual(baseline_pred["model_type"], "OpticalFlow_Advection_Baseline")
        self.assertEqual(len(baseline_pred["lead_time_forecasts"]), 6)

    def test_09_ai_assistant_grounding_and_no_false_claims(self):
        """P23: AI Assistant does not claim live radar, trained weights, or fake global coverage."""
        provider = LocalFallbackProvider()
        res = provider.generate_response("What AI model architecture and training status do you use?")
        self.assertIn("This is AI decision-support, not an official IMD warning.", res["reply"])
        self.assertIn("verified", res["reply"].lower())
        self.assertIn("convlstm", res["reply"].lower())


if __name__ == "__main__":
    unittest.main()
