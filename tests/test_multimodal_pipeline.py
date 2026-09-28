#!/usr/bin/env python3
"""
STORMTRACE Multimodal Data Pipeline & Provenance Test Suite
Phase 19: Validates satellite, lightning/WGLC, radar, ERA5 NWP, GPM IMERG loaders,
temporal alignment, common grid resampling, missing-data masks, manifest integrity,
regional high-res grid, proxy convective labeling, model training, evaluation metrics,
and downstream forecasting/tracking/analog integration.
"""

import os
import sys
import json
import csv
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from ml.provenance import (
        DataType, TemporalSemantics, SystemMode,
        get_wglc_climatology_metadata, get_insat3ds_metadata,
        get_era5_metadata, get_imerg_metadata, get_radar_demo_metadata
    )
    from dataset.grid import StormTraceGrid, GridDomain, MODALITY_SPECS
    from dataset.alignment import MultimodalTemporalAligner, TemporalToleranceConfig, parse_iso_timestamp
    from dataset.loaders.satellite_loader import Insat3dsSatelliteLoader
    from dataset.loaders.lightning_loader import WglcLightningLoader
    from dataset.loaders.radar_loader import RadarDataLoader
    from dataset.loaders.nwp_loader import NwpEra5Loader
    from dataset.loaders.imerg_loader import ImergPrecipitationLoader
    from dataset.sample_builder import MultimodalSampleBuilder
    from ml.train_model import MultimodalNowcastTrainer, derive_convective_proxy_label
    from ml.evaluate_model import compute_contingency_metrics, persistence_forecast, optical_flow_extrapolation_forecast, run_evaluation
    from ml.extrapolator import ForecastExtrapolator
    from ml.tracking.cell_tracker import StormCellTracker
    from ml.analogs.analog_matcher import HistoricalAnalogMatcher
except ImportError:
    from stormtrace.data.provenance import (
        DataType, TemporalSemantics, SystemMode,
        get_wglc_climatology_metadata, get_insat3ds_metadata,
        get_era5_metadata, get_imerg_metadata, get_radar_demo_metadata
    )
    from stormtrace.data.grid import StormTraceGrid, GridDomain, MODALITY_SPECS
    from stormtrace.data.alignment import MultimodalTemporalAligner, TemporalToleranceConfig, parse_iso_timestamp
    from stormtrace.data.satellite_loader import Insat3dsSatelliteLoader
    from stormtrace.data.lightning_loader import WglcLightningLoader
    from stormtrace.data.radar_loader import RadarDataLoader
    from stormtrace.data.nwp_loader import NwpEra5Loader
    from stormtrace.data.imerg_loader import ImergPrecipitationLoader
    from stormtrace.data.sample_builder import MultimodalSampleBuilder
    from scripts.train_model import MultimodalNowcastTrainer, derive_convective_proxy_label
    from scripts.evaluate_model import compute_contingency_metrics, persistence_forecast, optical_flow_extrapolation_forecast, run_evaluation
    from backend.stormtrace.forecast.extrapolator import ForecastExtrapolator
    from backend.stormtrace.tracking.cell_tracker import StormCellTracker
    from backend.stormtrace.analogs.analog_matcher import HistoricalAnalogMatcher

passed = 0
failed = 0

def assert_test(cond, msg):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✓ {msg}")
    else:
        failed += 1
        print(f"  ✗ FAIL: {msg}")


def run_all_tests():
    print("\n================================================================================")
    print("🧪 RUNNING STORMTRACE MULTIMODAL DATA PIPELINE TEST SUITE")
    print("================================================================================\n")

    # Group 1: Provenance & Semantic Data Types (Phase 1 & 16)
    print("--- Group 1: Provenance & Data Integrity Classification ---")
    wglc_meta = get_wglc_climatology_metadata()
    assert_test(wglc_meta["data_type"] == "REAL_CLIMATOLOGY", "WGLC classified strictly as REAL_CLIMATOLOGY")
    assert_test(wglc_meta["real_time_capability"] is False, "WGLC real_time_capability is False")
    assert_test(wglc_meta["event_level"] is False, "WGLC event_level is False")
    assert_test(wglc_meta["role_in_model"] == "auxiliary_climatological_baseline", "WGLC role is auxiliary climatological baseline")
    assert_test("not an event-level or real-time" in wglc_meta["disclaimer"].lower(), "WGLC disclaimer contains mandatory non-real-time statement")

    insat_meta = get_insat3ds_metadata()
    assert_test(insat_meta["source"] == "ISRO_MOSDAC", "INSAT-3DS source is ISRO_MOSDAC")
    assert_test(insat_meta["product_id"] == "3SIMG_L1C_ASIA_MER", "INSAT-3DS product ID is 3SIMG_L1C_ASIA_MER")
    assert_test(insat_meta["data_type"] == "REAL_OBSERVATION", "INSAT-3DS is REAL_OBSERVATION")

    demo_radar_meta = get_radar_demo_metadata()
    assert_test(demo_radar_meta["data_type"] == "DEMO_DATA", "Offline radar explicitly tagged as DEMO_DATA")

    # Group 2: Common Spatiotemporal Grid & Bilinear Resampling (Phase 7)
    print("\n--- Group 2: Common Spatiotemporal Grid & Resampling ---")
    grid = StormTraceGrid(min_lon=68.0, min_lat=6.0, max_lon=98.0, max_lat=36.0, height=32, width=32)
    assert_test(grid.height == 32 and grid.width == 32, "Grid initialized with 32x32 dimensions")
    assert_test(len(grid.lons) == 32 and len(grid.lats) == 32, "Grid coordinates match dimensions")

    # Resample test source array
    src_lons = [65.0, 75.0, 85.0, 95.0, 105.0]
    src_lats = [5.0, 15.0, 25.0, 35.0, 45.0]
    src_grid = [
        [10.0, 20.0, 30.0, 40.0, 50.0],
        [15.0, 25.0, 35.0, 45.0, 55.0],
        [20.0, 30.0, 40.0, 50.0, 60.0],
        [25.0, 35.0, 45.0, 65.0, 75.0],
        [30.0, 40.0, 50.0, 60.0, 70.0]
    ]
    resampled = grid.resample_2d_bilinear(src_grid, src_lons, src_lats)
    assert_test(len(resampled) == 32 and len(resampled[0]) == 32, "Resampled array matches target grid dimensions")
    assert_test(resampled[16][16] > 0.0, "Bilinear interpolation produces non-zero internal values")

    # Group 3: Temporal Alignment & Tolerance Matching (Phase 8)
    print("\n--- Group 3: Temporal Alignment & Modality Tolerance ---")
    aligner = MultimodalTemporalAligner(TemporalToleranceConfig(
        radar_tolerance_sec=600,
        satellite_tolerance_sec=1800,
        imerg_tolerance_sec=1800,
        era5_tolerance_sec=3600
    ))

    t0_target = "2025-05-12T14:30:00Z"
    sat_candidates = ["2025-05-12T14:15:00Z", "2025-05-12T15:30:00Z"]
    radar_candidates = ["2025-05-12T14:28:00Z", "2025-05-12T15:00:00Z"]
    imerg_candidates = ["2025-05-12T14:00:00Z"]
    era5_candidates = ["2025-05-12T14:00:00Z", "2025-05-12T15:00:00Z"]

    matched = aligner.match_modalities(
        t0_iso=t0_target,
        available_radar_timestamps=radar_candidates,
        available_satellite_timestamps=sat_candidates,
        available_imerg_timestamps=imerg_candidates,
        available_era5_timestamps=era5_candidates
    )

    assert_test(matched["modalities"]["satellite_insat3ds"]["available"] is True, "Satellite matched within 30 min tolerance")
    assert_test(matched["modalities"]["satellite_insat3ds"]["matched_timestamp_utc"] == "2025-05-12T14:15:00Z", "Closest satellite timestamp selected (14:15 UTC)")
    assert_test(matched["modalities"]["radar"]["available"] is True, "Radar matched within 10 min tolerance (14:28 UTC)")
    assert_test(matched["modalities"]["lightning_wglc"]["climatological_month"] == 5, "WGLC correctly assigned month 5 (May) baseline")
    assert_test(matched["modalities"]["lightning_wglc"]["matched_timestamp_utc"] is None, "WGLC matched_timestamp_utc is None (no fake event timestamp)")

    # Group 4: Satellite Loader (Phase 2)
    print("\n--- Group 4: INSAT-3DS Satellite Loader ---")
    sat_loader = Insat3dsSatelliteLoader("data/raw/satellite/insat3ds")
    mock_meta = sat_loader.extract_file_metadata("3SIMG_12MAY2025_1430_L1C_ASIA_MER.h5")
    assert_test(mock_meta["satellite"] == "INSAT-3DS", "Extracted satellite name INSAT-3DS")
    assert_test(mock_meta["product_id"] == "3SIMG_L1C_ASIA_MER", "Extracted product ID 3SIMG_L1C_ASIA_MER")
    assert_test(mock_meta["timestamp_utc"] == "2025-05-12T14:30:00Z", "Parsed MOSDAC filename timestamp to 2025-05-12T14:30:00Z")

    val_nonexistent = sat_loader.validate_file("data/raw/satellite/insat3ds/nonexistent.h5")
    assert_test(val_nonexistent["valid"] is False, "Non-existent file flagged as invalid")

    # Group 5: Lightning / WGLC Loader (Phase 3)
    print("\n--- Group 5: WGLC Lightning Climatology Loader ---")
    lgt_loader = WglcLightningLoader("data/raw/lightning/wglc")
    may_climatology = lgt_loader.get_monthly_climatology(5, grid)
    assert_test(may_climatology["status"] == "AVAILABLE_CLIMATOLOGY", "May climatology retrieved")
    assert_test(may_climatology["climatological_month"] == 5, "Month index is 5")
    assert_test(may_climatology["real_time_observation"] is False, "real_time_observation is False")
    assert_test(len(may_climatology["climatology_density_grid"]) == 32, "Climatology grid matches target height 32")

    inspect_info = lgt_loader.inspect_lightning_sources()
    assert_test(inspect_info["event_level_lightning_available"] is False, "Inspection confirms no event-level lightning is fabricated")

    # Group 6: Radar Loader (Phase 4)
    print("\n--- Group 6: Radar Loader & Mode Switching ---")
    radar_loader = RadarDataLoader("data/raw/radar")
    demo_frame = radar_loader.load_radar_frame(target_grid=grid)
    assert_test(demo_frame["is_demo"] is True, "Radar loader transparently reports is_demo = True when no live DWR is on disk")
    assert_test(demo_frame["provenance"]["data_type"] == "DEMO_DATA", "Radar provenance records DEMO_DATA")

    # Group 7: NWP ERA5 & IMERG Precipitation Loaders (Phase 5 & 6)
    print("\n--- Group 7: NWP ERA5 & GPM IMERG Loaders ---")
    nwp_loader = NwpEra5Loader("data/raw/nwp/era5")
    nwp_data = nwp_loader.load_variables_to_grid(None, grid)
    assert_test(nwp_data["status"] == "UNAVAILABLE", "Missing ERA5 file returns status UNAVAILABLE")
    assert_test(nwp_data["availability_masks"]["cape"][0][0] == 0, "Missing ERA5 sets availability mask to 0")

    imerg_loader = ImergPrecipitationLoader("data/raw/imerg")
    imerg_data = imerg_loader.load_precipitation_to_grid(None, grid)
    assert_test(imerg_data["status"] == "UNAVAILABLE", "Missing IMERG file returns status UNAVAILABLE")
    assert_test(imerg_data["availability_mask"][0][0] == 0, "Missing IMERG sets availability mask to 0")

    # Group 8: Multimodal Sample Builder & Manifest (Phase 9, 10, 11)
    print("\n--- Group 8: Multimodal Sample Builder & Manifest Export ---")
    builder = MultimodalSampleBuilder(grid=grid, data_root="data")
    sample = builder.build_sample_at_timestamp(
        event_id="TEST-SAMPLE-01",
        target_timestamp_iso="2025-05-12T14:30:00Z",
        lat=23.34,
        lon=85.31,
        allow_demo_fallback=True
    )
    assert_test(sample["event_id"] == "TEST-SAMPLE-01", "Sample built with correct event ID")
    assert_test(sample["labels"]["label_available"] is False, "Label ground-truth availability is False (no fake labels)")
    assert_test(sample["labels"]["label_source"] == "UNAVAILABLE", "Label source is UNAVAILABLE")
    assert_test("radar_reflectivity_dbz" in sample["tensors"], "Sample contains radar reflectivity tensor")
    assert_test("lightning_climatology_baseline" in sample["tensors"], "Sample contains lightning climatology tensor")

    # Test Manifest CSV Export
    manifest_path = "data/manifests/events_test.csv"
    builder.export_manifest_csv([sample], output_csv_path=manifest_path)
    assert_test(os.path.exists(manifest_path), "Manifest CSV exported to disk")

    with open(manifest_path, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        assert_test(len(reader) == 1, "Manifest CSV has 1 test row")
        assert_test(reader[0]["lightning_data_type"] == "climatology", "Manifest CSV column lightning_data_type is 'climatology'")
        assert_test(reader[0]["wglc_semantics"] == "monthly_climatological_average", "Manifest CSV column wglc_semantics is 'monthly_climatological_average'")
        assert_test(reader[0]["label_available"] == "False", "Manifest CSV column label_available is False")

    if os.path.exists(manifest_path):
        os.remove(manifest_path)

    # Group 9: Grid Domain Configuration (Section 1)
    print("\n--- Group 9: Regional Grid Domain Configuration ---")
    reg_grid = StormTraceGrid.regional_east_india(height=64, width=64)
    assert_test(reg_grid.domain == GridDomain.REGIONAL_EAST_INDIA, "Regional East India grid domain enum set")
    assert_test(reg_grid.min_lon == 83.5 and reg_grid.max_lon == 89.8, "Regional lon bounds [83.5, 89.8]")
    assert_test(reg_grid.min_lat == 20.0 and reg_grid.max_lat == 26.3, "Regional lat bounds [20.0, 26.3]")
    assert_test(abs(reg_grid.resolution_deg - 0.1) < 0.01, f"Regional resolution is ~0.1 deg (actual: {reg_grid.resolution_deg:.4f})")
    assert_test(8.0 < reg_grid.cell_size_km < 14.0, f"Regional cell size in km is ~11km (actual: {reg_grid.cell_size_km:.1f}km)")

    syn_grid = StormTraceGrid.south_asia_synoptic(height=64, width=64)
    assert_test(syn_grid.domain == GridDomain.SOUTH_ASIA_SYNOPTIC, "Synoptic grid domain configured")
    assert_test(syn_grid.min_lon == 68.0 and syn_grid.max_lon == 98.0, "Synoptic lon bounds [68.0, 98.0]")

    # Group 10: Convective Proxy Labeling Strategy (Section 2)
    print("\n--- Group 10: Convective Proxy Labeling Strategy ---")
    dummy_precip = [
        [0.0, 5.0, 12.5, 0.0],
        [2.0, 15.0, 25.0, 1.0],
        [0.0, 0.0, 8.0, 0.0],
        [0.0, 0.0, 0.0, 0.0]
    ]
    binary_label, label_meta = derive_convective_proxy_label(dummy_precip, threshold_mm_hr=10.0)
    assert_test(binary_label[0][2] == 1 and binary_label[1][1] == 1 and binary_label[1][2] == 1, "Pixels >= 10 mm/hr labeled positive")
    assert_test(binary_label[0][1] == 0 and binary_label[2][2] == 0, "Pixels < 10 mm/hr labeled negative")
    assert_test(label_meta["label_source"] == "IMERG_PRECIP_THRESHOLD_PROXY", "Label source explicitly recorded as IMERG_PRECIP_THRESHOLD_PROXY")
    assert_test(label_meta["positive_pixels"] == 3, "Positive pixel count matches")
    assert_test(label_meta["threshold_mm_hr"] == 10.0, "Threshold recorded in metadata")

    # Group 11: Multimodal Model Training & Checkpoints (Section 2)
    print("\n--- Group 11: Multimodal Model Training ---")
    trainer = MultimodalNowcastTrainer(epochs=3, learning_rate=0.01)
    train_set, val_set, test_set = trainer.load_dataset_splits()
    assert_test(len(train_set) > 0, "Training set contains synthetic sequence window samples")
    assert_test(len(val_set) > 0, "Validation set contains synthetic sequence window samples")
    assert_test(len(test_set) > 0, "Test set contains synthetic sequence window samples")

    # Train for 3 quick epochs in test mode
    train_res = trainer.train()
    history = train_res["training_history"]
    assert_test(len(history) == 3, "Training history recorded 3 epochs")
    assert_test("train_bce_loss" in history[0], "Training BCE loss logged per epoch")
    assert_test(os.path.exists("ml/models/stormtrace_multimodal_best.json") or os.path.exists("models/stormtrace_multimodal_best.json"), "Best model checkpoint serialized")

    # Group 12: Contingency Evaluation Metrics (Section 3)
    print("\n--- Group 12: Contingency Metrics Calculation ---")
    test_pred = [[0.8, 0.1], [0.9, 0.2]]
    test_true = [[1, 0], [1, 0]]
    metrics = compute_contingency_metrics(test_pred, test_true, prob_threshold=0.5)
    assert_test(metrics["hits"] == 2, "Hits = 2")
    assert_test(metrics["false_alarms"] == 0, "False alarms = 0")
    assert_test(metrics["misses"] == 0, "Misses = 0")
    assert_test(metrics["pod"] == 1.0, "POD = 1.0")
    assert_test(metrics["far"] == 0.0, "FAR = 0.0")
    assert_test(metrics["csi"] == 1.0, "CSI = 1.0")
    assert_test(metrics["brier_score"] < 0.1, f"Brier score low for accurate predictions ({metrics['brier_score']:.4f})")

    # Group 13: Downstream Forecasting, Tracking & Analogs Integration (Section 4 & 5)
    print("\n--- Group 13: Downstream Extrapolator, Cell Tracker & Analogs ---")
    extrapolator = ForecastExtrapolator()
    multimodal_sample = builder.build_sample_at_timestamp(
        event_id="TEST-INT-01",
        target_timestamp_iso="2025-05-12T14:30:00Z",
        lat=23.34,
        lon=85.31,
        allow_demo_fallback=True
    )
    fcst_result = extrapolator.predict_multimodal_sample(multimodal_sample)
    assert_test(fcst_result["status"] == "success", "Forecast extrapolation status is success")
    assert_test(len(fcst_result["lead_time_forecasts"]) == 6, "Forecast contains all 6 lead times (+15m to +120m)")
    assert_test(fcst_result["lead_time_forecasts"][0]["uncertainty"]["mc_passes"] == 25, "MC-Dropout executed 25 passes")
    assert_test("spread_std" in fcst_result["lead_time_forecasts"][0]["uncertainty"], "Epistemic uncertainty spread computed")

    tracker = StormCellTracker()
    tracked_cells = tracker.track_cells_2d(multimodal_sample["tensors"]["radar_reflectivity_dbz"])
    assert_test(isinstance(tracked_cells, list), "Cell tracker returns segmented cells from 2D grid")

    analog_matcher = HistoricalAnalogMatcher()
    analog_matches = analog_matcher.match_analog(query_max_dbz=54.0, query_region="Ranchi")
    assert_test(len(analog_matches) > 0, "Historical analogs matched")
    assert_test(analog_matches[0]["provenance_status"] == "BENCHMARK_CASE_STUDY", "Analog tagged as BENCHMARK_CASE_STUDY")

    # Summary
    print("\n================================================================================")
    print(f"📊 MULTIMODAL TEST RESULTS: {passed} PASSED | {failed} FAILED")
    print("================================================================================\n")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()
