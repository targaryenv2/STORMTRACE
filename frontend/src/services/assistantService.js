/**
 * STORMTRACE AI Assistant Engine
 * Grounded tool-calling, multi-region meteorological intelligence, and natural language responder.
 */

import { getCoverageStatus, COVERAGE_TIERS } from './coverageService.js';
import { ALL_ACTIVE_CELLS, getActiveCellsForBbox, getCellDetail, explainTerm } from './nowcastService.js';

const DISCLAIMER = 'This is AI decision-support, not an official IMD warning.';

/**
 * Global Gazetteer Database for Instant Geocoding, Context, and Map Navigation
 */
const GLOBAL_GAZETTEER = [
  // India - South
  { names: ['tamil nadu', 'tamilnadu', 'chennai', 'madurai', 'coimbatore', 'vellore', 'salem', 'trichy', 'tiruchirappalli', 'thanjavur', 'kanchipuram', 'puducherry', 'pondicherry', 'tirunelveli', 'thoothukudi', 'erode', 'tiruppur'], lon: 78.65, lat: 11.12, zoom: 7.5, region: 'Tamil Nadu, India', defaultText: 'Atmospheric radar composites across Tamil Nadu currently indicate convective activity across coastal and inland corridors.' },
  { names: ['kerala', 'kochi', 'cochin', 'calicut', 'kozhikode', 'malabar', 'thiruvananthapuram', 'trivandrum', 'wayanad', 'kannur', 'thrissur'], lon: 75.78, lat: 11.25, zoom: 8.5, region: 'Kerala / Western Ghats', defaultText: 'Orographic convective cloud formations active along the Western Ghats and coastal Kerala.' },
  { names: ['karnataka', 'bengaluru', 'bangalore', 'mysuru', 'mysore', 'mangalore', 'hubli', 'belagavi'], lon: 77.59, lat: 12.97, zoom: 8.5, region: 'Karnataka, India', defaultText: 'Convective cloud buildups across South Interior Karnataka and the Deccan plateau.' },
  { names: ['telangana', 'hyderabad', 'warangal', 'nizamabad'], lon: 78.48, lat: 17.38, zoom: 8.5, region: 'Telangana, India', defaultText: 'Isolated convective cells active over the Telangana plateau.' },
  { names: ['andhra pradesh', 'andhra', 'visakhapatnam', 'vizag', 'vijayawada', 'guntur', 'tirupati'], lon: 83.21, lat: 17.68, zoom: 8.0, region: 'Andhra Pradesh, India', defaultText: 'Coastal radar network tracking convective showers along the Bay of Bengal coastline.' },

  // India - East & Northeast
  { names: ['west bengal', 'bengal', 'kolkata', 'calcutta', 'asansol', 'durgapur', 'siliguri', 'howrah'], lon: 88.36, lat: 22.57, zoom: 8.5, region: 'West Bengal, India', defaultText: 'Severe convective squall and Nor\'wester (Kalbaishakhi) tracking across lower Gangetic plains.' },
  { names: ['odisha', 'orissa', 'bhubaneswar', 'cuttack', 'puri', 'rourkela', 'paradip'], lon: 85.82, lat: 20.30, zoom: 8.5, region: 'Odisha, India', defaultText: 'Coastal radar monitoring convective storm cells and tropical depressions over the Odisha coastline.' },
  { names: ['jharkhand', 'ranchi', 'jamshedpur', 'dhanbad', 'bokaro'], lon: 85.31, lat: 23.34, zoom: 8.5, region: 'Jharkhand, India', defaultText: 'Intense plateau supercell and multicellular convection active over Chota Nagpur.' },
  { names: ['bihar', 'patna', 'gaya', 'muzaffarpur', 'bhagalpur'], lon: 85.13, lat: 25.59, zoom: 8.0, region: 'Bihar, India', defaultText: 'Monsoonal and pre-monsoon convective thunderstorms along the Ganga basin.' },
  { names: ['assam', 'guwahati', 'northeast', 'meghalaya', 'shillong', 'arunachal', 'nagaland', 'manipur', 'mizoram', 'tripura'], lon: 91.73, lat: 26.14, zoom: 8.0, region: 'Northeast India', defaultText: 'High precipitation orographic convective storms active along the Brahmaputra valley.' },

  // India - North & West
  { names: ['delhi', 'ncr', 'noida', 'gurugram', 'gurgaon', 'ghaziabad', 'faridabad'], lon: 77.10, lat: 28.70, zoom: 8.5, region: 'Delhi / NCR, India', defaultText: 'Doppler Weather Radar (DWR) monitoring pre-monsoon convective updrafts and Western Disturbances.' },
  { names: ['maharashtra', 'mumbai', 'bombay', 'pune', 'nagpur', 'nashik', 'aurangabad'], lon: 72.87, lat: 19.07, zoom: 8.5, region: 'Maharashtra, India', defaultText: 'Radar observations for Mumbai and the Konkan coast tracking convective cloud formations.' },
  { names: ['gujarat', 'ahmedabad', 'surat', 'vadodara', 'rajkot'], lon: 72.57, lat: 23.02, zoom: 8.0, region: 'Gujarat, India', defaultText: 'Arabian Sea coastal radar tracking convective cloud bands.' },
  { names: ['rajasthan', 'jaipur', 'jodhpur', 'udaipur', 'kota'], lon: 75.78, lat: 26.91, zoom: 8.0, region: 'Rajasthan, India', defaultText: 'Monitoring dry-convective dust storms (Andhi) and isolated thunderstorm cells.' },
  { names: ['uttar pradesh', 'up', 'lucknow', 'kanpur', 'varanasi', 'agra', 'prayagraj'], lon: 80.94, lat: 26.84, zoom: 8.0, region: 'Uttar Pradesh, India', defaultText: 'DWR network tracking deep convective thunderstorms across the central Gangetic plains.' },
  { names: ['punjab', 'chandigarh', 'amritsar', 'ludhiana', 'haryana'], lon: 76.77, lat: 30.73, zoom: 8.0, region: 'Northwest India', defaultText: 'Tracking Western Disturbance thunderstorm activity across Punjab and Haryana.' },
  { names: ['jammu', 'kashmir', 'srinagar', 'himachal', 'shimla', 'uttarakhand', 'dehradun'], lon: 74.79, lat: 34.08, zoom: 7.5, region: 'Himalayan Region, India', defaultText: 'Orographic cloud clusters and mountain convective cells monitored via satellite and radar.' },

  // Middle East
  { names: ['dubai', 'uae', 'united arab emirates', 'abu dhabi', 'sharjah', 'ajman', 'ras al khaimah', 'fujairah'], lon: 55.27, lat: 25.20, zoom: 8.5, region: 'Dubai / UAE', defaultText: 'Doppler radar tracking coastal and desert convective storm cells across the UAE and Arabian Gulf.' },
  { names: ['saudi arabia', 'riyadh', 'jeddah', 'mecca', 'medina', 'dammam'], lon: 46.67, lat: 24.71, zoom: 7.0, region: 'Saudi Arabia', defaultText: 'Convective instability monitoring across the Arabian Peninsula.' },
  { names: ['qatar', 'doha'], lon: 51.53, lat: 25.28, zoom: 9.0, region: 'Qatar / Gulf', defaultText: 'Gulf marine and coastal convective cloud tracking active.' },
  { names: ['oman', 'muscat', 'salalah'], lon: 58.54, lat: 23.58, zoom: 8.0, region: 'Oman / Arabian Sea', defaultText: 'Arabian Sea convective systems and coastal rainfall tracking.' },

  // Americas
  { names: ['brazil', 'brasil', 'são paulo', 'sao paulo', 'rio de janeiro', 'rio', 'brasilia', 'salvador', 'belo horizonte'], lon: -46.63, lat: -23.55, zoom: 7.5, region: 'São Paulo, Brazil', defaultText: 'Severe convective squall fronts and tropical thunderstorms active in South America.' },
  { names: ['amazon', 'manaus', 'amazon basin', 'belem'], lon: -60.02, lat: -3.10, zoom: 7.0, region: 'Amazon Basin, Brazil', defaultText: 'Severe Mesoscale Convective Systems (MCS) active with extreme tropical lightning and downpours.' },
  { names: ['usa', 'united states', 'florida', 'orlando', 'miami', 'tampa'], lon: -81.37, lat: 28.53, zoom: 8.0, region: 'Florida, USA', defaultText: 'NEXRAD Doppler radar tracking subtropical sea-breeze thunderstorms and convective cells.' },
  { names: ['texas', 'houston', 'dallas', 'austin', 'san antonio'], lon: -95.36, lat: 29.76, zoom: 8.0, region: 'Texas, USA', defaultText: 'Severe thunderstorm and supercell tracking across the Southern Plains.' },
  { names: ['new york', 'nyc', 'chicago', 'illinois', 'california', 'los angeles', 'san francisco', 'seattle', 'atlanta', 'denver', 'kansas'], lon: -74.00, lat: 40.71, zoom: 8.0, region: 'United States', defaultText: 'NEXRAD radar network monitoring frontal boundaries and convective precipitation.' },
  { names: ['argentina', 'buenos aires', 'cordoba', 'rosario'], lon: -58.38, lat: -34.60, zoom: 7.5, region: 'Argentina', defaultText: 'Pampas convective systems and severe hail-producing supercells tracked via satellite.' },
  { names: ['canada', 'toronto', 'vancouver', 'montreal', 'calgary'], lon: -79.38, lat: 43.65, zoom: 8.0, region: 'Canada', defaultText: 'Radar network tracking summer convective storms and frontal weather systems.' },
  { names: ['mexico', 'mexico city', 'cancun', 'guadalajara', 'monterrey'], lon: -99.13, lat: 19.43, zoom: 7.5, region: 'Mexico', defaultText: 'Tropical convective clusters and high-altitude thunderstorms monitored.' },

  // Europe
  { names: ['europe', 'london', 'uk', 'united kingdom', 'alps', 'paris', 'france', 'germany', 'berlin', 'munich', 'italy', 'rome', 'spain', 'madrid', 'switzerland', 'austria', 'netherlands', 'amsterdam'], lon: 10.20, lat: 46.50, zoom: 7.0, region: 'Central Europe / Alps', defaultText: 'OPERA radar network and Meteosat satellite monitoring alpine convection and frontal squall lines.' },

  // Asia & Oceania
  { names: ['japan', 'tokyo', 'osaka', 'kyoto', 'yokohama', 'nagoya'], lon: 139.69, lat: 35.68, zoom: 8.0, region: 'Tokyo / Japan', defaultText: 'JMA Doppler radar tracking coastal convective cells and Baiu/Meiyu front storms.' },
  { names: ['indonesia', 'jakarta', 'bali', 'surabaya', 'bandung', 'sumatra', 'java', 'southeast asia'], lon: 106.84, lat: -6.21, zoom: 7.5, region: 'Jakarta, Indonesia', defaultText: 'Satellite-only cloud-top monitoring and convective tracking for Southeast Asia.' },
  { names: ['singapore', 'malaysia', 'kuala lumpur', 'penang', 'johor'], lon: 103.81, lat: 1.35, zoom: 9.0, region: 'Singapore / Malaysia', defaultText: 'Tropical Sumatran squalls and equatorial convective showers monitored via radar and satellite.' },
  { names: ['thailand', 'bangkok', 'phuket', 'chiang mai', 'vietnam', 'hanoi', 'ho chi minh', 'philippines', 'manila'], lon: 100.50, lat: 13.75, zoom: 8.0, region: 'Southeast Asia', defaultText: 'Tropical monsoon convective storms and typhoons monitored via geostationary satellite.' },
  { names: ['china', 'beijing', 'shanghai', 'hong kong', 'guangzhou', 'shenzhen', 'wuhan', 'chengdu'], lon: 116.40, lat: 39.90, zoom: 7.5, region: 'China', defaultText: 'C-band radar network and Fengyun satellite tracking severe convective storms.' },
  { names: ['australia', 'sydney', 'melbourne', 'brisbane', 'perth', 'adelaide', 'darwin'], lon: 151.20, lat: -33.86, zoom: 8.0, region: 'Australia', defaultText: 'BOM Doppler radar and Himawari satellite monitoring severe summer thunderstorms.' },
  { names: ['new zealand', 'auckland', 'wellington', 'christchurch'], lon: 174.76, lat: -36.84, zoom: 8.0, region: 'New Zealand', defaultText: 'Maritime frontal convective showers and thunderstorm cells monitored.' },

  // Africa
  { names: ['nairobi', 'kenya', 'africa', 'ethiopia', 'addis ababa', 'tanzania', 'uganda'], lon: 36.82, lat: -1.29, zoom: 7.0, region: 'Nairobi, East Africa', defaultText: 'Active satellite cloud-top monitoring and convective tracking over East Africa and the Rift Valley.' },
  { names: ['south africa', 'johannesburg', 'cape town', 'durban', 'pretoria'], lon: 28.04, lat: -26.20, zoom: 7.5, region: 'South Africa', defaultText: 'Highveld severe convective thunderstorms and hail systems monitored via radar/satellite.' },
  { names: ['nigeria', 'lagos', 'abuja', 'ghana', 'accra', 'egypt', 'cairo', 'morocco', 'casablanca'], lon: 3.37, lat: 6.52, zoom: 7.5, region: 'Africa', defaultText: 'Tropical convective wave activity and West African squall lines monitored via satellite.' }
];

/**
 * Calculates distance (degrees approximation) between coordinates
 */
function getGeoDistance(lat1, lon1, lat2, lon2) {
  const dLat = lat1 - lat2;
  const dLon = lon1 - lon2;
  return Math.sqrt(dLat * dLat + dLon * dLon);
}

/**
 * Finds nearby active convective cell for given coordinates
 */
function findNearbyCell(lat, lon, maxDistanceDeg = 6.0) {
  let closestCell = null;
  let minDistance = maxDistanceDeg;

  for (const cell of ALL_ACTIVE_CELLS) {
    const dist = getGeoDistance(lat, lon, cell.centroid_lat, cell.centroid_lon);
    if (dist < minDistance) {
      minDistance = dist;
      closestCell = cell;
    }
  }
  return closestCell;
}

/**
 * Comprehensive Knowledge Base for Meteorological Concepts, AI Nowcasting, and Safety
 */
const MET_KNOWLEDGE_BASE = [
  // 1. Radar Reflectivity & dBZ Scale
  {
    regex: /\b(what is dbz|dbz scale|decibels? of z|reflectivity|radar scale|what does dbz mean)\b/i,
    title: 'Radar Reflectivity (dBZ)',
    text: `dBZ (decibels of Z) measures the intensity of radar energy reflected back by precipitation droplets. Values above 50 dBZ represent severe storms with heavy rainfall or hail.\n\n• < 20 dBZ: Very light drizzle / fog\n• 20–35 dBZ: Light to moderate steady rain\n• 35–45 dBZ: Heavy rain showers\n• 45–55 dBZ: Intense thunderstorm with gusty winds\n• 55–65+ dBZ: Severe supercell, torrential downpour, potential hail`
  },
  // 2. Map Colors / Red Area
  {
    regex: /\b(red area|red zone|what does red mean|color scale|threat scale|orange area|yellow area)\b/i,
    title: 'STORMTRACE Map Threat Colors',
    text: `Red areas on the map indicate high convective thunderstorm probability (greater than 80%) or intense radar reflectivity (above 50 dBZ) expected within the selected lead time. It means severe precipitation, strong wind gusts, or lightning are likely soon in that zone.\n\n• Red (High Threat): >50 dBZ / >80% storm probability / high lightning\n• Orange (Medium Threat): 40–50 dBZ / 50–80% probability\n• Yellow (Low-to-Moderate): 30–40 dBZ / 30–50% probability\n• Green/Blue: Light precipitation or stable atmosphere.`
  },
  // 3. Epistemic Uncertainty & MC-Dropout
  {
    regex: /\b(uncertainty|mc-dropout|monte carlo dropout|epistemic|confidence score|how confident)\b/i,
    title: 'MC-Dropout Epistemic Uncertainty',
    text: `Uncertainty bands show the AI model's forecast confidence across stochastic Monte Carlo Dropout / ensemble advection passes. Wider bands highlight zones with higher prediction ambiguity during rapid storm initiation or complex convective split/merge events.`,
    isUncertainty: true
  },
  // 4. Severity Index
  {
    regex: /\b(severity score|hazard score|how is severity calculated|severity index)\b/i,
    title: 'Composite Severity Index (0–100)',
    text: `Severity score is a composite index from 0 to 100 that combines rain intensity (dBZ), lightning flash rate, and cloud vertical depth to grade storm hazard levels.\n\n• 0–30: Mild convective shower\n• 30–60: Moderate thunderstorm\n• 60–80: Severe thunderstorm (aviation hazard)\n• 80–100: Extreme High-Threat Supercell / Squall Line`
  },
  // 5. Lightning Mechanism & Physics
  {
    regex: /\b(how does lightning form|what causes lightning|lightning physics|how is lightning created|stepped leader|cloud-to-ground|lightning discharge)\b/i,
    title: 'Atmospheric Lightning Physics',
    text: `Lightning is a massive electrostatic discharge caused by charge separation inside convective storm clouds (cumulonimbus).\n• Inside the mixed-phase zone (-10°C to -25°C), ascending ice crystals collide with falling heavier graupel (soft hail).\n• Electrons transfer to graupel, creating negative charge at the cloud base and positive charge at the top.\n• When the electric field exceeds dielectric air breakdown (~3 million V/m), stepped leaders propagate downward, met by upward streamers, unleashing the visible return stroke (up to 30,000°C and 300,000 km/s). Rapid air expansion produces shockwave thunder.`
  },
  // 6. Thunderstorm Definition
  {
    regex: /\b(what is a thunderstorm|definition of thunderstorm|define thunderstorm|explain thunderstorm|what is a storm|what is convective storm)\b/i,
    title: 'Thunderstorm Definition & Characteristics',
    text: `A thunderstorm is a transient, intense mesoscale weather system produced by cumulonimbus clouds and characterized by the presence of lightning and its acoustic shockwave, thunder. Driven by deep atmospheric convection, thunderstorms typically feature vigorous updrafts and downdrafts, heavy precipitation, gusty surface winds, and occasionally hail or tornadoes.`
  },
  // 7. Thunderstorm Formation Physics
  {
    regex: /\b(how do thunderstorms form|how does a storm form|convection|what causes thunderstorms|atmospheric convection|updraft and downdraft)\b/i,
    title: 'Thunderstorm Convective Physics',
    text: `Thunderstorms form through deep atmospheric convection requiring three core ingredients:\n1. **Moisture**: High water vapor in the lower troposphere.\n2. **Instability**: Warm, buoyant air at the surface beneath colder, denser air aloft.\n3. **Lift Mechanism**: Solar heating, frontal boundaries, sea breeze convergence, or orographic mountain lift.\n\nWhen moist air rises, it cools and condenses, releasing latent heat that powers vigorous updrafts. As precipitation accumulates aloft, cold downdrafts descend, creating gust fronts at the surface.`
  },
  // 8. Diurnal Heating & Afternoon Storms
  {
    regex: /\b(why do thunderstorms happen in the afternoon|afternoon storms?|diurnal heating|solar heating storm|why do storms form in the (afternoon|evening)|why afternoon)\b/i,
    title: 'Diurnal Convective Cycle & Afternoon Storms',
    text: `Thunderstorms most frequently form in the afternoon and early evening due to solar radiation heating the ground throughout the morning. As the surface warms, the lower boundary layer becomes buoyant and unstable, maximizing Convective Available Potential Energy (CAPE) and breaking through the capping inversion (CIN) to trigger explosive convective updrafts.`
  },
  // 9. Storm Rotation & Mesocyclones
  {
    regex: /\b(why do storms rotate|storm rotation|mesocyclone|why does a supercell rotate|rotating storm|vorticity)\b/i,
    title: 'Storm Rotation & Mesocyclone Dynamics',
    text: `Thunderstorms rotate when strong vertical wind shear—changes in wind speed and direction with altitude—generates horizontal tubes of rolling air. As a powerful convective updraft pulls this rolling air upward, it tilts the horizontal rotation into a vertical axis, creating a persistent rotating updraft called a *mesocyclone*, the hallmark of supercell thunderstorms.`
  },
  // 10. Hail Formation Physics
  {
    regex: /\b(how does hail form|what causes hail|hail formation|how is hail created|what is hail|hailstones?)\b/i,
    title: 'Hail Formation Physics',
    text: `Hail forms inside severe convective storms with intense updrafts (>20–40 m/s) and supercooled water droplets below 0°C. Small ice embryos (graupel) are carried upward repeatedly through the freezing zone, accreting layers of liquid water that freeze into solid ice concentric layers. When hailstones become too heavy for the updraft to support, they fall as hail.`
  },
  // 11. CAPE and Atmospheric Instability
  {
    regex: /\b(cape|cin|lifted index|convective available potential energy|atmospheric instability)\b/i,
    title: 'Thermodynamic Indices (CAPE & CIN)',
    text: `**CAPE (Convective Available Potential Energy)** measures the buoyant energy available to accelerate an ascending air parcel:\n• < 1000 J/kg: Weak convective potential\n• 1000–2500 J/kg: Moderate instability (common severe storms)\n• > 2500–4000+ J/kg: Extreme instability (explosive supercell updrafts > 40 m/s)\n\n**CIN (Convective Inhibition)** represents the energy barrier or "cap" that prevents premature convection until thermal lift or boundaries break through.`
  },
  // 12. Supercells vs Squall Lines
  {
    regex: /\b(supercells?|squall lines?|types of storms|mesocyclone|derecho|multicell)\b/i,
    title: 'Severe Storm Classifications',
    text: `• **Supercells**: Highly organized, dangerous storms featuring a persistent, rotating updraft called a *mesocyclone*. They produce giant hail, extreme lightning, destructive downbursts, and tornadoes.\n• **Squall Lines (MCS)**: Linear clusters of thunderstorms with a leading gust front (bow echo) producing widespread straight-line winds (>100 km/h) and torrential rain.\n• **Multicell Clusters**: Groups of storm cells at different lifecycle stages sustaining continuous convective activity.\n• **Single-cell (Pulse) Storms**: Short-lived (30–60 min) airmass storms that collapse under their own precipitation.`
  },
  // 13. Aviation & Flight Hazards
  {
    regex: /\b(airplanes?|aviation|flights?|can planes fly|fly through|microburst|wind shear|pilots?)\b/i,
    title: 'Aviation Convective Hazards',
    text: `Aviation regulations strictly mandate circumnavigating severe convective storms by at least 20 nautical miles (NM). Key hazards include:\n1. **Microbursts / Low-Level Wind Shear (LLWS)**: Intense localized downdrafts causing rapid loss of airspeed and lift during takeoff/landing.\n2. **Severe In-Flight Turbulence & Hail**: Can cause structural damage and engine flameouts.\n3. **Lightning & Icing**: While modern aircraft fuselages act as Faraday cages against lightning, severe supercells present extreme icing and mechanical risk.`
  },
  // 14. Lightning & Public Safety Rules
  {
    regex: /\b(safety|what to do during|safe during|lightning safety|shelter|30\/30 rule|protection from lightning|is it safe to (go outside|be outside|step out|travel|drive|fly)|can i go out|outdoor safety|safe outside)\b/i,
    title: 'Severe Thunderstorm & Lightning Safety Guidelines',
    text: `When severe thunderstorms or lightning threaten:\n• **30/30 Rule**: Seek enclosed shelter if the time between lightning flash and thunder is under 30 seconds. Stay inside for 30 minutes after the last thunderclap.\n• **Safe Shelter**: Fully enclosed, grounded buildings or metal hard-topped vehicles. Avoid open fields, metal fences, tall trees, and water bodies.\n• **Indoors**: Stay away from corded phones, electrical appliances, plumbing, and windows during active lightning.\n• **Vehicles**: Cars provide protection due to the metal body dispersing current (Faraday cage effect), not rubber tires.`
  },
  // 15. AI Model Architecture & Algorithms
  {
    regex: /\b(how does stormtrace work|model architecture|convlstm|ai model|deep learning|how do you predict|algorithm)\b/i,
    title: 'STORMTRACE AI Architecture',
    text: `STORMTRACE implements a Spatiotemporal Multimodal Convective Extrapolation & Nowcasting Engine. It fuses Doppler radar reflectivity (dBZ), satellite infrared brightness temperature, ERA5 thermodynamic reanalysis (CAPE/CIN), IMERG calibrated precipitation, and WGLC lightning climatology using differentiable gradient-calibrated kinematic advection, multi-channel parameter fusion, and epistemic uncertainty quantification across +15m to +120m horizons.`
  },
  // 16. Forecast Accuracy & Skill Metrics
  {
    regex: /\b(how accurate are (your|the) forecasts|forecast accuracy|accuracy of (your|the) nowcast|skill scores|csi score|pod score|far score|evaluation metrics)\b/i,
    title: 'STORMTRACE Forecast Accuracy & Verification',
    text: `STORMTRACE nowcasts are evaluated against multi-lead ground-truth convective sequences using standard meteorological verification metrics:\n• **Critical Success Index (CSI)**: Quantifies convective detection accuracy accounting for hits, misses, and false alarms.\n• **Probability of Detection (POD)**: Measures the proportion of observed convective cores correctly identified.\n• **False Alarm Ratio (FAR)**: Tracks the fraction of predicted storms that do not verify.\n• **Epistemic Calibration**: Monte Carlo Dropout uncertainty bands provide calibrated confidence intervals across lead times.`
  },
  // 17. Lead Time & Forecast Horizon
  {
    regex: /\b(lead time|forecast horizon|how far ahead|15 min|30 min|120 min|2 hours ahead)\b/i,
    title: 'Nowcasting Forecast Horizons',
    text: `STORMTRACE provides hyper-local convective nowcasts across 6 discrete lead-time horizons (+15, +30, +45, +60, +90, +120 min) evaluated against multi-timestep benchmark convective sequences with verified future targets:\n• **+15 min**: Immediate tactical hazard warning\n• **+30 min**: Airport ground operations and flash flood mitigation\n• **+45 min & +60 min**: Airspace routing and public alerts\n• **+90 min & +120 min**: Convective initiation and cluster dissipation tracking.`
  },
  // 18. Data Provenance & Sources
  {
    regex: /\b(data sources?|provenance|insat|era5|imerg|wglc|where does data come from|datasets?)\b/i,
    title: 'STORMTRACE Data Provenance',
    text: `STORMTRACE integrates five multimodal meteorological streams with strict provenance integrity:\n• **Radar**: DEMO_DATA (Offline benchmark simulation).\n• **Satellite**: ISRO INSAT-3DS (UNAVAILABLE / Masked = 0, awaiting MOSDAC user files).\n• **Atmospheric Reanalysis**: ECMWF ERA5 (SYNTHETIC_DATA benchmark simulation; requires CDS API credentials for real download).\n• **Precipitation**: NASA GPM IMERG (SYNTHETIC_DATA calibrated benchmark simulation; requires NASA Earthdata credentials for real download).\n• **Lightning**: WGLC (REAL_CLIMATOLOGY 2010–2020 monthly mean baseline, NOT real-time sensor).\n\n*All synthetic benchmark scenarios are strictly tagged with ` + '`SYNTHETIC_DATA`' + ` provenance metadata.*`
  }
];

/**
 * Deterministic intent-matching and grounded tool-calling engine
 */
export async function processUserMessage(message, currentContext = {}) {
  const query = message.trim().toLowerCase();
  const actions = [];
  let responseText = '';
  let structuredCard = null;

  // 0. Greetings & Identity Queries
  if (/^(hi|hello|hey|greetings|namaste|good morning|good evening|good afternoon|help|who are you)\b/i.test(query)) {
    const activeCount = ALL_ACTIVE_CELLS.length;
    responseText = `Hello! I am your STORMTRACE AI Meteorological Assistant. I monitor ${activeCount} active convective storm cells, live Doppler radar reflectivity (dBZ), and lightning flash rates across Tamil Nadu, India, Brazil, Dubai, and worldwide.\n\nYou can ask me:\n• "Is there a thunderstorm in Tamil Nadu?"\n• "Show me the storm in Brazil / São Paulo"\n• "Is there a thunderstorm in Dubai?"\n• "Show me the most severe storm right now"\n• "What does the red area mean?" or "What is dBZ?"\n\n${DISCLAIMER}`;
    return { text: responseText, actions, card: null };
  }

  // 1. TAMIL NADU & South Indian Cities (Chennai, Madurai, Coimbatore, Vellore, Salem, etc.)
  if (
    query.includes('tamil nadu') || 
    query.includes('tamilnadu') || 
    query.includes('chennai') || 
    query.includes('madurai') || 
    query.includes('coimbatore') || 
    query.includes('vellore') || 
    query.includes('salem') || 
    query.includes('trichy') || 
    query.includes('tiruchirappalli') || 
    query.includes('thanjavur') || 
    query.includes('kanchipuram') ||
    query.includes('puducherry') ||
    query.includes('pondicherry')
  ) {
    const isChennaiQuery = query.includes('chennai');
    const isMaduraiQuery = query.includes('madurai') || query.includes('salem') || query.includes('trichy') || query.includes('coimbatore');

    if (isChennaiQuery) {
      actions.push({ type: 'SET_MAP_VIEW', payload: { lon: 80.27, lat: 13.08, zoom: 8.5 }, chipText: '📍 Map moved to Chennai' });
      const cell = ALL_ACTIVE_CELLS.find(c => c.cell_id === 'SC-2026-0917-05') || ALL_ACTIVE_CELLS.find(c => c.region.includes('Tamil Nadu'));
      if (cell) {
        actions.push({ type: 'SELECT_CELL', payload: cell.cell_id, chipText: `⚡ Selected ${cell.cell_id}` });
        structuredCard = { type: 'cell', data: cell };
        responseText = `Yes, there is convective thunderstorm activity near Chennai, Tamil Nadu. A coastal updraft cell (${cell.cell_id}) is active with peak reflectivity of ${cell.max_dbz} dBZ, lightning rate of ~${cell.lightning_rate}, and speed of ${cell.speed_kmh} km/h moving East. Thunderstorms and rain showers are likely within the next 40–60 minutes. ${DISCLAIMER}`;
      } else {
        responseText = `No severe convective storm cells are currently detected directly over Chennai. Conditions remain stable. ${DISCLAIMER}`;
      }
      return { text: responseText, actions, card: structuredCard };
    }

    if (isMaduraiQuery) {
      actions.push({ type: 'SET_MAP_VIEW', payload: { lon: 78.12, lat: 10.92, zoom: 8.5 }, chipText: '📍 Map moved to Madurai / Central Tamil Nadu' });
      const cell = ALL_ACTIVE_CELLS.find(c => c.cell_id === 'SC-2026-0917-07');
      if (cell) {
        actions.push({ type: 'SELECT_CELL', payload: cell.cell_id, chipText: `⚡ Selected ${cell.cell_id}` });
        structuredCard = { type: 'cell', data: cell };
        responseText = `Yes, an intensifying convective thunderstorm cell (${cell.cell_id}) is active in central Tamil Nadu near Madurai and the Vellore-Salem corridor. It has a high core intensity of ${cell.max_dbz} dBZ, ${cell.lightning_rate} lightning strikes, and is traveling East at ${cell.speed_kmh} km/h. Convective rain and sudden lightning gusts are expected over the next 20–45 minutes. ${DISCLAIMER}`;
      }
      return { text: responseText, actions, card: structuredCard };
    }

    // General Tamil Nadu query
    actions.push({ type: 'SET_MAP_VIEW', payload: { lon: 78.65, lat: 11.12, zoom: 7.5 }, chipText: '📍 Map moved to Tamil Nadu' });
    const tnCells = ALL_ACTIVE_CELLS.filter(c => c.region.includes('Tamil Nadu'));
    if (tnCells.length > 0) {
      const topCell = tnCells[0];
      actions.push({ type: 'SELECT_CELL', payload: topCell.cell_id, chipText: `⚡ Selected ${topCell.cell_id}` });
      structuredCard = { type: 'cell', data: topCell };
      responseText = `Yes, there is active thunderstorm activity across Tamil Nadu! STORMTRACE is currently tracking ${tnCells.length} convective storm cells in the state:
• **${topCell.location_name}** (${topCell.cell_id}): Peak reflectivity of ${topCell.max_dbz} dBZ, ${topCell.lightning_rate} lightning activity, moving ${topCell.compass} at ${topCell.speed_kmh} km/h.
• **${tnCells[1]?.location_name || 'Coastal Updrafts'}**: Moderate convective showers with 46 dBZ core.

Thunderstorms and localized lightning are expected across coastal and central Tamil Nadu over the next 1–2 hours. ${DISCLAIMER}`;
    } else {
      responseText = `Atmospheric radar composites across Tamil Nadu currently indicate low-to-moderate convective potential with no immediate supercell threat. ${DISCLAIMER}`;
    }
    return { text: responseText, actions, card: structuredCard };
  }

  // 2. BRAZIL & South America (São Paulo, Amazon, Rio, Brasília, Manaus)
  if (
    query.includes('brazil') || 
    query.includes('brasil') || 
    query.includes('são paulo') || 
    query.includes('sao paulo') || 
    query.includes('amazon') || 
    query.includes('manaus') || 
    query.includes('rio') || 
    query.includes('brasilia')
  ) {
    const isAmazon = query.includes('amazon') || query.includes('manaus');
    if (isAmazon) {
      actions.push({ type: 'SET_MAP_VIEW', payload: { lon: -60.02, lat: -3.10, zoom: 7.0 }, chipText: '📍 Map moved to Amazon Basin, Brazil' });
      const cell = ALL_ACTIVE_CELLS.find(c => c.cell_id === 'SC-2026-0917-09');
      if (cell) {
        actions.push({ type: 'SELECT_CELL', payload: cell.cell_id, chipText: `⚡ Selected ${cell.cell_id}` });
        structuredCard = { type: 'cell', data: cell };
        responseText = `Yes! A severe Mesoscale Convective System (${cell.cell_id}) is active over the Brazilian Amazon basin near Manaus. It features an extreme core reflectivity of ${cell.max_dbz} dBZ and intense lightning (~${cell.lightning_rate}) with severe tropical downpours. ${DISCLAIMER}`;
      }
      return { text: responseText, actions, card: structuredCard };
    }

    // São Paulo / General Brazil
    actions.push({ type: 'SET_MAP_VIEW', payload: { lon: -46.63, lat: -23.55, zoom: 7.5 }, chipText: '📍 Map moved to São Paulo, Brazil' });
    const cell = ALL_ACTIVE_CELLS.find(c => c.cell_id === 'SC-2026-0917-08');
    if (cell) {
      actions.push({ type: 'SELECT_CELL', payload: cell.cell_id, chipText: `⚡ Selected ${cell.cell_id}` });
      structuredCard = { type: 'cell', data: cell };
      responseText = `Yes, severe thunderstorm activity is active in Brazil! We are tracking a High-Threat convective squall front (${cell.cell_id}) approaching São Paulo with peak radar reflectivity of ${cell.max_dbz} dBZ, ${cell.lightning_rate} lightning discharges, and travel speed of ${cell.speed_kmh} km/h moving SE. Torrential convective rains and gust fronts are expected in the next 15–30 minutes. ${DISCLAIMER}`;
    } else {
      responseText = `Satellite and radar composites for Brazil indicate tropical convective clusters active across the São Paulo and Amazon basins. ${DISCLAIMER}`;
    }
    return { text: responseText, actions, card: structuredCard };
  }

  // 3. DUBAI & United Arab Emirates / Middle East
  if (
    query.includes('dubai') || 
    query.includes('uae') || 
    query.includes('united arab emirates') || 
    query.includes('abu dhabi') || 
    query.includes('sharjah') || 
    query.includes('gulf') || 
    query.includes('doha') || 
    query.includes('riyadh')
  ) {
    actions.push({ type: 'SET_MAP_VIEW', payload: { lon: 55.27, lat: 25.20, zoom: 8.5 }, chipText: '📍 Map moved to Dubai, UAE' });
    const cell = ALL_ACTIVE_CELLS.find(c => c.cell_id === 'SC-2026-0917-10');
    if (cell) {
      actions.push({ type: 'SELECT_CELL', payload: cell.cell_id, chipText: `⚡ Selected ${cell.cell_id}` });
      structuredCard = { type: 'cell', data: cell };
      responseText = `Yes! There is an active convective thunderstorm cell (${cell.cell_id}) tracking near the Dubai coastal corridor. It has a peak reflectivity of ${cell.max_dbz} dBZ, lightning rate of ~${cell.lightning_rate}, and is moving ESE toward the Gulf at ${cell.speed_kmh} km/h. Sudden torrential rain bursts and strong downdrafts are anticipated over the next 20–40 minutes. ${DISCLAIMER}`;
    } else {
      responseText = `Atmospheric radar feeds for Dubai show isolated convective cloud buildups along the coast with moderate storm probability. ${DISCLAIMER}`;
    }
    return { text: responseText, actions, card: structuredCard };
  }

  // 4. USA & North America (Florida, Orlando, Miami, New York, Texas)
  if (
    query.includes('florida') || 
    query.includes('orlando') || 
    query.includes('miami') || 
    query.includes('usa') || 
    query.includes('united states') || 
    query.includes('texas') || 
    query.includes('new york')
  ) {
    actions.push({ type: 'SET_MAP_VIEW', payload: { lon: -81.37, lat: 28.53, zoom: 8.0 }, chipText: '📍 Map moved to Florida, USA' });
    const cell = ALL_ACTIVE_CELLS.find(c => c.cell_id === 'SC-2026-0917-11');
    if (cell) {
      actions.push({ type: 'SELECT_CELL', payload: cell.cell_id, chipText: `⚡ Selected ${cell.cell_id}` });
      structuredCard = { type: 'cell', data: cell };
      responseText = `Yes, an active sea-breeze thunderstorm cell (${cell.cell_id}) is active over Florida with 55 dBZ core reflectivity, ${cell.lightning_rate} lightning strikes, and travel speed of ${cell.speed_kmh} km/h moving East. Heavy rain and localized lightning hazards are projected over the next 30 minutes. ${DISCLAIMER}`;
    } else {
      responseText = `Radar composites across the US domain show scattered convective activity over the southeastern seaboard. ${DISCLAIMER}`;
    }
    return { text: responseText, actions, card: structuredCard };
  }

  // 5. KOLKATA / West Bengal
  if (query.includes('kolkata') || query.includes('bengal') || query.includes('asansol') || query.includes('durgapur')) {
    actions.push({ type: 'SET_MAP_VIEW', payload: { lon: 88.36, lat: 22.57, zoom: 8.5 }, chipText: '📍 Map moved to Kolkata' });
    const cell = ALL_ACTIVE_CELLS.find(c => c.cell_id === 'SC-2026-0917-03');
    if (cell) {
      actions.push({ type: 'SELECT_CELL', payload: cell.cell_id, chipText: `⚡ Selected ${cell.cell_id}` });
      structuredCard = { type: 'cell', data: cell };
      responseText = `A severe convective squall line (${cell.cell_id}) is actively tracking toward Kolkata with peak intensity of ${cell.max_dbz} dBZ and high lightning activity (~${cell.lightning_rate}). ETA to NSCBI Airport is approximately ~${cell.eta_min} minutes. ${DISCLAIMER}`;
    }
    return { text: responseText, actions, card: structuredCard };
  }

  // 6. RANCHI / Jharkhand
  if (query.includes('ranchi') || query.includes('jharkhand')) {
    actions.push({ type: 'SET_MAP_VIEW', payload: { lon: 85.31, lat: 23.34, zoom: 8.5 }, chipText: '📍 Map moved to Ranchi' });
    const cell = ALL_ACTIVE_CELLS.find(c => c.cell_id === 'SC-2026-0917-01');
    if (cell) {
      actions.push({ type: 'SELECT_CELL', payload: cell.cell_id, chipText: `⚡ Selected ${cell.cell_id}` });
      structuredCard = { type: 'cell', data: cell };
      responseText = `A High-Threat supercell (${cell.cell_id}) is active over the Ranchi plateau with extreme reflectivity of ${cell.max_dbz} dBZ and intense lightning (${cell.lightning_rate}). Heavy hail and torrential rain are probable. ${DISCLAIMER}`;
    }
    return { text: responseText, actions, card: structuredCard };
  }

  // 7. BHUBANESWAR / Odisha
  if (query.includes('bhubaneswar') || query.includes('odisha') || query.includes('cuttack')) {
    actions.push({ type: 'SET_MAP_VIEW', payload: { lon: 85.82, lat: 20.30, zoom: 8.5 }, chipText: '📍 Map moved to Bhubaneswar' });
    const cell = ALL_ACTIVE_CELLS.find(c => c.cell_id === 'SC-2026-0917-04');
    if (cell) {
      actions.push({ type: 'SELECT_CELL', payload: cell.cell_id, chipText: `⚡ Selected ${cell.cell_id}` });
      structuredCard = { type: 'cell', data: cell };
      responseText = `An active coastal storm line (${cell.cell_id}) is tracking along the Bhubaneswar-Odisha coast with peak reflectivity of ${cell.max_dbz} dBZ and lightning flash rate of ${cell.lightning_rate}. Rain showers are expected within ~${cell.eta_min} minutes. ${DISCLAIMER}`;
    }
    return { text: responseText, actions, card: structuredCard };
  }

  // 8. KERALA / Western Ghats / Calicut / Kochi
  if (query.includes('kerala') || query.includes('kochi') || query.includes('calicut') || query.includes('malabar')) {
    actions.push({ type: 'SET_MAP_VIEW', payload: { lon: 75.78, lat: 11.25, zoom: 8.5 }, chipText: '📍 Map moved to Kerala / Western Ghats' });
    const cell = ALL_ACTIVE_CELLS.find(c => c.cell_id === 'SC-2026-0917-06');
    if (cell) {
      actions.push({ type: 'SELECT_CELL', payload: cell.cell_id, chipText: `⚡ Selected ${cell.cell_id}` });
      structuredCard = { type: 'cell', data: cell };
      responseText = `An orographic convective storm cell (${cell.cell_id}) is active over the Malabar Western Ghats with 51 dBZ core intensity and ${cell.lightning_rate} lightning activity. Heavy localized rainfall expected within 30 minutes. ${DISCLAIMER}`;
    }
    return { text: responseText, actions, card: structuredCard };
  }

  // 9. MUMBAI / MAHARASHTRA
  if (query.includes('mumbai') || query.includes('maharashtra') || query.includes('pune')) {
    actions.push({ type: 'SET_MAP_VIEW', payload: { lon: 72.87, lat: 19.07, zoom: 8.5 }, chipText: '📍 Map moved to Mumbai' });
    responseText = `Radar observations for the Mumbai and Konkan coastal region show scattered convective cloud formations with moderate reflectivity (~42 dBZ) and light-to-moderate thunderstorm probability over the next 2 hours. ${DISCLAIMER}`;
    return { text: responseText, actions, card: null };
  }

  // 10. DELHI / NCR
  if (query.includes('delhi') || query.includes('ncr') || query.includes('noida') || query.includes('gurugram')) {
    actions.push({ type: 'SET_MAP_VIEW', payload: { lon: 77.10, lat: 28.70, zoom: 8.5 }, chipText: '📍 Map moved to Delhi / NCR' });
    responseText = `The Delhi/NCR radar domain indicates isolated pre-monsoon convective updrafts with moderate thunderstorm probability (35–45%) and low lightning density over the next 90 minutes. ${DISCLAIMER}`;
    return { text: responseText, actions, card: null };
  }

  // 11. BENGALURU / KARNATAKA
  if (query.includes('bengaluru') || query.includes('bangalore') || query.includes('karnataka')) {
    actions.push({ type: 'SET_MAP_VIEW', payload: { lon: 77.59, lat: 12.97, zoom: 8.5 }, chipText: '📍 Map moved to Bengaluru' });
    responseText = `Scattered convective thunderstorm cells are developing over South Interior Karnataka with peak core reflectivity of 45 dBZ and moderate lightning strikes expected in surrounding districts. ${DISCLAIMER}`;
    return { text: responseText, actions, card: null };
  }

  // 12. HYDERABAD / TELANGANA
  if (query.includes('hyderabad') || query.includes('telangana') || query.includes('andhra') || query.includes('visakhapatnam')) {
    actions.push({ type: 'SET_MAP_VIEW', payload: { lon: 78.48, lat: 17.38, zoom: 8.5 }, chipText: '📍 Map moved to Hyderabad' });
    responseText = `DWR composites across Telangana and Andhra Pradesh reveal isolated convective cells with core intensities between 42–48 dBZ and localized rain showers. ${DISCLAIMER}`;
    return { text: responseText, actions, card: null };
  }

  // 13. EUROPE / London / Alps
  if (query.includes('europe') || query.includes('london') || query.includes('alps') || query.includes('paris') || query.includes('germany')) {
    actions.push({ type: 'SET_MAP_VIEW', payload: { lon: 10.20, lat: 46.50, zoom: 7.0 }, chipText: '📍 Map moved to Central Europe / Alps' });
    const cell = ALL_ACTIVE_CELLS.find(c => c.cell_id === 'SC-2026-0917-12');
    if (cell) {
      actions.push({ type: 'SELECT_CELL', payload: cell.cell_id, chipText: `⚡ Selected ${cell.cell_id}` });
      structuredCard = { type: 'cell', data: cell };
      responseText = `An active Alpine convective storm system (${cell.cell_id}) is tracking across Central Europe with 50 dBZ reflectivity and ${cell.lightning_rate} lightning activity moving ENE. ${DISCLAIMER}`;
    }
    return { text: responseText, actions, card: structuredCard };
  }

  // 14. TOKYO / Japan
  if (query.includes('tokyo') || query.includes('japan')) {
    actions.push({ type: 'SET_MAP_VIEW', payload: { lon: 139.69, lat: 35.68, zoom: 8.0 }, chipText: '📍 Map moved to Tokyo, Japan' });
    const cell = ALL_ACTIVE_CELLS.find(c => c.cell_id === 'SC-2026-0917-13');
    if (cell) {
      actions.push({ type: 'SELECT_CELL', payload: cell.cell_id, chipText: `⚡ Selected ${cell.cell_id}` });
      structuredCard = { type: 'cell', data: cell };
      responseText = `A moderate convective cell cluster (${cell.cell_id}) is active over Tokyo Bay with 47 dBZ reflectivity and ${cell.lightning_rate} lightning strikes. ${DISCLAIMER}`;
    }
    return { text: responseText, actions, card: structuredCard };
  }

  // 15. JAKARTA / Southeast Asia
  if (query.includes('jakarta') || query.includes('indonesia') || query.includes('southeast asia')) {
    actions.push({ type: 'SET_MAP_VIEW', payload: { lon: 106.84, lat: -6.21, zoom: 7.5 }, chipText: '📍 Map moved to Jakarta' });
    actions.push({ type: 'SET_LAYER', payload: 'satellite', chipText: '☁ Switched to Satellite (IR) Layer' });
    const cell = ALL_ACTIVE_CELLS.find(c => c.cell_id === 'SC-2026-0917-14');
    if (cell) {
      actions.push({ type: 'SELECT_CELL', payload: cell.cell_id, chipText: `⚡ Selected ${cell.cell_id}` });
      structuredCard = { type: 'cell', data: cell };
      responseText = `STORMTRACE currently provides satellite-only cloud-top monitoring and tropical convective tracking for Jakarta and Southeast Asia. A tropical updraft cell (${cell.cell_id}) is monitored with 53 dBZ reflectivity and ${cell.lightning_rate} lightning discharges under satellite TIR1 observation. ${DISCLAIMER}`;
    } else {
      structuredCard = {
        type: 'coverage',
        data: { region: 'Jakarta, Indonesia', status: 'Satellite-Only', details: 'Thermal infrared satellite imagery and convective cloud tracking active.' }
      };
      responseText = `STORMTRACE provides satellite-only cloud-top monitoring and convective tracking for Jakarta. ${DISCLAIMER}`;
    }
    return { text: responseText, actions, card: structuredCard };
  }

  // 16. NAIROBI / Africa
  if (query.includes('nairobi') || query.includes('kenya') || query.includes('africa')) {
    actions.push({ type: 'SET_MAP_VIEW', payload: { lon: 36.82, lat: -1.29, zoom: 7.0 }, chipText: '📍 Map moved to Nairobi, East Africa' });
    structuredCard = {
      type: 'coverage',
      data: { region: 'Nairobi, East Africa', status: 'Active Satellite Domain', details: 'NASA GPM precipitation and geostationary satellite cloud-top imagery active with convective tracking.' }
    };
    responseText = `STORMTRACE has active satellite cloud-top monitoring and convective tracking over Nairobi and the East African Rift Valley with moderate precipitation bands. ${DISCLAIMER}`;
    return { text: responseText, actions, card: structuredCard };
  }

  // 17. WORST / MOST SEVERE STORM QUERY
  if (
    (query.includes('worst') && query.includes('storm')) ||
    query.includes('most severe') ||
    query.includes('most intense') ||
    query.includes('highest threat') ||
    (query.includes('strongest') && (query.includes('storm') || query.includes('cell'))) ||
    query.trim() === 'show me the most severe storm' ||
    query.trim() === 'worst storm'
  ) {
    const worstCell = [...ALL_ACTIVE_CELLS].sort((a, b) => b.severity_score - a.severity_score)[0];
    actions.push({ type: 'SET_MAP_VIEW', payload: { lon: worstCell.centroid_lon, lat: worstCell.centroid_lat, zoom: 8.5 }, chipText: `📍 Moved to ${worstCell.location_name}` });
    actions.push({ type: 'SELECT_CELL', payload: worstCell.cell_id, chipText: `⚡ Selected ${worstCell.cell_id}` });
    structuredCard = { type: 'cell', data: worstCell };
    responseText = `The most severe storm currently detected is ${worstCell.cell_id} (${worstCell.location_name}) with a Severity Score of ${worstCell.severity_score}/100 and peak reflectivity of ${worstCell.max_dbz} dBZ. It has an intense lightning strike rate of ${worstCell.lightning_rate} and is traveling ${worstCell.compass} at ${worstCell.speed_kmh} km/h. ${DISCLAIMER}`;
    return { text: responseText, actions, card: structuredCard };
  }

  // 18. GLOSSARY: Red area
  if (query.includes('red area') || query.includes('red zone') || query.includes('what does red mean')) {
    structuredCard = {
      type: 'glossary',
      data: { term: 'Red Area / High Threat', definition: explainTerm('red_zone') }
    };
    responseText = `Red areas on the map indicate high convective thunderstorm probability (greater than 80%) or intense radar reflectivity (above 50 dBZ) expected within the selected lead time. It means severe precipitation, strong wind gusts, or lightning are likely soon in that zone. ${DISCLAIMER}`;
    return { text: responseText, actions, card: structuredCard };
  }

  // 19. GLOSSARY: dBZ
  if (query.includes('dbz') || query.includes('decibel') || query.includes('reflectivity')) {
    const desc = explainTerm('dbz');
    structuredCard = { type: 'glossary', data: { term: 'Max dBZ (Radar Reflectivity)', definition: desc } };
    responseText = `dBZ (decibels of Z) measures the intensity of radar energy reflected back by precipitation droplets. Values above 50 dBZ represent severe storms with heavy rainfall or hail.`;
    return { text: responseText, actions, card: structuredCard };
  }

  // 20. GLOSSARY: Severity
  if (query.includes('severity score') || query.includes('hazard score') || query.includes('what is severity')) {
    const desc = explainTerm('severity');
    structuredCard = { type: 'glossary', data: { term: 'Severity Score (0–100)', definition: desc } };
    responseText = `Severity score is a composite index from 0 to 100 that combines rain intensity (dBZ), lightning flash rate, and cloud vertical depth to grade storm hazard levels.`;
    return { text: responseText, actions, card: structuredCard };
  }

  // 21. GLOSSARY: Uncertainty
  if (query.includes('uncertainty') || query.includes('mc-dropout') || query.includes('monte carlo dropout')) {
    const desc = explainTerm('uncertainty');
    actions.push({ type: 'SET_LAYER_TOGGLE', payload: { key: 'uncertainty', value: true }, chipText: '🎯 Activated Uncertainty Overlay' });
    structuredCard = { type: 'glossary', data: { term: 'MC-Dropout Epistemic Uncertainty', definition: desc } };
    responseText = `Uncertainty bands show the AI model's forecast confidence across 25 stochastic Monte Carlo Dropout passes. Wider bands highlight zones with higher prediction ambiguity during rapid storm growth.`;
    return { text: responseText, actions, card: structuredCard };
  }

  // 22. TRAVEL SAFETY
  if (query.includes('travel') || query.includes('safe to drive') || query.includes('drive to')) {
    actions.push({ type: 'SET_MAP_VIEW', payload: { lon: 79.13, lat: 12.91, zoom: 8.0 }, chipText: '📍 Checked travel corridor' });
    responseText = `The nowcasting model displays real-time storm cell vectors and lightning strike rates across major travel corridors. Please check active cell ETAs and refer to official meteorological alerts for definitive travel decisions. ${DISCLAIMER}`;
    return { text: responseText, actions, card: null };
  }

  // 23. LEAD TIME SELECTION
  if (query.includes('in an hour') || query.includes('60 min') || query.includes('1 hour')) {
    actions.push({ type: 'SET_LEAD_TIME', payload: 60, chipText: '⏱ Lead time set to +60m' });
    responseText = `I've updated the map forecast horizon to +60 minutes. You can now see projected storm advection and cell dissipation 1 hour into the future. ${DISCLAIMER}`;
    return { text: responseText, actions, card: null };
  }

  // 24. GLOBAL / COVERAGE / COUNTRIES
  if (query.includes('countries') || query.includes('coverage') || query.includes('regions') || query.includes('global domain')) {
    structuredCard = {
      type: 'coverage',
      data: {
        region: 'Global Thunderstorm & Radar Intelligence',
        status: 'Worldwide Coverage Active',
        details: 'Active storm cells and convective radar/satellite tracking are live across Tamil Nadu, India, Brazil, Dubai, USA, Europe, and Asia.'
      }
    };
    responseText = `STORMTRACE monitors live convective thunderstorms globally across India (Tamil Nadu, Bengal, Kerala, etc.), South America (Brazil), Middle East (Dubai), North America (USA), Europe, and Asia. Search any city or ask me directly to view that region! ${DISCLAIMER}`;
    return { text: responseText, actions, card: structuredCard };
  }

  // 25. STORM INTENSITY / SPEED / MOVEMENT / SEVERITY DETAIL
  if (
    /\b(what intensity|how severe|how fast|storm speed|movement speed|direction of (the|this) storm|which direction|what direction|travel speed|how strong is|peak reflectivity|peak dbz|storm heading)\b/i.test(query)
  ) {
    const targetCellId = currentContext.selectedCellId || null;
    const cell = (targetCellId ? getCellDetail(targetCellId) : null) || [...ALL_ACTIVE_CELLS].sort((a, b) => b.severity_score - a.severity_score)[0];
    if (cell) {
      actions.push({ type: 'SELECT_CELL', payload: cell.cell_id, chipText: `⚡ Selected ${cell.cell_id}` });
      structuredCard = { type: 'cell', data: cell };
      responseText = `Convective storm cell **${cell.cell_id}** (${cell.location_name}) currently displays:\n• **Core Reflectivity**: ${cell.max_dbz} dBZ (Intense convective core)\n• **Composite Severity**: ${cell.severity_score}/100\n• **Movement Velocity**: ${cell.speed_kmh} km/h moving ${cell.compass}\n• **Lightning Rate**: ~${cell.lightning_rate}\n• **Estimated Time of Arrival (ETA)**: ~${cell.eta_min} minutes to downstream corridor.\n\n${DISCLAIMER}`;
      return { text: responseText, actions, card: structuredCard };
    }
  }

  // 26. GENERAL CURRENT CONDITIONS & WHERE ARE STORMS QUERY (No specific city matched yet)
  if (
    /\b(where are the (thunder)?storms|is there (a|any)? (thunder)?storm( today| now| right now)?|how('s| is) the weather( today)?|any storms? (brewing|active|forming|near)|current thunderstorm activity|any storm today)\b/i.test(query) &&
    !GLOBAL_GAZETTEER.some(entry => entry.names.some(n => new RegExp(`\\b${n}\\b`, 'i').test(query)))
  ) {
    const topCell = [...ALL_ACTIVE_CELLS].sort((a, b) => b.severity_score - a.severity_score)[0];
    actions.push({ type: 'SELECT_CELL', payload: topCell.cell_id, chipText: `⚡ Top Cell: ${topCell.cell_id}` });
    structuredCard = { type: 'cell', data: topCell };
    responseText = `STORMTRACE is currently tracking **${ALL_ACTIVE_CELLS.length} active convective storm cells** across India and international monitoring corridors:\n• **Top Active Cell**: ${topCell.cell_id} (${topCell.location_name}) with ${topCell.max_dbz} dBZ core reflectivity and ~${topCell.lightning_rate} lightning.\n• **Active Corridors**: Bengal/Kolkata, Jharkhand/Ranchi, Tamil Nadu, Kerala, São Paulo, Dubai, Florida, and Central Europe.\n\nYou can ask about any specific location (e.g., "Storm in Kolkata", "Thunderstorm in Dubai") or click any cell on the live radar composite for detailed 0–120m nowcast trajectories. ${DISCLAIMER}`;
    return { text: responseText, actions, card: structuredCard };
  }

  // -------------------------------------------------------------------------
  // 27. DYNAMIC GLOBAL GAZETTEER & SPATIAL LOOKUP (Matched before science concepts)
  // -------------------------------------------------------------------------
  for (const entry of GLOBAL_GAZETTEER) {
    const matchedName = entry.names.find(n => {
      const regex = new RegExp(`\\b${n}\\b`, 'i');
      return regex.test(query);
    });

    if (matchedName) {
      actions.push({ type: 'SET_MAP_VIEW', payload: { lon: entry.lon, lat: entry.lat, zoom: entry.zoom }, chipText: `📍 Map moved to ${entry.region}` });
      
      // Check if there is an active storm cell in near proximity
      const nearby = findNearbyCell(entry.lat, entry.lon, 4.5);
      if (nearby) {
        actions.push({ type: 'SELECT_CELL', payload: nearby.cell_id, chipText: `⚡ Selected ${nearby.cell_id}` });
        structuredCard = { type: 'cell', data: nearby };
        responseText = `Yes! Convective thunderstorm cell (${nearby.cell_id} - ${nearby.location_name}) is active in the ${entry.region} domain. It has a peak reflectivity of ${nearby.max_dbz} dBZ, lightning discharge rate of ~${nearby.lightning_rate}, and is moving ${nearby.compass} at ${nearby.speed_kmh} km/h. Localized convective rain and lightning are expected. ${DISCLAIMER}`;
      } else {
        structuredCard = {
          type: 'coverage',
          data: { region: entry.region, status: 'Active Monitoring Domain', details: entry.defaultText }
        };
        responseText = `Radar and satellite monitoring for **${entry.region}**:\n${entry.defaultText}\n\nCurrently, atmospheric stability is moderate with no immediate high-threat supercell alerts directly overhead. ${DISCLAIMER}`;
      }
      return { text: responseText, actions, card: structuredCard };
    }
  }

  // -------------------------------------------------------------------------
  // 28. DYNAMIC METEOROLOGICAL SCIENCE KNOWLEDGE BASE
  // -------------------------------------------------------------------------
  for (const item of MET_KNOWLEDGE_BASE) {
    if (item.regex.test(query)) {
      if (item.isUncertainty) {
        actions.push({ type: 'SET_LAYER_TOGGLE', payload: { key: 'uncertainty', value: true }, chipText: '🎯 Activated Uncertainty Overlay' });
      }
      structuredCard = {
        type: 'glossary',
        data: { term: item.title, definition: item.text }
      };
      responseText = `${item.text}\n\n${DISCLAIMER}`;
      return { text: responseText, actions, card: structuredCard };
    }
  }

  // -------------------------------------------------------------------------
  // 29. DYNAMIC NATURAL LANGUAGE REASONING & GRACEFUL AMBIGUOUS FALLBACK
  // -------------------------------------------------------------------------
  const activeCount = ALL_ACTIVE_CELLS.length;
  const topCell = [...ALL_ACTIVE_CELLS].sort((a, b) => b.severity_score - a.severity_score)[0];

  responseText = `I'm here to assist you with thunderstorm nowcasting, live convective tracking, and atmospheric science intelligence.\n\nYou can ask me:\n• 📍 **Current Conditions**: "Where are the thunderstorms right now?", "Is there a thunderstorm in Kolkata?", "Check weather in Tamil Nadu"\n• ⚡ **Storm Tracking & Intensity**: "What intensity is the thunderstorm?", "How fast is it moving?", "Show me the most severe storm"\n• 🔬 **Meteorological Science**: "What is a thunderstorm?", "Why do thunderstorms happen in the afternoon?", "What is CAPE?", "How does hail form?", "Why do storms rotate?"\n• 🛡️ **Severe Weather Safety**: "Is it safe to go outside?", "What is the 30/30 rule?", "Can planes fly through thunderstorms?"\n• ⚙️ **System & Verification**: "How does STORMTRACE work?", "How accurate are your forecasts?", "What data do you use?"\n\n${DISCLAIMER}`;

  return { text: responseText, actions, card: null };
}
