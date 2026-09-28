#!/usr/bin/env python3
"""
STORMTRACE Multimodal Sample Builder
Phase 11: Combines aligned Radar, INSAT-3DS, WGLC Climatology, ERA5, and GPM IMERG streams
into model-ready multimodal sample tensors while strictly preserving missing-data masks,
modality availability, and label provenance.
"""

import os
import json
import csv
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

try:
    from dataset.grid import StormTraceGrid
    from dataset.alignment import MultimodalTemporalAligner
    from dataset.loaders.satellite_loader import Insat3dsSatelliteLoader
    from dataset.loaders.lightning_loader import WglcLightningLoader
    from dataset.loaders.radar_loader import RadarDataLoader
    from dataset.loaders.nwp_loader import NwpEra5Loader
    from dataset.loaders.imerg_loader import ImergPrecipitationLoader
    from dataset.provenance import (
        DataType, TemporalSemantics, SystemMode,
        get_insat3ds_metadata, get_wglc_climatology_metadata,
        get_era5_metadata, get_imerg_metadata, get_radar_demo_metadata
    )
except ImportError:
    from stormtrace.data.grid import StormTraceGrid
    from stormtrace.data.alignment import MultimodalTemporalAligner
    from stormtrace.data.satellite_loader import Insat3dsSatelliteLoader
    from stormtrace.data.lightning_loader import WglcLightningLoader
    from stormtrace.data.radar_loader import RadarDataLoader
    from stormtrace.data.nwp_loader import NwpEra5Loader
    from stormtrace.data.imerg_loader import ImergPrecipitationLoader
    from stormtrace.data.provenance import (
        DataType, TemporalSemantics, SystemMode,
        get_insat3ds_metadata, get_wglc_climatology_metadata,
        get_era5_metadata, get_imerg_metadata, get_radar_demo_metadata
    )


class MultimodalSampleBuilder:
    """
    Constructs unified multimodal samples for STORMTRACE nowcasting and deep learning models.
    Preserves missing-data masks without silently inventing data.
    """

    def __init__(
        self,
        grid: Optional[StormTraceGrid] = None,
        data_root: str = "dataset"
    ):
        self.grid = grid or StormTraceGrid()
        if not os.path.exists(data_root) and os.path.exists("data"):
            self.data_root = "data"
        else:
            self.data_root = data_root

        # Initialize loaders
        self.sat_loader = Insat3dsSatelliteLoader(os.path.join(self.data_root, "raw/satellite/insat3ds"))
        self.lgt_loader = WglcLightningLoader(os.path.join(self.data_root, "raw/lightning/wglc"))
        self.radar_loader = RadarDataLoader(os.path.join(self.data_root, "raw/radar"))
        self.nwp_loader = NwpEra5Loader(os.path.join(self.data_root, "raw/nwp/era5"))
        self.imerg_loader = ImergPrecipitationLoader(os.path.join(self.data_root, "raw/imerg"))
        self.aligner = MultimodalTemporalAligner()

    def build_sample_at_timestamp(
        self,
        event_id: str,
        target_timestamp_iso: str,
        lat: float = 22.57,
        lon: float = 88.36,
        allow_demo_fallback: bool = True
    ) -> Dict[str, Any]:
        """
        Constructs a complete multimodal sample dictionary for a single initialization timestamp.
        """
        # Discover available timestamps from each loader
        sat_files = self.sat_loader.discover_files()
        sat_ts = [f["timestamp_utc"] for f in sat_files]

        radar_files = self.radar_loader.discover_real_files()
        radar_ts = [f["timestamp_utc"] for f in radar_files]

        nwp_files = self.nwp_loader.discover_files()
        nwp_ts = [f["timestamp_utc"] for f in nwp_files]

        imerg_files = self.imerg_loader.discover_files()
        imerg_ts = [f["timestamp_utc"] for f in imerg_files]

        # Temporal alignment
        alignment = self.aligner.match_modalities(
            t0_iso=target_timestamp_iso,
            available_radar_timestamps=radar_ts,
            available_satellite_timestamps=sat_ts,
            available_imerg_timestamps=imerg_ts,
            available_era5_timestamps=nwp_ts
        )

        # 1. Ingest Satellite (INSAT-3DS)
        if alignment["modalities"]["satellite_insat3ds"]["available"]:
            sat_match_ts = alignment["modalities"]["satellite_insat3ds"]["matched_timestamp_utc"]
            sat_file = next((f["filepath"] for f in sat_files if f["timestamp_utc"] == sat_match_ts), "")
            sat_data = self.sat_loader.load_channels_to_grid(sat_file, self.grid)
        else:
            sat_data = self.sat_loader.load_channels_to_grid("", self.grid)

        # 2. Ingest Lightning (WGLC Climatology)
        month = alignment["target_calendar_month"]
        lgt_data = self.lgt_loader.get_monthly_climatology(month, self.grid)

        # 3. Ingest Radar
        if alignment["modalities"]["radar"]["available"]:
            radar_data = self.radar_loader.load_radar_frame(
                timestamp_iso=alignment["modalities"]["radar"]["matched_timestamp_utc"],
                target_grid=self.grid
            )
        elif allow_demo_fallback:
            radar_data = self.radar_loader.load_radar_frame(
                timestamp_iso=target_timestamp_iso,
                scenario_id="single_developing_storm",
                target_grid=self.grid
            )
        else:
            radar_data = {
                "status": "UNAVAILABLE",
                "is_demo": False,
                "timestamp_utc": target_timestamp_iso,
                "provenance": get_radar_demo_metadata(),
                "reflectivity_dbz": self.grid.create_empty_grid(0.0),
                "availability_mask": self.grid.create_availability_mask(is_available=False)
            }

        # 4. Ingest ERA5 NWP
        if alignment["modalities"]["nwp_era5"]["available"]:
            nwp_match_ts = alignment["modalities"]["nwp_era5"]["matched_timestamp_utc"]
            nwp_file = next((f["filepath"] for f in nwp_files if f["timestamp_utc"] == nwp_match_ts), None)
            nwp_data = self.nwp_loader.load_variables_to_grid(nwp_file, self.grid)
        else:
            nwp_data = self.nwp_loader.load_variables_to_grid(None, self.grid)

        # 5. Ingest GPM IMERG
        if alignment["modalities"]["imerg_precipitation"]["available"]:
            imerg_match_ts = alignment["modalities"]["imerg_precipitation"]["matched_timestamp_utc"]
            imerg_file = next((f["filepath"] for f in imerg_files if f["timestamp_utc"] == imerg_match_ts), None)
            imerg_data = self.imerg_loader.load_precipitation_to_grid(imerg_file, self.grid)
        else:
            imerg_data = self.imerg_loader.load_precipitation_to_grid(None, self.grid)

        # Determine overall system data mode
        is_all_real = (
            alignment["modalities"]["satellite_insat3ds"]["available"] and
            alignment["modalities"]["radar"]["available"] and
            alignment["modalities"]["nwp_era5"]["available"] and
            alignment["modalities"]["imerg_precipitation"]["available"]
        )
        is_all_demo = (
            not alignment["modalities"]["satellite_insat3ds"]["available"] and
            radar_data.get("is_demo", True) and
            not alignment["modalities"]["nwp_era5"]["available"]
        )

        if is_all_real:
            data_mode = SystemMode.REAL_HISTORICAL_MODE
        elif is_all_demo:
            data_mode = SystemMode.DEMO_MODE
        else:
            data_mode = SystemMode.MIXED_MODE

        # Construct multimodal tensor sample structure
        sample = {
            "event_id": event_id,
            "target_initialization_time_utc": target_timestamp_iso,
            "valid_time_utc": target_timestamp_iso,
            "centroid_lat": lat,
            "centroid_lon": lon,
            "system_mode": data_mode.value,
            "spatial_grid": self.grid.to_dict(),
            "alignment": alignment,
            "tensors": {
                "radar_reflectivity_dbz": radar_data.get("reflectivity_dbz"),
                "satellite_tir1_cloud_top": sat_data.get("channel_grids", {}).get("TIR1"),
                "satellite_wv_vapor": sat_data.get("channel_grids", {}).get("WV"),
                "satellite_vis_reflectance": sat_data.get("channel_grids", {}).get("VIS"),
                "lightning_climatology_baseline": lgt_data.get("climatology_density_grid"),
                "nwp_cape_j_kg": nwp_data.get("variables", {}).get("cape"),
                "nwp_shear_0_6km": nwp_data.get("variables", {}).get("shear_0_6km"),
                "imerg_precipitation_rate_mm_hr": imerg_data.get("precipitation_mm_hr")
            },
            "availability_masks": {
                "radar": radar_data.get("availability_mask"),
                "satellite_tir1": sat_data.get("availability_masks", {}).get("TIR1"),
                "lightning_climatology": lgt_data.get("availability_mask"),
                "nwp_cape": nwp_data.get("availability_masks", {}).get("cape"),
                "imerg_precipitation": imerg_data.get("availability_mask")
            },
            "labels": {
                "label_available": False,
                "label_source": "UNAVAILABLE",
                "disclaimer": "Supervised real-world ground truth requires verified IMD storm damage / station records."
            },
            "provenance_registry": {
                "radar": radar_data.get("provenance"),
                "satellite": sat_data.get("provenance"),
                "lightning": lgt_data.get("provenance"),
                "nwp": nwp_data.get("provenance"),
                "imerg": imerg_data.get("provenance")
            }
        }

        return sample

    def export_manifest_csv(self, samples: List[Dict[str, Any]], output_csv_path: str = "dataset/manifests/events.csv") -> str:
        """
        Exports standardized dataset manifest CSV documenting each sample's exact provenance.
        """
        os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
        fieldnames = [
            "event_id", "timestamp", "valid_time", "latitude", "longitude",
            "system_mode", "radar_source", "radar_available",
            "satellite_source", "satellite_available",
            "lightning_source", "lightning_available", "lightning_data_type",
            "nwp_source", "nwp_available",
            "imerg_source", "imerg_available",
            "wglc_source", "wglc_available", "wglc_semantics",
            "label_source", "label_available", "data_quality"
        ]

        with open(output_csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for s in samples:
                al = s["alignment"]["modalities"]
                row = {
                    "event_id": s["event_id"],
                    "timestamp": s["target_initialization_time_utc"],
                    "valid_time": s["valid_time_utc"],
                    "latitude": s["centroid_lat"],
                    "longitude": s["centroid_lon"],
                    "system_mode": s["system_mode"],
                    "radar_source": "IMD_DWR" if not s["provenance_registry"]["radar"].get("data_type") == "DEMO_DATA" else "DEMO_DWR",
                    "radar_available": al["radar"]["available"],
                    "satellite_source": "ISRO_MOSDAC_INSAT3DS",
                    "satellite_available": al["satellite_insat3ds"]["available"],
                    "lightning_source": "WGLC_MONTHLY_CLIMATOLOGY",
                    "lightning_available": True,
                    "lightning_data_type": "climatology",
                    "nwp_source": "ECMWF_ERA5",
                    "nwp_available": al["nwp_era5"]["available"],
                    "imerg_source": "NASA_GPM",
                    "imerg_available": al["imerg_precipitation"]["available"],
                    "wglc_source": "WGLC_2010_2020",
                    "wglc_available": True,
                    "wglc_semantics": "monthly_climatological_average",
                    "label_source": s["labels"]["label_source"],
                    "label_available": s["labels"]["label_available"],
                    "data_quality": "VERIFIED_STRUCTURE"
                }
                writer.writerow(row)

        return output_csv_path
