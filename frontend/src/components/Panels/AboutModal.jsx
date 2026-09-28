import React from 'react';
import { useTranslation } from 'react-i18next';
import { Info, ShieldAlert, X } from 'lucide-react';

export default function AboutModal({ isOpen, onClose }) {
  const { t } = useTranslation();
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white border border-slate-200 rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden text-slate-800 animate-in fade-in zoom-in-95 duration-150 flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/80 shrink-0">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-blue-50 border border-blue-100 text-blue-600 flex items-center justify-center">
              <Info className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-slate-900">{t('about.title')}</h2>
              <p className="text-[11px] text-slate-500">{t('about.subtitle')}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Static Read-Only Content */}
        <div className="p-6 overflow-y-auto space-y-4 text-xs text-slate-600 custom-scrollbar">
          {/* Plain-language explanation */}
          <div className="space-y-1.5">
            <h3 className="font-semibold text-blue-600 text-xs uppercase tracking-wider">{t('about.whatIs')}</h3>
            <p className="text-slate-600 leading-relaxed">
              {t('about.whatIsDesc')}
            </p>
          </div>

          {/* SIH Metadata Grid */}
          <div className="grid grid-cols-2 gap-3 py-3 border-y border-slate-100">
            <div className="space-y-0.5">
              <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">{t('about.event')}</span>
              <p className="font-semibold text-slate-800">Smart India Hackathon 2026</p>
            </div>
            <div className="space-y-0.5">
              <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">{t('about.problemStatement')}</span>
              <p className="font-semibold text-slate-800">PS 26072 (MoES / IMD)</p>
            </div>
            <div className="space-y-0.5">
              <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">{t('about.team')}</span>
              <p className="font-semibold text-slate-800">Team Targaryen</p>
            </div>
            <div className="space-y-0.5">
              <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">{t('about.pipeline')}</span>
              <p className="font-semibold text-slate-800">ConvLSTM + MC-Dropout + PostGIS</p>
            </div>
          </div>

          {/* Plain Language Data Sources */}
          <div className="space-y-2">
            <h3 className="font-semibold text-blue-600 text-xs uppercase tracking-wider">{t('about.dataSources')}</h3>
            <div className="space-y-1.5 text-[11px] text-slate-600">
              <div className="flex items-start space-x-2">
                <div className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5 shrink-0" />
                <span>{t('about.dwr')}</span>
              </div>
              <div className="flex items-start space-x-2">
                <div className="w-1.5 h-1.5 rounded-full bg-indigo-500 mt-1.5 shrink-0" />
                <span>{t('about.satelliteDesc')}</span>
              </div>
              <div className="flex items-start space-x-2">
                <div className="w-1.5 h-1.5 rounded-full bg-amber-500 mt-1.5 shrink-0" />
                <span>{t('about.lightningDesc')}</span>
              </div>
              <div className="flex items-start space-x-2">
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 mt-1.5 shrink-0" />
                <span>{t('about.ncumDesc')}</span>
              </div>
            </div>
          </div>

          {/* Mandatory Operational Disclaimer */}
          <div className="p-3 bg-amber-50 rounded-xl border border-amber-200/80 space-y-1 text-amber-800">
            <div className="flex items-center space-x-1.5 font-bold text-xs">
              <ShieldAlert className="w-4 h-4 text-amber-600 shrink-0" />
              <span className="text-amber-900">{t('about.advisoryTitle')}</span>
            </div>
            <p className="text-[11px] text-amber-800 leading-relaxed">
              {t('common.operationalAdvisory')}
            </p>
          </div>

          {/* Version & Build info */}
          <div className="flex items-center justify-between text-[11px] text-slate-400 pt-2">
            <span>{t('about.build')} <strong className="text-slate-600">v2.4.0-prod (Release)</strong></span>
            <span>{t('about.platform')} <strong className="text-slate-600">React 18 + OpenLayers 10</strong></span>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-slate-100 bg-slate-50/80 flex justify-end shrink-0">
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-slate-200 hover:bg-slate-300 text-slate-700 font-medium transition text-xs"
          >
            {t('common.close')}
          </button>
        </div>
      </div>
    </div>
  );
}
