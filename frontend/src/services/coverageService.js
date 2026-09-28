/**
 * STORMTRACE Coverage Service
 * Evaluates geographic bounding boxes and coordinates against sensor coverage tiers.
 */

export const COVERAGE_TIERS = {
  FULL: 'FULL',                   // Radar (34 DWR) + Lightning + Satellite (INSAT-3DR) + ConvLSTM Model
  SATELLITE_ONLY: 'SATELLITE_ONLY', // Satellite Cloud-Top (GPM / Himawari / Meteosat), No DWR radar or lightning
  NO_COVERAGE: 'NO_COVERAGE'       // Out of geostationary convective processing domain
};

// Known regional bounding boxes [minLon, minLat, maxLon, maxLat]
export const REGIONAL_BOUNDS = {
  INDIA: {
    bbox: [68.0, 6.5, 97.5, 37.5],
    tier: COVERAGE_TIERS.FULL,
    name: 'India (Operational Core)',
    dwrStations: 34,
    description: 'Full 34-station Doppler weather radar mosaic, lightning detection network, INSAT-3DR satellite, and ConvLSTM nowcasting.'
  },
  SE_ASIA: {
    bbox: [95.0, -11.0, 141.0, 20.0],
    tier: COVERAGE_TIERS.SATELLITE_ONLY,
    name: 'Southeast Asia (Jakarta / Bangkok / Singapore)',
    dwrStations: 0,
    description: 'Satellite thermal infrared (TIR1) cloud-top monitoring active. Doppler radar and lightning feeds are in onboarding.'
  },
  EAST_AFRICA: {
    bbox: [28.0, -12.0, 52.0, 15.0],
    tier: COVERAGE_TIERS.SATELLITE_ONLY,
    name: 'East Africa (Nairobi / Addis Ababa)',
    dwrStations: 0,
    description: 'NASA GPM precipitation and geostationary satellite imagery active. Local radar composites pending integration.'
  },
  EUROPE: {
    bbox: [-15.0, 35.0, 40.0, 65.0],
    tier: COVERAGE_TIERS.SATELLITE_ONLY,
    name: 'Europe (London / Paris / Berlin)',
    dwrStations: 0,
    description: 'Satellite cloud-top monitoring active. Local radar networks operate under separate national systems.'
  },
  AMERICAS: {
    bbox: [-130.0, -55.0, -35.0, 50.0],
    tier: COVERAGE_TIERS.SATELLITE_ONLY,
    name: 'Americas (New York / São Paulo)',
    dwrStations: 0,
    description: 'Geostationary satellite imagery available. Radar nowcasting scoped to India operational domain.'
  }
};

/**
 * Check coverage tier for given coordinates or bounding box
 */
export function getCoverageStatus(lon, lat) {
  // India Domain Check
  if (lon >= 68.0 && lon <= 97.5 && lat >= 6.5 && lat <= 37.5) {
    return {
      tier: COVERAGE_TIERS.FULL,
      name: 'India (Operational Core)',
      hasRadar: true,
      hasLightning: true,
      hasSatellite: true,
      hasModelInference: true,
      message: 'Full operational coverage active.'
    };
  }

  // Southeast Asia Check
  if (lon >= 95.0 && lon <= 141.0 && lat >= -11.0 && lat <= 20.0) {
    return {
      tier: COVERAGE_TIERS.SATELLITE_ONLY,
      name: 'Southeast Asia',
      hasRadar: false,
      hasLightning: false,
      hasSatellite: true,
      hasModelInference: false,
      message: 'STORMTRACE currently has full radar and lightning coverage for India. Other regions show satellite-only data until additional feeds are connected.'
    };
  }

  // East Africa Check
  if (lon >= 28.0 && lon <= 52.0 && lat >= -12.0 && lat <= 15.0) {
    return {
      tier: COVERAGE_TIERS.SATELLITE_ONLY,
      name: 'East Africa',
      hasRadar: false,
      hasLightning: false,
      hasSatellite: true,
      hasModelInference: false,
      message: 'STORMTRACE currently has full radar and lightning coverage for India. Other regions show satellite-only data until additional feeds are connected.'
    };
  }

  // Global Convective Belt (Tropics / Mid-latitudes)
  if (lat >= -55.0 && lat <= 65.0) {
    return {
      tier: COVERAGE_TIERS.SATELLITE_ONLY,
      name: 'Global Satellite Domain',
      hasRadar: false,
      hasLightning: false,
      hasSatellite: true,
      hasModelInference: false,
      message: 'Satellite cloud-top monitoring active. Doppler radar nowcasting currently operational for India.'
    };
  }

  // Out of domain
  return {
    tier: COVERAGE_TIERS.NO_COVERAGE,
    name: 'Out of Coverage',
    hasRadar: false,
    hasLightning: false,
    hasSatellite: false,
    hasModelInference: false,
    message: 'No live meteorological data available for this region.'
  };
}
