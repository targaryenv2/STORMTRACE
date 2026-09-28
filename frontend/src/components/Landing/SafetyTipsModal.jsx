import React from 'react';
import { useTranslation } from 'react-i18next';
import { 
  ShieldAlert, 
  Zap, 
  X, 
  CheckCircle2, 
  AlertTriangle, 
  Plane, 
  Home, 
  TreePine, 
  Car, 
  PhoneCall,
  Info
} from 'lucide-react';

export default function SafetyTipsModal({ isOpen, onClose }) {
  const { t } = useTranslation();

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in select-none">
      <div 
        className="bg-white rounded-3xl max-w-2xl w-full border border-slate-200 shadow-2xl flex flex-col max-h-[90vh] overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-6 py-5 border-b border-slate-100 flex items-center justify-between bg-slate-50/70">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-2xl bg-amber-100 border border-amber-200 flex items-center justify-center text-amber-700 shadow-sm">
              <Zap className="w-5 h-5 fill-amber-400" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-900">Thunderstorm & Lightning Safety Guide</h2>
              <p className="text-xs text-slate-500 mt-0.5">Official safety protocols, 30/30 rule & convective hazard precautions</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-slate-700 hover:bg-slate-200/60 transition"
            aria-label="Close"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-6 text-xs text-slate-700 custom-scrollbar">
          {/* 1. Golden 30/30 Rule */}
          <div className="p-4 bg-gradient-to-br from-amber-50 to-orange-50 border border-amber-200 rounded-2xl space-y-2">
            <div className="flex items-center space-x-2 text-amber-900 font-bold text-sm">
              <ShieldAlert className="w-4 h-4 text-amber-600 shrink-0" />
              <span>The 30/30 Lightning Safety Rule</span>
            </div>
            <p className="text-amber-800 leading-relaxed text-xs">
              <strong>1. Count the seconds:</strong> If the time between seeing a lightning flash and hearing the thunder is less than <strong>30 seconds</strong>, the storm is within 10 km (~6 miles). Seek immediate substantial shelter.
            </p>
            <p className="text-amber-800 leading-relaxed text-xs">
              <strong>2. Wait 30 minutes:</strong> Remain inside your shelter for at least <strong>30 minutes</strong> after hearing the very last clap of thunder before resuming outdoor activities.
            </p>
          </div>

          {/* 2. Indoor vs Outdoor Rules Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Outdoor Precautions */}
            <div className="p-4 bg-rose-50/70 border border-rose-200 rounded-2xl space-y-2.5">
              <div className="flex items-center space-x-2 font-bold text-rose-900 text-xs">
                <TreePine className="w-4 h-4 text-rose-600" />
                <span>If Caught Outdoors</span>
              </div>
              <ul className="space-y-1.5 text-[11px] text-rose-800 leading-normal">
                <li className="flex items-start space-x-1.5">
                  <span className="text-rose-500 font-bold">•</span>
                  <span><strong>AVOID</strong> tall isolated trees, hilltops, open fields, and metal fences.</span>
                </li>
                <li className="flex items-start space-x-1.5">
                  <span className="text-rose-500 font-bold">•</span>
                  <span><strong>EXIT</strong> lakes, ponds, swimming pools, and open water bodies immediately.</span>
                </li>
                <li className="flex items-start space-x-1.5">
                  <span className="text-rose-500 font-bold">•</span>
                  <span><strong>HARDTOP VEHICLES:</strong> Fully enclosed metal cars provide safe Faraday protection. Do not touch bare metal frame.</span>
                </li>
              </ul>
            </div>

            {/* Indoor Precautions */}
            <div className="p-4 bg-blue-50/70 border border-blue-200 rounded-2xl space-y-2.5">
              <div className="flex items-center space-x-2 font-bold text-blue-900 text-xs">
                <Home className="w-4 h-4 text-blue-600" />
                <span>Inside Buildings</span>
              </div>
              <ul className="space-y-1.5 text-[11px] text-blue-800 leading-normal">
                <li className="flex items-start space-x-1.5">
                  <span className="text-blue-500 font-bold">•</span>
                  <span><strong>AVOID</strong> corded phones and electrical appliances plugged into wall outlets.</span>
                </li>
                <li className="flex items-start space-x-1.5">
                  <span className="text-blue-500 font-bold">•</span>
                  <span><strong>STAY AWAY</strong> from plumbing, sinks, showers, and water faucets during active strikes.</span>
                </li>
                <li className="flex items-start space-x-1.5">
                  <span className="text-blue-500 font-bold">•</span>
                  <span><strong>CLOSE</strong> windows and doors; stay away from exterior glass panes and ungrounded balconies.</span>
                </li>
              </ul>
            </div>
          </div>

          {/* 3. Aviation & Terminal Airspace Hazards */}
          <div className="p-4 bg-slate-50 border border-slate-200 rounded-2xl space-y-2">
            <div className="flex items-center space-x-2 font-bold text-slate-800 text-xs">
              <Plane className="w-4 h-4 text-slate-600" />
              <span>Aviation & Terminal Operations (TITAN Proximity)</span>
            </div>
            <p className="text-slate-600 text-[11px] leading-relaxed">
              Severe convective cores ($Z \ge 50\text{ dBZ}$) produce severe low-level wind shear, microburst downdrafts, and turbulent roll clouds. Aircraft must maintain at least <strong>20 nautical miles</strong> lateral clearance from severe thunderstorm tops above FL300.
            </p>
          </div>

          {/* 4. Advisory Footer */}
          <div className="p-3 bg-slate-100/80 rounded-xl flex items-start space-x-2 text-[11px] text-slate-600">
            <Info className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" />
            <span>
              <strong>Operational Advisory:</strong> STORMTRACE forecasts are automated AI decision-support aids. In emergencies, always adhere to official warnings issued by the <strong>India Meteorological Department (IMD)</strong> and local State Disaster Management Authorities (SDMA).
            </span>
          </div>
        </div>

        {/* Footer Action */}
        <div className="px-6 py-4 border-t border-slate-100 bg-slate-50/50 flex justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-semibold text-xs transition shadow-sm"
          >
            I Understand
          </button>
        </div>
      </div>
    </div>
  );
}
