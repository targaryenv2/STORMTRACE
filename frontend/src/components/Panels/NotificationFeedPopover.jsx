import React, { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { 
  Bell, 
  X, 
  AlertTriangle, 
  CheckCircle2, 
  Info, 
  ShieldAlert, 
  ArrowRight, 
  Radio 
} from 'lucide-react';
import { ALL_ACTIVE_CELLS } from '../../services/nowcastService';

export default function NotificationFeedPopover({
  isOpen,
  onClose,
  onSelectCell
}) {
  const { t } = useTranslation();
  const popoverRef = useRef(null);

  // Read dismissed notifications from localStorage or memory
  const [dismissedIds, setDismissedIds] = useState(() => {
    try {
      const stored = localStorage.getItem('stormtrace_dismissed_notifications');
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  });

  // Handle outside click & Esc key
  useEffect(() => {
    if (!isOpen) return;

    const handleOutsideClick = (e) => {
      if (popoverRef.current && !popoverRef.current.contains(e.target)) {
        // Prevent closing if clicking the notification toggle button itself
        const isBellButton = e.target.closest('[aria-label="Notifications"]') || 
                             e.target.closest('button[title*="Notification"]') ||
                             e.target.closest('button[aria-label="Notifications"]');
        if (!isBellButton) {
          onClose();
        }
      }
    };

    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('mousedown', handleOutsideClick);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('mousedown', handleOutsideClick);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onClose]);

  // Build list of active notifications from severe storm cells + telemetry
  const severeCells = ALL_ACTIVE_CELLS.filter(c => c.warning_level === 'RED' || c.warning_level === 'ORANGE');

  const cellNotifications = severeCells.map(cell => ({
    id: `cell-${cell.cell_id}`,
    cellId: cell.cell_id,
    type: cell.warning_level === 'RED' ? 'critical' : 'warning',
    title: cell.warning_level === 'RED' 
      ? `${t('notificationsFeed.severeStorm', 'Severe Thunderstorm Warning')} (${cell.cell_id})`
      : `${t('notificationsFeed.highLightning', 'High Lightning & Squall Advisory')} (${cell.cell_id})`,
    location: cell.location_name || cell.region,
    detail: `${cell.max_dbz} dBZ max reflectivity · ${cell.speed_kmh} km/h ${cell.compass} · Severity ${cell.severity_score}/100`,
    time: 'Live Telemetry',
    severity: cell.warning_level
  }));

  const systemNotification = {
    id: 'sys-telemetry-active',
    type: 'info',
    title: t('notificationsFeed.radarTelemetryActive', 'Radar Telemetry Feed Active'),
    location: 'Kolkata Doppler Radar & INSAT-3D',
    detail: t('notificationsFeed.radarTelemetryDesc', 'Kolkata Doppler Radar & satellite feeds streaming normally.'),
    time: 'Real-time',
    severity: 'INFO'
  };

  const allFeedItems = [...cellNotifications, systemNotification];
  const activeItems = allFeedItems.filter(item => !dismissedIds.includes(item.id));

  const [missingCellId, setMissingCellId] = useState(null);

  const handleCellClick = (cellId) => {
    if (!cellId || !onSelectCell) return;
    const res = onSelectCell(cellId);
    if (res !== false) {
      setMissingCellId(null);
      onClose();
    } else {
      setMissingCellId(cellId);
    }
  };

  const handleDismiss = (id, e) => {
    e.stopPropagation();
    const updated = [...dismissedIds, id];
    setDismissedIds(updated);
    try {
      localStorage.setItem('stormtrace_dismissed_notifications', JSON.stringify(updated));
    } catch (e) {
      // ignore
    }
  };

  const handleMarkAllRead = () => {
    const allIds = allFeedItems.map(item => item.id);
    setDismissedIds(allIds);
    try {
      localStorage.setItem('stormtrace_dismissed_notifications', JSON.stringify(allIds));
    } catch (e) {
      // ignore
    }
  };

  const handleClearDismissed = () => {
    setDismissedIds([]);
    try {
      localStorage.removeItem('stormtrace_dismissed_notifications');
    } catch (e) {
      // ignore
    }
  };

  if (!isOpen) return null;

  return (
    <div 
      ref={popoverRef}
      role="dialog"
      aria-label="Notifications feed"
      className="absolute top-14 right-4 w-96 max-w-[calc(100vw-2rem)] bg-white rounded-2xl shadow-2xl border border-slate-200 z-50 overflow-hidden flex flex-col animate-in fade-in slide-in-from-top-2 duration-150"
    >
      {/* Header */}
      <div className="p-4 bg-slate-900 text-white flex items-center justify-between border-b border-slate-800">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-lg bg-blue-500/20 border border-blue-400/30 flex items-center justify-center text-blue-400">
            <Bell className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="font-bold text-sm tracking-tight text-white">
                {t('notificationsFeed.title', 'Alerts & Notifications')}
              </h3>
              {activeItems.length > 0 && (
                <span className="px-1.5 py-0.5 rounded-full bg-rose-500 text-white text-[10px] font-bold">
                  {activeItems.length}
                </span>
              )}
            </div>
            <p className="text-[11px] text-slate-400 mt-0.5">
              {t('notificationsFeed.subtitle', 'Live severe weather telemetry & dispatched alerts')}
            </p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          aria-label={t('common.close', 'Close')}
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Sub-header Banner: Demo Mode Indicator */}
      <div className="px-4 py-2 bg-amber-50 border-b border-amber-200 flex items-center justify-between text-xs text-amber-900 font-medium">
        <div className="flex items-center space-x-1.5">
          <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
          <span className="text-[11px] font-bold">{t('notificationsFeed.demoBadge', 'LIVE MODE · Real-time Feed')}</span>
        </div>
        {activeItems.length > 0 ? (
          <button
            onClick={handleMarkAllRead}
            className="text-[11px] text-amber-800 hover:text-amber-950 font-semibold underline underline-offset-2 transition"
          >
            {t('notificationsFeed.markAllRead', 'Mark all as read')}
          </button>
        ) : (
          <button
            onClick={handleClearDismissed}
            className="text-[11px] text-amber-800 hover:text-amber-950 font-semibold underline underline-offset-2 transition"
          >
            {t('notificationsFeed.clearAll', 'Reset feed')}
          </button>
        )}
      </div>

      {/* Notification List */}
      <div className="max-h-[380px] overflow-y-auto divide-y divide-slate-100">
        {activeItems.length === 0 ? (
          <div className="p-8 text-center text-slate-500">
            <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-3 text-slate-400">
              <CheckCircle2 className="w-6 h-6 text-emerald-500" />
            </div>
            <p className="text-sm font-semibold text-slate-800">
              {t('notificationsFeed.emptyTitle', 'No Active Notifications')}
            </p>
            <p className="text-xs text-slate-500 mt-1 max-w-xs mx-auto">
              {t('notificationsFeed.emptyDesc', 'All convective storm cell warnings and alert dispatches have been cleared.')}
            </p>
          </div>
        ) : (
          activeItems.map((item) => {
            const isCritical = item.severity === 'RED';
            const isWarning = item.severity === 'ORANGE';
            const isInfo = item.severity === 'INFO';

            return (
              <div 
                key={item.id} 
                className={`p-3.5 transition hover:bg-slate-50 relative group ${
                  isCritical ? 'bg-rose-50/30' : isWarning ? 'bg-amber-50/20' : 'bg-white'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-2.5">
                    <div className={`mt-0.5 p-1.5 rounded-lg shrink-0 ${
                      isCritical 
                        ? 'bg-rose-100 text-rose-700 border border-rose-200' 
                        : isWarning 
                        ? 'bg-amber-100 text-amber-700 border border-amber-200' 
                        : 'bg-blue-100 text-blue-700 border border-blue-200'
                    }`}>
                      {isCritical ? (
                        <ShieldAlert className="w-3.5 h-3.5" />
                      ) : isWarning ? (
                        <AlertTriangle className="w-3.5 h-3.5" />
                      ) : (
                        <Info className="w-3.5 h-3.5" />
                      )}
                    </div>
                    <div className="space-y-0.5">
                      <div className="flex items-center space-x-2">
                        <h4 className="text-xs font-bold text-slate-900 leading-tight">
                          {item.title}
                        </h4>
                        <span className={`text-[9px] font-bold px-1.5 py-0.2 rounded font-mono ${
                          isCritical 
                            ? 'bg-rose-100 text-rose-800 border border-rose-200' 
                            : isWarning 
                            ? 'bg-amber-100 text-amber-800 border border-amber-200' 
                            : 'bg-blue-100 text-blue-800 border border-blue-200'
                        }`}>
                          {item.severity}
                        </span>
                      </div>
                      <p className="text-[11px] font-medium text-slate-700">
                        {item.location}
                      </p>
                      <p className="text-[10px] text-slate-500 leading-relaxed">
                        {item.detail}
                      </p>
                    </div>
                  </div>

                  <button
                    onClick={(e) => handleDismiss(item.id, e)}
                    className="opacity-40 group-hover:opacity-100 p-1 text-slate-400 hover:text-slate-600 rounded transition"
                    title={t('common.close', 'Dismiss')}
                    aria-label="Dismiss notification"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>

                {/* Footer / Action */}
                <div className="mt-2.5 flex items-center justify-between pt-2 border-t border-slate-100/80">
                  <span className="text-[10px] text-slate-400 font-mono">
                    {item.time}
                  </span>
                  {item.cellId && onSelectCell && (
                    <div className="flex items-center space-x-2">
                      {missingCellId === item.cellId && (
                        <span className="text-[10px] font-bold text-rose-600">
                          {t('notificationsFeed.cellNotFound', 'Location unavailable')}
                        </span>
                      )}
                      <button
                        onClick={() => handleCellClick(item.cellId)}
                        className="inline-flex items-center space-x-1 text-[11px] font-bold text-blue-600 hover:text-blue-800 transition cursor-pointer"
                        title={`View ${item.cellId} on map`}
                      >
                        <span>{t('notificationsFeed.viewCell', 'View on Map')}</span>
                        <ArrowRight className="w-3 h-3" />
                      </button>
                    </div>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Popover Footer */}
      <div className="p-3 bg-slate-50 border-t border-slate-200 text-center text-[10px] text-slate-500">
        <p className="leading-tight">
          {t('common.operationalAdvisory', 'AI decision-support output — not official IMD warnings')}
        </p>
      </div>
    </div>
  );
}
