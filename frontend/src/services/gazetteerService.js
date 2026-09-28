/**
 * STORMTRACE Gazetteer & Geographic Coverage Verification Service
 * Strictly distinguishes between the active Regional East India nowcasting domain
 * (83.5°E - 89.8°E, 20.0°N - 26.3°N) and recognized outer/global locations where
 * convective nowcast radar data is currently unavailable.
 */

export const REGIONAL_NOWCAST_BOUNDS = {
  minLon: 83.5,
  maxLon: 89.8,
  minLat: 20.0,
  maxLat: 26.3,
  name: 'Regional East India Domain',
  states: 'West Bengal, Odisha, Jharkhand, Gangetic Basin',
  description: 'Active 64x64 grid (~11 km resolution) with convective initiation, TITAN tracking, and +15m to +120m nowcast predictions.'
};

export const DOMAIN_STATUS = {
  SUPPORTED_NOWCAST: 'SUPPORTED_NOWCAST',
  RECOGNIZED_UNAVAILABLE: 'RECOGNIZED_UNAVAILABLE',
  UNKNOWN: 'UNKNOWN'
};

export const GAZETTEER_LOCATIONS = [
  // --- IN-DOMAIN LOCATIONS (Regional East India 83.5°E - 89.8°E, 20.0°N - 26.3°N) ---
  { 
    id: 'kolkata',
    name: 'Kolkata, West Bengal, India', 
    shortName: 'Kolkata', 
    lon: 88.3639, 
    lat: 22.5726, 
    zoom: 8.5, 
    inDomain: true,
    region: 'West Bengal',
    airport: 'Kolkata NSCBI Airport (CCU)'
  },
  { 
    id: 'ranchi',
    name: 'Ranchi, Jharkhand, India', 
    shortName: 'Ranchi', 
    lon: 85.3096, 
    lat: 23.3441, 
    zoom: 8.5, 
    inDomain: true,
    region: 'Jharkhand',
    airport: 'Birsa Munda Airport (IXR)'
  },
  { 
    id: 'bhubaneswar',
    name: 'Bhubaneswar, Odisha, India', 
    shortName: 'Bhubaneswar', 
    lon: 85.8245, 
    lat: 20.2961, 
    zoom: 8.5, 
    inDomain: true,
    region: 'Odisha',
    airport: 'Biju Patnaik Airport (BBI)'
  },
  { 
    id: 'durgapur',
    name: 'Durgapur, West Bengal, India', 
    shortName: 'Durgapur', 
    lon: 87.3119, 
    lat: 23.5204, 
    zoom: 8.5, 
    inDomain: true,
    region: 'West Bengal',
    airport: 'Kazi Nazrul Islam Airport (RDP)'
  },
  { 
    id: 'asansol',
    name: 'Asansol, West Bengal, India', 
    shortName: 'Asansol', 
    lon: 86.9842, 
    lat: 23.6889, 
    zoom: 8.5, 
    inDomain: true,
    region: 'West Bengal',
    airport: 'Kazi Nazrul Islam Airport (RDP)'
  },
  { 
    id: 'cuttack',
    name: 'Cuttack, Odisha, India', 
    shortName: 'Cuttack', 
    lon: 85.8830, 
    lat: 20.4625, 
    zoom: 8.5, 
    inDomain: true,
    region: 'Odisha',
    airport: 'Biju Patnaik Airport (BBI)'
  },
  { 
    id: 'jamshedpur',
    name: 'Jamshedpur, Jharkhand, India', 
    shortName: 'Jamshedpur', 
    lon: 86.1821, 
    lat: 22.8046, 
    zoom: 8.5, 
    inDomain: true,
    region: 'Jharkhand',
    airport: 'Sonari Airport (IXW)'
  },
  { 
    id: 'kharagpur',
    name: 'Kharagpur, West Bengal, India', 
    shortName: 'Kharagpur', 
    lon: 87.3215, 
    lat: 22.3460, 
    zoom: 8.5, 
    inDomain: true,
    region: 'West Bengal',
    airport: 'Kolkata NSCBI Airport (CCU)'
  },
  { 
    id: 'purulia',
    name: 'Purulia, West Bengal, India', 
    shortName: 'Purulia', 
    lon: 86.3652, 
    lat: 23.3322, 
    zoom: 8.5, 
    inDomain: true,
    region: 'West Bengal',
    airport: 'Birsa Munda Airport (IXR)'
  },
  { 
    id: 'balasore',
    name: 'Balasore, Odisha, India', 
    shortName: 'Balasore', 
    lon: 86.9324, 
    lat: 21.4934, 
    zoom: 8.5, 
    inDomain: true,
    region: 'Odisha',
    airport: 'Biju Patnaik Airport (BBI)'
  },

  // --- OUT-OF-DOMAIN LOCATIONS (Recognized in gazetteer, but nowcast data unavailable) ---
  { 
    id: 'chennai',
    name: 'Chennai, Tamil Nadu, India', 
    shortName: 'Chennai', 
    lon: 80.2707, 
    lat: 13.0827, 
    zoom: 8.5, 
    inDomain: false,
    region: 'Tamil Nadu / South India',
    tier: 'SATELLITE_ONLY'
  },
  { 
    id: 'mumbai',
    name: 'Mumbai, Maharashtra, India', 
    shortName: 'Mumbai', 
    lon: 72.8777, 
    lat: 19.0760, 
    zoom: 8.5, 
    inDomain: false,
    region: 'Maharashtra / West India',
    tier: 'SATELLITE_ONLY'
  },
  { 
    id: 'delhi',
    name: 'Delhi NCR, India', 
    shortName: 'Delhi', 
    lon: 77.1025, 
    lat: 28.7041, 
    zoom: 8.5, 
    inDomain: false,
    region: 'Northern India',
    tier: 'SATELLITE_ONLY'
  },
  { 
    id: 'bengaluru',
    name: 'Bengaluru, Karnataka, India', 
    shortName: 'Bengaluru', 
    lon: 77.5946, 
    lat: 12.9716, 
    zoom: 8.5, 
    inDomain: false,
    region: 'Karnataka / South India',
    tier: 'SATELLITE_ONLY'
  },
  { 
    id: 'hyderabad',
    name: 'Hyderabad, Telangana, India', 
    shortName: 'Hyderabad', 
    lon: 78.4867, 
    lat: 17.3850, 
    zoom: 8.5, 
    inDomain: false,
    region: 'Telangana',
    tier: 'SATELLITE_ONLY'
  },
  { 
    id: 'singapore',
    name: 'Singapore', 
    shortName: 'Singapore', 
    lon: 103.8198, 
    lat: 1.3521, 
    zoom: 8.5, 
    inDomain: false,
    region: 'Southeast Asia',
    tier: 'SATELLITE_ONLY'
  },
  { 
    id: 'dubai',
    name: 'Dubai, United Arab Emirates', 
    shortName: 'Dubai', 
    lon: 55.2708, 
    lat: 25.2048, 
    zoom: 8.5, 
    inDomain: false,
    region: 'Middle East',
    tier: 'SATELLITE_ONLY'
  },
  { 
    id: 'london',
    name: 'London, United Kingdom', 
    shortName: 'London', 
    lon: -0.1276, 
    lat: 51.5074, 
    zoom: 8.0, 
    inDomain: false,
    region: 'Europe',
    tier: 'SATELLITE_ONLY'
  },
  { 
    id: 'jakarta',
    name: 'Jakarta, Indonesia', 
    shortName: 'Jakarta', 
    lon: 106.8456, 
    lat: -6.2088, 
    zoom: 8.0, 
    inDomain: false,
    region: 'Southeast Asia',
    tier: 'SATELLITE_ONLY'
  },
  { 
    id: 'sydney',
    name: 'Sydney, Australia', 
    shortName: 'Sydney', 
    lon: 151.2093, 
    lat: -33.8688, 
    zoom: 8.0, 
    inDomain: false,
    region: 'Australia',
    tier: 'SATELLITE_ONLY'
  }
];

/**
 * Check whether geographic coordinates fall inside the active nowcast domain
 */
export function isLocationInNowcastDomain(lon, lat) {
  return (
    lon >= REGIONAL_NOWCAST_BOUNDS.minLon &&
    lon <= REGIONAL_NOWCAST_BOUNDS.maxLon &&
    lat >= REGIONAL_NOWCAST_BOUNDS.minLat &&
    lat <= REGIONAL_NOWCAST_BOUNDS.maxLat
  );
}

/**
 * Search the gazetteer for matching locations and evaluate domain coverage
 */
export function searchGazetteer(query) {
  if (!query || typeof query !== 'string' || query.trim().length === 0) {
    return [];
  }

  const q = query.toLowerCase().trim();

  return GAZETTEER_LOCATIONS.filter(loc => {
    return (
      loc.name.toLowerCase().includes(q) ||
      loc.shortName.toLowerCase().includes(q) ||
      (loc.region && loc.region.toLowerCase().includes(q))
    );
  }).map(loc => {
    const inDomain = isLocationInNowcastDomain(loc.lon, loc.lat);
    return {
      ...loc,
      inDomain,
      status: inDomain ? DOMAIN_STATUS.SUPPORTED_NOWCAST : DOMAIN_STATUS.RECOGNIZED_UNAVAILABLE,
      statusLabel: inDomain 
        ? 'Active Nowcast Domain (East India)' 
        : 'Location Recognized · Nowcast Data Unavailable'
    };
  });
}

/**
 * Check coverage details for a specific location object or coordinates
 */
export function evaluateLocationCoverage(locOrLon, lat = null) {
  let lon, latitude, name;
  if (typeof locOrLon === 'object' && locOrLon !== null) {
    lon = locOrLon.lon;
    latitude = locOrLon.lat;
    name = locOrLon.name || locOrLon.shortName || 'Specified Location';
  } else {
    lon = locOrLon;
    latitude = lat;
    name = `${latitude.toFixed(2)}°N, ${lon.toFixed(2)}°E`;
  }

  const inDomain = isLocationInNowcastDomain(lon, latitude);

  if (inDomain) {
    return {
      status: DOMAIN_STATUS.SUPPORTED_NOWCAST,
      inDomain: true,
      name,
      lon,
      lat: latitude,
      headline: 'SUPPORTED WEATHER DATA',
      domainName: REGIONAL_NOWCAST_BOUNDS.name,
      details: 'Full convective initiation, TITAN storm cell centroid tracking, radar reflectivity, and +15m to +120m forecast models active.',
      badgeColor: 'emerald'
    };
  }

  return {
    status: DOMAIN_STATUS.RECOGNIZED_UNAVAILABLE,
    inDomain: false,
    name,
    lon,
    lat: latitude,
    headline: 'LOCATION RECOGNIZED · CONVECTIVE NOWCAST UNAVAILABLE',
    domainName: 'Outside Active Regional Domain',
    details: `STORMTRACE currently has active convective nowcast data for the Regional East India domain (83.5°E–89.8°E, 20.0°N–26.3°N: Kolkata, Ranchi, Bhubaneswar). ${name} is recognized in the global gazetteer, but local radar nowcast data is not yet integrated.`,
    badgeColor: 'amber'
  };
}
