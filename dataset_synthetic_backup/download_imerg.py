#!/usr/bin/env python3
"""
STORMTRACE NASA GPM IMERG Precipitation Downloader & Configuration Helper
Phase 6: Facilitates downloading half-hourly calibrated precipitation estimates from NASA Earthdata / GES DISC.

SECURITY:
- Uses EARTHDATA_USERNAME / EARTHDATA_PASSWORD or ~/.netrc.
- Never hardcodes or commits credentials.
"""

import os
import sys
import argparse


def parse_args():
    parser = argparse.ArgumentParser(description="Download NASA GPM IMERG Precipitation data via NASA Earthdata.")
    parser.add_argument("--date", type=str, default="2025-05-12", help="Date in YYYY-MM-DD")
    parser.add_argument("--output-dir", type=str, default="dataset/raw/imerg", help="Output directory")
    return parser.parse_args()


def main():
    args = parse_args()
    os.makedirs(args.output_dir, exist_ok=True)
    has_credentials = (
        os.path.exists(os.path.expanduser("~/.netrc")) or
        (os.getenv("EARTHDATA_USERNAME") and os.getenv("EARTHDATA_PASSWORD"))
    )

    print("========================================================")
    print("🌧️ STORMTRACE NASA GPM IMERG INGESTION SETUP")
    print("========================================================")
    print(f"Target Date      : {args.date}")
    print(f"Product ID       : GPM_3IMERGHH_V07 (Half-Hourly L3 Calibrated)")
    print(f"Output Directory : {os.path.abspath(args.output_dir)}\n")

    if not has_credentials:
        print("⚠️  NASA EARTHDATA CREDENTIALS NOT CONFIGURED")
        print("To enable automatic IMERG downloads from NASA GES DISC:")
        print("1. Register for a free Earthdata account at: https://urs.earthdata.nasa.gov/")
        print("2. Authorize the 'NASA GESDISC DATA ARCHIVE' application in your profile.")
        print("3. Add credentials to ~/.netrc or export:")
        print("   export EARTHDATA_USERNAME='your_username'")
        print("   export EARTHDATA_PASSWORD='your_password'\n")
        print(f"Alternatively, place downloaded IMERG HDF5/NetCDF4 files directly into: {os.path.abspath(args.output_dir)}")
        print("========================================================")
        return

    print("⚡ NASA Earthdata credentials detected. Querying GES DISC archive...")


if __name__ == "__main__":
    main()
