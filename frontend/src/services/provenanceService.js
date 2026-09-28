/**
 * STORMTRACE Provenance Registry Service (Frontend Dynamic Source)
 * Sourced directly from the verified backend / dataset provenance registry.
 * Reflects genuine operational states: Real Climatology, Demo Data, Benchmark Simulation, Pending/Unavailable.
 */

export const MODALITY_PROVENANCE_CARDS = [
  {
    id: 'satellite_insat3ds',
    name: 'INSAT-3DS Satellite (Imager)',
    shortCode: 'INSAT-3DS',
    source: 'ISRO MOSDAC',
    productId: '3SIMG_L1C_ASIA_MER',
    statusType: 'UNAVAILABLE',
    statusBadge: 'Pending Integration',
    statusTheme: 'slate', // muted gray / slate
    description: 'Level-1C calibrated multi-spectral radiances (VIS, SWIR, MIR, TIR1, TIR2, WV) from ISRO INSAT-3DS Asian sector imager.',
    resolution: '1.0 km VIS / 4.0 km IR · 30 min',
    role: 'Primary convective cloud-top cooling ($T_b < -60^\\circ\\text{C}$) & upper moisture predictor.',
    provenanceNote: 'Awaiting authenticated user ISRO MOSDAC account downloads. Channel currently masked (= 0.0) in inference.',
    isLive: false,
    isReal: true,
    isDemo: false,
    isClimatology: false,
    isPending: true
  },
  {
    id: 'radar_dwr',
    name: 'Doppler Weather Radar (DWR)',
    shortCode: 'IMD DWR',
    source: 'IMD Radar Network',
    productId: 'DWR_COMPOSITE_DEMO_V1',
    statusType: 'DEMO_DATA',
    statusBadge: 'Demo Data',
    statusTheme: 'amber', // amber badge for demo
    description: 'Base reflectivity mosaics (dBZ) and radial velocity volume scans for convective precipitation cores and TITAN centroid tracking.',
    resolution: '1.0 km composite grid · 10 min',
    role: 'Direct measurement of convective core precipitation & 2D Kalman filter velocity vectors.',
    provenanceNote: 'Operating on offline benchmark demonstration sequences pending live IMD DWR feed ingestion.',
    isLive: false,
    isReal: false,
    isDemo: true,
    isClimatology: false,
    isPending: false
  },
  {
    id: 'lightning_wglc',
    name: 'WGLC Lightning Climatology',
    shortCode: 'WGLC',
    source: 'World Gridded Climatology',
    productId: 'WGLC_MONTHLY_V1',
    statusType: 'REAL_CLIMATOLOGY',
    statusBadge: 'Monthly Climatology',
    statusTheme: 'blue', // blue badge for climatology
    description: 'High-resolution 0.5° gridded monthly mean flash density (flashes/km²/month) derived from long-term 2010–2020 sensors.',
    resolution: '0.50° grid (~50 km) · Monthly Mean',
    role: 'Auxiliary static background baseline providing geographic and seasonal strike propensity.',
    provenanceNote: 'Verified 2010–2020 monthly climatological average. Explicitly NOT an instantaneous or real-time strike observation.',
    isLive: false,
    isReal: true,
    isDemo: false,
    isClimatology: true,
    isPending: false
  },
  {
    id: 'nwp_era5',
    name: 'ERA5 Atmospheric Reanalysis',
    shortCode: 'ECMWF ERA5',
    source: 'Copernicus ECMWF CDS',
    productId: 'SYNTHETIC_ERA5_BENCHMARK_V1',
    statusType: 'SYNTHETIC_DATA',
    statusBadge: 'Benchmark Simulation',
    statusTheme: 'amber',
    description: 'Hourly atmospheric soundings supplying thermodynamic instability: CAPE (J/kg), CIN, bulk vertical wind shear, and moisture.',
    resolution: '0.25° grid (~25 km) · 1 Hour',
    role: 'Environmental convective instability fields & synoptic steering flow background.',
    provenanceNote: 'Mathematical synthetic test field for offline pipeline verification. Genuine ECMWF CDS retrievals require user .cdsapirc.',
    isLive: false,
    isReal: false,
    isDemo: true,
    isClimatology: false,
    isPending: false
  },
  {
    id: 'imerg_precipitation',
    name: 'NASA GPM IMERG Precipitation',
    shortCode: 'GPM IMERG',
    source: 'NASA GES DISC / Earthdata',
    productId: 'SYNTHETIC_IMERG_BENCHMARK_V1',
    statusType: 'SYNTHETIC_DATA',
    statusBadge: 'Benchmark Simulation',
    statusTheme: 'amber',
    description: 'Half-hourly calibrated multi-satellite surface precipitation rate fields (mm/hr) for convective proxy validation.',
    resolution: '0.10° grid (~11 km) · 30 Min',
    role: 'Surface rain rate predictor & historical convective initiation validation.',
    provenanceNote: 'Mathematical synthetic test field for offline pipeline verification. Genuine GPM IMERG retrievals require Earthdata .netrc.',
    isLive: false,
    isReal: false,
    isDemo: true,
    isClimatology: false,
    isPending: false
  }
];

export function getModalityProvenance(modalityId) {
  return MODALITY_PROVENANCE_CARDS.find(m => m.id === modalityId) || null;
}

export function getAllProvenanceCards() {
  return MODALITY_PROVENANCE_CARDS;
}
