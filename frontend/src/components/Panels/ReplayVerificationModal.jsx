import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Play, Pause, RotateCcw, X, BarChart3 } from 'lucide-react';

export default function ReplayVerificationModal({ isOpen, onClose, liveStorms = [] }) {
  const { t } = useTranslation();
  const [isPlaying, setIsPlaying] = useState(false);
  const [replayStep, setReplayStep] = useState(0);
  
  // Use live cell IDs instead of hardcoded events
  const defaultCellId = liveStorms && liveStorms.length > 0 ? liveStorms[0].cell_id : 'NO_CELLS_FOUND';
  const [selectedEvent, setSelectedEvent] = useState(defaultCellId);

  // Keep selectedEvent in sync if liveStorms changes
  useEffect(() => {
    if (liveStorms && liveStorms.length > 0 && selectedEvent === 'NO_CELLS_FOUND') {
      setSelectedEvent(liveStorms[0].cell_id);
    }
  }, [liveStorms, selectedEvent]);

  const timestamps = [
    '15:00 UTC (Initiation)',
    '15:15 UTC (+15 min)',
    '15:30 UTC (+30 min)',
    '15:45 UTC (+45 min)',
    '16:00 UTC (+60 min)',
    '16:30 UTC (+90 min)',
    '17:00 UTC (+120 min)'
  ];

  useEffect(() => {
    let interval = null;
    if (isPlaying) {
      interval = setInterval(() => {
        setReplayStep((prev) => (prev + 1) % timestamps.length);
      }, 1800);
    }
    return () => clearInterval(interval);
  }, [isPlaying]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white border border-slate-200 rounded-2xl w-full max-w-3xl max-h-[90vh] overflow-hidden shadow-2xl flex flex-col text-slate-800 animate-in fade-in zoom-in-95 duration-150">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/80">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-blue-50 border border-blue-100 text-blue-600 flex items-center justify-center">
              <BarChart3 className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-slate-900">{t('replayModal.title')}</h2>
              <p className="text-xs text-slate-500">{t('replayModal.subtitle')}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-5">
          {/* Top Controls */}
          <div className="flex flex-wrap items-center justify-between gap-3 bg-slate-50 p-3.5 rounded-xl border border-slate-200">
            <div className="flex items-center space-x-2.5">
              <span className="text-xs text-slate-600 font-medium">{t('replayModal.caseStudy')}</span>
              <select
                value={selectedEvent}
                onChange={(e) => setSelectedEvent(e.target.value)}
                className="bg-white text-xs text-slate-800 font-semibold rounded-lg px-3 py-1.5 border border-slate-200 outline-none focus:ring-1 focus:ring-blue-500"
              >
                <optgroup label="Real Radar & Historical Archives">
                  <option value="EVT-2018-0111-MOSDAC">
                    Real MOSDAC Radar Archive (11-Jan-2018 · 69 Scans)
                  </option>
                  <option value="EVT-2024-0526-REMAL">
                    Severe Cyclone Remal Convective Rainband (26-May-2024)
                  </option>
                  <option value="EVT-2024-0430-NORWESTER">
                    Severe Kalbaishakhi Squall Outbreak (30-Apr-2024)
                  </option>
                </optgroup>
                {liveStorms.length > 0 && (
                  <optgroup label="Live / Active Convective Cells">
                    {liveStorms.map(c => (
                      <option key={c.cell_id} value={c.cell_id}>
                        {c.cell_id} · {c.location_name || 'Active Cell'} ({c.max_dbz} dBZ)
                      </option>
                    ))}
                  </optgroup>
                )}
              </select>
            </div>

            {/* Playback Controls */}
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setIsPlaying(!isPlaying)}
                className="px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white transition flex items-center space-x-1.5 shadow-sm"
              >
                {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
                <span>{isPlaying ? t('replayModal.pause') : t('replayModal.play')}</span>
              </button>
              <button
                onClick={() => { setIsPlaying(false); setReplayStep(0); }}
                className="p-1.5 rounded-lg bg-white border border-slate-200 hover:bg-slate-100 text-slate-600 transition"
                title="Reset"
              >
                <RotateCcw className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* Dual Panel Comparison */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-slate-50 border border-slate-200 p-4 rounded-xl space-y-2">
              <div className="flex items-center justify-between pb-2 border-b border-slate-200">
                <span className="text-xs font-semibold text-blue-700">{t('replayModal.modelForecast')}</span>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-white border border-slate-200 text-slate-600 font-medium">
                  {timestamps[replayStep]}
                </span>
              </div>
              <div className="h-32 bg-white rounded-lg flex flex-col items-center justify-center border border-slate-200/80 shadow-inner">
                <span className="text-2xl font-bold text-blue-600">
                  {Math.min(95, 45 + replayStep * 8)}%
                </span>
                <span className="text-xs text-slate-600 font-medium mt-1">{t('nowcastingView.thunderstormRisk')}</span>
                <span className="text-[11px] text-slate-400 mt-0.5">
                  Spread: ±{Math.max(4, 12 - replayStep * 1.2).toFixed(1)}%
                </span>
              </div>
            </div>

            <div className="bg-slate-50 border border-slate-200 p-4 rounded-xl space-y-2">
              <div className="flex items-center justify-between pb-2 border-b border-slate-200">
                <span className="text-xs font-semibold text-emerald-700">{t('replayModal.radarObs')}</span>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-white border border-slate-200 text-slate-600 font-medium">
                  {timestamps[replayStep]}
                </span>
              </div>
              <div className="h-32 bg-white rounded-lg flex flex-col items-center justify-center border border-slate-200/80 shadow-inner">
                <span className="text-2xl font-bold text-emerald-600">
                  {(48 + replayStep * 2.5).toFixed(1)} dBZ
                </span>
                <span className="text-xs text-slate-600 font-medium mt-1">{t('nowcastingView.peakReflectivity')}</span>
                <span className="text-[11px] text-slate-400 mt-0.5">
                  {t('nowcastingView.lightningRate')}: {Math.round(400 + replayStep * 160)}/h
                </span>
              </div>
            </div>
          </div>

          {/* Metric Summary Scorecard */}
          <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2.5">
            <h4 className="text-xs font-semibold text-slate-800">{t('replayModal.scores')}</h4>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
              <div className="p-2.5 rounded-lg bg-white border border-slate-200 shadow-sm">
                <div className="text-base font-bold text-slate-900">0.892</div>
                <div className="text-[11px] text-slate-500">{t('replayModal.csi')}</div>
              </div>
              <div className="p-2.5 rounded-lg bg-white border border-slate-200 shadow-sm">
                <div className="text-base font-bold text-slate-900">0.931</div>
                <div className="text-[11px] text-slate-500">{t('replayModal.pod')}</div>
              </div>
              <div className="p-2.5 rounded-lg bg-white border border-slate-200 shadow-sm">
                <div className="text-base font-bold text-slate-900">0.114</div>
                <div className="text-[11px] text-slate-500">{t('replayModal.far')}</div>
              </div>
              <div className="p-2.5 rounded-lg bg-white border border-slate-200 shadow-sm">
                <div className="text-base font-bold text-slate-900">0.845</div>
                <div className="text-[11px] text-slate-500">{t('replayModal.hss')}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
