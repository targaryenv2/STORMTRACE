# STORMTRACE Training Data Audit Report

**Audit Date**: September 22, 2026  
**Target Operational Domain**: Regional East India (West Bengal / Odisha / Jharkhand)  
**Target Coordinates**: Longitude: $83.5^\circ\text{E} - 89.8^\circ\text{E}$, Latitude: $20.0^\circ\text{N} - 26.3^\circ\text{N}$  
**Target Temporal Window**: 2020+ Operational Radar & Satellite Sequences  

---

## 1. Summary Audit Table

| Dataset / Modality | Real Files Present? | Date Range | Geographic Coverage | Resolution (Spatial & Temporal) | Variables / Channels | 2020+? | East India Overlap? | Final Training Usable? |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **ISRO TERLS DWR Radar** | **YES** (69 NetCDF files, ~10 GB) | 2018-01-11 (00:12–17:53 UTC) | South India / Kerala ($74.5^\circ\text{E}–79.2^\circ\text{E}$, $6.2^\circ\text{N}–10.9^\circ\text{N}$) | $1.0\text{ km} \times 1.0\text{ km}$, $\approx 15.3\text{ min}$ | `DBZ` (reflectivity), `VEL` (radial velocity), `WIDTH` | **No** (2018) | **No** ($74.5^\circ\text{E}–79.2^\circ\text{E}$, $6.2^\circ\text{N}–10.9^\circ\text{N}$) | **No** (Pipeline validation & DWR ingestion only; NOT for final East India model) |
| **IMD East India DWR Radar** (Kolkata, Paradip, Ranchi) | **No** | None | Regional East India ($83.5^\circ\text{E}–89.8^\circ\text{E}$, $20.0^\circ\text{N}–26.3^\circ\text{N}$) | Expected $1.0\text{ km}$, $10\text{ min}$ | Expected `reflectivity_dbz`, `velocity_mps` | N/A | **Yes** (Intended) | **Blocked** (Pending acquisition from IMD data portal) |
| **ISRO MOSDAC INSAT-3DS Satellite** | **No** (`data/raw/satellite/insat3ds` empty) | None | South Asia / Asia-Pacific ($40.0^\circ\text{E}–120.0^\circ\text{E}$, $-10.0^\circ\text{N}–50.0^\circ\text{N}$) | $1.0\text{ km}$ (VIS), $4.0\text{ km}$ (IR/WV), $30\text{ min}$ | VIS, SWIR, MIR, TIR1, TIR2, WV | N/A | **Yes** (Intended) | **Blocked** (Pending MOSDAC API credentials and archive download) |
| **ECMWF ERA5 Reanalysis** | **Synthetic Only** (11 JSON simulation files in `dataset/raw/nwp/era5/`) | Synthetic Event Dates (2020–2026) | Regional East India ($83.5^\circ\text{E}–89.8^\circ\text{E}$, $20.0^\circ\text{N}–26.3^\circ\text{N}$) | $0.25^\circ \times 0.25^\circ$ ($64 \times 64$ resampled) | CAPE, CIN, Wind Shear (u/v 10m, 850hPa, 500hPa) | Mixed | **Yes** (Domain-matched) | **No** (Simulated JSON snapshots; real GRIB/NetCDF ERA5 reanalysis required) |
| **NASA GPM IMERG Precipitation** | **Synthetic Only** (11 JSON simulation files in `dataset/raw/imerg/`) | Synthetic Event Dates (2020–2026) | Regional East India ($83.5^\circ\text{E}–89.8^\circ\text{E}$, $20.0^\circ\text{N}–26.3^\circ\text{N}$) | $0.1^\circ \times 0.1^\circ$ ($64 \times 64$ resampled) | `precipitationCal`, `precipitationUncal` | Mixed | **Yes** (Domain-matched) | **No** (Simulated JSON snapshots; real HDF5/NetCDF IMERG required) |
| **WGLC Lightning Climatology** | **Synthetic Baseline** | 2010–2020 Monthly Mean Baseline | Global / Regional East India | $0.5^\circ \times 0.5^\circ$ ($64 \times 64$ resampled) | `lightning_flash_climatology_density` | Climatology | **Yes** (Domain-matched) | **No** (Monthly mean climatological baseline, not real-time lightning feed) |

---

## 2. Key Scientific Findings

1. **Physical Radar Availability**:
   - The only real radar dataset physically present on disk is the ISRO TERLS DWR dataset (`data/raw/radar/terls/*.nc`, 69 NetCDF files from January 11, 2018).
   - This dataset provides **authentic real-world radar volume scans** with genuine Doppler radial velocity (`VEL`) and 2D composite reflectivity (`DBZ`), proving that our ingestion, coordinate transformation, and sequence formatting pipelines function on true NetCDF binary formats.
   - However, because it covers Thumba/Kerala ($8.5^\circ\text{N}, 76.9^\circ\text{E}$, South India) in 2018, **it CANNOT be used to train or claim forecast skill for 2020+ East India weather**.

2. **Training Status & Governance Policy**:
   - In strict compliance with scientific integrity principles, **final model training is paused / blocked** until genuine 2020+ East India radar archives (IMD DWR Kolkata/Paradip) or MOSDAC INSAT-3DS temporal volumes are ingested.
   - All dataset loaders, temporal sequencing classes, PyTorch `Dataset`/`DataLoader` pipelines, and loss functions are fully built and tested below so that training can be launched immediately once the verified East India data files are supplied.
