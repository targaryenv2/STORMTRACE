import React, { useEffect, useState } from 'react';
import { History, RefreshCw, X, AlertTriangle, ExternalLink } from 'lucide-react';

export default function HistoricalAnalogsPanel({ selectedCellId, onClose }) {
  const [loading, setLoading] = useState(false);
  const [analogsData, setAnalogsData] = useState(null);

  useEffect(() => {
    fetchAnalogs();
  }, [selectedCellId]);

  const fetchAnalogs = async () => {
    setLoading(true);
    try {
      const cellParam = selectedCellId ? `?cell_id=${selectedCellId}` : '';
      const res = await fetch(`/api/v1/analogs/current${cellParam}`);
      if (res.ok) {
        const data = await res.json();
        setAnalogsData(data);
      } else {
        setAnalogsData({
          query_cell_id: selectedCellId || 'No Cell Selected',
          analog_events: []
        });
      }
    } catch (err) {
      console.warn('Using offline analogs fallback:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-2xl w-84 text-slate-200 select-none flex flex-col max-h-[calc(100vh-140px)] space-y-3 animate-in fade-in slide-in-from-left-4 duration-150">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-2.5">
        <div className="flex items-center space-x-2">
          <History className="w-4 h-4 text-sky-400" />
          <div>
            <h3 className="font-semibold text-sm text-slate-100">Historical analogs</h3>
          </div>
        </div>
        <div className="flex items-center space-x-1">
          <button
            onClick={fetchAnalogs}
            disabled={loading}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition"
            title="Refresh analogs"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
          {onClose && (
            <button
              onClick={onClose}
              className="p-1 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      <div className="text-[11px] text-slate-400">
        Past convective events with similar radar, satellite, and atmospheric profiles:
      </div>

      {loading ? (
        <div className="py-8 flex flex-col items-center justify-center text-slate-400 space-y-2">
          <RefreshCw className="w-4 h-4 animate-spin text-sky-400" />
          <span className="text-xs">Finding matching historical patterns...</span>
        </div>
      ) : (
        <div className="space-y-2.5 overflow-y-auto pr-1 flex-1 custom-scrollbar">
          {(analogsData?.analogs || analogsData?.analog_events || []).map((analog, idx) => (
            <div
              key={analog.analog_id || idx}
              className="p-3 rounded-xl bg-slate-950/40 border border-slate-800/80 hover:border-slate-700 transition text-left space-y-2"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-200">
                  {analog.location || analog.location_name}
                </span>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-sky-500/10 text-sky-300 border border-sky-500/20 font-medium">
                  {Math.round((analog.similarity_score || 0.85) * 100)}% match
                </span>
              </div>

              <div className="text-[11px] text-slate-400">
                {analog.date} · {analog.observed_outcome || analog.outcome_summary}
              </div>

              <div className="grid grid-cols-3 gap-1.5 pt-2 border-t border-slate-800/60 text-[11px]">
                <div className="bg-slate-900 px-2 py-1 rounded-lg">
                  <span className="text-slate-400 text-[10px] block">Radar</span>
                  <span className="text-slate-200 font-medium">{analog.max_dbz || analog.peak_dbz} dBZ</span>
                </div>
                <div className="bg-slate-900 px-2 py-1 rounded-lg">
                  <span className="text-slate-400 text-[10px] block">Lightning</span>
                  <span className="text-slate-200 font-medium">{analog.max_lightning_rate || analog.max_wind_kmh}</span>
                </div>
                <div className="bg-slate-900 px-2 py-1 rounded-lg">
                  <span className="text-slate-400 text-[10px] block">CSI Skill</span>
                  <span className="text-slate-200 font-medium">{analog.skill_score_csi || analog.lightning_flash_count || '--'}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
