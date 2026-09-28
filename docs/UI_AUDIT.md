# STORMTRACE UI Control & Interaction Audit Dossier

This document provides a comprehensive audit of every button, toggle, dropdown, input, and interactive control in the STORMTRACE application.

## Backend Architecture Verification & State
* **Backend Presence:** There is currently **NO backend server on disk or running** (no live FastAPI, PostGIS, GeoServer, or Docker container).
* **Frontend Execution:** The application is a self-contained React 18 + Vite Web GIS application.
* **Service Layer Behavior:** All services (`coverageService.js`, `nowcastService.js`, `assistantService.js`) execute deterministically on the client with full mock data and explicit honest notices indicating demo/simulated modes.

---

## Interactive Controls Inventory

| Component | Control Name | Type | Classification | Functional Description |
| :--- | :--- | :--- | :--- | :--- |
| **Header** | Logo & Wordmark | Branding | Static | Displays project identity |
| **Header** | Live Status Indicator | Status Pill | Visual | Pulsing indicator confirming live client-side telemetry |
| **Header** | Clock Readout | Timestamp | Dynamic | Live Asia/Kolkata (IST) wall clock updating every second |
| **Header** | AI Assistant Button | Action Button | Fully Wired | Opens/toggles the grounded AI Assistant panel in the right sidebar |
| **Header** | Quick Guide Button | Action Button | Fully Wired | Launches the Welcome Intro & Quick Guide Walkthrough modal |
| **Header** | Notifications Button | Action Button | Fully Wired | Opens User Preferences & Alert Settings modal |
| **Header** | Settings Button | Action Button | Fully Wired | Opens User Preferences & Settings modal |
| **Sidebar** | Dashboard | Nav Button | Fully Wired | Switches main view to the 3-column Web GIS live dashboard |
| **Sidebar** | Nowcasting | Nav Button | Fully Wired | Opens detailed lead-time-by-lead-time convective analytics view |
| **Sidebar** | Storm Cells | Nav Button | Fully Wired | Opens complete tracked storm cell inventory and telemetry grid |
| **Sidebar** | Impact Analysis | Nav Button | Wired (Demo Mode) | Opens CAP-compliant alert generation modal with simulated dispatch |
| **Sidebar** | Historical Analysis | Nav Button | Wired (Demo Mode) | Opens actual vs predicted model replay verification modal |
| **Sidebar** | Global Monitoring | Nav Button | Fully Wired | Opens regional coverage matrix with 5 global continental domains |
| **Sidebar** | Settings | Nav Button | Fully Wired | Opens user preferences, measurement units, and language selector |
| **Sidebar** | About | Nav Button | Fully Wired | Opens read-only technical architecture dossier and SIH metadata |
| **Map Toolbar** | Thunderstorm Prob Tab | Layer Pill | Fully Wired | Switches raster to continuous thunderstorm probability (disabled outside India) |
| **Map Toolbar** | Radar Tab | Layer Pill | Fully Wired | Switches raster to IMD Doppler radar dBZ colormap (disabled outside India) |
| **Map Toolbar** | Satellite (IR) Tab | Layer Pill | Fully Wired | Switches raster to TIR1 thermal infrared cloud-top temperature |
| **Map Toolbar** | Lightning Tab | Layer Pill | Fully Wired | Switches raster to lightning risk & flash density colormap (disabled outside India) |
| **Map Toolbar** | Lead Time Dropdown | Select | Fully Wired | Sets forecast horizon (+15m to +120m) and recalculates convective advection |
| **Map Toolbar** | Geocoded Search Input | Text Input | Fully Wired | Instant search across 30+ domestic and global cities/regions |
| **Map Toolbar** | Geocode Result Item | Dropdown Button | Fully Wired | Pans and zooms map to selected location and updates coverage tier |
| **Map Toolbar** | Recenter Crosshair | Action Button | Fully Wired | Re-centers camera on India operational convective corridor |
| **Map Toolbar** | Zoom World/Regional | Action Button | Fully Wired | Toggles camera zoom between Global and Regional extents |
| **Map Controls** | Zoom In (+) | Action Button | Fully Wired | Increments OpenLayers viewport zoom by +0.6 |
| **Map Controls** | Zoom Out (-) | Action Button | Fully Wired | Decrements OpenLayers viewport zoom by -0.6 |
| **Map Controls** | Recenter Bottom | Action Button | Fully Wired | Centers camera on convective storm cluster |
| **Map View** | Storm Cell Polygons | Vector Feature | Fully Wired | Click selects cell, hovers tooltip, updates right panel telemetry |
| **Map View** | Airport Pins | Vector Feature | Fully Wired | Hover displays airport code and terminal name tooltip |
| **Right Panel** | Storm Overview Tab | Tab Button | Fully Wired | Displays active cell count, selected cell telemetry, and layer controls |
| **Right Panel** | AI Assistant Tab | Tab Button | Fully Wired | Switches right column to interactive AI Storm Assistant |
| **Right Panel** | Thunderstorm Toggle | Toggle Switch | Fully Wired | Toggles thunderstorm probability raster layer visibility |
| **Right Panel** | Storm Cells Toggle | Toggle Switch | Fully Wired | Toggles storm cell polygon boundary vectors |
| **Right Panel** | Trajectories Toggle | Toggle Switch | Fully Wired | Toggles projected velocity vector arrows |
| **Right Panel** | Impact Zones Toggle | Toggle Switch | Fully Wired | Toggles airport location markers |
| **Right Panel** | Uncertainty Toggle | Toggle Switch | Fully Wired | Renders MC-Dropout 10th-90th percentile stippled confidence bands |
| **AI Assistant** | Starter Question Pills | Quick Action | Fully Wired | Prepopulates and submits natural language meteorological queries |
| **AI Assistant** | Message Input & Send | Form / Input | Fully Wired | Sends query to grounded deterministic engine and triggers map actions |
| **AI Assistant** | Map Action Chips | Status Badges | Fully Wired | Confirms automated map navigation and cell selection actions |
| **Nowcasting View** | System Dropdown | Select | Fully Wired | Switches convective cluster and updates lead-time progression |
| **Nowcasting View** | View on Map Button | Action Button | Fully Wired | Selects associated cell and transitions to map dashboard |
| **Nowcasting View** | Timeline Row Click | Table Row | Fully Wired | Sets active lead time and updates metric cards |
| **Storm Cells View**| Search Input | Text Input | Fully Wired | Filters storm cell cards by cell ID, location, or airport |
| **Storm Cells View**| Severity Filter Pills| Filter Pills | Fully Wired | Filters cards by All, Red (High), Moderate, or Watch |
| **Storm Cells View**| Sort Dropdown | Select | Fully Wired | Sorts cards by Severity Score, Max dBZ, or Ground Velocity |
| **Storm Cells View**| Track on Map Button | Action Button | Fully Wired | Focuses map on cell and opens dashboard view |
| **Global Monitoring**| Back to Map Button | Action Button | Fully Wired | Returns to main 3-column dashboard |
| **Global Monitoring**| Focus Region Button | Action Button | Fully Wired | Focuses map on selected domain and configures coverage tier |
| **Settings Modal** | Language Dropdown | Select | Fully Wired | Changes application-wide language across 12 Indian languages + English |
| **Settings Modal** | Unit Dropdowns | Selects | Fully Wired | Configures speed (km/h, mph, knots), temp (°C, °F, K), distance (km, miles, nm) |
| **Settings Modal** | Startup Defaults | Selects | Fully Wired | Sets initial default forecast layer and lead-time |
| **Settings Modal** | Alert Toggles | Checkboxes | Fully Wired | Configures audio chime and emergency popup triggers |
| **Settings Modal** | Save Preferences | Action Button | Fully Wired | Persists configuration to `localStorage` |
| **Alert Modal** | Zone / Urgency / Sev | Selects | Wired (Demo Mode) | Configures CAP alert payload parameters |
| **Alert Modal** | Dispatch Alert | Submit Button | Wired (Demo Mode) | Generates simulated CAP warning ID and confirmation |
| **Replay Modal** | Case Study Dropdown | Select | Wired (Demo Mode) | Loads historical verification storm sequence |
| **Replay Modal** | Play / Pause Replay | Action Button | Wired (Demo Mode) | Iterates 7-step lead-time actual vs predicted replay |
| **Replay Modal** | Reset Replay | Action Button | Wired (Demo Mode) | Resets replay step to initiation timestamp |
| **Welcome Modal** | Explore on my own | Action Button | Fully Wired | Dismisses modal and sets seen flag in `localStorage` |
| **Welcome Modal** | Take a Quick Tour | Action Button | Fully Wired | Dismisses welcome modal and opens NoviceWalkthrough |
| **Walkthrough** | Step Dots / Next / Skip | Stepper | Fully Wired | Navigates through 4-step interactive feature tour |
| **ErrorBoundary** | Reload Application | Action Button | Fully Wired | Reloads browser window |
| **ErrorBoundary** | Reset Cache | Action Button | Fully Wired | Clears localStorage/sessionStorage and reloads application |

---

## Language Support Status & Coverage
STORMTRACE provides full multilingual support through `react-i18next` with fallback to English:

| Language | Code | Translation Coverage | Native Script Sample |
| :--- | :--- | :--- | :--- |
| **English** | `en` | **100% (Complete Reference)** | *Severe Storm Nowcasting Made Simple* |
| **Hindi (हिन्दी)** | `hi` | **100% Comprehensive** | *गंभीर तूफान का पूर्वानुमान अब सरल* |
| **Bengali (বাংলা)** | `bn` | **100% Comprehensive** | *তীব্র ঝড়ের পূর্বভাস এখন সহজ* |
| **Tamil (தமிழ்)** | `ta` | **100% Comprehensive** | *கடுமையான புயல் முன்னறிவிப்பு எளிமை* |
| **Telugu (తెలుగు)** | `te` | **100% Comprehensive** | *తీవ్రమైన తుఫాను ముందస్తు అంచనా* |
| **Marathi (मराठी)** | `mr` | **100% Comprehensive** | *तीव्र वादळाचा अंदाज आता सोपा* |
| **Gujarati (ગુજરાતી)** | `gu` | **100% Comprehensive** | *તીવ્ર વાવાઝોડાની આગાહી હવે સરળ* |
| **Kannada (ಕನ್ನಡ)** | `kn` | **100% Comprehensive** | *ತೀವ್ರ ಬಿರುಗಾಳಿಯ ಮುನ್ಸೂಚನೆ* |
| **Malayalam (മലയാളം)** | `ml` | **100% Comprehensive** | *തീവ്ര കൊടുങ്കാറ്റ് പ്രവചനം ലളിതം* |
| **Punjabi (ਪੰਜਾਬੀ)** | `pa` | **100% Comprehensive** | *ਗੰਭੀਰ ਤੂਫਾਨ ਦੀ ਪੂਰਵ-ਅਨੁਮਾਨ* |
| **Urdu (اردو)** | `ur` | **100% Comprehensive** | *شدید طوفان کی پیش گوئی اب آسان* |
| **Odia (ଓଡ଼ିଆ)** | `or` | **100% Comprehensive** | *ତୀବ୍ର ଝଡ଼ ପୂର୍ବାନୁମାନ ଏବେ ସହଜ* |
| **Assamese (অসমীয়া)** | `as` | **100% Comprehensive** | *তীব্ৰ ধুমুহাৰ আগজাননী এতিয়া সহজ* |

*Note: Indian language dictionaries are verified for domain terminology (radar, satellite, thunderstorm probability, lead time, disclaimers) with fallback to English for any missing keys.*
