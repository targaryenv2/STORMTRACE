import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Layers, Clock, ShieldAlert, Sparkles, X, ChevronRight, Check } from 'lucide-react';

export default function NoviceWalkthrough({ isOpen, onClose }) {
  const { t } = useTranslation();
  const [step, setStep] = useState(0);

  const steps = [
    {
      title: t('walkthrough.step1Title'),
      icon: Sparkles,
      iconColor: 'text-sky-400 bg-sky-500/10 border-sky-500/20',
      description: t('walkthrough.step1Desc'),
      tip: t('walkthrough.step1Tip')
    },
    {
      title: t('walkthrough.step2Title'),
      icon: Layers,
      iconColor: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
      description: t('walkthrough.step2Desc'),
      tip: t('walkthrough.step2Tip')
    },
    {
      title: t('walkthrough.step3Title'),
      icon: Clock,
      iconColor: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
      description: t('walkthrough.step3Desc'),
      tip: t('walkthrough.step3Tip')
    },
    {
      title: t('walkthrough.step4Title'),
      icon: ShieldAlert,
      iconColor: 'text-rose-400 bg-rose-500/10 border-rose-500/20',
      description: t('walkthrough.step4Desc'),
      tip: t('walkthrough.step4Tip')
    }
  ];

  if (!isOpen) return null;

  const current = steps[step];
  const Icon = current.icon;

  const handleNext = () => {
    if (step < steps.length - 1) {
      setStep(step + 1);
    } else {
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white border border-slate-200 rounded-3xl w-full max-w-md overflow-hidden shadow-2xl text-slate-800 animate-in fade-in zoom-in-95 duration-150 flex flex-col">
        {/* Header */}
        <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/80">
          <div className="flex items-center space-x-2">
            <span className="text-xs font-bold uppercase tracking-wider text-blue-600 font-mono">
              {t('walkthrough.quickGuide')} ({step + 1}/{steps.length})
            </span>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition"
            title="Dismiss guide"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          <div className="flex items-start space-x-3.5">
            <div className={`w-10 h-10 rounded-2xl border flex items-center justify-center shrink-0 ${current.iconColor}`}>
              <Icon className="w-5 h-5" />
            </div>
            <div className="space-y-1">
              <h3 className="font-bold text-sm text-slate-900">{current.title}</h3>
              <p className="text-xs text-slate-600 leading-relaxed">{current.description}</p>
            </div>
          </div>

          <div className="p-3 bg-slate-50 rounded-2xl border border-slate-200/80 text-[11px] text-slate-600">
            <span className="font-bold text-slate-800">💡 Tip: </span>
            {current.tip}
          </div>

          {/* Stepper Dots & Action Buttons */}
          <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
            <div className="flex space-x-1.5">
              {steps.map((_, i) => (
                <span
                  key={i}
                  className={`w-2 h-2 rounded-full transition-all ${
                    i === step ? 'w-5 bg-blue-600' : 'bg-slate-200'
                  }`}
                />
              ))}
            </div>

            <div className="flex items-center space-x-2">
              <button
                onClick={onClose}
                className="px-3 py-1.5 rounded-lg text-xs font-medium text-slate-500 hover:text-slate-800 transition"
              >
                {t('common.skip')}
              </button>
              <button
                onClick={handleNext}
                className="px-4 py-1.5 rounded-lg text-xs font-bold bg-blue-600 hover:bg-blue-700 text-white shadow-sm transition flex items-center space-x-1"
              >
                <span>{step === steps.length - 1 ? t('common.gotIt') : t('common.next')}</span>
                {step === steps.length - 1 ? (
                  <Check className="w-3.5 h-3.5 ml-1" />
                ) : (
                  <ChevronRight className="w-3.5 h-3.5" />
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
