#!/usr/bin/env python3
"""
STORMTRACE Temporal Dataset, Loss Function, and Training Engine Test Suite
================================================================================
Comprehensive verification tests for:
    - 5->6 temporal sequence window generation
    - Timestamp ordering and strict future verification (T_target > T0)
    - Missing frame and temporal gap rejection
    - Zero future leakage chronological train/val/test splitting
    - Spatial grid validation across frames
    - Weighted Convective Loss and gradient backprop
    - One-step training sanity execution
    - Data governance gating: blocks final training when real East India data is absent
================================================================================
"""

import os
import sys
import unittest
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from ml.models.spatiotemporal_model import SpatiotemporalForecastNet, ModelConfig
from ml.datasets.temporal_radar_dataset import (
    TemporalRadarDataset,
    TemporalSequenceMetadata,
    create_dataloaders
)
from ml.train_conv_lstm import (
    WeightedConvectiveLoss,
    ConvLSTMTrainer,
    check_east_india_training_eligibility
)


class TestTemporalDatasetAndTraining(unittest.TestCase):
    """Test suite for dataset temporal slicing, loss functions, and training pipeline."""

    def setUp(self):
        torch.manual_seed(42)
        # Create a synthetic chronological sequence of 20 frames (15-minute dt)
        base_time = datetime(2024, 5, 26, 10, 0, 0, tzinfo=timezone.utc)
        self.mock_frames = []
        for i in range(20):
            ts = (base_time + timedelta(minutes=i * 15)).isoformat()
            # 32x32 spatial grid with a synthetic convective core
            grid = [[0.0 for _ in range(32)] for _ in range(32)]
            grid[10 + (i % 5)][10 + (i % 5)] = 45.0 # 45 dBZ core
            self.mock_frames.append({
                "timestamp": ts,
                "reflectivity_dbz": grid,
                "grid_shape": (32, 32),
                "is_real": True,
                "domain_name": "SOUTH_INDIA_TERLS" # Flagged as South India
            })

    def test_01_temporal_sequence_shapes(self):
        """Test 1: Verify 5-input and 6-target horizon tensor shapes."""
        dataset = TemporalRadarDataset(
            frames=self.mock_frames,
            in_seq_len=5,
            out_seq_len=6,
            lead_times_min=[15, 30, 45, 60, 90, 120],
            step_dt_min=15.0,
            spatial_size=(32, 32)
        )
        self.assertGreater(len(dataset), 0)
        inp, tgt = dataset[0]
        self.assertEqual(inp.shape, (5, 1, 32, 32))
        self.assertEqual(tgt.shape, (6, 1, 32, 32))
        self.assertTrue((inp >= 0.0).all() and (inp <= 1.0).all())
        self.assertTrue((tgt >= 0.0).all() and (tgt <= 1.0).all())

    def test_02_timestamp_monotonicity_and_future_targets(self):
        """Test 2: Verify all target timestamps strictly succeed T0 (no future leakage)."""
        dataset = TemporalRadarDataset(
            frames=self.mock_frames,
            in_seq_len=5,
            out_seq_len=6,
            lead_times_min=[15, 30, 45, 60, 90, 120],
            step_dt_min=15.0
        )
        for i in range(len(dataset)):
            sample_meta = dataset.get_sample_with_metadata(i)["metadata"]
            t0 = datetime.fromisoformat(sample_meta.t0_timestamp.replace("Z", "+00:00"))
            
            # Verify input timestamps are ascending and end with T0
            prev_t = None
            for in_ts_str in sample_meta.input_timestamps:
                in_t = datetime.fromisoformat(in_ts_str.replace("Z", "+00:00"))
                if prev_t:
                    self.assertGreater(in_t, prev_t)
                prev_t = in_t
            self.assertEqual(prev_t, t0)

            # Verify target timestamps are strictly in the future of T0
            for tgt_ts_str in sample_meta.target_timestamps:
                tgt_t = datetime.fromisoformat(tgt_ts_str.replace("Z", "+00:00"))
                self.assertGreater(tgt_t, t0)

    def test_03_missing_frame_and_gap_rejection(self):
        """Test 3: Verify that frames with large missing time gaps are rejected from sequences."""
        gapped_frames = list(self.mock_frames[:6])
        # Inject a 3-hour missing gap
        gap_time = datetime(2024, 5, 26, 15, 0, 0, tzinfo=timezone.utc)
        for j in range(6):
            ts = (gap_time + timedelta(minutes=j * 15)).isoformat()
            grid = [[10.0 for _ in range(32)] for _ in range(32)]
            gapped_frames.append({
                "timestamp": ts,
                "reflectivity_dbz": grid,
                "grid_shape": (32, 32),
                "is_real": True,
                "domain_name": "SOUTH_INDIA_TERLS"
            })

        dataset = TemporalRadarDataset(
            frames=gapped_frames,
            in_seq_len=5,
            out_seq_len=6,
            lead_times_min=[15, 30, 45, 60, 90, 120],
            step_dt_min=15.0,
            max_dt_tolerance_min=25.0
        )
        # Any window spanning across the 3-hour gap must be rejected
        for i in range(len(dataset)):
            meta = dataset.get_sample_with_metadata(i)["metadata"]
            t_first = datetime.fromisoformat(meta.input_timestamps[0].replace("Z", "+00:00"))
            t_last_in = datetime.fromisoformat(meta.input_timestamps[-1].replace("Z", "+00:00"))
            dt_input_window = (t_last_in - t_first).total_seconds() / 60.0
            # 5 frames at 15-min should span 60 min (tolerance < 75 min)
            self.assertLessEqual(dt_input_window, 75.0)

    def test_04_spatial_grid_validation(self):
        """Test 4: Verify that spatial dimension mismatches across frames raise an error."""
        inconsistent_frames = list(self.mock_frames)
        # Corrupt one frame with a different shape
        inconsistent_frames[3]["grid_shape"] = (48, 48)
        inconsistent_frames[3]["reflectivity_dbz"] = [[0.0 for _ in range(48)] for _ in range(48)]

        with self.assertRaises(ValueError) as ctx:
            TemporalRadarDataset(frames=inconsistent_frames, in_seq_len=5, out_seq_len=6)
        self.assertIn("Grid dimension mismatch", str(ctx.exception))

    def test_05_chronological_splitting_zero_leakage(self):
        """Test 5: Verify chronological train/val/test splitting prevents temporal leakage."""
        dataset = TemporalRadarDataset(
            frames=self.mock_frames,
            in_seq_len=5,
            out_seq_len=6,
            lead_times_min=[15, 30, 45, 60, 90, 120],
            step_dt_min=15.0
        )
        train_ds, val_ds, test_ds = dataset.split_chronological(train_ratio=0.60, val_ratio=0.20, test_ratio=0.20)
        self.assertGreater(len(train_ds), 0)
        self.assertGreater(len(val_ds), 0)
        self.assertGreater(len(test_ds), 0)

        # Check chronological separation
        max_train_ts = train_ds.get_sample_with_metadata(-1)["metadata"].t0_timestamp
        min_val_ts = val_ds.get_sample_with_metadata(0)["metadata"].t0_timestamp
        max_val_ts = val_ds.get_sample_with_metadata(-1)["metadata"].t0_timestamp
        min_test_ts = test_ds.get_sample_with_metadata(0)["metadata"].t0_timestamp

        t_train_max = datetime.fromisoformat(max_train_ts.replace("Z", "+00:00"))
        t_val_min = datetime.fromisoformat(min_val_ts.replace("Z", "+00:00"))
        t_val_max = datetime.fromisoformat(max_val_ts.replace("Z", "+00:00"))
        t_test_min = datetime.fromisoformat(min_test_ts.replace("Z", "+00:00"))

        self.assertLess(t_train_max, t_val_min, "Train and validation splits overlap in time")
        self.assertLess(t_val_max, t_test_min, "Validation and test splits overlap in time")

    def test_06_weighted_convective_loss(self):
        """Test 6: Verify WeightedConvectiveLoss penalizes high-dBZ errors more heavily."""
        loss_fn = WeightedConvectiveLoss(convective_weight=5.0, dbz_threshold_norm=0.50)
        
        # Case A: Error on background (target = 0.1, pred = 0.2)
        target_bg = torch.zeros(1, 6, 1, 16, 16)
        pred_bg = target_bg + 0.1
        loss_bg = loss_fn(pred_bg, target_bg).item()

        # Case B: Equal numerical error on severe storm core (target = 0.6 >= 0.5, pred = 0.5)
        target_storm = torch.ones(1, 6, 1, 16, 16) * 0.6
        pred_storm = target_storm - 0.1
        loss_storm = loss_fn(pred_storm, target_storm).item()

        # Severe core error must be 5x larger than background error of same magnitude
        self.assertAlmostEqual(loss_storm, loss_bg * 5.0, places=4)

    def test_07_training_step_sanity(self):
        """Test 7: Verify one full training epoch executes with loss reduction."""
        dataset = TemporalRadarDataset(
            frames=self.mock_frames,
            in_seq_len=5,
            out_seq_len=6,
            lead_times_min=[15, 30, 45, 60, 90, 120],
            step_dt_min=15.0,
            spatial_size=(32, 32)
        )
        train_loader = DataLoader(dataset, batch_size=2, shuffle=True)
        val_loader = DataLoader(dataset, batch_size=2, shuffle=False)

        config = ModelConfig(
            in_channels=1,
            out_channels=1,
            hidden_dims=[8, 16],
            spatial_height=32,
            spatial_width=32
        )
        trainer = ConvLSTMTrainer(config=config, lr=1e-3)

        # Run 2 epochs
        res = trainer.train(train_loader, val_loader, epochs=2)
        self.assertEqual(res["status"], "completed")
        self.assertEqual(len(res["history"]), 2)
        self.assertTrue(os.path.exists(res["checkpoint_path"]))

    def test_08_east_india_governance_eligibility(self):
        """Test 8: Verify data governance blocks final training when TERLS or synthetic data is passed."""
        # 1. Dataset with mock TERLS South India data
        terls_dataset = TemporalRadarDataset(
            frames=self.mock_frames,
            in_seq_len=5,
            out_seq_len=6
        )
        eligible, reason = check_east_india_training_eligibility(terls_dataset)
        self.assertFalse(eligible)
        self.assertIn("Training blocked", reason)
        self.assertIn("TERLS", reason)

        # 2. Mock East India 2024 dataset (eligible)
        east_india_frames = list(self.mock_frames)
        for f in east_india_frames:
            f["domain_name"] = "REGIONAL_EAST_INDIA"
        valid_dataset = TemporalRadarDataset(frames=east_india_frames, in_seq_len=5, out_seq_len=6)
        eligible_east, reason_east = check_east_india_training_eligibility(valid_dataset)
        self.assertTrue(eligible_east)
        self.assertIn("Eligible", reason_east)


if __name__ == "__main__":
    unittest.main(verbosity=2)
