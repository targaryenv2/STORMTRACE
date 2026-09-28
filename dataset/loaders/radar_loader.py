#!/usr/bin/env python3
"""
STORMTRACE Radar Data Loader & Preprocessing Adapter
Ingests real Doppler Weather Radar (DWR) NetCDF volume scans (e.g. ISRO TERLS DWR),
extracts volumetric/composite DBZ and radial velocity (VEL), performs temporal validation,
and verifies domain compatibility while maintaining rigorous data provenance.
"""

import os
import glob
import json
import re
import struct
import math
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

try:
    from dataset.provenance import (
        get_radar_demo_metadata,
        get_terls_dwr_metadata,
        create_dataset_metadata,
        DataType,
        TemporalSemantics
    )
    from dataset.grid import StormTraceGrid, MODALITY_SPECS
    from ml.synthetic.storm_generator import SyntheticStormGenerator
except ImportError:
    from stormtrace.data.provenance import (
        get_radar_demo_metadata,
        get_terls_dwr_metadata,
        create_dataset_metadata,
        DataType,
        TemporalSemantics
    )
    from stormtrace.data.grid import StormTraceGrid, MODALITY_SPECS
    from stormtrace.synthetic.storm_generator import SyntheticStormGenerator


class RadarDataLoader:
    """
    Adapter for Doppler Weather Radar (DWR) data streams.
    Handles ingestion of real DWR NetCDF volume scans from ISRO TERLS DWR and other stations,
    handles missing-value masking, extracts composite reflectivity and velocity,
    validates physical ranges, and bridges to demo feeds when real data is unavailable.
    """

    CHANNELS = ["DBZ", "VEL", "reflectivity_dbz", "velocity_radial_mps"]

    def __init__(self, raw_data_dir: str = "data/raw/radar"):
        # Search candidate directories: data/raw/radar/terls, data/raw/radar, dataset/raw/radar
        candidate_dirs = [
            os.path.join(raw_data_dir, "terls"),
            raw_data_dir,
            raw_data_dir.replace("data/", "dataset/"),
            "data/raw/radar/terls",
            "data/raw/radar",
            "dataset/raw/radar"
        ]
        resolved = None
        for cd in candidate_dirs:
            if os.path.exists(cd):
                resolved = cd
                break
        self.raw_data_dir = resolved or raw_data_dir
        self.generator = SyntheticStormGenerator(grid_width=64, grid_height=64, time_step_min=5)

    def discover_real_files(self, search_dir: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Scans raw radar directory and subdirectories for real DWR NetCDF (.nc),
        HDF5 (.h5), GeoTIFF (.tif), or JSON files, extracting timestamps and metadata.
        Returns a chronologically sorted list of discovered files.
        """
        base_dir = search_dir or self.raw_data_dir
        if not os.path.exists(base_dir):
            return []

        discovered = []
        patterns = ["*.nc", "*.h5", "*.hdf5", "*.tif", "*.tiff", "*.json", "**/*.nc"]
        seen_paths = set()

        for pat in patterns:
            for path in glob.glob(os.path.join(base_dir, pat), recursive=True):
                if path in seen_paths or path.endswith(".gitkeep"):
                    continue
                seen_paths.add(path)
                meta = self._extract_file_meta(path)
                if meta is not None:
                    discovered.append(meta)

        # Sort chronologically by acquisition datetime
        discovered.sort(key=lambda x: x["acquisition_dt"] or datetime.min.replace(tzinfo=timezone.utc))
        return discovered

    def _extract_file_meta(self, filepath: str) -> Optional[Dict[str, Any]]:
        """Extracts file size, timestamp, instrument, and format from file and path."""
        if not os.path.exists(filepath):
            return None

        filename = os.path.basename(filepath)
        size = os.path.getsize(filepath)

        # 1. Match TERLS NetCDF format: v2_YYYY_MM_DD_HH_MM_SS_dprf_corrected.nc
        match_terls = re.match(r"v2_(\d{4})_(\d{2})_(\d{2})_(\d{2})_(\d{2})_(\d{2})", filename)
        dt_utc = None
        source_inst = "DWR_RADAR"

        if match_terls:
            y, m, d, hh, mm, ss = match_terls.groups()
            try:
                dt_utc = datetime(int(y), int(m), int(d), int(hh), int(mm), int(ss), tzinfo=timezone.utc)
                source_inst = "ISRO TERLS DWR"
            except Exception:
                pass
        else:
            # 2. Match standard DWR naming: DWR_LOCATION_YYYYMMDD_HHMMSS.nc
            match_std = re.search(r"(\d{4})(\d{2})(\d{2})_?(\d{2})(\d{2})", filename)
            if match_std:
                y, m, d, hh, mm = match_std.groups()
                try:
                    dt_utc = datetime(int(y), int(m), int(d), int(hh), int(mm), tzinfo=timezone.utc)
                    source_inst = "IMD DWR"
                except Exception:
                    pass

        if not dt_utc:
            dt_utc = datetime.fromtimestamp(os.path.getmtime(filepath), tz=timezone.utc)

        fmt = "NetCDF" if filepath.endswith(".nc") else "JSON" if filepath.endswith(".json") else "HDF5" if filepath.endswith((".h5", ".hdf5")) else "GeoTIFF"

        return {
            "filepath": filepath,
            "filename": filename,
            "size_bytes": size,
            "timestamp_utc": dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "acquisition_dt": dt_utc,
            "format": fmt,
            "source_instrument": source_inst,
            "is_real_observation": True
        }

    def read_netcdf_header(self, filepath: str) -> Dict[str, Any]:
        """
        Reads NetCDF-3 (CDF-1/CDF-2) header, dimensions, global attributes, and variables.
        Implemented in pure Python without third-party C-library dependencies.
        """
        with open(filepath, "rb") as f:
            magic = f.read(4)
            if magic not in (b"CDF\x01", b"CDF\x02"):
                raise ValueError(f"Invalid NetCDF-3 magic signature: {magic}")

            numrecs = struct.unpack(">I", f.read(4))[0]

            # 1. Dimensions
            dim_tag = struct.unpack(">I", f.read(4))[0]
            dims = []
            if dim_tag == 0x0000000A:
                dim_count = struct.unpack(">I", f.read(4))[0]
                for _ in range(dim_count):
                    nlen = struct.unpack(">I", f.read(4))[0]
                    padded = (nlen + 3) & ~3
                    name = f.read(padded)[:nlen].decode("utf-8", errors="ignore")
                    size = struct.unpack(">I", f.read(4))[0]
                    dims.append((name, size))
            elif dim_tag == 0:
                f.read(4)

            # 2. Global attributes
            gatt_tag = struct.unpack(">I", f.read(4))[0]
            gatts = {}
            if gatt_tag == 0x0000000C:
                gatt_count = struct.unpack(">I", f.read(4))[0]
                for _ in range(gatt_count):
                    nlen = struct.unpack(">I", f.read(4))[0]
                    padded = (nlen + 3) & ~3
                    aname = f.read(padded)[:nlen].decode("utf-8", errors="ignore")
                    type_code = struct.unpack(">I", f.read(4))[0]
                    vcount = struct.unpack(">I", f.read(4))[0]
                    gatts[aname] = self._read_netcdf_attr_val(f, type_code, vcount)
            elif gatt_tag == 0:
                f.read(4)

            # 3. Variables
            var_tag = struct.unpack(">I", f.read(4))[0]
            vars_dict = {}
            if var_tag == 0x0000000B:
                var_count = struct.unpack(">I", f.read(4))[0]
                for _ in range(var_count):
                    nlen = struct.unpack(">I", f.read(4))[0]
                    padded = (nlen + 3) & ~3
                    vname = f.read(padded)[:nlen].decode("utf-8", errors="ignore")
                    dim_indices_count = struct.unpack(">I", f.read(4))[0]
                    dim_indices = [struct.unpack(">I", f.read(4))[0] for _ in range(dim_indices_count)]

                    # Variable attributes
                    vatt_tag = struct.unpack(">I", f.read(4))[0]
                    vatts = {}
                    if vatt_tag == 0x0000000C:
                        vatt_count = struct.unpack(">I", f.read(4))[0]
                        for _ in range(vatt_count):
                            anlen = struct.unpack(">I", f.read(4))[0]
                            apadded = (anlen + 3) & ~3
                            vaname = f.read(apadded)[:anlen].decode("utf-8", errors="ignore")
                            type_code = struct.unpack(">I", f.read(4))[0]
                            vcount = struct.unpack(">I", f.read(4))[0]
                            vatts[vaname] = self._read_netcdf_attr_val(f, type_code, vcount)
                    elif vatt_tag == 0:
                        f.read(4)

                    type_code = struct.unpack(">I", f.read(4))[0]
                    vsize = struct.unpack(">I", f.read(4))[0]
                    begin = struct.unpack(">I", f.read(4))[0] if magic == b"CDF\x01" else struct.unpack(">Q", f.read(8))[0]

                    vars_dict[vname] = {
                        "name": vname,
                        "dims": [dims[i][0] for i in dim_indices if i < len(dims)],
                        "dim_sizes": [dims[i][1] for i in dim_indices if i < len(dims)],
                        "type_code": type_code,
                        "vsize": vsize,
                        "begin": begin,
                        "attrs": vatts
                    }

        return {
            "format": "NetCDF-3 Classic" if magic == b"CDF\x01" else "NetCDF-3 64-bit Offset",
            "numrecs": numrecs,
            "dims": dict(dims),
            "global_attrs": gatts,
            "variables": vars_dict
        }

    def _read_netcdf_attr_val(self, f, type_code: int, count: int) -> Any:
        """Helper to read variable or global attribute value bytes."""
        if type_code == 2:  # char / string
            padded = (count + 3) & ~3
            return f.read(padded)[:count].decode("utf-8", errors="ignore")
        elif type_code == 5:  # float
            return struct.unpack(f">{count}f", f.read(count * 4))
        elif type_code == 6:  # double
            return struct.unpack(f">{count}d", f.read(count * 8))
        elif type_code == 4:  # int
            return struct.unpack(f">{count}i", f.read(count * 4))
        elif type_code == 3:  # short
            padded = (count * 2 + 3) & ~3
            return struct.unpack(f">{count}h", f.read(padded)[:count * 2])
        elif type_code == 1:  # byte
            padded = (count + 3) & ~3
            return f.read(padded)[:count]
        return None

    def read_terls_netcdf_frame(
        self,
        filepath: str,
        extract_vel: bool = True,
        max_composite: bool = True
    ) -> Dict[str, Any]:
        """
        Reads a full volumetric TERLS NetCDF radar file:
        - Extracts 1D latitude and longitude coordinate vectors (481 points)
        - Extracts 81 vertical height levels (0 to 20 km)
        - Computes 2D column-maximum composite reflectivity (DBZ) [481 x 481]
        - Handles NaNs (fills with 0.0) and filters physical range [0.0, 75.0 dBZ]
        - Extracts radial velocity (VEL) [481 x 481]
        - Attaches explicit REAL_OBSERVATION provenance metadata.
        """
        header = self.read_netcdf_header(filepath)
        vars_info = header["variables"]

        lat_info = vars_info.get("latitude")
        lon_info = vars_info.get("longitude")
        height_info = vars_info.get("height")
        dbz_info = vars_info.get("DBZ")
        vel_info = vars_info.get("VEL")

        if not lat_info or not lon_info or not dbz_info:
            raise ValueError(f"NetCDF file missing essential radar variables (lat/lon/DBZ): {filepath}")

        lat_count = lat_info["dim_sizes"][0] if lat_info["dim_sizes"] else 481
        lon_count = lon_info["dim_sizes"][0] if lon_info["dim_sizes"] else 481
        h_count = height_info["dim_sizes"][0] if height_info and height_info["dim_sizes"] else 81

        with open(filepath, "rb") as f:
            # 1. Read Latitudes (lat_count floats)
            f.seek(lat_info["begin"])
            lats = list(struct.unpack(f">{lat_count}f", f.read(lat_count * 4)))

            # 2. Read Longitudes (lon_count floats)
            f.seek(lon_info["begin"])
            lons = list(struct.unpack(f">{lon_count}f", f.read(lon_count * 4)))

            # 3. Read Heights
            heights = []
            if height_info:
                f.seek(height_info["begin"])
                heights = list(struct.unpack(f">{h_count}i", f.read(h_count * 4)))

            # 4. Read DBZ and compute 2D composite reflectivity grid [lat_idx][lon_idx]
            # DBZ storage layout: dims = [time, height, lon, lat]
            # Shape: 1 x h_count x lon_count x lat_count
            f.seek(dbz_info["begin"])
            grid_dbz = [[0.0 for _ in range(lon_count)] for _ in range(lat_count)]
            valid_pixels_count = 0
            convective_core_count = 0
            max_dbz_seen = 0.0

            # Compute column-max composite across height levels
            slice_floats = lon_count * lat_count
            for h_idx in range(h_count):
                level_data = struct.unpack(f">{slice_floats}f", f.read(slice_floats * 4))
                for lon_idx in range(lon_count):
                    offset = lon_idx * lat_count
                    for lat_idx in range(lat_count):
                        val = level_data[offset + lat_idx]
                        if not math.isnan(val) and val > -30.0:
                            # Clamp physical bounds
                            val_clamped = min(75.0, max(0.0, val))
                            if val_clamped > grid_dbz[lat_idx][lon_idx]:
                                grid_dbz[lat_idx][lon_idx] = round(val_clamped, 2)

            for r in grid_dbz:
                for v in r:
                    if v > 0.0:
                        valid_pixels_count += 1
                        if v > max_dbz_seen:
                            max_dbz_seen = v
                        if v >= 35.0:
                            convective_core_count += 1

            # 5. Read VEL (Radial Velocity) if requested
            grid_vel = None
            if extract_vel and vel_info:
                f.seek(vel_info["begin"])
                grid_vel = [[0.0 for _ in range(lon_count)] for _ in range(lat_count)]
                # Extract mid-level velocity (e.g. level 10 ~ 2.5km)
                f.seek(vel_info["begin"] + 10 * slice_floats * 4)
                vel_data = struct.unpack(f">{slice_floats}f", f.read(slice_floats * 4))
                for lon_idx in range(lon_count):
                    offset = lon_idx * lat_count
                    for lat_idx in range(lat_count):
                        v_val = vel_data[offset + lat_idx]
                        if not math.isnan(v_val):
                            grid_vel[lat_idx][lon_idx] = round(min(60.0, max(-60.0, v_val)), 2)

        spatial_extent = {
            "lat_min": round(min(lats), 4),
            "lat_max": round(max(lats), 4),
            "lon_min": round(min(lons), 4),
            "lon_max": round(max(lons), 4),
            "n_lat": lat_count,
            "n_lon": lon_count
        }

        meta = self._extract_file_meta(filepath)
        ts_utc = meta["timestamp_utc"] if meta else datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        provenance = get_terls_dwr_metadata(spatial_extent=spatial_extent, observation_date=ts_utc[:10])

        return {
            "status": "AVAILABLE_REAL_RADAR",
            "is_demo": False,
            "is_real_observation": True,
            "filepath": filepath,
            "filename": os.path.basename(filepath),
            "timestamp_utc": ts_utc,
            "acquisition_dt": meta["acquisition_dt"] if meta else None,
            "spatial_extent": spatial_extent,
            "lats": lats,
            "lons": lons,
            "heights": heights,
            "reflectivity_dbz": grid_dbz,
            "velocity_radial_mps": grid_vel,
            "max_dbz": round(max_dbz_seen, 2),
            "valid_pixel_count": valid_pixels_count,
            "convective_core_count": convective_core_count,
            "missing_value_pct": round((1.0 - (valid_pixels_count / (lat_count * lon_count))) * 100.0, 2),
            "provenance": provenance
        }

    def evaluate_grid_compatibility(
        self,
        spatial_extent: Dict[str, float],
        target_grid: Optional[StormTraceGrid] = None
    ) -> Dict[str, Any]:
        """
        Evaluates spatial compatibility between the radar's bounding box and the target grid domain.
        Strictly reports if the radar is outside the active STORMTRACE training domain.
        """
        grid = target_grid or StormTraceGrid()

        r_lat_min = spatial_extent.get("lat_min", 0.0)
        r_lat_max = spatial_extent.get("lat_max", 0.0)
        r_lon_min = spatial_extent.get("lon_min", 0.0)
        r_lon_max = spatial_extent.get("lon_max", 0.0)

        t_lat_min = grid.min_lat
        t_lat_max = grid.max_lat
        t_lon_min = grid.min_lon
        t_lon_max = grid.max_lon

        # Check for intersection
        lat_overlap = (r_lat_min <= t_lat_max) and (r_lat_max >= t_lat_min)
        lon_overlap = (r_lon_min <= t_lon_max) and (r_lon_max >= t_lon_min)
        is_compatible = lat_overlap and lon_overlap

        if is_compatible:
            return {
                "compatible": True,
                "status": "COMPATIBLE_DOMAIN",
                "message": f"Radar spatial extent [{r_lon_min:.2f}E–{r_lon_max:.2f}E, {r_lat_min:.2f}N–{r_lat_max:.2f}N] overlaps with target grid domain {grid.domain_name}."
            }

        return {
            "compatible": False,
            "status": "REAL RADAR DATA — OUTSIDE CURRENT STORMTRACE TRAINING DOMAIN",
            "message": (
                f"REAL RADAR DATA — OUTSIDE CURRENT STORMTRACE TRAINING DOMAIN: "
                f"TERLS DWR coverage [{r_lon_min:.2f}°E–{r_lon_max:.2f}°E, {r_lat_min:.2f}°N–{r_lat_max:.2f}°N] in South India "
                f"is completely disjoint from the active STORMTRACE Regional East India domain "
                f"[{t_lon_min:.2f}°E–{t_lon_max:.2f}°E, {t_lat_min:.2f}°N–{t_lat_max:.2f}°N]. "
                f"This dataset validates the real radar loader and preprocessing pipeline, but cannot be used for East India model evaluation."
            ),
            "radar_extent": [r_lon_min, r_lat_min, r_lon_max, r_lat_max],
            "target_grid_domain": grid.domain_name,
            "target_extent": [t_lon_min, t_lat_min, t_lon_max, t_lat_max]
        }

    def create_temporal_inventory(self, files: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Reads all real radar files and constructs a comprehensive temporal inventory,
        checking for duplicates, missing timestamps, irregular intervals, and corruption.
        """
        file_list = files or self.discover_real_files()
        if not file_list:
            return {
                "total_files": 0,
                "successfully_opened": 0,
                "corrupted_files": 0,
                "inventory": [],
                "intervals_minutes": {}
            }

        inventory = []
        corrupted = []

        for f_meta in file_list:
            fpath = f_meta["filepath"]
            try:
                # Fast check header and spatial bounds
                header = self.read_netcdf_header(fpath) if fpath.endswith(".nc") else None
                vars_dict = header["variables"] if header else {}

                inventory.append({
                    "filename": f_meta["filename"],
                    "filepath": fpath,
                    "timestamp_utc": f_meta["timestamp_utc"],
                    "acquisition_dt": f_meta["acquisition_dt"],
                    "size_bytes": f_meta["size_bytes"],
                    "format": f_meta["format"],
                    "dbz_available": "DBZ" in vars_dict or fpath.endswith(".json"),
                    "vel_available": "VEL" in vars_dict,
                    "height_levels": header["dims"].get("height", 81) if header else 0,
                    "lat_points": header["dims"].get("lat", 481) if header else 0,
                    "lon_points": header["dims"].get("lon", 481) if header else 0
                })
            except Exception as e:
                corrupted.append({
                    "filename": f_meta["filename"],
                    "filepath": fpath,
                    "error": str(e)
                })

        # Sort chronologically
        inventory.sort(key=lambda x: x["acquisition_dt"] or datetime.min.replace(tzinfo=timezone.utc))

        # Calculate time interval deltas
        deltas_sec = []
        interval_counts = {}
        duplicate_timestamps = []
        seen_timestamps = set()

        for i, item in enumerate(inventory):
            ts = item["timestamp_utc"]
            if ts in seen_timestamps:
                duplicate_timestamps.append(ts)
            seen_timestamps.add(ts)

            if i > 0 and inventory[i]["acquisition_dt"] and inventory[i - 1]["acquisition_dt"]:
                dt_diff = (inventory[i]["acquisition_dt"] - inventory[i - 1]["acquisition_dt"]).total_seconds()
                deltas_sec.append(dt_diff)
                diff_min = round(dt_diff / 60.0, 1)
                interval_counts[diff_min] = interval_counts.get(diff_min, 0) + 1

        mean_interval_min = round(sum(deltas_sec) / len(deltas_sec) / 60.0, 2) if deltas_sec else 0.0
        min_interval_min = round(min(deltas_sec) / 60.0, 2) if deltas_sec else 0.0
        max_interval_min = round(max(deltas_sec) / 60.0, 2) if deltas_sec else 0.0

        return {
            "total_files_discovered": len(file_list),
            "successfully_opened": len(inventory),
            "corrupted_files_count": len(corrupted),
            "corrupted_files": corrupted,
            "duplicate_timestamps": duplicate_timestamps,
            "start_timestamp_utc": inventory[0]["timestamp_utc"] if inventory else None,
            "end_timestamp_utc": inventory[-1]["timestamp_utc"] if inventory else None,
            "total_observation_span_hours": round((inventory[-1]["acquisition_dt"] - inventory[0]["acquisition_dt"]).total_seconds() / 3600.0, 2) if len(inventory) >= 2 else 0.0,
            "mean_interval_minutes": mean_interval_min,
            "min_interval_minutes": min_interval_min,
            "max_interval_minutes": max_interval_min,
            "interval_distribution_minutes": dict(sorted(interval_counts.items())),
            "all_files_have_dbz": all(x["dbz_available"] for x in inventory),
            "all_files_have_vel": all(x["vel_available"] for x in inventory),
            "inventory_records": inventory
        }

    def preprocess_sequence(
        self,
        file_paths: List[str],
        target_grid: Optional[StormTraceGrid] = None,
        normalize: bool = True
    ) -> Dict[str, Any]:
        """
        Loads, temporally orders, normalizes, and resamples a sequence of consecutive radar frames
        (e.g., T0-60, T0-45, T0-30, T0-15, T0) into a standard STORMTRACE input tensor representation.
        """
        if not file_paths:
            raise ValueError("No radar file paths provided for sequence preprocessing.")

        grid = target_grid or StormTraceGrid()
        frames_data = []

        for fp in file_paths:
            frame_res = self.read_terls_netcdf_frame(fp, extract_vel=False)
            frames_data.append(frame_res)

        # Sort chronologically
        frames_data.sort(key=lambda x: x["acquisition_dt"] or datetime.min.replace(tzinfo=timezone.utc))

        # Check compatibility with target domain
        compat = self.evaluate_grid_compatibility(frames_data[0]["spatial_extent"], grid)

        # Build tensor representation: [T, H, W, C]
        sequence_tensors = []
        normalized_max_dbz = []

        for frame in frames_data:
            # Resample native 481x481 onto target grid (or local 64x64 grid)
            native_grid = frame["reflectivity_dbz"]
            native_lons = frame["lons"]
            native_lats = frame["lats"]

            # If grid is custom or regional East India, perform bilinear resampling
            # If target grid is disjoint, bilinear resample produces 0.0 on target grid as expected
            resampled = grid.resample_2d_bilinear(native_grid, native_lons, native_lats, fill_missing=0.0)

            # Normalize to [0.0, 1.0] using standard radar max 70 dBZ
            if normalize:
                tensor_2d = [[min(1.0, max(0.0, round(val / 70.0, 4))) for val in row] for row in resampled]
            else:
                tensor_2d = resampled

            sequence_tensors.append(tensor_2d)
            normalized_max_dbz.append(frame["max_dbz"])

        return {
            "status": "PREPROCESSED_SUCCESS",
            "frame_count": len(sequence_tensors),
            "tensor_shape": [len(sequence_tensors), grid.height, grid.width, 1],
            "timestamps_utc": [f["timestamp_utc"] for f in frames_data],
            "filenames": [f["filename"] for f in frames_data],
            "target_grid": grid.to_dict(),
            "domain_compatibility": compat,
            "observed_max_dbz_per_frame": normalized_max_dbz,
            "normalized": normalize,
            "tensors": sequence_tensors,
            "provenance": frames_data[0]["provenance"]
        }

    def load_radar_frame(
        self,
        timestamp_iso: Optional[str] = None,
        scenario_id: str = "single_developing_storm",
        target_grid: Optional[StormTraceGrid] = None
    ) -> Dict[str, Any]:
        """
        Loads a radar frame for a given timestamp or falls back to demo mode with explicit metadata.
        """
        grid = target_grid or StormTraceGrid()
        real_files = self.discover_real_files()

        # 1. Attempt to load Real Radar Observation if present
        if real_files:
            target_file = real_files[0]
            if timestamp_iso:
                # Find closest timestamp
                min_diff = float("inf")
                target_dt = None
                try:
                    target_dt = datetime.fromisoformat(timestamp_iso.replace("Z", "+00:00"))
                except Exception:
                    pass

                for rf in real_files:
                    if rf["timestamp_utc"] == timestamp_iso:
                        target_file = rf
                        break
                    elif target_dt and rf["acquisition_dt"]:
                        diff = abs((rf["acquisition_dt"] - target_dt).total_seconds())
                        if diff < min_diff:
                            min_diff = diff
                            target_file = rf

            # Read NetCDF frame
            if target_file["filepath"].endswith(".nc"):
                frame_data = self.read_terls_netcdf_frame(target_file["filepath"])
                compat = self.evaluate_grid_compatibility(frame_data["spatial_extent"], grid)

                # Resample onto target grid
                resampled = grid.resample_2d_bilinear(
                    frame_data["reflectivity_dbz"],
                    frame_data["lons"],
                    frame_data["lats"],
                    fill_missing=0.0
                )

                return {
                    "status": "AVAILABLE_REAL_RADAR",
                    "is_demo": False,
                    "is_real_observation": True,
                    "filename": target_file["filename"],
                    "filepath": target_file["filepath"],
                    "timestamp_utc": frame_data["timestamp_utc"],
                    "provenance": frame_data["provenance"],
                    "spatial_extent": frame_data["spatial_extent"],
                    "domain_compatibility": compat,
                    "target_grid": grid.to_dict(),
                    "reflectivity_dbz": resampled,
                    "native_reflectivity_dbz": frame_data["reflectivity_dbz"],
                    "native_max_dbz": frame_data["max_dbz"],
                    "availability_mask": grid.create_availability_mask(is_available=True)
                }

        # 2. Fallback to Demo / Offline Benchmark
        gen = self.generator if (grid.height == 64 and grid.width == 64) else SyntheticStormGenerator(grid_width=grid.width, grid_height=grid.height)
        seq = gen.generate_sequence(scenario_id, seed=42)
        demo_frame = seq["frames"][0]
        demo_meta = get_radar_demo_metadata()

        return {
            "status": "AVAILABLE_DEMO_RADAR",
            "is_demo": True,
            "is_real_observation": False,
            "timestamp_utc": timestamp_iso or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "provenance": demo_meta,
            "target_grid": grid.to_dict(),
            "reflectivity_dbz": demo_frame["grids"]["reflectivity_dbz"],
            "availability_mask": grid.create_availability_mask(is_available=True),
            "demo_scenario": scenario_id
        }

