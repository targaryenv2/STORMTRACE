import React from 'react';
import { useTranslation } from 'react-i18next';
import { CloudLightning, ArrowRight, X, ShieldAlert, Sparkles } from 'lucide-react';

export default function WelcomeIntroModal({
  isOpen,
  onClose,
  onStartTour
}) {
  const { t } = useTranslation();
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white border border-slate-200 rounded-3xl w-full max-w-lg shadow-2xl overflow-hidden text-slate-800 animate-in fade-in zoom-in-95 duration-200 flex flex-col">
        {/* Top Banner Accent */}
        <div className="bg-gradient-to-r from-blue-600 via-indigo-600 to-sky-500 p-6 text-white relative">
          <button
            onClick={onClose}
            className="absolute top-4 right-4 p-1.5 rounded-full bg-white/20 hover:bg-white/30 text-white transition"
            title="Dismiss"
          >
            <X className="w-4 h-4" />
          </button>

          <div className="w-12 h-12 rounded-2xl bg-white/15 backdrop-blur-md border border-white/20 flex items-center justify-center mb-3">
            <CloudLightning className="w-6 h-6 text-white" />
          </div>

          <div className="inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full bg-white/20 text-white text-[11px] font-semibold mb-2">
            <Sparkles className="w-3 h-3 text-amber-300" />
            <span>{t('welcomeIntro.welcome')}</span>
          </div>

          <h2 className="text-xl font-bold tracking-tight text-white">
            {t('welcomeIntro.title')}
          </h2>
        </div>

        {/* Plain Language Message */}
        <div className="p-6 space-y-4">
          <p className="text-slate-700 text-sm leading-relaxed font-normal">
            {t('welcomeIntro.message')}
          </p>

          <div className="p-3 bg-amber-50 rounded-2xl border border-amber-200/80 flex items-start space-x-2.5 text-xs text-amber-900">
            <ShieldAlert className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
            <div>
              <span className="font-bold">{t('welcomeIntro.importantNotice')}</span>{' '}
              <span className="text-amber-800">
                {t('common.disclaimer')}
              </span>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="pt-2 flex items-center justify-between">
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition"
            >
              {t('welcomeIntro.exploreOwn')}
            </button>

            <button
              onClick={() => {
                onClose();
                if (onStartTour) onStartTour();
              }}
              className="px-5 py-2.5 rounded-xl text-xs font-bold bg-blue-600 hover:bg-blue-700 text-white shadow-sm transition flex items-center space-x-2"
            >
              <span>{t('welcomeIntro.takeTour')}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
