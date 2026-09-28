#!/usr/bin/env python3
"""
STORMTRACE Common Spatiotemporal Grid
Phase 7: Defines common model spatial representation and resampling routines
while preserving native resolution and projection metadata for every modality.
"""

import math
from typing import List, Tuple, Dict, Any, Optional


class NativeModalitySpec:
    """Documents native spatial, temporal, and coordinate properties of each source."""
    def __init__(
        self,
        name: str,
        native_spatial_res: str,
        native_temporal_res: str,
        projection: str,
        native_bbox: List[float],
        units: str,
        channels: List[str],
        temporal_semantics: str
    ):
        self.name = name
        self.native_spatial_res = native_spatial_res
        self.native_temporal_res = native_temporal_res
        self.projection = projection
        self.native_bbox = native_bbox  # [min_lon, min_lat, max_lon, max_lat]
        self.units = units
        self.channels = channels
        self.temporal_semantics = temporal_semantics

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "native_spatial_res": self.native_spatial_res,
            "native_temporal_res": self.native_temporal_res,
            "projection": self.projection,
            "native_bbox": self.native_bbox,
            "units": self.units,
            "channels": self.channels,
            "temporal_semantics": self.temporal_semantics
        }


MODALITY_SPECS = {
    "radar": NativeModalitySpec(
        name="Doppler Weather Radar (DWR)",
        native_spatial_res="1.0 km (~0.01 deg)",
        native_temporal_res="10 minutes",
        projection="EPSG:4326 / Azimuthal Polar Radar Grid",
        native_bbox=[68.0, 6.0, 98.0, 36.0],
        units="dBZ (reflectivity), m/s (radial velocity)",
        channels=["reflectivity_dbz", "velocity_mps", "spectrum_width"],
        temporal_semantics="Instantaneous Radar Volume Scan"
    ),
    "satellite_insat3ds": NativeModalitySpec(
        name="INSAT-3DS IMAGER 3SIMG_L1C_ASIA_MER",
        native_spatial_res="1.0 km (VIS), 4.0 km (IR/WV)",
        native_temporal_res="30 minutes",
        projection="Mercator (ASIA_MER)",
        native_bbox=[40.0, -10.0, 120.0, 50.0],
        units="Brightness Temperature (Kelvin) / Radiance Counts",
        channels=["VIS", "SWIR", "MIR", "TIR1", "TIR2", "WV"],
        temporal_semantics="Instantaneous Satellite Scan"
    ),
    "lightning_wglc": NativeModalitySpec(
        name="World Gridded Lightning Climatology (WGLC)",
        native_spatial_res="0.5 deg (~50 km)",
        native_temporal_res="Monthly Climatology (2010-2020 Mean)",
        projection="EPSG:4326 (WGS84 Equirectangular)",
        native_bbox=[-180.0, -90.0, 180.0, 90.0],
        units="flashes / km^2 / month",
        channels=["lightning_flash_climatology_density"],
        temporal_semantics="Monthly Climatological Average (NOT Real-Time)"
    ),
    "nwp_era5": NativeModalitySpec(
        name="ECMWF ERA5 Reanalysis",
        native_spatial_res="0.25 deg (~25 km)",
        native_temporal_res="1 hour",
        projection="EPSG:4326 (Regular Lat/Lon)",
        native_bbox=[-180.0, -90.0, 180.0, 90.0],
        units="J/kg (CAPE/CIN), K (Temp), m/s (Wind), Pa (Pressure)",
        channels=["cape", "cin", "t2m", "u10", "v10", "sp", "u850", "v850", "u500", "v500", "t850", "t500", "q850"],
        temporal_semantics="Reanalysis Time Step"
    ),
    "imerg_precipitation": NativeModalitySpec(
        name="NASA GPM IMERG Calibrated Precipitation",
        native_spatial_res="0.1 deg (~10 km)",
        native_temporal_res="30 minutes",
        projection="EPSG:4326 (Global 60S-60N)",
        native_bbox=[-180.0, -60.0, 180.0, 60.0],
        units="mm / hour",
        channels=["precipitationCal", "precipitationUncal"],
        temporal_semantics="30-Minute Accumulation / Mean Rate"
    )
}


from enum import Enum


class GridDomain(str, Enum):
    """Supported geographical domain presets for STORMTRACE."""
    REGIONAL_EAST_INDIA = "REGIONAL_EAST_INDIA"    # West Bengal / Odisha / Jharkhand (~0.1 deg / 11km)
    SOUTH_ASIA_SYNOPTIC = "SOUTH_ASIA_SYNOPTIC"    # Full Indian Subcontinent synoptic overview (~0.5 deg / 52km)


# Domain presets bounding boxes: [min_lon, min_lat, max_lon, max_lat]
DOMAIN_PRESETS = {
    GridDomain.REGIONAL_EAST_INDIA: {
        "name": "Regional East India (West Bengal / Odisha / Jharkhand)",
        "min_lon": 83.5,
        "min_lat": 20.0,
        "max_lon": 89.8,
        "max_lat": 26.3,
        "default_height": 64,
        "default_width": 64,
        "description": "High-resolution convective storm domain matching IMERG 0.1 deg (~11km) native grid."
    },
    GridDomain.SOUTH_ASIA_SYNOPTIC: {
        "name": "South Asia Synoptic Domain",
        "min_lon": 68.0,
        "min_lat": 6.0,
        "max_lon": 98.0,
        "max_lat": 36.0,
        "default_height": 64,
        "default_width": 64,
        "description": "Coarse synoptic overview grid for macro-scale atmospheric circulation."
    }
}


class StormTraceGrid:
    """
    Standardized target spatial grid for STORMTRACE multimodal tensors.
    Defaults to the high-resolution East India regional domain (West Bengal / Odisha / Jharkhand ~11 km)
    with optional South Asia synoptic domain configuration.
    """

    def __init__(
        self,
        min_lon: Optional[float] = None,
        min_lat: Optional[float] = None,
        max_lon: Optional[float] = None,
        max_lat: Optional[float] = None,
        height: Optional[int] = None,
        width: Optional[int] = None,
        domain: Optional[str] = None
    ):
        # Resolve domain preset
        domain_key = None
        if domain:
            dom_upper = domain.upper()
            if "SOUTH" in dom_upper or "SYNOPTIC" in dom_upper:
                domain_key = GridDomain.SOUTH_ASIA_SYNOPTIC
            else:
                domain_key = GridDomain.REGIONAL_EAST_INDIA
        elif min_lon is None and min_lat is None and max_lon is None and max_lat is None:
            # Default to High-Res Regional East India domain (~0.1 deg / 11 km)
            domain_key = GridDomain.REGIONAL_EAST_INDIA

        if domain_key:
            preset = DOMAIN_PRESETS[domain_key]
            self.domain_name = domain_key.value
            self.min_lon = float(min_lon if min_lon is not None else preset["min_lon"])
            self.min_lat = float(min_lat if min_lat is not None else preset["min_lat"])
            self.max_lon = float(max_lon if max_lon is not None else preset["max_lon"])
            self.max_lat = float(max_lat if max_lat is not None else preset["max_lat"])
            self.height = int(height if height is not None else preset["default_height"])
            self.width = int(width if width is not None else preset["default_width"])
        else:
            # Explicit coordinate initialization (e.g. South Asia bounding box passed directly)
            self.domain_name = "CUSTOM_DOMAIN"
            self.min_lon = float(min_lon if min_lon is not None else 83.5)
            self.min_lat = float(min_lat if min_lat is not None else 20.0)
            self.max_lon = float(max_lon if max_lon is not None else 89.8)
            self.max_lat = float(max_lat if max_lat is not None else 26.3)
            self.height = int(height if height is not None else 64)
            self.width = int(width if width is not None else 64)

        self.dlon = (self.max_lon - self.min_lon) / max(1, self.width - 1)
        self.dlat = (self.max_lat - self.min_lat) / max(1, self.height - 1)

        # 1D coordinate vectors
        self.lons = [self.min_lon + i * self.dlon for i in range(self.width)]
        self.lats = [self.min_lat + j * self.dlat for j in range(self.height)]

    @property
    def domain(self) -> GridDomain:
        if self.domain_name == GridDomain.SOUTH_ASIA_SYNOPTIC.value:
            return GridDomain.SOUTH_ASIA_SYNOPTIC
        return GridDomain.REGIONAL_EAST_INDIA

    @property
    def resolution_deg(self) -> float:
        return round((self.dlon + self.dlat) / 2.0, 4)

    @property
    def cell_size_km(self) -> float:
        return round(self.dlat * 111.0, 2)

    @classmethod
    def regional_east_india(cls, height: int = 64, width: int = 64) -> 'StormTraceGrid':
        """High-resolution East India / Bengal / Odisha / Jharkhand convective domain (~11 km)."""
        return cls(domain=GridDomain.REGIONAL_EAST_INDIA.value, height=height, width=width)

    @classmethod
    def south_asia_synoptic(cls, height: int = 64, width: int = 64) -> 'StormTraceGrid':
        """Coarse synoptic South Asia domain."""
        return cls(domain=GridDomain.SOUTH_ASIA_SYNOPTIC.value, height=height, width=width)

    @classmethod
    def create_regional_east_india(cls, height: int = 64, width: int = 64) -> 'StormTraceGrid':
        """High-resolution East India / Bengal / Odisha / Jharkhand convective domain (~11 km)."""
        return cls.regional_east_india(height=height, width=width)

    @classmethod
    def create_south_asia_synoptic(cls, height: int = 64, width: int = 64) -> 'StormTraceGrid':
        """Coarse synoptic South Asia domain."""
        return cls.south_asia_synoptic(height=height, width=width)

    def get_lat_lon_mesh(self):
        """Returns 2D (lats_mesh, lons_mesh) numpy arrays for vectorized calculations."""
        import numpy as np
        lons_arr = np.array(self.lons, dtype=np.float32)
        lats_arr = np.array(self.lats, dtype=np.float32)
        lons_mesh, lats_mesh = np.meshgrid(lons_arr, lats_arr)
        return lats_mesh, lons_mesh

    def create_empty_grid(self, fill_value: float = 0.0) -> List[List[float]]:
        """Create a 2D height x width float array initialized with fill_value."""
        return [[fill_value for _ in range(self.width)] for _ in range(self.height)]

    def create_availability_mask(self, is_available: bool = True) -> List[List[int]]:
        """Create a 2D boolean/integer mask (1 = observed/available, 0 = missing)."""
        val = 1 if is_available else 0
        return [[val for _ in range(self.width)] for _ in range(self.height)]

    def resample_2d_bilinear(
        self,
        src_grid: List[List[float]],
        src_lons: List[float],
        src_lats: List[float],
        fill_missing: float = 0.0
    ) -> List[List[float]]:
        """
        Bilinear interpolation resampling from native (src_lons, src_lats) grid
        onto the STORMTRACE target grid (self.lons, self.lats).
        Works in pure Python without external library dependencies.
        """
        src_h = len(src_lats)
        src_w = len(src_lons)
        if src_h < 2 or src_w < 2:
            return self.create_empty_grid(fill_missing)

        src_min_lon, src_max_lon = src_lons[0], src_lons[-1]
        src_min_lat, src_max_lat = src_lats[0], src_lats[-1]
        lon_ascending = src_max_lon > src_min_lon
        lat_ascending = src_max_lat > src_min_lat

        out = self.create_empty_grid(fill_missing)

        for j, tgt_lat in enumerate(self.lats):
            # Check lat bounding box
            if (lat_ascending and not (src_min_lat <= tgt_lat <= src_max_lat)) or \
               (not lat_ascending and not (src_max_lat <= tgt_lat <= src_min_lat)):
                continue

            # Find bounding lat indices
            if lat_ascending:
                lat_frac = (tgt_lat - src_min_lat) / (src_max_lat - src_min_lat) * (src_h - 1)
            else:
                lat_frac = (tgt_lat - src_min_lat) / (src_max_lat - src_min_lat) * (src_h - 1)
            y0 = max(0, min(src_h - 2, int(math.floor(lat_frac))))
            y1 = y0 + 1
            dy = max(0.0, min(1.0, lat_frac - y0))

            for i, tgt_lon in enumerate(self.lons):
                # Check lon bounding box
                if (lon_ascending and not (src_min_lon <= tgt_lon <= src_max_lon)) or \
                   (not lon_ascending and not (src_max_lon <= tgt_lon <= src_min_lon)):
                    continue

                if lon_ascending:
                    lon_frac = (tgt_lon - src_min_lon) / (src_max_lon - src_min_lon) * (src_w - 1)
                else:
                    lon_frac = (tgt_lon - src_min_lon) / (src_max_lon - src_min_lon) * (src_w - 1)
                x0 = max(0, min(src_w - 2, int(math.floor(lon_frac))))
                x1 = x0 + 1
                dx = max(0.0, min(1.0, lon_frac - x0))

                # 4 corner values
                v00 = src_grid[y0][x0]
                v01 = src_grid[y0][x1]
                v10 = src_grid[y1][x0]
                v11 = src_grid[y1][x1]

                # Bilinear interpolate
                val = (1.0 - dx) * (1.0 - dy) * v00 + \
                      dx * (1.0 - dy) * v01 + \
                      (1.0 - dx) * dy * v10 + \
                      dx * dy * v11

                out[j][i] = round(val, 3)

        return out

    def to_dict(self) -> Dict[str, Any]:
        return {
            "min_lon": self.min_lon,
            "min_lat": self.min_lat,
            "max_lon": self.max_lon,
            "max_lat": self.max_lat,
            "height": self.height,
            "width": self.width,
            "dlon_deg": round(self.dlon, 4),
            "dlat_deg": round(self.dlat, 4),
            "approx_spatial_res_km": round(self.dlat * 111.0, 2)
        }
