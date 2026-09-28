import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { 
  CloudLightning, 
  Search, 
  MapPin, 
  AlertTriangle, 
  ShieldAlert, 
  Activity, 
  Zap, 
  Globe, 
  ArrowRight, 
  ShieldCheck, 
  Clock, 
  Layers, 
  Navigation, 
  ExternalLink,
  Info,
  CheckCircle2,
  Sliders,
  ChevronRight,
  Sparkles,
  Maximize2
} from 'lucide-react';
import { searchGazetteer, evaluateLocationCoverage, REGIONAL_NOWCAST_BOUNDS } from '../../services/gazetteerService';
import { getAllProvenanceCards } from '../../services/provenanceService';
import SafetyTipsModal from './SafetyTipsModal';

export default function LandingPage({
  onNavigate,
  onOpenAbout,
  onOpenAlerts,
  onOpenSettings,
  onSelectCityOnMap
}) {
  const { t, i18n } = useTranslation();

  // Search Bar State
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [selectedLocationCoverage, setSelectedLocationCoverage] = useState(null);
  const [isSearching, setIsSearching] = useState(false);

  // Map Preview Layer State
  const [previewLayer, setPreviewLayer] = useState('thunderstorm'); // 'thunderstorm' | 'radar' | 'satellite' | 'lightning'
  const [isSafetyTipsOpen, setIsSafetyTipsOpen] = useState(false);

  // Provenance Cards
  const provenanceCards = getAllProvenanceCards();

  // Functional Languages List (strictly confirmed functional locales)
  const functionalLanguages = [
    { code: 'en', name: 'English' },
    { code: 'hi', name: 'हिन्दी (Hindi)' },
    { code: 'bn', name: 'বাংলা (Bengali)' },
    { code: 'ta', name: 'தமிழ் (Tamil)' },
    { code: 'te', name: 'తెలుగు (Telugu)' },
    { code: 'mr', name: 'मराठी (Marathi)' },
    { code: 'gu', name: 'ગુજરાતી (Gujarati)' },
    { code: 'kn', name: 'ಕನ್ನಡ (Kannada)' },
    { code: 'ml', name: 'മലയാളം (Malayalam)' },
    { code: 'pa', name: 'ਪੰਜਾਬੀ (Punjabi)' },
    { code: 'ur', name: 'اردو (Urdu)' },
    { code: 'or', name: 'ଓଡ଼ିଆ (Odia)' },
    { code: 'as', name: 'অসমীয়া (Assamese)' }
  ];

  // In-domain example quick search chips
  const exampleSupportedLocations = ['Kolkata', 'Ranchi', 'Bhubaneswar', 'Durgapur', 'Jamshedpur'];

  const handleSearchChange = (e) => {
    const val = e.target.value;
    setSearchQuery(val);
    if (val.trim().length > 0) {
      const results = searchGazetteer(val);
      setSearchResults(results);
      setIsSearching(true);
      if (results.length > 0) {
        setSelectedLocationCoverage(evaluateLocationCoverage(results[0]));
      } else {
        setSelectedLocationCoverage(null);
      }
    } else {
      setSearchResults([]);
      setIsSearching(false);
      setSelectedLocationCoverage(null);
    }
  };

  const handleSelectSearchResult = (loc) => {
    setSearchQuery(loc.shortName || loc.name);
    setIsSearching(false);
    const cov = evaluateLocationCoverage(loc);
    setSelectedLocationCoverage(cov);
  };

  const handleQuickChipClick = (cityName) => {
    setSearchQuery(cityName);
    const results = searchGazetteer(cityName);
    if (results.length > 0) {
      const cov = evaluateLocationCoverage(results[0]);
      setSelectedLocationCoverage(cov);
    }
    setIsSearching(false);
  };

  const handleLaunchLocationOnMap = (cov) => {
    if (onSelectCityOnMap) {
      onSelectCityOnMap({ lon: cov.lon, lat: cov.lat, name: cov.name, isIndia: true });
    }
    onNavigate('dashboard');
  };

  const handleMyLocationClick = () => {
    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const lat = pos.coords.latitude;
          const lon = pos.coords.longitude;
          const cov = evaluateLocationCoverage(lon, lat);
          setSelectedLocationCoverage(cov);
          setSearchQuery(`Current Location (${lat.toFixed(2)}°N, ${lon.toFixed(2)}°E)`);
          setIsSearching(false);
        },
        () => {
          // Geolocation denied or unavailable — test default Kolkata
          const cov = evaluateLocationCoverage(88.36, 22.57);
          setSelectedLocationCoverage(cov);
          setSearchQuery('Kolkata, West Bengal (Default)');
        }
      );
    }
  };

  return (
    <div className="min-h-screen bg-[#f8fafc] text-slate-800 flex flex-col selection:bg-blue-100 selection:text-blue-900 font-sans select-none overflow-x-hidden">
      
      {/* ========================================================================= */}
      {/* 1. HEADER (Sticky, Full Width) */}
      {/* ========================================================================= */}
      <header className="sticky top-0 z-40 w-full bg-white/95 backdrop-blur-md border-b border-slate-200 shadow-xs px-6 py-3.5 flex items-center justify-between">
        {/* Left: Brand Logo & Wordmark */}
        <div className="flex items-center space-x-3 cursor-pointer" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
          <div className="w-9 h-9 rounded-xl bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-600 shadow-xs">
            <CloudLightning className="w-5 h-5 text-blue-600 fill-blue-100" />
          </div>
          <div>
            <div className="text-base font-black tracking-tight flex items-center leading-none">
              <span className="text-slate-900">STORM</span>
              <span className="text-blue-600">TRACE</span>
            </div>
            <div className="text-[10px] text-slate-500 font-medium tracking-tight mt-0.5">
              AI-Based Thunderstorm & Lightning Nowcasting
            </div>
          </div>
        </div>

        {/* Center: Navigation Links */}
        <nav className="hidden md:flex items-center space-x-1 lg:space-x-2 text-xs font-semibold text-slate-600">
          <button 
            onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
            className="px-3 py-1.5 rounded-lg text-blue-600 bg-blue-50 font-bold transition"
          >
            Home
          </button>
          <button 
            onClick={() => onNavigate('nowcasting')}
            className="px-3 py-1.5 rounded-lg hover:text-slate-900 hover:bg-slate-100 transition"
          >
            Forecast
          </button>
          <button 
            onClick={() => onNavigate('dashboard')}
            className="px-3 py-1.5 rounded-lg hover:text-slate-900 hover:bg-slate-100 transition flex items-center space-x-1"
          >
            <span>Live Map</span>
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
          </button>
          <button 
            onClick={onOpenAlerts}
            className="px-3 py-1.5 rounded-lg hover:text-slate-900 hover:bg-slate-100 transition"
          >
            Alerts
          </button>
          <button 
            onClick={() => setIsSafetyTipsOpen(true)}
            className="px-3 py-1.5 rounded-lg hover:text-slate-900 hover:bg-slate-100 transition"
          >
            Safety Tips
          </button>
          <button 
            onClick={onOpenAbout}
            className="px-3 py-1.5 rounded-lg hover:text-slate-900 hover:bg-slate-100 transition"
          >
            About
          </button>
        </nav>

        {/* Right: Language Selector & Primary View Alerts Button */}
        <div className="flex items-center space-x-3">
          {/* Functional Language Dropdown */}
          <select
            value={i18n.language || 'en'}
            onChange={(e) => {
              i18n.changeLanguage(e.target.value);
              localStorage.setItem('stormtrace_language', e.target.value);
            }}
            className="text-xs bg-slate-50 border border-slate-200 text-slate-700 font-medium rounded-xl px-2.5 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer shadow-2xs"
            aria-label="Select Language"
          >
            {functionalLanguages.map((lang) => (
              <option key={lang.code} value={lang.code}>
                {lang.name}
              </option>
            ))}
          </select>

          {/* View Alerts Button (Adheres strictly to Alert Rule) */}
          <button
            onClick={onOpenAlerts}
            className="px-3.5 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold shadow-sm transition flex items-center space-x-1.5"
          >
            <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
            <span>View Alerts</span>
          </button>
        </div>
      </header>

      {/* ========================================================================= */}
      {/* 2. HERO SECTION */}
      {/* ========================================================================= */}
      <section className="relative w-full bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900 text-white pt-16 pb-20 px-6 overflow-hidden">
        {/* Decorative Atmospheric Glows */}
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-600/15 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-amber-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="max-w-4xl mx-auto text-center relative z-10 space-y-6">
          {/* Eyebrow Pill */}
          <div className="inline-flex items-center space-x-2 px-3.5 py-1 rounded-full bg-blue-500/10 border border-blue-400/25 text-blue-300 text-xs font-semibold backdrop-blur-md shadow-inner">
            <Zap className="w-3.5 h-3.5 text-amber-400" />
            <span>Operational AI Decision Support · 0 to 2 Hour Lead Time</span>
          </div>

          {/* Two-line Headline */}
          <h1 className="text-3xl sm:text-4xl md:text-5xl font-extrabold tracking-tight leading-tight text-white">
            Real-Time Thunderstorm Nowcasting<br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-300 via-sky-200 to-amber-300">
              High-Precision Convective Storm & Lightning Intelligence
            </span>
          </h1>

          {/* Subheading */}
          <p className="text-sm sm:text-base text-slate-300 max-w-2xl mx-auto leading-relaxed font-normal">
            Spatiotemporal convective initiation, radar precipitation intensity, and lightning propensity prediction up to 2 hours in advance across the <strong>Regional East India corridor</strong>.
          </p>

          {/* Location Search Bar with Domain Verification */}
          <div className="max-w-2xl mx-auto relative pt-2">
            <div className="relative flex items-center bg-white rounded-2xl shadow-xl border border-slate-100 overflow-hidden p-1.5">
              <div className="pl-3.5 pr-2 text-slate-400">
                <Search className="w-5 h-5 text-slate-500" />
              </div>
              <input
                type="text"
                value={searchQuery}
                onChange={handleSearchChange}
                placeholder="Search city in supported domain (e.g. Kolkata, Ranchi, Bhubaneswar)..."
                className="w-full text-xs sm:text-sm text-slate-800 placeholder-slate-400 focus:outline-none py-2 pr-4 font-medium"
              />
              <button
                onClick={() => {
                  if (selectedLocationCoverage?.inDomain) {
                    handleLaunchLocationOnMap(selectedLocationCoverage);
                  } else {
                    onNavigate('dashboard');
                  }
                }}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-xl transition shrink-0 shadow-sm flex items-center space-x-1.5"
              >
                <span>Find Nowcast</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Live Autocomplete Dropdown */}
            {isSearching && searchResults.length > 0 && (
              <div className="absolute left-0 right-0 top-full mt-2 bg-white rounded-2xl shadow-2xl border border-slate-200 p-2 z-30 text-left text-xs max-h-60 overflow-y-auto">
                <div className="px-3 py-1.5 text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                  Gazetteer Matches
                </div>
                {searchResults.map((loc) => (
                  <button
                    key={loc.id}
                    onClick={() => handleSelectSearchResult(loc)}
                    className="w-full flex items-center justify-between px-3 py-2 rounded-xl hover:bg-slate-50 text-slate-800 transition text-left"
                  >
                    <div className="flex items-center space-x-2">
                      <MapPin className={`w-3.5 h-3.5 ${loc.inDomain ? 'text-emerald-600' : 'text-slate-400'}`} />
                      <span className="font-semibold text-slate-900">{loc.name}</span>
                    </div>
                    <span className={`text-[10px] px-2 py-0.5 rounded-md font-bold ${
                      loc.inDomain 
                        ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' 
                        : 'bg-amber-50 text-amber-700 border border-amber-200'
                    }`}>
                      {loc.inDomain ? 'In-Domain' : 'Outside Domain'}
                    </span>
                  </button>
                ))}
              </div>
            )}

            {/* Domain Coverage Result Banner (Strictly Distinguishes In-Domain vs Out-of-Domain) */}
            {selectedLocationCoverage && (
              <div className={`mt-3 p-3.5 rounded-2xl text-left text-xs shadow-md border animate-fade-in ${
                selectedLocationCoverage.inDomain
                  ? 'bg-emerald-950/90 border-emerald-500/50 text-emerald-100 backdrop-blur-md'
                  : 'bg-amber-950/90 border-amber-500/50 text-amber-100 backdrop-blur-md'
              }`}>
                <div className="flex items-start justify-between gap-3">
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2 font-bold text-[11px] tracking-wide uppercase">
                      {selectedLocationCoverage.inDomain ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                      ) : (
                        <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
                      )}
                      <span>{selectedLocationCoverage.headline}</span>
                    </div>
                    <p className="text-[11px] leading-relaxed text-slate-200 font-normal">
                      {selectedLocationCoverage.details}
                    </p>
                  </div>
                  {selectedLocationCoverage.inDomain ? (
                    <button
                      onClick={() => handleLaunchLocationOnMap(selectedLocationCoverage)}
                      className="px-3 py-1.5 bg-emerald-500 hover:bg-emerald-600 text-slate-950 rounded-xl font-bold text-xs shrink-0 transition shadow-sm"
                    >
                      View on Live Map
                    </button>
                  ) : (
                    <button
                      onClick={() => onNavigate('dashboard')}
                      className="px-3 py-1.5 bg-amber-500/20 hover:bg-amber-500/30 text-amber-200 border border-amber-400/40 rounded-xl font-semibold text-xs shrink-0 transition"
                    >
                      Explore East India
                    </button>
                  )}
                </div>
              </div>
            )}

            {/* Example In-Domain Quick Search Chips */}
            <div className="flex flex-wrap items-center justify-center gap-1.5 mt-3 text-xs text-slate-400">
              <span className="text-[11px] font-medium text-slate-400 mr-1">Supported areas:</span>
              {exampleSupportedLocations.map((city) => (
                <button
                  key={city}
                  onClick={() => handleQuickChipClick(city)}
                  className="px-2.5 py-0.5 rounded-full bg-slate-800/80 hover:bg-slate-700 text-slate-200 border border-slate-700 text-[11px] font-medium transition cursor-pointer"
                >
                  {city}
                </button>
              ))}
            </div>
          </div>

          {/* 4 Quick Action Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-6 max-w-3xl mx-auto">
            {/* Quick Action 1: My Location */}
            <button
              onClick={handleMyLocationClick}
              className="p-3.5 rounded-2xl bg-slate-800/60 hover:bg-slate-800 border border-slate-700/80 text-left transition space-y-1.5 group cursor-pointer"
            >
              <div className="w-7 h-7 rounded-lg bg-blue-500/20 flex items-center justify-center text-blue-400 group-hover:bg-blue-500 group-hover:text-white transition">
                <Navigation className="w-4 h-4" />
              </div>
              <div className="font-bold text-xs text-white">My Location</div>
              <div className="text-[10px] text-slate-400">Check domain coverage</div>
            </button>

            {/* Quick Action 2: Today's Forecast */}
            <button
              onClick={() => onNavigate('nowcasting')}
              className="p-3.5 rounded-2xl bg-slate-800/60 hover:bg-slate-800 border border-slate-700/80 text-left transition space-y-1.5 group cursor-pointer"
            >
              <div className="w-7 h-7 rounded-lg bg-sky-500/20 flex items-center justify-center text-sky-400 group-hover:bg-sky-500 group-hover:text-white transition">
                <Activity className="w-4 h-4" />
              </div>
              <div className="font-bold text-xs text-white">Today's Forecast</div>
              <div className="text-[10px] text-slate-400">+15m to +120m curves</div>
            </button>

            {/* Quick Action 3: View Alerts */}
            <button
              onClick={onOpenAlerts}
              className="p-3.5 rounded-2xl bg-slate-800/60 hover:bg-slate-800 border border-slate-700/80 text-left transition space-y-1.5 group cursor-pointer"
            >
              <div className="w-7 h-7 rounded-lg bg-rose-500/20 flex items-center justify-center text-rose-400 group-hover:bg-rose-500 group-hover:text-white transition">
                <ShieldAlert className="w-4 h-4" />
              </div>
              <div className="font-bold text-xs text-white">View Alerts</div>
              <div className="text-[10px] text-slate-400">Active warning cells</div>
            </button>

            {/* Quick Action 4: Safety Tips */}
            <button
              onClick={() => setIsSafetyTipsOpen(true)}
              className="p-3.5 rounded-2xl bg-slate-800/60 hover:bg-slate-800 border border-slate-700/80 text-left transition space-y-1.5 group cursor-pointer"
            >
              <div className="w-7 h-7 rounded-lg bg-amber-500/20 flex items-center justify-center text-amber-400 group-hover:bg-amber-500 group-hover:text-white transition">
                <ShieldCheck className="w-4 h-4" />
              </div>
              <div className="font-bold text-xs text-white">Safety Tips</div>
              <div className="text-[10px] text-slate-400">30/30 Lightning rule</div>
            </button>
          </div>

          {/* Small Corner Tagline */}
          <div className="text-[11px] text-slate-500 font-mono pt-4">
            Smart India Hackathon 2026 · Problem Statement PS 26072 (MoES / IMD)
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* 3. LIVE MAP PREVIEW (Floating Card) */}
      {/* ========================================================================= */}
      <section className="w-full max-w-5xl mx-auto px-6 -mt-10 relative z-20">
        <div className="bg-white rounded-3xl border border-slate-200/90 shadow-2xl overflow-hidden p-5 space-y-4">
          
          {/* Map Preview Header & Layer Tabs */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
            <div>
              <div className="flex items-center space-x-2">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
                <h3 className="text-sm font-bold text-slate-900">Regional Nowcast Map Preview</h3>
                <span className="px-2 py-0.5 rounded-md bg-amber-100 text-amber-800 font-bold text-[10px] border border-amber-200">
                  DEMO BENCHMARK DATA
                </span>
              </div>
              <p className="text-[11px] text-slate-500 mt-0.5">
                Target Domain: East India Regional Grid (64x64, 83.5°E–89.8°E, 20.0°N–26.3°N)
              </p>
            </div>

            {/* 4 Layer Tabs matching Dashboard */}
            <div className="flex items-center space-x-1 bg-slate-100 p-1 rounded-2xl border border-slate-200 text-xs font-semibold">
              <button
                onClick={() => setPreviewLayer('thunderstorm')}
                className={`px-3 py-1 rounded-xl transition ${
                  previewLayer === 'thunderstorm'
                    ? 'bg-blue-600 text-white shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Thunderstorm Prob
              </button>
              <button
                onClick={() => setPreviewLayer('radar')}
                className={`px-3 py-1 rounded-xl transition ${
                  previewLayer === 'radar'
                    ? 'bg-blue-600 text-white shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Radar
              </button>
              <button
                onClick={() => setPreviewLayer('satellite')}
                className={`px-3 py-1 rounded-xl transition ${
                  previewLayer === 'satellite'
                    ? 'bg-blue-600 text-white shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Satellite (IR)
              </button>
              <button
                onClick={() => setPreviewLayer('lightning')}
                className={`px-3 py-1 rounded-xl transition ${
                  previewLayer === 'lightning'
                    ? 'bg-blue-600 text-white shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Lightning
              </button>
            </div>
          </div>

          {/* Interactive Map Preview Window */}
          <div 
            onClick={() => onNavigate('dashboard')}
            className="relative w-full h-80 sm:h-96 rounded-2xl bg-slate-950 overflow-hidden border border-slate-200 shadow-inner group cursor-pointer"
          >
            {/* Map Canvas Visual Simulation */}
            <div className="absolute inset-0 bg-gradient-to-br from-slate-900 via-slate-950 to-blue-950 flex items-center justify-center">
              {/* Radar Reflectivity / Probability Synthetic Contour Grid */}
              <div className="relative w-72 h-72 rounded-full bg-blue-500/10 border border-blue-400/20 animate-pulse flex items-center justify-center">
                <div className="w-48 h-48 rounded-full bg-amber-500/15 border border-amber-400/30 flex items-center justify-center">
                  <div className="w-24 h-24 rounded-full bg-rose-500/25 border border-rose-400/40 flex items-center justify-center">
                    <span className="text-[10px] font-bold text-rose-300">Convective Core (58 dBZ)</span>
                  </div>
                </div>
              </div>

              {/* Geographic Grid Overlay Line */}
              <div className="absolute inset-0 flex flex-col justify-between p-6 pointer-events-none opacity-40 text-[9px] font-mono text-slate-400">
                <div className="flex justify-between">
                  <span>26.3°N, 83.5°E</span>
                  <span>26.3°N, 89.8°E (Gangetic Delta)</span>
                </div>
                <div className="flex justify-between">
                  <span>20.0°N, 83.5°E</span>
                  <span>20.0°N, 89.8°E (Bay of Bengal)</span>
                </div>
              </div>

              {/* Centered Hover Launch Action */}
              <div className="absolute inset-0 bg-slate-950/40 group-hover:bg-slate-950/20 backdrop-blur-2xs transition flex flex-col items-center justify-center text-white space-y-2">
                <div className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-2xl font-bold text-xs shadow-lg transition flex items-center space-x-2 group-hover:scale-105">
                  <Maximize2 className="w-4 h-4" />
                  <span>Launch Full Interactive Dashboard</span>
                </div>
                <span className="text-[11px] text-slate-300 font-medium">Click to interact with full OpenLayers GIS controls & AI Assistant</span>
              </div>
            </div>

            {/* Bottom Legend & Verification Timestamp */}
            <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between bg-slate-900/90 backdrop-blur-md px-3.5 py-2 rounded-xl text-white text-xs border border-slate-700/60 pointer-events-none">
              <div className="flex items-center space-x-2">
                <Clock className="w-3.5 h-3.5 text-blue-400" />
                <span className="font-mono text-[11px]">17 Sep 2026 14:25 IST · Lead Time: +30m</span>
              </div>
              <div className="flex items-center space-x-1.5 text-[10px] text-amber-300 font-semibold">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                <span>Modality: {previewLayer.toUpperCase()} (Benchmark Simulation)</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* 4. MULTI-SOURCE INTELLIGENCE SECTION */}
      {/* ========================================================================= */}
      <section className="w-full max-w-5xl mx-auto px-6 py-20 space-y-10">
        <div className="space-y-3">
          <div className="text-xs font-bold text-blue-600 uppercase tracking-wider">
            Data Provenance & Integrity
          </div>
          <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
            Multi-Source Meteorological Intelligence
          </h2>
          <p className="text-xs sm:text-sm text-slate-600 max-w-3xl leading-relaxed">
            STORMTRACE ingests satellite radiances, Doppler radar volume mosaics, lightning climatology, numerical weather prediction, and calibrated precipitation. Every ingested modality is strictly governed by our provenance registry.
          </p>
          <div>
            <button
              onClick={onOpenAbout}
              className="text-xs font-bold text-blue-600 hover:text-blue-800 inline-flex items-center space-x-1 mt-1"
            >
              <span>Learn more about data provenance & verification</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Row of 5 Dynamically-Sourced Modality Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {provenanceCards.map((card) => {
            const isPending = card.isPending;
            const isClimatology = card.isClimatology;
            const isDemo = card.isDemo;

            return (
              <div
                key={card.id}
                className="p-5 rounded-2xl bg-white border border-slate-200/90 shadow-xs hover:shadow-md transition flex flex-col justify-between space-y-4"
              >
                <div className="space-y-2.5">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold text-slate-400 tracking-wider uppercase">
                      {card.source}
                    </span>
                    <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold ${
                      isClimatology
                        ? 'bg-blue-50 text-blue-700 border border-blue-200'
                        : isDemo
                        ? 'bg-amber-50 text-amber-700 border border-amber-200'
                        : 'bg-slate-100 text-slate-600 border border-slate-200'
                    }`}>
                      {card.statusBadge}
                    </span>
                  </div>

                  <h4 className="text-sm font-bold text-slate-900">{card.name}</h4>
                  <p className="text-xs text-slate-600 leading-relaxed">{card.description}</p>
                </div>

                <div className="pt-3 border-t border-slate-100 space-y-1.5 text-[11px]">
                  <div className="text-slate-500">
                    <span className="font-semibold text-slate-700">Resolution:</span> {card.resolution}
                  </div>
                  <div className="text-[10.5px] text-slate-500 italic">
                    {card.provenanceNote}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* ========================================================================= */}
      {/* 5. MISSION BANNER */}
      {/* ========================================================================= */}
      <section className="w-full bg-slate-900 text-white py-16 px-6 mt-auto">
        <div className="max-w-4xl mx-auto text-center space-y-6">
          <div className="w-12 h-12 rounded-2xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400 mx-auto shadow-inner">
            <Sparkles className="w-6 h-6" />
          </div>

          <div className="space-y-2">
            <h3 className="text-xl sm:text-2xl font-bold tracking-tight">Our Mission</h3>
            <p className="text-xs sm:text-sm text-slate-300 max-w-2xl mx-auto leading-relaxed font-normal">
              To empower operational meteorologists, aviation air traffic controllers, and disaster response agencies with transparent, verifiable AI decision support for severe convective storms and lightning.
            </p>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
            <button
              onClick={() => onNavigate('dashboard')}
              className="px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs transition shadow-md flex items-center space-x-1.5"
            >
              <span>Explore Live Nowcasting Map</span>
              <ArrowRight className="w-4 h-4" />
            </button>
            <button
              onClick={onOpenAbout}
              className="px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold text-xs border border-slate-700 transition"
            >
              Read Technical Dossier
            </button>
          </div>

          <div className="pt-8 border-t border-slate-800/80 text-[11px] text-slate-500 flex flex-col sm:flex-row items-center justify-between gap-2">
            <span>© 2026 STORMTRACE · Team Targaryen (PS 26072)</span>
            <span>Operational Advisory: Automated AI Guidance · Not an Official IMD Warning</span>
          </div>
        </div>
      </section>

      {/* Safety Tips Modal */}
      <SafetyTipsModal
        isOpen={isSafetyTipsOpen}
        onClose={() => setIsSafetyTipsOpen(false)}
      />
    </div>
  );
}
