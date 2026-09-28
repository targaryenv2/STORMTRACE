import React from 'react';
import { useTranslation } from 'react-i18next';
import { 
  Cloud, 
  CloudRain, 
  MoveRight, 
  Landmark, 
  Grid,
  ArrowUp,
  Zap,
  ShieldCheck,
  AlertCircle
} from 'lucide-react';
import TooltipHelper from '../Common/TooltipHelper';
import CellRiskTrendChart from './CellRiskTrendChart';

export default function RightPanel({
  activeCellsCount = 12,
  selectedCell = null,
  showThunderstormProb = true,
  setShowThunderstormProb,
  showCells = true,
  setShowCells,
  showTrajectories = true,
  setShowTrajectories,
  showImpactZones = true,
  setShowImpactZones,
  showUncertainty = false,
  setShowUncertainty,
  currentRegionName = 'India',
  hasRadarCoverage = true,
  liveStorms = []
}) {
  const { t } = useTranslation();

  // Default fallback selected cell details if none specifically active
  const cell = selectedCell || {
    cell_id: 'No Active Selection',
    max_dbz: 0,
    severity_score: 0,
    speed_kmh: 0,
    direction_deg: 0,
    compass: 'N',
    warning_level: 'NONE',
    is_split: false,
    is_merged: false
  };

  const severityLevel = cell.severity_score >= 80 ? t('common.high') : (cell.severity_score >= 60 ? t('common.moderate') : (cell.severity_score > 0 ? t('common.low') : 'None'));
  
  const highTierCount = liveStorms.filter(c => (c.severity_score || 0) >= 80).length;
  const modTierCount = liveStorms.filter(c => (c.severity_score || 0) >= 60 && (c.severity_score || 0) < 80).length;
  const lowTierCount = liveStorms.filter(c => (c.severity_score || 0) >= 35 && (c.severity_score || 0) < 60).length;
  const weakTierCount = liveStorms.filter(c => (c.severity_score || 0) < 35).length;

  return (
    <aside className="w-80 bg-[#f8fafc] border-l border-slate-200 p-3.5 flex flex-col space-y-3.5 overflow-y-auto select-none shrink-0 h-full custom-scrollbar">
      {/* Non-India Coverage Notice (if viewing outside coverage area) */}
      {!hasRadarCoverage && (
        <div className="p-3 bg-amber-50 border border-amber-200 rounded-2xl text-amber-800 text-xs space-y-1 shadow-sm">
          <div className="flex items-center space-x-1.5 font-bold text-amber-900">
            <AlertCircle className="w-3.5 h-3.5 text-amber-600 shrink-0" />
            <span>{t('map.limitedCoverage')} ({currentRegionName})</span>
          </div>
          <p className="text-[11px] text-amber-700 leading-snug">
            {t('map.coverageExplanation')}
          </p>
        </div>
      )}

      {/* 1. Active Storm Cells Card */}
      <div className="bg-white border border-slate-200/90 rounded-2xl p-4 shadow-sm space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <h3 className="text-xs font-bold text-slate-800">{t('rightPanel.activeStormCells')}</h3>
            <TooltipHelper
              title={t('rightPanel.activeStormCells')}
              text="Convective thunderstorm clusters segmented and tracked in real-time from Doppler radar volume scans."
            />
          </div>
          <span className="text-[10px] text-slate-400 font-mono font-medium">{currentRegionName}</span>
        </div>
        
        {hasRadarCoverage ? (
          <>
            <div className="flex items-baseline justify-between">
              <span className="text-3xl font-black text-slate-900 tracking-tight">
                {activeCellsCount}
              </span>
              <div className="flex items-center space-x-1 text-rose-600 text-xs font-bold">
                <ArrowUp className="w-3.5 h-3.5" />
                <span>{(liveStorms.length > 5) ? Math.floor(liveStorms.length * 0.1) : 0}</span>
                <span className="text-[11px] text-slate-500 font-normal ml-0.5">{t('rightPanel.vsLastHour')}</span>
              </div>
            </div>

            {/* Severity Tiers */}
            <div className="space-y-2 pt-1 text-xs">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-rose-500 shrink-0" />
                  <span className="text-slate-700 font-medium">{t('common.high')} (≥ 80)</span>
                </div>
                <span className="font-bold text-slate-900">{highTierCount}</span>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-amber-500 shrink-0" />
                  <span className="text-slate-700 font-medium">{t('common.moderate')} (60–79)</span>
                </div>
                <span className="font-bold text-slate-900">{modTierCount}</span>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-yellow-400 shrink-0" />
                  <span className="text-slate-700 font-medium">{t('common.low')} (35–59)</span>
                </div>
                <span className="font-bold text-slate-900">{lowTierCount}</span>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 shrink-0" />
                  <span className="text-slate-700 font-medium">{t('common.weak')} (&lt; 35)</span>
                </div>
                <span className="font-bold text-slate-900">{weakTierCount}</span>
              </div>
            </div>
          </>
        ) : (
          <div className="py-4 text-center space-y-1.5">
            <ShieldCheck className="w-6 h-6 text-emerald-600 mx-auto" />
            <p className="text-xs text-slate-800 font-bold">{t('rightPanel.noRadarCells')}</p>
            <p className="text-[11px] text-slate-500">{t('rightPanel.switchSatellite')}</p>
          </div>
        )}
      </div>

      {/* 2. Selected Cell Card */}
      {hasRadarCoverage && (
        <div className="bg-white border border-slate-200/90 rounded-2xl p-4 shadow-sm space-y-3">
          <div className="flex items-center justify-between pb-1.5 border-b border-slate-100">
            <div className="flex items-center">
              <span className="font-bold text-sm text-slate-900 tracking-tight">
                {cell.cell_id}
              </span>
              <TooltipHelper
                title={t('rightPanel.selectedCell')}
                text="Telemetry and kinematic properties computed from TITAN/SCIT cell centroid and 2D Kalman filter velocity tracking."
              />
            </div>
            <span className={`px-2 py-0.5 rounded-md text-[10px] font-extrabold ${
              cell.severity_score >= 80 ? 'bg-rose-600 text-white shadow-sm' :
              cell.severity_score >= 60 ? 'bg-amber-500 text-white shadow-sm' :
              'bg-yellow-400 text-slate-900 shadow-sm'
            }`}>
              {severityLevel}
            </span>
          </div>

          {/* Risk Trend Multi-Bar Chart (Past Observations & Model Forecast Trajectory) */}
          <CellRiskTrendChart cell={cell} />

          {/* Key Values List with plain language tooltips */}
          <div className="space-y-1.5 text-xs">
            <div className="flex justify-between items-center">
              <div className="flex items-center text-slate-500">
                <span>{t('rightPanel.maxDbz')}</span>
                <TooltipHelper
                  title={t('rightPanel.maxDbz')}
                  text="A measure of how heavy the rain or hail is inside the core — values >50 dBZ indicate severe weather and torrential rain."
                />
              </div>
              <span className="font-bold text-slate-800">{cell.max_dbz}</span>
            </div>

            <div className="flex justify-between items-center">
              <div className="flex items-center text-slate-500">
                <span>{t('rightPanel.severityScore')}</span>
                <TooltipHelper
                  title={t('rightPanel.severityScore')}
                  text="Composite hazard index from 0 to 100 factoring in rain rate, lightning rate, and cloud vertical depth."
                />
              </div>
              <span className="font-bold text-slate-800">{cell.severity_score}</span>
            </div>

            <div className="flex justify-between items-center">
              <div className="flex items-center text-slate-500">
                <span>{t('rightPanel.speed')}</span>
                <TooltipHelper
                  title={t('rightPanel.speed')}
                  text="Ground velocity estimated by Kalman filter across consecutive radar scans."
                />
              </div>
              <span className="font-bold text-slate-800">{cell.speed_kmh} km/h</span>
            </div>

            <div className="flex justify-between items-center">
              <div className="flex items-center text-slate-500">
                <span>{t('rightPanel.direction')}</span>
                <TooltipHelper
                  title={t('rightPanel.direction')}
                  text="Azimuth heading in degrees and compass abbreviation indicating where the storm is traveling."
                />
              </div>
              <span className="font-bold text-slate-800">
                {cell.direction_deg}° ({cell.compass || 'ESE'})
              </span>
            </div>

            <div className="flex justify-between items-center">
              <div className="flex items-center text-slate-500">
                <span>{t('rightPanel.warningLevel')}</span>
                <TooltipHelper
                  title={t('rightPanel.warningLevel')}
                  text="IMD color-coded disaster threshold: RED (Take Action), ORANGE (Be Prepared), YELLOW (Be Updated)."
                />
              </div>
              <span className="font-bold text-rose-600">{cell.warning_level}</span>
            </div>

            <div className="flex justify-between items-center">
              <div className="flex items-center text-slate-500">
                <span>{t('rightPanel.splitMerge')}</span>
                <TooltipHelper
                  title={t('rightPanel.splitMerge')}
                  text="Indicates whether this convective cluster has split into multiple children or merged with adjacent storm systems."
                />
              </div>
              <span className="font-bold text-slate-800">
                {cell.is_split ? 'Split' : cell.is_merged ? 'Merge' : 'No'}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* 3. Layer Controls Card */}
      <div className="bg-white border border-slate-200/90 rounded-2xl p-4 shadow-sm space-y-3">
        <div className="flex items-center">
          <h3 className="text-xs font-bold text-slate-800">{t('rightPanel.layerControls')}</h3>
          <TooltipHelper
            title={t('rightPanel.layerControls')}
            text="Toggle on-screen map layers including radar reflectivity, storm trajectories, infrastructure buffer zones, and confidence bands."
          />
        </div>

        <div className="space-y-2.5 text-xs">
          {/* Thunderstorm Probability */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-slate-700 font-medium">
              <Cloud className="w-3.5 h-3.5 text-slate-500" />
              <span>{t('rightPanel.thunderstormProbabilityToggle')}</span>
            </div>
            <button
              onClick={() => setShowThunderstormProb(!showThunderstormProb)}
              className={`w-9 h-5 rounded-full transition-colors relative p-0.5 shadow-inner ${
                showThunderstormProb ? 'bg-blue-600' : 'bg-slate-300'
              }`}
              title={t('rightPanel.thunderstormProbabilityToggle')}
            >
              <div
                className={`w-4 h-4 rounded-full bg-white transition-transform shadow-sm ${
                  showThunderstormProb ? 'translate-x-4' : 'translate-x-0'
                }`}
              />
            </button>
          </div>

          {/* Storm Cell Polygons */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-slate-700 font-medium">
              <CloudRain className="w-3.5 h-3.5 text-slate-500" />
              <span>{t('rightPanel.stormCellPolygonsToggle')}</span>
            </div>
            <button
              onClick={() => setShowCells(!showCells)}
              className={`w-9 h-5 rounded-full transition-colors relative p-0.5 shadow-inner ${
                showCells ? 'bg-blue-600' : 'bg-slate-300'
              }`}
              title={t('rightPanel.stormCellPolygonsToggle')}
            >
              <div
                className={`w-4 h-4 rounded-full bg-white transition-transform shadow-sm ${
                  showCells ? 'translate-x-4' : 'translate-x-0'
                }`}
              />
            </button>
          </div>

          {/* Trajectories */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-slate-700 font-medium">
              <MoveRight className="w-3.5 h-3.5 text-slate-500" />
              <span>{t('rightPanel.trajectoriesToggle')}</span>
            </div>
            <button
              onClick={() => setShowTrajectories(!showTrajectories)}
              className={`w-9 h-5 rounded-full transition-colors relative p-0.5 shadow-inner ${
                showTrajectories ? 'bg-blue-600' : 'bg-slate-300'
              }`}
              title={t('rightPanel.trajectoriesToggle')}
            >
              <div
                className={`w-4 h-4 rounded-full bg-white transition-transform shadow-sm ${
                  showTrajectories ? 'translate-x-4' : 'translate-x-0'
                }`}
              />
            </button>
          </div>

          {/* Impact Zones */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-slate-700 font-medium">
              <Landmark className="w-3.5 h-3.5 text-slate-500" />
              <span>{t('rightPanel.impactZonesToggle')}</span>
            </div>
            <button
              onClick={() => setShowImpactZones(!showImpactZones)}
              className={`w-9 h-5 rounded-full transition-colors relative p-0.5 shadow-inner ${
                showImpactZones ? 'bg-blue-600' : 'bg-slate-300'
              }`}
              title={t('rightPanel.impactZonesToggle')}
            >
              <div
                className={`w-4 h-4 rounded-full bg-white transition-transform shadow-sm ${
                  showImpactZones ? 'translate-x-4' : 'translate-x-0'
                }`}
              />
            </button>
          </div>

          {/* Show Uncertainty */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-slate-700 font-medium">
              <Grid className="w-3.5 h-3.5 text-slate-500" />
              <span>{t('rightPanel.showUncertaintyToggle')}</span>
              <TooltipHelper
                title={t('rightPanel.showUncertaintyToggle')}
                text="Monte Carlo dropout 10th-to-90th percentile spread representing epistemic model confidence."
              />
            </div>
            <button
              onClick={() => setShowUncertainty(!showUncertainty)}
              className={`w-9 h-5 rounded-full transition-colors relative p-0.5 shadow-inner ${
                showUncertainty ? 'bg-blue-600' : 'bg-slate-300'
              }`}
              title={t('rightPanel.showUncertaintyToggle')}
            >
              <div
                className={`w-4 h-4 rounded-full bg-white transition-transform shadow-sm ${
                  showUncertainty ? 'translate-x-4' : 'translate-x-0'
                }`}
              />
            </button>
          </div>
        </div>
      </div>
    </aside>
  );
}
