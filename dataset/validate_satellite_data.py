#!/usr/bin/env python3
"""
STORMTRACE INSAT-3DS Satellite Data Validator
Phase 2 & Phase 12: Performs comprehensive radiometric, spatial, temporal,
and file integrity checks on downloaded INSAT-3DS Level-1C products.
"""

import os
import sys
import argparse
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from dataset.loaders.satellite_loader import Insat3dsSatelliteLoader
except ImportError:
    from stormtrace.data.satellite_loader import Insat3dsSatelliteLoader


def parse_args():
    parser = argparse.ArgumentParser(description="Validate INSAT-3DS satellite data files.")
    parser.add_argument("--data-dir", type=str, default="dataset/raw/satellite/insat3ds", help="Directory containing raw INSAT-3DS files")
    return parser.parse_args()


def main():
    args = parse_args()
    print("========================================================")
    print("🛰️  STORMTRACE INSAT-3DS DATA INTEGRITY VALIDATION")
    print("========================================================")
    print(f"Target Directory: {os.path.abspath(args.data_dir)}\n")

    loader = Insat3dsSatelliteLoader(args.data_dir)
    files = loader.discover_files()

    if not files:
        print(f"ℹ️ No INSAT-3DS files currently found in {args.data_dir}")
        print("  Place your downloaded .h5, .nc, or .json files here and re-run.")
        return

    valid_count = 0
    invalid_count = 0

    for item in files:
        filepath = item["filepath"]
        val = loader.validate_file(filepath)
        filename = item["filename"]
        size_kb = item["size_bytes"] / 1024.0

        if val["valid"]:
            valid_count += 1
            print(f"✓ VALID: {filename} ({size_kb:.1f} KB)")
            print(f"   Acquisition UTC: {item['timestamp_utc']}")
            print(f"   Product: {item['product_id']} | Sensor: {item['sensor']}")
            print(f"   Channels Available: {', '.join(val['channels_found'])}")
        else:
            invalid_count += 1
            print(f"✗ INVALID: {filename} ({size_kb:.1f} KB)")
            for err in val["errors"]:
                print(f"   Error: {err}")
        print("")

    print("--------------------------------------------------------")
    print(f"Validation Summary: {valid_count} VALID | {invalid_count} INVALID | Total: {len(files)}")
    print("========================================================")


if __name__ == "__main__":
    main()
