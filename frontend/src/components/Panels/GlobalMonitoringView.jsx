import React from 'react';
import { useTranslation } from 'react-i18next';
import { Globe, Radio, Satellite, Zap, CloudLightning, ArrowRight, AlertCircle, ArrowLeft } from 'lucide-react';

export default function GlobalMonitoringView({ onSelectRegion, onBackToDashboard }) {
  const { t } = useTranslation();

  const regions = [
    {
      id: 'india',
      name: 'India & South Asian Convective Domain',
      status: 'Full Coverage (Operational)',
      statusColor: 'bg-emerald-50 text-emerald-700 border-emerald-200',
      description: 'Full multi-sensor fusion with 34+ IMD Doppler radars, INSAT-3DR/3DS imagery, ground lightning detection network, and high-res NCUM NWP.',
      center: [82.5, 22.0],
      zoom: 5.4,
      radar: 'Live (34 DWR)',
      satellite: 'INSAT-3DR/3DS (4km)',
      lightning: 'Integrated Real-time',
      nwp: 'NCUM 4km'
    }
  ];

  return (
    <div className="h-full w-full bg-[#f8fafc] overflow-y-auto p-6 text-slate-800 select-none custom-scrollbar">
      {/* Top Bar */}
      <div className="flex items-center justify-between border-b border-slate-200 pb-4 mb-6">
        <div>
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-blue-50 border border-blue-200 text-blue-600 flex items-center justify-center">
              <Globe className="w-4 h-4" />
            </div>
            <h1 className="text-lg font-bold text-slate-900">{t('globalMonitoring.title')}</h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            {t('globalMonitoring.subtitle')}
          </p>
        </div>

        <button
          onClick={onBackToDashboard}
          className="flex items-center space-x-2 px-3.5 py-1.5 rounded-xl bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 text-xs font-semibold shadow-sm transition"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>{t('globalMonitoring.backToMap')}</span>
        </button>
      </div>

      {/* Honest Operational Coverage Notice */}
      <div className="mb-6 p-4 rounded-2xl bg-blue-50 border border-blue-200 flex items-start space-x-3 text-xs text-blue-900 shadow-sm">
        <AlertCircle className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />
        <div>
          <span className="font-bold text-blue-950 block mb-0.5">{t('globalMonitoring.multiRegionNote')}</span>
          {t('globalMonitoring.multiRegionBody')}
        </div>
      </div>

      {/* Regional Coverage Grid */}
      <div className="space-y-4">
        <h2 className="text-xs font-bold uppercase tracking-wider text-slate-500">{t('globalMonitoring.matrixTitle')}</h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {regions.map((reg) => (
            <div
              key={reg.id}
              className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm hover:border-slate-300 transition flex flex-col justify-between space-y-3"
            >
              <div>
                <div className="flex items-start justify-between gap-2 mb-1.5">
                  <h3 className="font-bold text-sm text-slate-900">{reg.name}</h3>
                  <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold border shrink-0 ${reg.statusColor}`}>
                    {reg.status}
                  </span>
                </div>

                <p className="text-xs text-slate-600 leading-relaxed mb-3">
                  {reg.description}
                </p>

                {/* Sensor Matrix Breakdown */}
                <div className="grid grid-cols-2 gap-2 text-[11px] font-mono bg-slate-50 p-2.5 rounded-xl border border-slate-100">
                  <div className="flex items-center space-x-1.5">
                    <Radio className="w-3.5 h-3.5 text-blue-600 shrink-0" />
                    <span className="text-slate-500">Radar:</span>
                    <span className="text-slate-800 font-semibold">{reg.radar}</span>
                  </div>

                  <div className="flex items-center space-x-1.5">
                    <Satellite className="w-3.5 h-3.5 text-indigo-600 shrink-0" />
                    <span className="text-slate-500">Satellite:</span>
                    <span className="text-slate-800 font-semibold">{reg.satellite}</span>
                  </div>

                  <div className="flex items-center space-x-1.5">
                    <Zap className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                    <span className="text-slate-500">Lightning:</span>
                    <span className="text-slate-800 font-semibold">{reg.lightning}</span>
                  </div>

                  <div className="flex items-center space-x-1.5">
                    <CloudLightning className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                    <span className="text-slate-500">NWP Model:</span>
                    <span className="text-slate-800 font-semibold">{reg.nwp}</span>
                  </div>
                </div>
              </div>

              <div className="pt-2 flex justify-end">
                <button
                  onClick={() => onSelectRegion(reg.center, reg.zoom, reg.name)}
                  className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-sm transition"
                >
                  <span>{t('globalMonitoring.focusRegion')}</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
