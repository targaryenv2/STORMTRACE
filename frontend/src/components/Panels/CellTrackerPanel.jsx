import React from 'react';
import { 
  ShieldAlert, 
  Navigation, 
  MapPin, 
  X, 
  AlertTriangle,
  GitFork,
  Layers as MergeIcon
} from 'lucide-react';

export default function CellTrackerPanel({
  activeCellsGeojson = null,
  selectedCellId = null,
  onSelectCell,
  impactZonesGeojson = null,
  onClose
}) {
  const features = activeCellsGeojson?.features || [];
  const cells = features.map(f => f.properties);
  const selectedCell = cells.find(c => c.cell_id === selectedCellId) || cells[0];

  const [backendZones, setBackendZones] = React.useState([]);

  React.useEffect(() => {
    fetch('http://127.0.0.1:8000/api/pois')
      .then(res => res.json())
      .then(data => {
        if (data.status === 'success' && data.pois) {
          setBackendZones(data.pois.map(p => ({
            name: `${p.name} (${p.code})`,
            latitude: p.lat,
            longitude: p.lon
          })));
        }
      })
      .catch(console.error);
  }, []);

  const zones = backendZones.length > 0 ? backendZones : (impactZonesGeojson?.features?.map(f => f.properties) || [
    { name: 'Kolkata Airport (CCU)', latitude: 22.65, longitude: 88.44 },
    { name: 'Howrah Junction', latitude: 22.58, longitude: 88.34 },
    { name: 'Kharagpur Station', latitude: 22.33, longitude: 87.32 }
  ]);

  const sortedZones = React.useMemo(() => {
    if (!selectedCell) return [];
    const lat1 = selectedCell.centroid_lat || 22.5;
    const lon1 = selectedCell.centroid_lon || 88.0;
    
    return [...zones].map(zone => {
      const lat2 = zone.latitude || 22.65;
      const lon2 = zone.longitude || 88.44;
      const dLat = (lat2 - lat1) * 111.0;
      const dLon = (lon2 - lon1) * 111.0 * Math.cos((lat1 * Math.PI) / 180);
      const distKm = Math.sqrt(dLat * dLat + dLon * dLon);
      return { ...zone, distKm };
    }).sort((a, b) => a.distKm - b.distKm);
  }, [zones, selectedCell]);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-2xl w-84 text-slate-200 select-none flex flex-col max-h-[calc(100vh-140px)] space-y-3 animate-in fade-in slide-in-from-left-4 duration-150">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-2.5">
        <div className="flex items-center space-x-2">
          <ShieldAlert className="w-4 h-4 text-sky-400" />
          <h3 className="font-semibold text-sm text-slate-100">
            Active storms {cells.length > 0 && `(${cells.length})`}
          </h3>
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

      {/* Storms List */}
      <div className="space-y-2 overflow-y-auto pr-1 flex-shrink-0 max-h-56 custom-scrollbar">
        {cells.length === 0 ? (
          <div className="py-8 text-center space-y-2">
            <div className="w-9 h-9 rounded-full bg-slate-800/80 text-slate-400 flex items-center justify-center mx-auto">
              <ShieldAlert className="w-4 h-4" />
            </div>
            <p className="text-xs text-slate-400">No severe convective storms currently detected in domain.</p>
          </div>
        ) : (
          cells.map((cell) => {
            const isSelected = cell.cell_id === (selectedCell?.cell_id);
            const warningLevel = cell.warning_level || (cell.max_dbz >= 55 ? 'RED' : cell.max_dbz >= 45 ? 'ORANGE' : 'YELLOW');

            return (
              <div
                key={cell.cell_id}
                onClick={() => onSelectCell && onSelectCell(cell.cell_id)}
                className={`p-3 rounded-xl cursor-pointer transition border text-left ${
                  isSelected
                    ? 'bg-sky-950/30 border-sky-500/50 shadow-sm'
                    : 'bg-slate-950/40 hover:bg-slate-800/50 border-slate-800/80'
                }`}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center space-x-2">
                    <span className="font-medium text-xs text-slate-100">
                      {cell.cell_id}
                    </span>
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${
                      warningLevel === 'RED' ? 'bg-rose-500/10 text-rose-300 border border-rose-500/20' :
                      warningLevel === 'ORANGE' ? 'bg-amber-500/10 text-amber-300 border border-amber-500/20' :
                      'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20'
                    }`}>
                      {warningLevel === 'RED' ? 'High threat' : warningLevel === 'ORANGE' ? 'Moderate' : 'Low'}
                    </span>
                    {cell.is_split && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-purple-500/10 text-purple-300 border border-purple-500/20 flex items-center space-x-0.5">
                        <GitFork className="w-2.5 h-2.5" />
                        <span>Split</span>
                      </span>
                    )}
                  </div>
                  <span className="text-xs font-semibold text-slate-200">
                    {cell.max_dbz ? `${Math.round(cell.max_dbz)} dBZ` : '--'}
                  </span>
                </div>

                <div className="flex items-center space-x-4 text-[11px] text-slate-400">
                  <span>Speed: <strong className="text-slate-300 font-normal">{Math.round(cell.speed_kmh || 0)} km/h</strong></span>
                  <span>Heading: <strong className="text-slate-300 font-normal">{Math.round(cell.direction_deg || 0)}°</strong></span>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Selected Storm Arrival ETAs */}
      {selectedCell && (
        <div className="border-t border-slate-800/80 pt-3 space-y-2.5 flex-1 overflow-y-auto custom-scrollbar">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-200 flex items-center space-x-1.5">
              <Navigation className="w-3.5 h-3.5 text-sky-400" />
              <span>Arrival estimates for {selectedCell.cell_id}</span>
            </span>
          </div>

          <div className="bg-slate-950/50 rounded-xl p-2.5 border border-slate-800/80 space-y-1.5">
            {sortedZones.slice(0, 3).map((zone, idx) => {
              const distKm = Math.max(2, zone.distKm);
              const speed = Math.max(20, selectedCell.speed_kmh || 40);
              const etaMin = Math.round((distKm / speed) * 60);

              return (
                <div key={zone.name || idx} className="flex items-center justify-between text-xs py-1">
                  <div className="flex items-center space-x-1.5 truncate text-slate-300">
                    <MapPin className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                    <span className="truncate">{zone.name?.split('(')[0]}</span>
                  </div>
                  <div className="flex items-center space-x-2 text-[11px] shrink-0">
                    <span className="text-slate-400">{Math.round(distKm)} km</span>
                    <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-200 font-medium">
                      ~{etaMin} min
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
