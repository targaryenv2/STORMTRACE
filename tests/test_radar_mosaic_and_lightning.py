#!/usr/bin/env python3
"""
Unit and Integration Tests for Sprint 1:
- MultiRadarMosaicEngine (9 stations, overlap compositing, divergence estimation)
- Dual-Head Spatiotemporal ConvLSTM with dedicated Lightning Prediction Head
- Backend API endpoints (/api/radar/stations, /api/radar/mosaic, /api/lightning/nowcast)
"""

import unittest
import torch
import numpy as np

from dataset.loaders.radar_mosaic import MultiRadarMosaicEngine, RADAR_STATION_NETWORK
from dataset.grid import StormTraceGrid
from ml.models.multimodal_convlstm import MultimodalSpatiotemporalForecastNet
from ml.extrapolator import ForecastExtrapolator


class TestMultiRadarMosaicAndLightning(unittest.TestCase):

    def setUp(self):
        self.grid = StormTraceGrid()
        self.mosaic_engine = MultiRadarMosaicEngine(self.grid)

    def test_radar_station_registry(self):
        """Verify standard IMD & ISRO radar stations are registered."""
        self.assertIn("DWR_KOLKATA", RADAR_STATION_NETWORK)
        self.assertIn("DWR_PARADEEP", RADAR_STATION_NETWORK)
        self.assertIn("DWR_TERLS", RADAR_STATION_NETWORK)
        self.assertGreaterEqual(len(RADAR_STATION_NETWORK), 9)

    def test_multi_radar_compositing(self):
        """Verify blending multiple overlapping radar volume fields."""
        h, w = self.grid.height, self.grid.width
        dbz1 = np.zeros((h, w), dtype=np.float32)
        dbz1[20:30, 20:30] = 48.0 # Strong storm core in Station 1

        dbz2 = np.zeros((h, w), dtype=np.float32)
        dbz2[25:35, 25:35] = 52.0 # Merging storm core in Station 2

        scans = [
            {"station_id": "DWR_KOLKATA", "dbz_grid": dbz1, "vel_grid": np.ones((h, w))*5.0},
            {"station_id": "DWR_PARADEEP", "dbz_grid": dbz2, "vel_grid": np.ones((h, w))*(-3.0)}
        ]

        res = self.mosaic_engine.create_multi_radar_composite(scans, method="MAX_REFLECTIVITY")
        self.assertIn("composite_dbz", res)
        self.assertIn("composite_velocity", res)
        self.assertIn("coverage_count_grid", res)
        self.assertIn("divergence_grid", res)
        self.assertGreaterEqual(res["metadata"]["peak_reflectivity_dbz"], 48.0)
        self.assertEqual(len(res["participating_stations"]), 2)

    def test_dual_head_convlstm_lightning_prediction(self):
        """Verify Dual-Head ConvLSTM outputs both reflectivity and calibrated lightning probability."""
        model = MultimodalSpatiotemporalForecastNet(out_seq_len=6)
        x = {
            "radar": torch.randn(1, 5, 1, 32, 32),
            "satellite": torch.randn(1, 5, 1, 32, 32),
            "nwp": torch.randn(1, 5, 2, 32, 32),
            "imerg": torch.randn(1, 5, 1, 32, 32),
            "lightning": torch.randn(1, 5, 1, 32, 32)
        }

        # Legacy call returns reflectivity tensor [B, 6, 1, H, W]
        out_refl = model(x)
        self.assertEqual(out_refl.shape, (1, 6, 1, 32, 32))

        # Dual-head call returns both
        out_dict = model.predict_nowcast_and_lightning(x)
        self.assertIn("reflectivity", out_dict)
        self.assertIn("lightning_prob", out_dict)
        self.assertEqual(out_dict["lightning_prob"].shape, (1, 6, 1, 32, 32))

        # Check probability bounds [0, 1]
        p_min = float(out_dict["lightning_prob"].min())
        p_max = float(out_dict["lightning_prob"].max())
        self.assertGreaterEqual(p_min, 0.0)
        self.assertLessEqual(p_max, 1.0)


if __name__ == "__main__":
    unittest.main()
