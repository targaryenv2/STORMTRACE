import React, { useState } from 'react';
import { 
  Layers, 
  CloudLightning, 
  Zap, 
  Flame, 
  Radar, 
  Satellite, 
  ShieldAlert, 
  Navigation, 
  Building2, 
  Gauge,
  X,
  ChevronDown,
  ChevronRight
} from 'lucide-react';

export default function LayerControls({
  activeLayer = 'thunderstorm',
  setActiveLayer,
  showUncertainty = true,
  setShowUncertainty,
  showCells = true,
  setShowCells,
  showTrajectories = true,
  setShowTrajectories,
  showImpactZones = true,
  setShowImpactZones,
  onClose
}) {
  const [showTechnicalDetails, setShowTechnicalDetails] = useState(false);

  const forecastLayers = [
    {
      id: 'thunderstorm',
      label: 'Thunderstorm risk',
      icon: CloudLightning,
      description: 'Probability of thunderstorm occurrence'
    },
    {
      id: 'lightning',
      label: 'Lightning risk',
      icon: Zap,
      description: 'Probability of cloud-to-ground lightning'
    },
    {
      id: 'severity',
      label: 'Storm severity',
      icon: Flame,
      description: 'Estimated convective intensity index'
    }
  ];

  const observationLayers = [
    {
      id: 'radar',
      label: 'Radar',
      icon: Radar,
      description: 'Current Doppler weather radar reflectivity'
    },
    {
      id: 'satellite',
      label: 'Satellite',
      icon: Satellite,
      description: 'INSAT-3DR thermal infrared cloud tops'
    }
  ];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-2xl w-80 text-slate-200 select-none space-y-4 animate-in fade-in slide-in-from-left-4 duration-150">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-2.5">
        <div className="flex items-center space-x-2">
          <Layers className="w-4 h-4 text-sky-400" />
          <h3 className="font-semibold text-sm text-slate-100">Map layers</h3>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Forecast Layers */}
      <div className="space-y-1.5">
        <span className="text-[11px] font-medium text-slate-400">Forecast maps</span>
        <div className="space-y-1">
          {forecastLayers.map((layer) => {
            const Icon = layer.icon;
            const isSelected = activeLayer === layer.id;
            return (
              <button
                key={layer.id}
                onClick={() => setActiveLayer(layer.id)}
                className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs transition text-left ${
                  isSelected
                    ? 'bg-sky-600/20 text-sky-300 font-medium border border-sky-500/30'
                    : 'text-slate-300 hover:bg-slate-800/60 border border-transparent'
                }`}
              >
                <div className="flex items-center space-x-2.5">
                  <Icon className={`w-4 h-4 ${isSelected ? 'text-sky-400' : 'text-slate-400'}`} />
                  <span>{layer.label}</span>
                </div>
                {isSelected && (
                  <span className="w-1.5 h-1.5 rounded-full bg-sky-400" />
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Observations */}
      <div className="space-y-1.5">
        <span className="text-[11px] font-medium text-slate-400">Live observations</span>
        <div className="space-y-1">
          {observationLayers.map((layer) => {
            const Icon = layer.icon;
            const isSelected = activeLayer === layer.id;
            return (
              <button
                key={layer.id}
                onClick={() => setActiveLayer(layer.id)}
                className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs transition text-left ${
                  isSelected
                    ? 'bg-sky-600/20 text-sky-300 font-medium border border-sky-500/30'
                    : 'text-slate-300 hover:bg-slate-800/60 border border-transparent'
                }`}
              >
                <div className="flex items-center space-x-2.5">
                  <Icon className={`w-4 h-4 ${isSelected ? 'text-sky-400' : 'text-slate-400'}`} />
                  <span>{layer.label}</span>
                </div>
                {isSelected && (
                  <span className="w-1.5 h-1.5 rounded-full bg-sky-400" />
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Overlays */}
      <div className="space-y-2 pt-2 border-t border-slate-800/80">
        <span className="text-[11px] font-medium text-slate-400">Map overlays</span>
        <div className="space-y-1">
          <label className="flex items-center justify-between px-3 py-2 rounded-lg hover:bg-slate-800/50 cursor-pointer transition">
            <div className="flex items-center space-x-2.5 text-xs text-slate-300">
              <ShieldAlert className="w-4 h-4 text-slate-400" />
              <span>Storm cells</span>
            </div>
            <input
              type="checkbox"
              checked={showCells}
              onChange={(e) => setShowCells(e.target.checked)}
              className="rounded bg-slate-800 border-slate-700 text-sky-600 focus:ring-sky-500 focus:ring-offset-slate-900 w-4 h-4"
            />
          </label>

          <label className="flex items-center justify-between px-3 py-2 rounded-lg hover:bg-slate-800/50 cursor-pointer transition">
            <div className="flex items-center space-x-2.5 text-xs text-slate-300">
              <Navigation className="w-4 h-4 text-slate-400" />
              <span>Projected storm paths</span>
            </div>
            <input
              type="checkbox"
              checked={showTrajectories}
              onChange={(e) => setShowTrajectories(e.target.checked)}
              className="rounded bg-slate-800 border-slate-700 text-sky-600 focus:ring-sky-500 focus:ring-offset-slate-900 w-4 h-4"
            />
          </label>

          <label className="flex items-center justify-between px-3 py-2 rounded-lg hover:bg-slate-800/50 cursor-pointer transition">
            <div className="flex items-center space-x-2.5 text-xs text-slate-300">
              <Building2 className="w-4 h-4 text-slate-400" />
              <span>Infrastructure zones</span>
            </div>
            <input
              type="checkbox"
              checked={showImpactZones}
              onChange={(e) => setShowImpactZones(e.target.checked)}
              className="rounded bg-slate-800 border-slate-700 text-sky-600 focus:ring-sky-500 focus:ring-offset-slate-900 w-4 h-4"
            />
          </label>

          <label className="flex items-center justify-between px-3 py-2 rounded-lg hover:bg-slate-800/50 cursor-pointer transition">
            <div className="flex items-center space-x-2.5 text-xs text-slate-300">
              <Gauge className="w-4 h-4 text-slate-400" />
              <span>Confidence range</span>
            </div>
            <input
              type="checkbox"
              checked={showUncertainty}
              onChange={(e) => setShowUncertainty(e.target.checked)}
              className="rounded bg-slate-800 border-slate-700 text-sky-600 focus:ring-sky-500 focus:ring-offset-slate-900 w-4 h-4"
            />
          </label>
        </div>
      </div>

      {/* Technical details toggle (collapsed by default) */}
      <div className="pt-2 border-t border-slate-800/80">
        <button
          onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
          className="w-full flex items-center justify-between text-[11px] text-slate-400 hover:text-slate-300 py-1 transition"
        >
          <span>Technical details</span>
          {showTechnicalDetails ? (
            <ChevronDown className="w-3.5 h-3.5" />
          ) : (
            <ChevronRight className="w-3.5 h-3.5" />
          )}
        </button>

        {showTechnicalDetails && (
          <div className="mt-2 p-2.5 bg-slate-950/60 rounded-lg border border-slate-800/80 text-[10px] font-mono text-slate-400 space-y-1">
            <div>WMS 1.3.0 · GeoServer Raster Layer</div>
            <div>WFS 2.0.0 · PostGIS Spatial Engine</div>
            <div>Projection: EPSG:3857 (Web Mercator)</div>
            <div>Model: Spatio-Temporal ConvLSTM + MC-Dropout</div>
          </div>
        )}
      </div>
    </div>
  );
}
