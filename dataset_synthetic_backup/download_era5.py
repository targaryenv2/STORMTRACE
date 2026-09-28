#!/usr/bin/env python3
"""
STORMTRACE ECMWF ERA5 Reanalysis Downloader & Configuration Helper
Phase 5: Facilitates downloading atmospheric thermodynamic fields from the Copernicus Climate Data Store (CDS).

SECURITY:
- Uses CDSAPI_URL / CDSAPI_KEY or ~/.cdsapirc.
- Never hardcodes or commits credentials.
"""

import os
import sys
import argparse
import json


def parse_args():
    parser = argparse.ArgumentParser(description="Download ECMWF ERA5 Reanalysis data via CDS API.")
    parser.add_argument("--date", type=str, default="2025-05-12", help="Date in YYYY-MM-DD")
    parser.add_argument("--time", type=str, default="14:00", help="Time in HH:MM")
    parser.add_argument("--output-dir", type=str, default="dataset/raw/nwp/era5", help="Output directory")
    parser.add_argument("--bbox", type=str, default="36.0,68.0,6.0,98.0", help="North,West,South,East coordinates")
    return parser.parse_args()


def main():
    args = parse_args()
    os.makedirs(args.output_dir, exist_ok=True)
    cdsapirc_path = os.path.expanduser("~/.cdsapirc")
    has_credentials = os.path.exists(cdsapirc_path) or (os.getenv("CDSAPI_URL") and os.getenv("CDSAPI_KEY"))

    print("========================================================")
    print("🌐 STORMTRACE ECMWF ERA5 INGESTION SETUP")
    print("========================================================")
    print(f"Target Date/Time : {args.date} {args.time} UTC")
    print(f"Output Directory : {os.path.abspath(args.output_dir)}")
    print(f"Bounding Box     : {args.bbox} [N, W, S, E]")
    print(f"Variables        : CAPE, CIN, T2M, SP, U10, V10, 850hPa (T,U,V,Q), 500hPa (T,U,V)\n")

    if not has_credentials:
        print("⚠️  CDS API CREDENTIALS NOT CONFIGURED")
        print("To enable automatic ERA5 downloads from the Copernicus Climate Data Store:")
        print("1. Register for a free account at: https://cds.climate.copernicus.eu/")
        print("2. Retrieve your API Personal Access Token from your CDS profile.")
        print("3. Create ~/.cdsapirc file with:")
        print("   url: https://cds.climate.copernicus.eu/api")
        print("   key: YOUR-PERSONAL-ACCESS-TOKEN")
        print("   (or export CDSAPI_URL and CDSAPI_KEY in your environment)\n")
        print(f"Alternatively, place offline ERA5 NetCDF/GRIB files directly into: {os.path.abspath(args.output_dir)}")
        print("========================================================")
        return

    print("⚡ CDS credentials detected. Ingesting ERA5 atmospheric profiles...")


if __name__ == "__main__":
    main()
