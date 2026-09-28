#!/usr/bin/env python3
"""
STORMTRACE Synthetic Benchmark Dataset Populator
================================================================================
⚠️ WARNING: This script generates mathematical synthetic fields for pipeline testing.
It does NOT download or retrieve real ERA5, IMERG, radar, satellite, or lightning observations.
All generated files are classified strictly as SYNTHETIC_DATA.
================================================================================
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.populate_real_datasets import populate_synthetic_benchmarks

if __name__ == "__main__":
    populate_synthetic_benchmarks()
