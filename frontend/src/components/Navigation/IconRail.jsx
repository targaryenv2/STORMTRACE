import React from 'react';
import { Layers, ShieldAlert, History } from 'lucide-react';

export default function IconRail({
  activeDrawer = null,
  onToggleDrawer,
  cellCount = 0
}) {
  const items = [
    {
      id: 'layers',
      label: 'Map layers',
      icon: Layers
    },
    {
      id: 'cells',
      label: 'Active storms',
      icon: ShieldAlert,
      badge: cellCount > 0 ? cellCount : null
    },
    {
      id: 'analogs',
      label: 'Historical analogs',
      icon: History
    }
  ];

  return (
    <div id="icon-rail" className="absolute top-4 left-4 z-30 flex flex-col items-center bg-slate-900 border border-slate-800 rounded-xl p-1.5 shadow-xl select-none space-y-1">
      {items.map((item) => {
        const Icon = item.icon;
        const isActive = activeDrawer === item.id;
        return (
          <div key={item.id} className="relative group">
            <button
              onClick={() => onToggleDrawer(item.id)}
              className={`relative p-2.5 rounded-lg transition flex items-center justify-center ${
                isActive
                  ? 'bg-sky-600/20 text-sky-400 border border-sky-500/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
              title={item.label}
              aria-label={item.label}
            >
              <Icon className="w-5 h-5" />
              {item.badge !== null && (
                <span className="absolute -top-1 -right-1 min-w-[16px] h-4 px-1 rounded-full bg-rose-600 text-white text-[9px] font-bold font-mono flex items-center justify-center shadow-sm">
                  {item.badge}
                </span>
              )}
            </button>

            {/* Tooltip on hover */}
            <div className="absolute left-full ml-2 top-1/2 -translate-y-1/2 px-2.5 py-1 bg-slate-900 border border-slate-800 text-slate-200 text-xs rounded-md shadow-lg pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-50">
              {item.label}
            </div>
          </div>
        );
      })}
    </div>
  );
}
