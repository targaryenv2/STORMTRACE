#!/usr/bin/env python3
"""
STORMTRACE Data Provenance and Semantic Metadata Registry
Phase 1 & Phase 16: Rigorous metadata tracking distinguishing real observations,
reanalysis, climatology, synthetic/demo data, and missing modalities.
"""

from enum import Enum
from typing import Dict, Any, Optional
import time


class DataType(str, Enum):
    """Explicit classification of dataset provenance."""
    REAL_OBSERVATION = "REAL_OBSERVATION"
    REAL_REANALYSIS = "REAL_REANALYSIS"
    REAL_CLIMATOLOGY = "REAL_CLIMATOLOGY"
    DEMO_DATA = "DEMO_DATA"
    SYNTHETIC_DATA = "SYNTHETIC_DATA"
    DERIVED_DATA = "DERIVED_DATA"
    MODEL_OUTPUT = "MODEL_OUTPUT"
    PLACEHOLDER_UNAVAILABLE = "PLACEHOLDER_UNAVAILABLE"


class TemporalSemantics(str, Enum):
    """Explicit semantic meaning of dataset timestamps."""
    INSTANTANEOUS_OBSERVATION = "INSTANTANEOUS_OBSERVATION"
    TIME_WINDOW_AGGREGATE = "TIME_WINDOW_AGGREGATE"
    MONTHLY_CLIMATOLOGY_AVERAGE = "MONTHLY_CLIMATOLOGY_AVERAGE"
    REANALYSIS_STEP = "REANALYSIS_STEP"
    FORECAST_STEP = "FORECAST_STEP"
    STATIC_REFERENCE = "STATIC_REFERENCE"


class SystemMode(str, Enum):
    """System-wide operational / data modes."""
    DEMO_MODE = "DEMO_MODE"
    REAL_HISTORICAL_MODE = "REAL_HISTORICAL_MODE"
    MIXED_MODE = "MIXED_MODE"


def create_dataset_metadata(
    source: str,
    dataset_name: str,
    dataset_id: str,
    processing_level: str,
    data_type: DataType,
    temporal_semantics: TemporalSemantics,
    spatial_resolution: str,
    temporal_resolution: str,
    geographic_domain: str,
    observation_period: str,
    real_time_capability: bool,
    event_level: bool,
    role_in_model: str,
    units: str,
    variables: list,
    disclaimer: Optional[str] = None
) -> Dict[str, Any]:
    """Generates standardized metadata dictionary for any ingested dataset."""
    return {
        "source": source,
        "dataset_name": dataset_name,
        "dataset_id": dataset_id,
        "product_id": dataset_id,
        "processing_level": processing_level,
        "data_type": data_type.value if isinstance(data_type, DataType) else str(data_type),
        "temporal_semantics": temporal_semantics.value if isinstance(temporal_semantics, TemporalSemantics) else str(temporal_semantics),
        "spatial_resolution": spatial_resolution,
        "temporal_resolution": temporal_resolution,
        "geographic_domain": geographic_domain,
        "observation_period": observation_period,
        "real_time_capability": real_time_capability,
        "event_level": event_level,
        "role_in_model": role_in_model,
        "units": units,
        "variables": variables,
        "disclaimer": disclaimer or "",
        "created_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }


def get_wglc_climatology_metadata() -> Dict[str, Any]:
    """
    Standardized metadata for WGLC (World Gridded Lightning Climatology).
    CRITICAL: Explicitly labels WGLC as a monthly climatological baseline over 2010-2020,
    NOT a real-time observation or event-level ground truth.
    """
    return create_dataset_metadata(
        source="WGLC",
        dataset_name="World Gridded Lightning Climatology",
        dataset_id="WGLC_MONTHLY_V1",
        processing_level="L3_CLIMATOLOGY",
        data_type=DataType.REAL_CLIMATOLOGY,
        temporal_semantics=TemporalSemantics.MONTHLY_CLIMATOLOGY_AVERAGE,
        spatial_resolution="0.5_DEGREE_GRID",
        temporal_resolution="MONTHLY_CLIMATOLOGICAL_AVERAGE",
        geographic_domain="GLOBAL",
        observation_period="2010-2020",
        real_time_capability=False,
        event_level=False,
        role_in_model="auxiliary_climatological_baseline",
        units="flashes_per_km2_per_month",
        variables=["lightning_flash_climatology_density"],
        disclaimer=(
            "WGLC is a monthly climatological lightning dataset representing average lightning patterns "
            "over approximately 2010-2020. It is NOT an event-level or real-time lightning observation "
            "and must not be interpreted as evidence of lightning at a specific forecast timestamp."
        )
    )


def get_insat3ds_metadata() -> Dict[str, Any]:
    """Standardized metadata for INSAT-3DS IMAGER Level-1C Asian sector product."""
    return create_dataset_metadata(
        source="ISRO_MOSDAC",
        dataset_name="INSAT-3DS IMAGER 6-Channel Level-1C Mercator",
        dataset_id="3SIMG_L1C_ASIA_MER",
        processing_level="L1C",
        data_type=DataType.REAL_OBSERVATION,
        temporal_semantics=TemporalSemantics.INSTANTANEOUS_OBSERVATION,
        spatial_resolution="1km_VIS_4km_IR_WV",
        temporal_resolution="30_MINUTES",
        geographic_domain="ASIA_SECTOR_MERCATOR",
        observation_period="OPERATIONAL_2024_PRESENT",
        real_time_capability=True,
        event_level=True,
        role_in_model="primary_convective_cloud_top_predictor",
        units="Kelvin_and_Counts",
        variables=["VIS", "SWIR", "MIR", "TIR1", "TIR2", "WV"],
        disclaimer="Requires authenticated user credentials from ISRO MOSDAC portal."
    )


def get_era5_metadata() -> Dict[str, Any]:
    """Standardized metadata for ECMWF ERA5 Atmospheric Reanalysis."""
    return create_dataset_metadata(
        source="ECMWF_CDS",
        dataset_name="ERA5 Hourly Reanalysis Single & Pressure Levels",
        dataset_id="reanalysis-era5-single-levels",
        processing_level="L4_REANALYSIS",
        data_type=DataType.REAL_REANALYSIS,
        temporal_semantics=TemporalSemantics.REANALYSIS_STEP,
        spatial_resolution="0.25_DEGREE_GRID",
        temporal_resolution="1_HOUR",
        geographic_domain="GLOBAL_OR_REGIONAL_SUBSET",
        observation_period="1979_PRESENT",
        real_time_capability=False,
        event_level=True,
        role_in_model="atmospheric_instability_and_shear_environment",
        units="SI_UNITS (J/kg, K, m/s, Pa)",
        variables=["cape", "cin", "t2m", "u10", "v10", "sp", "u850", "v850", "u500", "v500", "t850", "t500", "q850"],
        disclaimer="Reanalysis fields provide thermodynamic background; not instantaneous radar/satellite measurements."
    )


def get_imerg_metadata() -> Dict[str, Any]:
    """Standardized metadata for NASA GPM IMERG Precipitation Estimates."""
    return create_dataset_metadata(
        source="NASA_GPM",
        dataset_name="GPM IMERG Half-Hourly Precipitation Calibrated L3",
        dataset_id="GPM_3IMERGHH_V07",
        processing_level="L3_CALIBRATED",
        data_type=DataType.REAL_OBSERVATION,
        temporal_semantics=TemporalSemantics.TIME_WINDOW_AGGREGATE,
        spatial_resolution="0.1_DEGREE_GRID",
        temporal_resolution="30_MINUTES",
        geographic_domain="GLOBAL_60S_60N",
        observation_period="2000_PRESENT",
        real_time_capability=True,
        event_level=True,
        role_in_model="precipitation_rate_predictor_and_surface_water_flux",
        units="mm_per_hour",
        variables=["precipitationCal", "precipitationUncal", "probabilityLiquidPrecipitation"],
        disclaimer="Multi-satellite precipitation estimate calibrated with gauge analysis."
    )


def get_synthetic_era5_metadata() -> Dict[str, Any]:
    """Standardized metadata for synthetic mathematical ERA5 benchmark fields."""
    return create_dataset_metadata(
        source="STORMTRACE_SYNTHETIC_BENCHMARK",
        dataset_name="Synthetic Mathematical ERA5 Test Field (Demonstration)",
        dataset_id="SYNTHETIC_ERA5_BENCHMARK_V1",
        processing_level="SYNTHETIC_MATHEMATICAL_MODEL",
        data_type=DataType.SYNTHETIC_DATA,
        temporal_semantics=TemporalSemantics.REANALYSIS_STEP,
        spatial_resolution="0.25_DEGREE_GRID",
        temporal_resolution="1_HOUR",
        geographic_domain="REGIONAL_EAST_INDIA",
        observation_period="SYNTHETIC_BENCHMARK",
        real_time_capability=False,
        event_level=True,
        role_in_model="atmospheric_instability_and_shear_environment",
        units="SI_UNITS (J/kg, K, m/s, Pa)",
        variables=["cape", "cin", "t2m", "u10", "v10", "sp", "shear_0_6km"],
        disclaimer="Mathematical synthetic test field generated for testing and demonstration only. NOT a real observation or reanalysis."
    )


def get_synthetic_imerg_metadata() -> Dict[str, Any]:
    """Standardized metadata for synthetic mathematical IMERG benchmark fields."""
    return create_dataset_metadata(
        source="STORMTRACE_SYNTHETIC_BENCHMARK",
        dataset_name="Synthetic Mathematical IMERG Precipitation Test Field (Demonstration)",
        dataset_id="SYNTHETIC_IMERG_BENCHMARK_V1",
        processing_level="SYNTHETIC_MATHEMATICAL_MODEL",
        data_type=DataType.SYNTHETIC_DATA,
        temporal_semantics=TemporalSemantics.TIME_WINDOW_AGGREGATE,
        spatial_resolution="0.1_DEGREE_GRID",
        temporal_resolution="30_MINUTES",
        geographic_domain="REGIONAL_EAST_INDIA",
        observation_period="SYNTHETIC_BENCHMARK",
        real_time_capability=False,
        event_level=True,
        role_in_model="precipitation_rate_predictor_and_surface_water_flux",
        units="mm_per_hour",
        variables=["precipitationCal"],
        disclaimer="Mathematical synthetic test field generated for testing and demonstration only. NOT a real GPM IMERG observation."
    )


def get_radar_demo_metadata() -> Dict[str, Any]:
    """Standardized metadata for current demo/offline Doppler Weather Radar feeds."""
    return create_dataset_metadata(
        source="STORMTRACE_DEMO_DWR",
        dataset_name="Doppler Weather Radar Composite Grid (Offline Demonstration)",
        dataset_id="DWR_COMPOSITE_DEMO_V1",
        processing_level="SYNTHETIC_CALIBRATED_MOSAIC",
        data_type=DataType.DEMO_DATA,
        temporal_semantics=TemporalSemantics.INSTANTANEOUS_OBSERVATION,
        spatial_resolution="1km_GRID",
        temporal_resolution="10_MINUTES",
        geographic_domain="INDIAN_SUBCONTINENT_RADAR_NETWORK",
        observation_period="DEMO_OFFLINE_BENCHMARK",
        real_time_capability=False,
        event_level=True,
        role_in_model="convective_core_reflectivity_predictor",
        units="dBZ",
        variables=["reflectivity_dbz", "velocity_radial_mps", "spectrum_width"],
        disclaimer="Currently running on demo/offline benchmark data pending live IMD DWR API access."
    )


def get_terls_dwr_metadata(
    spatial_extent: Optional[Dict[str, float]] = None,
    observation_date: str = "2018-01-11"
) -> Dict[str, Any]:
    """
    Standardized metadata for ISRO TERLS Doppler Weather Radar (DWR).
    REAL OBSERVATION from Thumba Equatorial Rocket Launching Station, Thiruvananthapuram, Kerala.
    Geographic domain is South India coastal domain (~6.37°N-10.71°N, 74.69°E-79.02°E),
    OUTSIDE the STORMTRACE Regional East India domain (83.5°E-89.8°E, 20.0°N-26.3°N).
    """
    extent_str = "6.37N-10.71N, 74.69E-79.02E (SOUTH_INDIA_TERLS)"
    if spatial_extent:
        extent_str = f"[{spatial_extent.get('lat_min', 6.37):.2f}N-{spatial_extent.get('lat_max', 10.71):.2f}N, {spatial_extent.get('lon_min', 74.69):.2f}E-{spatial_extent.get('lon_max', 79.02):.2f}E]"

    return create_dataset_metadata(
        source="ISRO TERLS DWR",
        dataset_name="ISRO TERLS Doppler Weather Radar Volumetric Scans",
        dataset_id="ISRO_TERLS_DWR_L2_VOLUMETRIC",
        processing_level="L2_DECLUTTERED_VOLUMETRIC_GRID",
        data_type=DataType.REAL_OBSERVATION,
        temporal_semantics=TemporalSemantics.INSTANTANEOUS_OBSERVATION,
        spatial_resolution="481x481_GRID (~1.0km)",
        temporal_resolution="~15_MINUTES",
        geographic_domain=extent_str,
        observation_period=observation_date,
        real_time_capability=False,
        event_level=True,
        role_in_model="real_radar_pipeline_validation_and_convective_core_reflectivity",
        units="dBZ, m/s",
        variables=["DBZ", "VEL", "height", "latitude", "longitude", "time"],
        disclaimer="Real radar volumetric scan observations from ISRO TERLS (South India). Strictly outside STORMTRACE Regional East India operational domain."
    )


