import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Settings, Sliders, Bell, Globe, Palette, Save, Check, X, Languages } from 'lucide-react';
import { SUPPORTED_LANGUAGES } from '../../i18n/i18n';

export default function SettingsModal({
  isOpen,
  onClose,
  settings,
  onUpdateSettings
}) {
  const { t, i18n } = useTranslation();

  const [localSettings, setLocalSettings] = useState(settings || {
    speedUnit: 'km/h',
    tempUnit: '°C',
    distanceUnit: 'km',
    defaultLeadTime: 30,
    defaultLayer: 'thunderstorm',
    mapTheme: 'light',
    audioAlerts: true,
    highThreatPush: true,
    autoRefreshInterval: 60
  });

  const [currentLang, setCurrentLang] = useState(i18n.language || 'en');
  const [saved, setSaved] = useState(false);

  if (!isOpen) return null;

  const handleLanguageChange = (langCode) => {
    setCurrentLang(langCode);
    i18n.changeLanguage(langCode);
    try {
      localStorage.setItem('stormtrace_language', langCode);
    } catch (e) {
      console.warn('Could not save language to storage:', e);
    }
  };

  const handleSave = () => {
    if (onUpdateSettings) {
      onUpdateSettings(localSettings);
    }
    i18n.changeLanguage(currentLang);
    try {
      localStorage.setItem('stormtrace_language', currentLang);
    } catch (e) {
      console.warn('Could not save language to storage:', e);
    }
    setSaved(true);
    setTimeout(() => {
      setSaved(false);
      onClose();
    }, 600);
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white border border-slate-200 rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden text-slate-800 animate-in fade-in zoom-in-95 duration-150 flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/80 shrink-0">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-blue-50 border border-blue-100 text-blue-600 flex items-center justify-center">
              <Sliders className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-slate-900">{t('settings.title')}</h2>
              <p className="text-[11px] text-slate-500">{t('settings.subtitle')}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Form Body */}
        <div className="p-6 overflow-y-auto space-y-5 text-xs text-slate-600 custom-scrollbar">
          {/* Language Selection */}
          <div className="space-y-3">
            <div className="flex items-center space-x-2 text-slate-800 font-semibold border-b border-slate-100 pb-1.5">
              <Languages className="w-4 h-4 text-blue-600" />
              <span>{t('settings.languageSection')}</span>
            </div>
            <div>
              <label className="block text-[11px] text-slate-500 mb-1 font-medium">{t('settings.languageLabel')}</label>
              <select
                value={currentLang}
                onChange={(e) => handleLanguageChange(e.target.value)}
                className="w-full bg-slate-50 text-slate-800 rounded-lg p-2.5 border border-slate-200 outline-none text-xs font-medium focus:ring-1 focus:ring-blue-500"
              >
                {SUPPORTED_LANGUAGES.map((lang) => (
                  <option key={lang.code} value={lang.code}>
                    {lang.nativeName} ({lang.label})
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Units Configuration */}
          <div className="space-y-3">
            <div className="flex items-center space-x-2 text-slate-800 font-semibold border-b border-slate-100 pb-1.5">
              <Globe className="w-4 h-4 text-blue-600" />
              <span>{t('settings.unitsSection')}</span>
            </div>
            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="block text-[11px] text-slate-500 mb-1 font-medium">{t('settings.windSpeed')}</label>
                <select
                  value={localSettings.speedUnit}
                  onChange={(e) => setLocalSettings({ ...localSettings, speedUnit: e.target.value })}
                  className="w-full bg-slate-50 text-slate-800 rounded-lg p-2 border border-slate-200 outline-none text-xs focus:ring-1 focus:ring-blue-500"
                >
                  <option value="km/h">km/h (km/hour)</option>
                  <option value="mph">mph (miles/hour)</option>
                  <option value="knots">knots</option>
                  <option value="m/s">m/s (meters/sec)</option>
                </select>
              </div>

              <div>
                <label className="block text-[11px] text-slate-500 mb-1 font-medium">{t('settings.temperature')}</label>
                <select
                  value={localSettings.tempUnit}
                  onChange={(e) => setLocalSettings({ ...localSettings, tempUnit: e.target.value })}
                  className="w-full bg-slate-50 text-slate-800 rounded-lg p-2 border border-slate-200 outline-none text-xs focus:ring-1 focus:ring-blue-500"
                >
                  <option value="°C">°C (Celsius)</option>
                  <option value="°F">°F (Fahrenheit)</option>
                  <option value="K">K (Kelvin)</option>
                </select>
              </div>

              <div>
                <label className="block text-[11px] text-slate-500 mb-1 font-medium">{t('settings.distance')}</label>
                <select
                  value={localSettings.distanceUnit}
                  onChange={(e) => setLocalSettings({ ...localSettings, distanceUnit: e.target.value })}
                  className="w-full bg-slate-50 text-slate-800 rounded-lg p-2 border border-slate-200 outline-none text-xs focus:ring-1 focus:ring-blue-500"
                >
                  <option value="km">km</option>
                  <option value="miles">miles</option>
                  <option value="nm">nm</option>
                </select>
              </div>
            </div>
          </div>

          {/* Default Layer & Lead-Time */}
          <div className="space-y-3">
            <div className="flex items-center space-x-2 text-slate-800 font-semibold border-b border-slate-100 pb-1.5">
              <Palette className="w-4 h-4 text-blue-600" />
              <span>{t('settings.mapDefaultsSection')}</span>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-[11px] text-slate-500 mb-1 font-medium">{t('settings.defaultLayer')}</label>
                <select
                  value={localSettings.defaultLayer}
                  onChange={(e) => setLocalSettings({ ...localSettings, defaultLayer: e.target.value })}
                  className="w-full bg-slate-50 text-slate-800 rounded-lg p-2 border border-slate-200 outline-none text-xs focus:ring-1 focus:ring-blue-500"
                >
                  <option value="thunderstorm">{t('map.thunderstormProb')}</option>
                  <option value="lightning">{t('map.lightning')}</option>
                  <option value="radar">{t('map.radar')}</option>
                  <option value="satellite">{t('map.satellite')}</option>
                </select>
              </div>

              <div>
                <label className="block text-[11px] text-slate-500 mb-1 font-medium">{t('settings.defaultLeadTime')}</label>
                <select
                  value={localSettings.defaultLeadTime}
                  onChange={(e) => setLocalSettings({ ...localSettings, defaultLeadTime: Number(e.target.value) })}
                  className="w-full bg-slate-50 text-slate-800 rounded-lg p-2 border border-slate-200 outline-none text-xs focus:ring-1 focus:ring-blue-500"
                >
                  <option value={15}>+15 Minutes</option>
                  <option value={30}>+30 Minutes</option>
                  <option value={45}>+45 Minutes</option>
                  <option value={60}>+60 Minutes</option>
                  <option value={90}>+90 Minutes</option>
                  <option value={120}>+120 Minutes</option>
                </select>
              </div>
            </div>
          </div>

          {/* Alerting Preferences */}
          <div className="space-y-3">
            <div className="flex items-center space-x-2 text-slate-800 font-semibold border-b border-slate-100 pb-1.5">
              <Bell className="w-4 h-4 text-blue-600" />
              <span>{t('settings.alertsSection')}</span>
            </div>
            <div className="space-y-2">
              <label className="flex items-center justify-between p-2.5 rounded-xl bg-slate-50 border border-slate-200/80 cursor-pointer hover:bg-slate-100/70 transition">
                <div>
                  <span className="font-semibold text-slate-800 block">{t('settings.audioChimeTitle')}</span>
                  <span className="text-[11px] text-slate-500">{t('settings.audioChimeDesc')}</span>
                </div>
                <input
                  type="checkbox"
                  checked={localSettings.audioAlerts}
                  onChange={(e) => setLocalSettings({ ...localSettings, audioAlerts: e.target.checked })}
                  className="rounded bg-white border-slate-300 text-blue-600 focus:ring-blue-500 w-4 h-4"
                />
              </label>

              <label className="flex items-center justify-between p-2.5 rounded-xl bg-slate-50 border border-slate-200/80 cursor-pointer hover:bg-slate-100/70 transition">
                <div>
                  <span className="font-semibold text-slate-800 block">{t('settings.highThreatPopupTitle')}</span>
                  <span className="text-[11px] text-slate-500">{t('settings.highThreatPopupDesc')}</span>
                </div>
                <input
                  type="checkbox"
                  checked={localSettings.highThreatPush}
                  onChange={(e) => setLocalSettings({ ...localSettings, highThreatPush: e.target.checked })}
                  className="rounded bg-white border-slate-300 text-blue-600 focus:ring-blue-500 w-4 h-4"
                />
              </label>
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="px-6 py-3 border-t border-slate-100 bg-slate-50/80 flex items-center justify-between shrink-0">
          <button
            onClick={onClose}
            className="px-3.5 py-1.5 rounded-lg text-slate-500 hover:text-slate-800 text-xs transition"
          >
            {t('common.cancel')}
          </button>
          <button
            onClick={handleSave}
            className="px-4 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs shadow-sm transition flex items-center space-x-1.5"
          >
            {saved ? <Check className="w-3.5 h-3.5" /> : <Save className="w-3.5 h-3.5" />}
            <span>{saved ? t('common.saved') : t('settings.savePreferences')}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
