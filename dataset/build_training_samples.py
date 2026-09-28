#!/usr/bin/env python3
"""
STORMTRACE Training & Inference Sample Builder CLI
Phase 11: Constructs aligned multimodal training/evaluation sample tensors and exports
the standardized data manifest (data/manifests/events.csv).
"""

import os
import sys
import argparse
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from dataset.sample_builder import MultimodalSampleBuilder
    from dataset.grid import StormTraceGrid
except ImportError:
    from stormtrace.data.sample_builder import MultimodalSampleBuilder
    from stormtrace.data.grid import StormTraceGrid


def parse_args():
    parser = argparse.ArgumentParser(description="Build multimodal training/evaluation samples.")
    parser.add_argument("--data-root", type=str, default="dataset", help="Root data directory")
    parser.add_argument("--manifest-out", type=str, default="dataset/manifests/events.csv", help="Manifest CSV output path")
    parser.add_argument("--samples-out", type=str, default="dataset/processed/multimodal_samples.json", help="Samples JSON output path")
    parser.add_argument("--grid-size", type=int, default=64, help="Grid size (default 64x64)")
    return parser.parse_args()


def main():
    args = parse_args()
    print("========================================================")
    print("📦 STORMTRACE MULTIMODAL TRAINING SAMPLE BUILDER")
    print("========================================================")
    print(f"Data Root    : {os.path.abspath(args.data_root)}")
    print(f"Manifest CSV : {os.path.abspath(args.manifest_out)}")
    print(f"Grid Size    : {args.grid_size}x{args.grid_size}\n")

    grid = StormTraceGrid(height=args.grid_size, width=args.grid_size)
    builder = MultimodalSampleBuilder(grid=grid, data_root=args.data_root)

    # Benchmark test events across diverse severe convective storm dates & regions
    events_to_build = [
        {"event_id": "EVT-2025-0512-RNC", "timestamp": "2025-05-12T14:30:00Z", "lat": 23.34, "lon": 85.31, "name": "Ranchi Plateau Supercell Outbreak"},
        {"event_id": "EVT-2024-0618-CCU", "timestamp": "2024-06-18T12:45:00Z", "lat": 22.57, "lon": 88.36, "name": "Gangetic Bengal Nor'wester Squall Line"},
        {"event_id": "EVT-2024-0922-MAA", "timestamp": "2024-09-22T10:15:00Z", "lat": 13.08, "lon": 80.27, "name": "Tamil Nadu Coastal Convective Core"},
        {"event_id": "EVT-2023-1104-CCJ", "timestamp": "2023-11-04T08:50:00Z", "lat": 11.25, "lon": 75.78, "name": "Arabian Sea Orographic Updraft Band"},
        {"event_id": "EVT-2026-0919-NOW", "timestamp": "2026-09-19T14:30:00Z", "lat": 22.57, "lon": 88.36, "name": "Current Operational Verification Sample"}
    ]

    samples = []
    for evt in events_to_build:
        s = builder.build_sample_at_timestamp(
            event_id=evt["event_id"],
            target_timestamp_iso=evt["timestamp"],
            lat=evt["lat"],
            lon=evt["lon"],
            allow_demo_fallback=True
        )
        samples.append(s)
        print(f"✓ Built sample {evt['event_id']}: {evt['name']}")
        print(f"   Timestamp: {s['target_initialization_time_utc']} | System Mode: {s['system_mode']}")

    # Export Manifest CSV
    manifest_path = builder.export_manifest_csv(samples, output_csv_path=args.manifest_out)
    print(f"\n📄 Exported Manifest CSV to: {manifest_path}")

    # Export Samples JSON
    os.makedirs(os.path.dirname(args.samples_out), exist_ok=True)
    with open(args.samples_out, "w", encoding="utf-8") as f:
        json.dump({"total_samples": len(samples), "samples": samples}, f, indent=2)
    print(f"💾 Exported Processed Samples to: {args.samples_out}")
    print("========================================================")
    print("✅ Training Sample Builder Execution Completed.")


if __name__ == "__main__":
    main()
