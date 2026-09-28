import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Settings, CloudLightning, Bell, HelpCircle, Bot } from 'lucide-react';

export default function Header({ 
  onOpenAbout, 
  onOpenSettings, 
  onOpenWalkthrough,
  onToggleAssistant,
  isAssistantOpen,
  onNavigateHome
}) {
  const { t } = useTranslation();
  const [timeStr, setTimeStr] = useState('');

  const [systemMode, setSystemMode] = useState('REAL_HISTORICAL_MODE');

  useEffect(() => {
    // Fetch system mode
    fetch('http://127.0.0.1:8000/api/health')
      .then(res => res.json())
      .then(data => setSystemMode(data.system_mode || 'DEMO_MODE'))
      .catch(err => console.error("Could not fetch API health", err));

    const updateTime = () => {
      const now = new Date();
      const options = { 
        day: '2-digit', 
        month: 'short', 
        year: 'numeric',
        hour: '2-digit', 
        minute: '2-digit', 
        hour12: false, 
        timeZone: 'Asia/Kolkata' 
      };
      const formatted = now.toLocaleDateString('en-GB', options).replace(',', '');
      setTimeStr(`${formatted} IST`);
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="h-14 bg-white border-b border-slate-200 px-5 flex items-center justify-between z-30 shrink-0 select-none shadow-sm">
      {/* Left: Logo + Wordmark + MoES/IMD Ministry Badge */}
      <div 
        className="flex items-center space-x-3.5 cursor-pointer hover:opacity-95 transition"
        onClick={onNavigateHome}
        title="Go to Overview / Landing Page"
      >
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-sm">
            <CloudLightning className="w-5 h-5 text-white" />
          </div>
          <div className="flex flex-col">
            <div className="text-base font-black tracking-tight flex items-center leading-none">
              <span className="text-slate-900">STORM</span>
              <span className="text-blue-600">TRACE</span>
            </div>
            <span className="text-[9px] font-bold text-slate-500 tracking-wider uppercase mt-0.5">
              MoES · IMD | PS #26072
            </span>
          </div>
        </div>
      </div>

      {/* Center: Live Multimodal Sensor Fusion Badges */}
      <div className="hidden lg:flex items-center space-x-2 text-[11px] font-medium">
        <span className="px-2.5 py-0.5 rounded-full bg-blue-50 border border-blue-200 text-blue-700 flex items-center space-x-1 font-semibold">
          <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" />
          <span>Multi-Radar: 9 DWR</span>
        </span>

        <span className="px-2.5 py-0.5 rounded-full bg-sky-50 border border-sky-200 text-sky-700 flex items-center space-x-1">
          <span className="w-1.5 h-1.5 rounded-full bg-sky-500" />
          <span>Sat: INSAT-3DS</span>
        </span>

        <span className="px-2.5 py-0.5 rounded-full bg-purple-50 border border-purple-200 text-purple-700 flex items-center space-x-1">
          <span className="w-1.5 h-1.5 rounded-full bg-purple-500" />
          <span>Lightning: IITM</span>
        </span>

        <span className="px-2.5 py-0.5 rounded-full bg-indigo-50 border border-indigo-200 text-indigo-700 flex items-center space-x-1">
          <span className="w-1.5 h-1.5 rounded-full bg-indigo-500" />
          <span>NWP: ERA5 CAPE</span>
        </span>
      </div>

      {/* Right: Live indicator + Date/Time + Help + Bell + Settings */}
      <div className="flex items-center space-x-3 text-xs">
        {/* Live Status Pill */}
        <div className="flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-700 font-semibold text-[11px]">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span>{t('common.live')}</span>
        </div>

        {/* Dynamic System Mode Badge */}
        {systemMode === 'REAL_HISTORICAL_MODE' ? (
          <div 
            className="flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full bg-emerald-50 border border-emerald-300 text-emerald-800 font-semibold text-[11px] shadow-xs"
            title="Running on real historical DWR radar, INSAT-3DS, and GPM IMERG data."
          >
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            <span className="hidden sm:inline">Real Radar: Live Analytics</span>
          </div>
        ) : (
          <div 
            className="flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full bg-amber-50 border border-amber-300 text-amber-800 font-semibold text-[11px] shadow-xs"
            title="Running on calibrated multimodal demonstration sequence."
          >
            <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
            <span className="hidden sm:inline">Benchmark Mode</span>
          </div>
        )}

        {/* Date / Time */}
        <span className="text-slate-600 font-mono text-[11px] hidden xl:inline-block">
          {timeStr || '17 Sep 2026 14:25 IST'}
        </span>

        {/* AI Assistant Button */}
        <button
          onClick={onToggleAssistant}
          className={`p-1.5 rounded-lg transition flex items-center space-x-1 ${
            isAssistantOpen 
              ? 'bg-blue-600 text-white shadow-sm' 
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
          }`}
          title={t('header.openAssistantTooltip')}
          aria-label={t('header.aiAssistant')}
        >
          <Bot className="w-4 h-4" />
          <span className="text-[11px] font-semibold hidden md:inline-block">{t('header.aiAssistant')}</span>
        </button>

        {/* Walkthrough / Guide Button */}
        <button
          onClick={onOpenWalkthrough}
          className="p-1.5 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition"
          title={t('header.userGuideTooltip')}
          aria-label={t('header.quickGuide')}
        >
          <HelpCircle className="w-4 h-4" />
        </button>

        {/* Notifications Bell */}
        <button
          onClick={onOpenSettings}
          className="p-1.5 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition relative"
          title={t('header.notificationsTooltip')}
          aria-label={t('header.alerts')}
        >
          <Bell className="w-4 h-4" />
          <span className="absolute top-1 right-1 w-1.5 h-1.5 bg-rose-500 rounded-full" />
        </button>

        {/* Settings Button */}
        <button
          onClick={onOpenSettings}
          className="p-1.5 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition"
          title={t('header.settingsTooltip')}
          aria-label={t('header.settings')}
        >
          <Settings className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
}
