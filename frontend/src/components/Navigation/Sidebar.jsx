import React from 'react';
import { useTranslation } from 'react-i18next';
import { 
  Sparkles,
  Home, 
  Cloud, 
  Crosshair, 
  BarChart2, 
  Clock, 
  Globe, 
  Settings, 
  Info,
  Award
} from 'lucide-react';

export default function Sidebar({
  activeNav = 'dashboard',
  onSelectNav
}) {
  const { t } = useTranslation();

  const navItems = [
    { id: 'landing', label: 'Overview / Landing', icon: Sparkles },
    { id: 'dashboard', label: t('sidebar.dashboard'), icon: Home },
    { id: 'nowcasting', label: t('sidebar.nowcasting'), icon: Cloud },
    { id: 'storm_cells', label: t('sidebar.stormCells'), icon: Crosshair },
    { id: 'model_evaluation', label: 'Model Benchmark & Skill', icon: Award },
    { id: 'impact', label: t('sidebar.impact'), icon: BarChart2 },
    { id: 'historical', label: t('sidebar.historical'), icon: Clock },
    { id: 'global_monitoring', label: t('sidebar.globalMonitoring'), icon: Globe },
    { id: 'settings', label: t('sidebar.settings'), icon: Settings },
    { id: 'about', label: t('sidebar.about'), icon: Info }
  ];

  return (
    <aside className="w-52 bg-white border-r border-slate-200 flex flex-col justify-between p-3 select-none shrink-0 h-full shadow-sm">
      {/* Navigation List */}
      <nav className="space-y-1 mt-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeNav === item.id;

          return (
            <button
              key={item.id}
              onClick={() => onSelectNav(item.id)}
              className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-xl text-xs transition text-left ${
                isActive
                  ? 'bg-blue-50 text-blue-600 font-semibold border border-blue-100 shadow-sm'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/80 font-medium'
              }`}
            >
              <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-blue-600' : 'text-slate-400'}`} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Bottom Brand Footer */}
      <div className="px-3 py-3 border-t border-slate-200 text-xs">
        <div className="font-black text-slate-800 tracking-tight text-[11px] flex items-center">
          <span>STORM</span>
          <span className="text-blue-600">TRACE</span>
        </div>
        <div className="text-[11px] text-slate-500 leading-tight mt-0.5">
          {t('common.tagline')}
        </div>
      </div>
    </aside>
  );
}
