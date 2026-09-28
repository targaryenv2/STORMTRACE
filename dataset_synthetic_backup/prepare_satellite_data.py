#!/usr/bin/env python3
"""
STORMTRACE INSAT-3DS Satellite Data Preprocessor
Phase 2: Reads raw INSAT-3DS L1C files, resamples all 6 channels onto the common
STORMTRACE grid, generates availability masks, and saves model-ready tensors to data/processed/satellite/.
"""

import os
import sys
import argparse
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from dataset.loaders.satellite_loader import Insat3dsSatelliteLoader
    from dataset.grid import StormTraceGrid
except ImportError:
    from stormtrace.data.satellite_loader import Insat3dsSatelliteLoader
    from stormtrace.data.grid import StormTraceGrid


def parse_args():
    parser = argparse.ArgumentParser(description="Prepare and resample INSAT-3DS data onto STORMTRACE model grid.")
    parser.add_argument("--raw-dir", type=str, default="dataset/raw/satellite/insat3ds", help="Raw files directory")
    parser.add_argument("--out-dir", type=str, default="dataset/processed/satellite", help="Processed output directory")
    parser.add_argument("--grid-size", type=int, default=64, help="Target grid width/height")
    return parser.parse_args()


def main():
    args = parse_args()
    os.makedirs(args.out_dir, exist_ok=True)
    grid = StormTraceGrid(height=args.grid_size, width=args.grid_size)
    loader = Insat3dsSatelliteLoader(args.raw_dir)

    files = loader.discover_files()
    print(f"🛰️ Processing INSAT-3DS Satellite Data into Model Tensors...")
    print(f"   Source Directory : {args.raw_dir}")
    print(f"   Output Directory : {args.out_dir}")
    print(f"   Target Grid Size : {args.grid_size}x{args.grid_size} (Spatial res: ~{grid.to_dict()['approx_spatial_res_km']} km)")
    print(f"   Discovered Files : {len(files)}\n")

    if not files:
        print("ℹ️ No raw INSAT-3DS files found to process. Awaiting user downloads in data/raw/satellite/insat3ds/.")
        return

    processed_count = 0
    for f in files:
        filepath = f["filepath"]
        res = loader.load_channels_to_grid(filepath, grid)
        timestamp_clean = f["timestamp_utc"].replace(":", "-")
        out_filename = f"insat3ds_processed_{timestamp_clean}.json"
        out_path = os.path.join(args.out_dir, out_filename)

        with open(out_path, "w", encoding="utf-8") as out_fp:
            json.dump(res, out_fp, indent=2)

        print(f"✓ Saved processed tensor: {out_filename} (Status: {res['status']})")
        processed_count += 1

    print(f"\n========================================================")
    print(f"✅ Completed preprocessing: {processed_count} files processed to {args.out_dir}")
    print("========================================================")


if __name__ == "__main__":
    main()
