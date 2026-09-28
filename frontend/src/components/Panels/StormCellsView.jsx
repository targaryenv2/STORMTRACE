import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { 
  Crosshair, 
  Search, 
  MapPin, 
  Navigation, 
  AlertTriangle, 
  ShieldAlert, 
  Zap, 
  GitFork, 
  ArrowRight,
  Activity,
  ArrowUpDown
} from 'lucide-react';
import TooltipHelper from '../Common/TooltipHelper';

export default function StormCellsView({
  onSelectCellOnMap,
  liveStorms = []
}) {
  const { t } = useTranslation();
  const [filterSeverity, setFilterSeverity] = useState('ALL');
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState('severity'); // 'severity' | 'dbz' | 'speed'

  const filteredCells = liveStorms.filter(cell => {
    const matchesFilter = filterSeverity === 'ALL' || cell.warning_level === filterSeverity;
    const matchesSearch = 
      cell.cell_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (cell.location_name && cell.location_name.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (cell.nearest_airport && cell.nearest_airport.toLowerCase().includes(searchTerm.toLowerCase()));
    return matchesFilter && matchesSearch;
  }).sort((a, b) => {
    if (sortBy === 'severity') return b.severity_score - a.severity_score;
    if (sortBy === 'dbz') return b.max_dbz - a.max_dbz;
    if (sortBy === 'speed') return b.speed_kmh - a.speed_kmh;
    return 0;
  });

  const highThreatCount = liveStorms.filter(c => c.warning_level === 'RED').length;
  const moderateThreatCount = liveStorms.filter(c => c.warning_level === 'ORANGE').length;
  const peakDbz = liveStorms.length > 0 ? Math.max(...liveStorms.map(c => c.max_dbz || 0)) : 0;
  const peakDbzLocation = liveStorms.length > 0 ? (liveStorms.find(c => c.max_dbz === peakDbz)?.location_name || 'Active Cell') : 'None';

  return (
    <div className="w-full h-full bg-[#f8fafc] overflow-y-auto p-6 space-y-6 text-slate-800 custom-scrollbar">
      {/* 1. Header & Summary Stats */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-xl font-bold text-slate-900">{t('stormCellsView.title')}</h1>
            <TooltipHelper
              title={t('stormCellsView.title')}
              text="Comprehensive inventory of all segmented convective storm cells currently tracked across the operational domain by Doppler radar and TITAN algorithms."
            />
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            {t('stormCellsView.subtitle')}
          </p>
        </div>

        {/* Mandatory IMD Advisory Disclaimer */}
        <div className="px-3.5 py-1.5 bg-amber-50 border border-amber-200 rounded-xl text-amber-800 text-xs flex items-center space-x-2 shadow-sm">
          <ShieldAlert className="w-4 h-4 text-amber-600 shrink-0" />
          <span className="text-[11px] font-medium">{t('common.operationalAdvisory')}</span>
        </div>
      </div>

      {/* 2. Top Summary KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm space-y-1">
          <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
            <span>{t('stormCellsView.totalActive')}</span>
            <Crosshair className="w-4 h-4 text-blue-600" />
          </div>
          <div className="text-2xl font-black text-slate-900">{liveStorms.length}</div>
          <div className="text-[11px] text-emerald-600 font-medium">Domain-wide coverage</div>
        </div>

        <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm space-y-1">
          <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
            <span>{t('stormCellsView.highThreat')}</span>
            <AlertTriangle className="w-4 h-4 text-rose-600" />
          </div>
          <div className="text-2xl font-black text-rose-600">{highThreatCount}</div>
          <div className="text-[11px] text-rose-600 font-medium">Max dBZ &gt; 55 / Lightning peak</div>
        </div>

        <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm space-y-1">
          <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
            <span>{t('stormCellsView.moderateThreat')}</span>
            <Activity className="w-4 h-4 text-amber-500" />
          </div>
          <div className="text-2xl font-black text-amber-600">{moderateThreatCount}</div>
          <div className="text-[11px] text-amber-600 font-medium">Precipitation cores 45–55 dBZ</div>
        </div>

        <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm space-y-1">
          <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
            <span>{t('stormCellsView.peakReflectivity')}</span>
            <Zap className="w-4 h-4 text-purple-600" />
          </div>
          <div className="text-2xl font-black text-slate-900">{peakDbz} dBZ</div>
          <div className="text-[11px] text-slate-500 font-medium">{peakDbzLocation}</div>
        </div>
      </div>

      {/* 3. Search, Filter & Sort Controls */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-white p-3.5 rounded-2xl border border-slate-200 shadow-sm">
        <div className="flex items-center space-x-2 flex-1 min-w-[240px]">
          <div className="flex items-center bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5 w-full max-w-xs focus-within:ring-1 focus-within:ring-blue-500">
            <Search className="w-3.5 h-3.5 text-slate-400 mr-2 shrink-0" />
            <input
              type="text"
              placeholder={t('stormCellsView.searchPlaceholder')}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="bg-transparent text-xs text-slate-800 placeholder-slate-400 outline-none w-full"
            />
          </div>
        </div>

        <div className="flex items-center space-x-3 text-xs">
          {/* Severity Filter Pills */}
          <div className="flex items-center space-x-1 bg-slate-50 p-1 rounded-xl border border-slate-200">
            {['ALL', 'RED', 'ORANGE', 'YELLOW'].map(sev => (
              <button
                key={sev}
                onClick={() => setFilterSeverity(sev)}
                className={`px-3 py-1 rounded-lg font-semibold transition ${
                  filterSeverity === sev
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                {sev === 'ALL' ? t('stormCellsView.allTiers') : sev === 'RED' ? t('common.high') : sev === 'ORANGE' ? t('common.moderate') : t('common.watch')}
              </button>
            ))}
          </div>

          {/* Sort selector */}
          <div className="flex items-center space-x-1.5 text-slate-600">
            <ArrowUpDown className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="bg-slate-50 text-slate-800 font-semibold px-2.5 py-1 rounded-xl border border-slate-200 outline-none text-xs"
            >
              <option value="severity">{t('stormCellsView.sortBySeverity')}</option>
              <option value="dbz">{t('stormCellsView.sortByDbz')}</option>
              <option value="speed">{t('stormCellsView.sortBySpeed')}</option>
            </select>
          </div>
        </div>
      </div>

      {/* 4. Detailed Storm Cells Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredCells.length === 0 ? (
          <div className="col-span-full py-12 text-center bg-white rounded-2xl border border-slate-200 p-8 space-y-2">
            <ShieldAlert className="w-8 h-8 text-slate-400 mx-auto" />
            <h3 className="font-bold text-slate-800 text-sm">{t('stormCellsView.emptyNotice')}</h3>
            <p className="text-xs text-slate-500">Try adjusting your search query or severity tier filter.</p>
          </div>
        ) : (
          filteredCells.map((cell) => (
            <div
              key={cell.cell_id}
              className="bg-white border border-slate-200/90 rounded-2xl p-5 shadow-sm hover:shadow-md transition space-y-3.5 flex flex-col justify-between"
            >
              <div>
                {/* Card Top: ID + Badge */}
                <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                  <div className="flex items-center space-x-2">
                    <span className="font-black text-sm text-slate-900">{cell.cell_id}</span>
                    {cell.is_split && (
                      <span className="px-1.5 py-0.5 rounded bg-purple-50 text-purple-700 border border-purple-200 text-[10px] font-semibold flex items-center space-x-0.5">
                        <GitFork className="w-2.5 h-2.5" />
                        <span>Split</span>
                      </span>
                    )}
                    {cell.is_merged && (
                      <span className="px-1.5 py-0.5 rounded bg-indigo-50 text-indigo-700 border border-indigo-200 text-[10px] font-semibold">
                        Merge
                      </span>
                    )}
                  </div>

                  <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-extrabold shadow-sm ${
                    cell.warning_level === 'RED' ? 'bg-rose-600 text-white' :
                    cell.warning_level === 'ORANGE' ? 'bg-amber-500 text-white' :
                    'bg-yellow-400 text-slate-900'
                  }`}>
                    {cell.warning_level === 'RED' ? 'HIGH THREAT' : cell.warning_level === 'ORANGE' ? 'MODERATE' : 'WATCH'}
                  </span>
                </div>

                {/* Location Subtitle */}
                <p className="text-xs font-semibold text-slate-700 mt-2 flex items-center space-x-1">
                  <MapPin className="w-3.5 h-3.5 text-blue-600 shrink-0" />
                  <span className="truncate">{cell.location_name}</span>
                </p>

                {/* Metrics Grid */}
                <div className="grid grid-cols-2 gap-2 mt-3 pt-3 border-t border-slate-100 text-xs">
                  <div className="bg-slate-50 p-2 rounded-xl border border-slate-100 space-y-0.5">
                    <div className="flex items-center text-slate-500 text-[11px]">
                      <span>{t('rightPanel.maxDbz')}</span>
                      <TooltipHelper
                        title={t('rightPanel.maxDbz')}
                        text="Peak Doppler reflectivity: >50 dBZ indicates torrential rain and possible hail."
                      />
                    </div>
                    <div className="text-sm font-bold text-slate-900">{cell.max_dbz} dBZ</div>
                  </div>

                  <div className="bg-slate-50 p-2 rounded-xl border border-slate-100 space-y-0.5">
                    <div className="flex items-center text-slate-500 text-[11px]">
                      <span>{t('rightPanel.severityScore')}</span>
                      <TooltipHelper
                        title={t('rightPanel.severityScore')}
                        text="Composite hazard index (0–100) combining radar reflectivity, vertical depth, and lightning activity."
                      />
                    </div>
                    <div className="text-sm font-bold text-slate-900">{cell.severity_score} / 100</div>
                  </div>

                  <div className="bg-slate-50 p-2 rounded-xl border border-slate-100 space-y-0.5">
                    <div className="flex items-center text-slate-500 text-[11px]">
                      <span>{t('rightPanel.speed')}</span>
                      <TooltipHelper
                        title={t('rightPanel.speed')}
                        text="Velocity vector computed by Kalman filter tracking."
                      />
                    </div>
                    <div className="text-xs font-bold text-slate-900">
                      {cell.speed_kmh} km/h · {cell.compass} ({cell.direction_deg}°)
                    </div>
                  </div>

                  <div className="bg-slate-50 p-2 rounded-xl border border-slate-100 space-y-0.5">
                    <div className="flex items-center text-slate-500 text-[11px]">
                      <span>Flash Density</span>
                      <TooltipHelper
                        title="Lightning Rate"
                        text="Estimated total cloud and ground lightning discharge rate per hour."
                      />
                    </div>
                    <div className="text-xs font-bold text-purple-700">{cell.lightning_rate}</div>
                  </div>
                </div>

                {/* Airport Impact ETA */}
                <div className="mt-3 p-2.5 bg-blue-50/70 border border-blue-100 rounded-xl flex items-center justify-between text-xs">
                  <div className="flex items-center space-x-1.5 truncate text-slate-700">
                    <Navigation className="w-3.5 h-3.5 text-blue-600 shrink-0" />
                    <span className="truncate text-[11px] font-medium">{cell.nearest_airport}</span>
                  </div>
                  <span className="px-2 py-0.5 rounded-md bg-blue-600 text-white font-mono font-bold text-[10px] shrink-0">
                    ETA ~{cell.eta_min}m
                  </span>
                </div>
              </div>

              {/* Action Button: Jump to Live Map */}
              <button
                onClick={() => onSelectCellOnMap && onSelectCellOnMap(cell.cell_id)}
                className="w-full py-2 rounded-xl bg-slate-100 hover:bg-blue-600 text-slate-700 hover:text-white font-semibold text-xs transition flex items-center justify-center space-x-1.5 shadow-sm group"
              >
                <span>{t('stormCellsView.trackOnMap')}</span>
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
