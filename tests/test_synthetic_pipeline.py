#!/usr/bin/env python3
"""
STORMTRACE Synthetic Pipeline Unit Tests (Python)
Validates Part 1 (Synthetic Storm Generator), Part 2 (Forecast Extrapolator & Cell Tracker),
and Part 3 (Historical Analog Matcher).
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, 'backend')

try:
    from ml.synthetic.storm_generator import SyntheticStormGenerator
    from ml.extrapolator import ForecastExtrapolator
    from ml.tracking.cell_tracker import StormCellTracker
    from ml.analogs.analog_matcher import HistoricalAnalogMatcher
except ImportError:
    from stormtrace.synthetic.storm_generator import SyntheticStormGenerator
    from stormtrace.forecast.extrapolator import ForecastExtrapolator
    from stormtrace.tracking.cell_tracker import StormCellTracker
    from stormtrace.analogs.analog_matcher import HistoricalAnalogMatcher

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

def run_tests():
    print("\n========================================")
    print("🧪 RUNNING PYTHON SYNTHETIC PIPELINE TESTS")
    print("========================================\n")

    # Part 1: Synthetic Generator
    print("--- Part 1: Synthetic Storm Generator ---")
    gen = SyntheticStormGenerator(grid_width=32, grid_height=32, time_step_min=5)
    scenarios = gen.list_scenarios()
    assert_test(len(scenarios) >= 5, "At least 5 distinct synthetic scenarios available")
    
    seq = gen.generate_sequence("single_developing_storm", seed=101)
    assert_test(len(seq["frames"]) >= 18, "Single developing storm generates at least 18 frames (90 min)")
    assert_test("reflectivity_dbz" in seq["frames"][0]["grids"], "Frame contains Radar Reflectivity grid")
    assert_test("satellite_ir_temp_c" in seq["frames"][0]["grids"], "Frame contains Satellite IR Cloud-Top grid")
    assert_test("lightning_flash_density" in seq["frames"][0]["grids"], "Frame contains Lightning Flash Density grid")
    assert_test("cape_j_kg" in seq["frames"][0]["grids"], "Frame contains Atmospheric CAPE grid")

    # Split Scenario
    seq_split = gen.generate_sequence("storm_splitting_near_airport", seed=42)
    assert_test(len(seq_split["frames"]) >= 10, "Split storm scenario produces multi-frame sequence")

    # Part 2: Forecast Extrapolator
    print("\n--- Part 2: Forecast Extrapolator & Uncertainty ---")
    extrap = ForecastExtrapolator(mc_dropout_passes=25, dropout_rate=0.2)
    pred = extrap.predict(seq["frames"][:6])
    assert_test(len(pred["lead_time_forecasts"]) == 6, "Forecast produces all 6 lead-time horizons (+15m to +120m)")
    h120 = pred["lead_time_forecasts"][-1]
    assert_test(h120["uncertainty"]["mc_passes"] == 25, "Epistemic uncertainty calculates 25 MC-Dropout passes")
    assert_test(h120["decay_factor"] < 1.0, "Convective decay applied across lead time horizons")

    # Part 2: Cell Tracker
    print("\n--- Part 2: Storm Cell Tracker ---")
    tracker = StormCellTracker(dbz_threshold=40.0)
    tracked = tracker.track_cells(seq["frames"])
    assert_test(len(tracked) > 0, "TITAN tracking extracts active cells from synthetic sequence")

    # Part 3: Historical Analog Matcher
    print("\n--- Part 3: Historical Analog Matcher ---")
    matcher = HistoricalAnalogMatcher()
    analogs = matcher.match_analog(62.0)
    assert_test(len(analogs) >= 4, "Catalog contains at least 4 benchmark analogs")
    assert_test(analogs[0]["computed_similarity"] > 0.85, "Top analog match has high similarity score (>0.85)")

    print("\n========================================")
    print(f"📊 PYTHON TEST RESULTS: {passed} PASSED | {failed} FAILED")
    print("========================================\n")

    if failed > 0:
        sys.exit(1)

if __name__ == '__main__':
    run_tests()
