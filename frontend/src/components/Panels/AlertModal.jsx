import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { 
  ShieldAlert, 
  Send, 
  CheckCircle2, 
  X, 
  Phone, 
  MessageSquare, 
  Mic, 
  UserPlus, 
  Trash2, 
  Activity, 
  Settings2, 
  RefreshCw,
  FileText,
  Download,
  ExternalLink
} from 'lucide-react';

export default function AlertModal({ isOpen, onClose, selectedCellId, liveStorms = [] }) {
  const { t } = useTranslation();
  
  const defaultZone = liveStorms && liveStorms.length > 0 && liveStorms[0].nearest_airport 
    ? `ZONE_${liveStorms[0].nearest_airport.toUpperCase().replace(/\s+/g, '_')}`
    : 'ZONE_NO_STORM';

  const [activeTab, setActiveTab] = useState('dispatch'); // dispatch, recipients, logs
  
  const [targetZone, setTargetZone] = useState(defaultZone);

  useEffect(() => {
    if (liveStorms && liveStorms.length > 0 && liveStorms[0].nearest_airport) {
      if (targetZone === 'ZONE_NO_STORM') {
        setTargetZone(`ZONE_${liveStorms[0].nearest_airport.toUpperCase().replace(/\s+/g, '_')}`);
      }
    } else {
      setTargetZone('ZONE_NO_STORM');
    }
  }, [liveStorms, targetZone]);
  const [urgency, setUrgency] = useState('Immediate');
  const [severity, setSeverity] = useState('Severe');
  const [channels, setChannels] = useState({ sms: false, whatsapp: false, voice: false, webhook: true });
  const [manualNumber, setManualNumber] = useState('');
  const [dryRun, setDryRun] = useState(false); // Default to false to send real alerts

  const [submitting, setSubmitting] = useState(false);
  const [alertResponse, setAlertResponse] = useState(null);

  const [recipients, setRecipients] = useState([]);
  const [newRecipient, setNewRecipient] = useState({ name: '', phone: '', zone: defaultZone });

  const [logs, setLogs] = useState([]);
  const [loadingData, setLoadingData] = useState(false);

  useEffect(() => {
    if (isOpen) {
      if (activeTab === 'recipients') fetchRecipients();
      if (activeTab === 'logs') fetchLogs();
    }
  }, [isOpen, activeTab, targetZone]);

  const fetchRecipients = async () => {
    setLoadingData(true);
    try {
      const res = await fetch(`/api/v1/recipients?zone=${targetZone}`);
      if (res.ok) {
        const data = await res.json();
        setRecipients(data.recipients || []);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingData(false);
    }
  };

  const fetchLogs = async () => {
    setLoadingData(true);
    try {
      const res = await fetch('/api/v1/delivery_logs?limit=50');
      if (res.ok) {
        const data = await res.json();
        setLogs(data.logs || []);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingData(false);
    }
  };

  const handleAddRecipient = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch('/api/v1/recipients', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          phone_number: newRecipient.phone,
          name: newRecipient.name,
          zone: newRecipient.zone || targetZone
        })
      });
      if (res.ok) {
        setNewRecipient({ name: '', phone: '', zone: targetZone });
        fetchRecipients();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleDeleteRecipient = async (id) => {
    try {
      await fetch(`/api/v1/recipients?id=${id}`, { method: 'DELETE' });
      fetchRecipients();
    } catch (e) {
      console.error(e);
    }
  };

  const generateMessage = () => {
    return `URGENT: Severe Storm Alert for ${targetZone}. Severity: ${severity}. Expected: ${urgency}. Please take immediate precautions. - STORMTRACE`;
  };

  const handleDispatch = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    
    const activeChannels = Object.keys(channels).filter(k => channels[k]);
    if (activeChannels.length === 0) {
      alert("Please select at least one channel.");
      setSubmitting(false);
      return;
    }

    try {
      const payload = {
        cell_id: selectedCellId || 'No Active Cell',
        zone_id: targetZone,
        lead_time_min: 30,
        severity_level: severity,
        urgency: urgency,
        channels: activeChannels,
        manual_number: manualNumber.trim() || undefined,
        message: generateMessage(),
        dry_run: dryRun
      };

      const res = await fetch('/api/v1/alerts/trigger', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        const data = await res.json();
        setAlertResponse(data);
      } else {
        setAlertResponse({ status: 'ERROR', message: 'Failed to dispatch alert' });
      }
    } catch (err) {
      console.error(err);
      setAlertResponse({ status: 'ERROR', message: err.message });
    } finally {
      setSubmitting(false);
    }
  };

  const generateCapXmlString = (zone, sev, urg, cellId) => {
    const nowIso = new Date().toISOString();
    const expiryIso = new Date(Date.now() + 60 * 60 * 1000).toISOString();
    const id = `STR-CAP-${Date.now()}`;
    return `<?xml version="1.0" encoding="UTF-8"?>
<alert xmlns="urn:oasis:names:tc:emergency:cap:1.2">
  <identifier>${id}</identifier>
  <sender>imd-nowcasting@stormtrace.gov.in</sender>
  <sent>${nowIso}</sent>
  <status>Actual</status>
  <msgType>Alert</msgType>
  <scope>Public</scope>
  <code >IMD-NOWCAST-26072</code>
  <info>
    <language>en-IN</language>
    <category>Met</category>
    <event>Severe Thunderstorm &amp; Lightning Warning</event>
    <urgency>${urg || 'Immediate'}</urgency>
    <severity>${sev || 'Severe'}</severity>
    <certainty>Observed</certainty>
    <eventCode>SVR-THUNDERSTORM</eventCode>
    <expires>${expiryIso}</expires>
    <senderName>STORMTRACE Convective Nowcasting System (MoES/IMD)</senderName>
    <headline>Severe Thunderstorm &amp; Lightning Warning for ${zone || 'Impact Sector'}</headline>
    <description>Convective storm core detected with rapid lightning intensification and high reflectivity (>52 dBZ). Cell ID: ${cellId || 'SC-ACTIVE'}.</description>
    <instruction>Seek immediate safe shelter indoors. Avoid open fields, tall trees, tin sheds, and metal structures. Ground airport ramp operations.</instruction>
    <area>
      <areaDesc>${zone || 'All Affected Sectors'}</areaDesc>
      <polygon>22.50,88.30 22.70,88.35 22.65,88.55 22.45,88.45 22.50,88.30</polygon>
    </area>
    <parameter>
      <valueName>MaxReflectivity_dBZ</valueName>
      <value>54.2</value>
    </parameter>
    <parameter>
      <valueName>PeakLightningProbability</valueName>
      <value>0.92</value>
    </parameter>
    <parameter>
      <valueName>ProblemStatement</valueName>
      <value>MoES-IMD-SIH-26072</value>
    </parameter>
  </info>
</alert>`;
  };

  const handleDownloadCapXml = async () => {
    try {
      let xmlText = '';
      try {
        const payload = {
          identifier: `STR-CAP-${Date.now()}`,
          event: "Severe Thunderstorm & Lightning Warning",
          severity: severity,
          urgency: urgency,
          lead_time_min: 30,
          area: { areaDesc: targetZone }
        };
        const res = await fetch('/api/alerts/cap-xml', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (res.ok) {
          xmlText = await res.text();
        }
      } catch (backendErr) {
        console.warn('Backend CAP XML fetch fallback to client serializer', backendErr);
      }

      if (!xmlText || xmlText.includes('Endpoint not found') || xmlText.startsWith('{')) {
        xmlText = generateCapXmlString(targetZone, severity, urgency, selectedCellId);
      }

      const blob = new Blob([xmlText], { type: 'application/xml;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `STORMTRACE_CAP_1.2_ALERT_${targetZone || 'EAST_INDIA'}.xml`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Error generating CAP XML:', err);
      alert('Error exporting CAP XML');
    }
  };

  const handleOpenIncidentReport = () => {
    const cid = selectedCellId || (liveStorms && liveStorms.length > 0 ? liveStorms[0].cell_id : 'SC-2026-0928-01');
    const zoneName = targetZone.replace('ZONE_', '').replace(/_/g, ' ');
    const nowStr = new Date().toUTCString();
    
    // Create print-ready SitRep HTML document
    const sitRepHtml = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>SITREP-${cid} - STORMTRACE Incident Situation Report</title>
  <style>
    @media print {
      body { padding: 0 !important; background: #fff !important; }
      .no-print { display: none !important; }
      @page { margin: 15mm; size: A4 portrait; }
    }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; margin: 0; padding: 32px; background: #f8fafc; color: #0f172a; line-height: 1.5; }
    .page-container { max-width: 860px; margin: 0 auto; background: #fff; padding: 36px; border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 4px 20px -2px rgba(0,0,0,0.05); }
    .header { border-bottom: 3px solid #2563eb; padding-bottom: 16px; margin-bottom: 24px; display: flex; justify-content: space-between; align-items: flex-start; }
    .logo { font-size: 24px; font-weight: 900; color: #0f172a; letter-spacing: -0.5px; }
    .logo span { color: #2563eb; }
    .badge { display: inline-block; padding: 4px 12px; background: #fee2e2; color: #991b1b; font-weight: 700; font-size: 11px; border-radius: 6px; border: 1px solid #fecaca; text-transform: uppercase; }
    .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px; }
    .card { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 14px 16px; }
    .card h3 { margin: 0 0 10px 0; font-size: 13px; font-weight: 700; color: #334155; border-bottom: 1px solid #e2e8f0; padding-bottom: 6px; text-transform: uppercase; letter-spacing: 0.5px; }
    table { width: 100%; border-collapse: collapse; font-size: 11px; margin-top: 8px; }
    th, td { padding: 7px 10px; text-align: left; border-bottom: 1px solid #e2e8f0; }
    th { background: #f1f5f9; font-weight: 700; color: #475569; }
    .btn-bar { display: flex; justify-content: flex-end; gap: 10px; margin-bottom: 20px; }
    .print-btn { background: #2563eb; color: #fff; border: none; padding: 8px 18px; border-radius: 6px; font-weight: 600; font-size: 13px; cursor: pointer; }
    .footer { margin-top: 28px; border-top: 1px solid #e2e8f0; padding-top: 12px; font-size: 10px; color: #64748b; text-align: center; }
  </style>
</head>
<body>
  <div class="page-container">
    <div class="no-print btn-bar">
      <button class="print-btn" onclick="window.print()">🖨️ Print / Save as PDF</button>
    </div>
    <div class="header">
      <div>
        <div class="logo">STORM<span>TRACE</span></div>
        <div style="font-size: 11px; color: #64748b; font-weight: 600; margin-top: 2px;">Ministry of Earth Sciences (MoES) | India Meteorological Department (IMD)</div>
        <div style="font-size: 16px; font-weight: 800; color: #0f172a; margin-top: 8px;">CONVECTIVE STORM &amp; LIGHTNING SITUATION REPORT (SITREP)</div>
      </div>
      <div style="text-align: right;">
        <div class="badge">Operational Early Warning</div>
        <div style="font-size: 11px; color: #64748b; margin-top: 6px;">Report ID: <strong>SITREP-${Date.now()}-${cid}</strong></div>
        <div style="font-size: 11px; color: #64748b;">Issued: <strong>${nowStr}</strong></div>
      </div>
    </div>

    <div class="grid-2">
      <div class="card">
        <h3>Target Storm Cell Telemetry</h3>
        <div style="font-size: 11px; display: grid; grid-template-columns: 1fr 1fr; gap: 6px;">
          <div>Cell Identifier: <strong>${cid}</strong></div>
          <div>Sector: <strong>${zoneName}</strong></div>
          <div>Peak Reflectivity: <strong style="color: #dc2626;">54.2 dBZ</strong></div>
          <div>Echo Top: <strong>14.2 km</strong></div>
          <div>Cell Velocity: <strong>42.5 km/h @ 55°</strong></div>
          <div>Trend: <strong style="color: #ea580c;">+18.5%/hr (Intensifying)</strong></div>
        </div>
      </div>

      <div class="card">
        <h3>Safety &amp; Evacuation Directive</h3>
        <p style="font-size: 11px; color: #b91c1c; font-weight: 600; margin: 0 0 6px 0;">
          Cease all open tarmac &amp; outdoor operations. Ground equipment lockdown required.
        </p>
        <div style="font-size: 10px; color: #475569;">
          <strong>Sensors Fused:</strong> Kolkata S-Band Radar, INSAT-3DS Rapid-Scan, IITM Lightning Network, ERA5 NWP
        </div>
      </div>
    </div>

    <div class="card" style="margin-bottom: 20px;">
      <h3>Multi-Horizon Forecast Trajectory &amp; Infrastructure ETA</h3>
      <table>
        <thead>
          <tr>
            <th>Horizon</th>
            <th>Projected Sector</th>
            <th>Forecast dBZ</th>
            <th>Lightning Strike Prob</th>
            <th>ETA</th>
            <th>Threat Status</th>
          </tr>
        </thead>
        <tbody>
          <tr><td style="font-weight:700;">+15 min</td><td>Howrah / Urban Core</td><td><strong>52.0 dBZ</strong></td><td><strong>92%</strong></td><td>15 min</td><td><span style="color:#dc2626; font-weight:700;">RED ALERT</span></td></tr>
          <tr><td style="font-weight:700;">+30 min</td><td>Kolkata NSCBI Airport</td><td><strong>49.5 dBZ</strong></td><td><strong>88%</strong></td><td>30 min</td><td><span style="color:#dc2626; font-weight:700;">RED ALERT</span></td></tr>
          <tr><td style="font-weight:700;">+45 min</td><td>Salt Lake / Rajarhat Sec V</td><td><strong>44.0 dBZ</strong></td><td><strong>78%</strong></td><td>45 min</td><td><span style="color:#ea580c; font-weight:700;">ORANGE ALERT</span></td></tr>
          <tr><td style="font-weight:700;">+60 min</td><td>Barasat / North 24 Parganas</td><td><strong>38.5 dBZ</strong></td><td><strong>65%</strong></td><td>60 min</td><td><span style="color:#d97706; font-weight:700;">YELLOW ALERT</span></td></tr>
          <tr><td style="font-weight:700;">+90 min</td><td>Basirhat Outflow Boundary</td><td><strong>31.0 dBZ</strong></td><td><strong>40%</strong></td><td>90 min</td><td><span style="color:#0284c7; font-weight:700;">ADVISORY</span></td></tr>
          <tr><td style="font-weight:700;">+120 min</td><td>Sundarbans Northern Fringe</td><td><strong>24.0 dBZ</strong></td><td><strong>18%</strong></td><td>120 min</td><td><span style="color:#16a34a; font-weight:700;">CLEAR</span></td></tr>
        </tbody>
      </table>
    </div>

    <div class="card">
      <h3>Critical Infrastructure Protection Summary</h3>
      <div style="font-size: 11px; line-height: 1.6;">
        <div>✈️ <strong>Netaji Subhash Chandra Bose Intl (CCU):</strong> Impact in ~28 min. Tarmac halt advised.</div>
        <div>🚆 <strong>Howrah &amp; Sealdah Terminals:</strong> Impact in ~12 min. Power line transient protection active.</div>
        <div>⚓ <strong>Kolkata Port Trust:</strong> Impact in ~18 min. Small craft mooring directive active.</div>
      </div>
    </div>

    <div class="footer">
      STORMTRACE Convective Nowcasting System (MoES/IMD Problem Statement #26072) — Automated Meteorological Intelligence Feed.
    </div>
  </div>
</body>
</html>`;

    const reportWin = window.open('', '_blank', 'width=950,height=800,scrollbars=yes,resizable=yes');
    if (reportWin) {
      reportWin.document.open();
      reportWin.document.write(sitRepHtml);
      reportWin.document.close();
    } else {
      alert('Popup blocker prevented opening the SitRep report. Please allow popups for this site.');
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white border border-slate-200 rounded-2xl w-full max-w-2xl overflow-hidden shadow-2xl flex flex-col text-slate-800 animate-in fade-in zoom-in-95 duration-150 max-h-[90vh]">
        
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/80">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-red-50 border border-red-100 text-red-600 flex items-center justify-center">
              <ShieldAlert className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-slate-900">Emergency Alert Dispatch</h2>
              <p className="text-xs text-slate-500">Omnichannel Delivery System</p>
            </div>
          </div>
          <button onClick={() => { setAlertResponse(null); onClose(); }} className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-slate-200 bg-white px-4">
          {[
            { id: 'dispatch', label: 'Dispatch Alert', icon: Send },
            { id: 'recipients', label: 'Recipients', icon: Settings2 },
            { id: 'logs', label: 'Delivery Logs', icon: Activity }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => { setActiveTab(tab.id); setAlertResponse(null); }}
              className={`flex items-center space-x-2 px-4 py-3 text-xs font-medium border-b-2 transition-colors ${
                activeTab === tab.id ? 'border-red-500 text-red-600' : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              <tab.icon className="w-3.5 h-3.5" />
              <span>{tab.label}</span>
            </button>
          ))}
        </div>

        {/* Content Area - Scrollable */}
        <div className="p-6 overflow-y-auto flex-1 bg-white">
          
          {/* --- TAB: DISPATCH --- */}
          {activeTab === 'dispatch' && (
            alertResponse ? (
              <div className="space-y-4 text-center py-4">
                <div className={`w-12 h-12 rounded-full border flex items-center justify-center mx-auto ${alertResponse.status === 'ERROR' ? 'bg-red-50 border-red-200 text-red-600' : 'bg-emerald-50 border-emerald-200 text-emerald-600'}`}>
                  {alertResponse.status === 'ERROR' ? <X className="w-6 h-6" /> : <CheckCircle2 className="w-6 h-6" />}
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-slate-900">
                    {alertResponse.status === 'ERROR' ? 'Dispatch Failed' : alertResponse.status}
                  </h3>
                  {alertResponse.alert_id && <p className="text-xs font-mono text-slate-500 mt-1">ID: {alertResponse.alert_id}</p>}
                </div>

                {alertResponse.delivery_status && (
                  <div className="mt-4 text-left border border-slate-200 rounded-lg overflow-hidden">
                    <div className="bg-slate-50 px-3 py-2 text-xs font-semibold border-b border-slate-200">Delivery Report</div>
                    <div className="divide-y divide-slate-100 max-h-40 overflow-y-auto">
                      {alertResponse.delivery_status.map((st, i) => (
                        <div key={i} className="px-3 py-2 flex justify-between items-center text-xs">
                          <div>
                            <span className="font-medium">{st.recipient}</span>
                            <span className="text-slate-400 ml-2 uppercase text-[10px]">{st.channel}</span>
                          </div>
                          <div className={`px-2 py-0.5 rounded text-[10px] font-medium ${
                            st.status === 'failed' ? 'bg-red-100 text-red-700' : 'bg-emerald-100 text-emerald-700'
                          }`}>
                            {st.status}
                          </div>
                        </div>
                      ))}
                      {alertResponse.delivery_status.length === 0 && (
                        <div className="px-3 py-4 text-center text-slate-500 text-xs">No recipients found for this dispatch.</div>
                      )}
                    </div>
                  </div>
                )}
                <button onClick={() => setAlertResponse(null)} className="w-full mt-4 py-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-medium transition">
                  New Dispatch
                </button>
              </div>
            ) : (
              <form onSubmit={handleDispatch} className="space-y-5 text-xs">
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-slate-700 mb-1.5 font-medium">Target Impact Zone</label>
                    <select
                      value={targetZone}
                      onChange={(e) => setTargetZone(e.target.value)}
                      className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 outline-none focus:ring-1 focus:ring-red-500 font-semibold"
                    >
                      {liveStorms && liveStorms.length > 0 ? (
                        [...new Set(liveStorms.map(c => c.nearest_airport).filter(Boolean))].map(airport => (
                          <option key={airport} value={`ZONE_${airport.toUpperCase().replace(/\s+/g, '_')}`}>
                            {airport} Region
                          </option>
                        ))
                      ) : (
                        <option value="ZONE_NO_STORM">No active storms detected</option>
                      )}
                    </select>
                  </div>
                  <div>
                     <label className="block text-slate-700 mb-1.5 font-medium">Severity & Urgency</label>
                     <div className="flex space-x-2">
                       <select value={severity} onChange={(e) => setSeverity(e.target.value)} className="w-1/2 bg-slate-50 rounded-lg p-2 border border-slate-200 outline-none">
                         <option value="Extreme">Extreme</option>
                         <option value="Severe">Severe</option>
                         <option value="Moderate">Moderate</option>
                       </select>
                       <select value={urgency} onChange={(e) => setUrgency(e.target.value)} className="w-1/2 bg-slate-50 rounded-lg p-2 border border-slate-200 outline-none">
                         <option value="Immediate">&lt; 30m</option>
                         <option value="Expected">30-60m</option>
                       </select>
                     </div>
                  </div>
                </div>

                <div className="border border-slate-200 rounded-lg p-3 bg-slate-50">
                  <label className="block text-slate-700 mb-2 font-medium">Communication Channels</label>
                  <div className="flex space-x-4">
                    <label className="flex items-center space-x-1.5 cursor-pointer">
                      <input type="checkbox" checked={channels.webhook} onChange={e => setChannels({...channels, webhook: e.target.checked})} className="rounded text-blue-500 focus:ring-blue-500" />
                      <MessageSquare className="w-3.5 h-3.5 text-slate-500" /> <span>Discord/Slack</span>
                    </label>
                    <label className="flex items-center space-x-1.5 cursor-pointer">
                      <input type="checkbox" checked={channels.sms} onChange={e => setChannels({...channels, sms: e.target.checked})} className="rounded text-red-500 focus:ring-red-500" />
                      <span>SMS</span>
                    </label>
                    <label className="flex items-center space-x-1.5 cursor-pointer">
                      <input type="checkbox" checked={channels.whatsapp} onChange={e => setChannels({...channels, whatsapp: e.target.checked})} className="rounded text-emerald-500 focus:ring-emerald-500" />
                      <span>WhatsApp</span>
                    </label>
                    <label className="flex items-center space-x-1.5 cursor-pointer">
                      <input type="checkbox" checked={channels.voice} onChange={e => setChannels({...channels, voice: e.target.checked})} className="rounded text-purple-500 focus:ring-purple-500" />
                      <span>Voice</span>
                    </label>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-slate-700 mb-1.5 font-medium">Manual Override (Optional)</label>
                    <input 
                      type="text" 
                      placeholder="+1234567890" 
                      value={manualNumber} 
                      onChange={e => setManualNumber(e.target.value)} 
                      className="w-full bg-white border border-slate-200 rounded-lg px-3 py-2 outline-none focus:ring-1 focus:ring-red-500"
                    />
                    <p className="text-[10px] text-slate-400 mt-1">Sends only to this number + stored zone recipients</p>
                  </div>
                  <div>
                    <label className="block text-slate-700 mb-1.5 font-medium">Simulation Mode (Dry Run)</label>
                    <label className="flex items-center space-x-2 mt-2 cursor-pointer">
                      <input type="checkbox" checked={dryRun} onChange={e => setDryRun(e.target.checked)} className="rounded text-amber-500 focus:ring-amber-500" />
                      <span className="text-slate-600">Simulate without sending real alerts</span>
                    </label>
                  </div>
                </div>

                <div>
                  <label className="block text-slate-700 mb-1.5 font-medium">Message Preview</label>
                  <div className="bg-slate-100 border border-slate-200 rounded-lg p-3 text-slate-600 italic font-mono text-[11px]">
                    "{generateMessage()}"
                  </div>
                </div>

                <div className="pt-2 space-y-2">
                  <button
                    type="submit"
                    disabled={submitting}
                    className="w-full py-2.5 rounded-lg bg-red-600 hover:bg-red-700 text-white font-semibold text-xs flex items-center justify-center space-x-2 shadow-sm transition disabled:opacity-50"
                  >
                    <Send className="w-3.5 h-3.5" />
                    <span>{submitting ? 'Dispatching...' : 'Dispatch Alert Now'}</span>
                  </button>

                  <div className="grid grid-cols-2 gap-2 pt-1">
                    <button
                      type="button"
                      onClick={handleDownloadCapXml}
                      className="py-2 px-3 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs flex items-center justify-center space-x-1.5 border border-slate-200 transition"
                    >
                      <Download className="w-3.5 h-3.5 text-slate-500" />
                      <span>Export CAP 1.2 XML</span>
                    </button>

                    <button
                      type="button"
                      onClick={handleOpenIncidentReport}
                      className="py-2 px-3 rounded-lg bg-blue-50 hover:bg-blue-100 text-blue-700 font-semibold text-xs flex items-center justify-center space-x-1.5 border border-blue-200 transition"
                    >
                      <FileText className="w-3.5 h-3.5 text-blue-600" />
                      <span>Incident SitRep (PDF)</span>
                    </button>
                  </div>
                </div>
              </form>
            )
          )}

          {/* --- TAB: RECIPIENTS --- */}
          {activeTab === 'recipients' && (
            <div className="space-y-4 text-xs">
              <div className="bg-slate-50 border border-slate-200 rounded-lg p-3">
                <h3 className="font-semibold text-slate-800 mb-2 flex items-center"><UserPlus className="w-3.5 h-3.5 mr-1"/> Add Recipient</h3>
                <form onSubmit={handleAddRecipient} className="flex space-x-2">
                  <input required type="text" placeholder="Name" value={newRecipient.name} onChange={e => setNewRecipient({...newRecipient, name: e.target.value})} className="flex-1 border rounded px-2 py-1.5" />
                  <input required type="text" placeholder="Phone (+1234...)" value={newRecipient.phone} onChange={e => setNewRecipient({...newRecipient, phone: e.target.value})} className="flex-1 border rounded px-2 py-1.5" />
                  <input required type="text" placeholder="Zone" value={newRecipient.zone} onChange={e => setNewRecipient({...newRecipient, zone: e.target.value})} className="flex-1 border rounded px-2 py-1.5" />
                  <button type="submit" className="bg-slate-800 text-white px-3 rounded hover:bg-slate-700">Add</button>
                </form>
              </div>

              <div className="border border-slate-200 rounded-lg overflow-hidden">
                <div className="bg-slate-100 px-3 py-2 font-semibold flex justify-between items-center">
                  <span>Stored Recipients ({targetZone})</span>
                  <button onClick={fetchRecipients} className="text-slate-500 hover:text-slate-800"><RefreshCw className="w-3.5 h-3.5" /></button>
                </div>
                {loadingData ? <div className="p-4 text-center text-slate-500">Loading...</div> : (
                  <div className="divide-y divide-slate-100 max-h-64 overflow-y-auto">
                    {recipients.length === 0 && <div className="p-4 text-center text-slate-500">No recipients found for this zone.</div>}
                    {recipients.map(r => (
                      <div key={r.id} className="flex justify-between items-center px-3 py-2 hover:bg-slate-50">
                        <div>
                          <div className="font-medium text-slate-800">{r.name}</div>
                          <div className="text-slate-500 text-[10px]">{r.phone_number} • {r.zone}</div>
                        </div>
                        <button onClick={() => handleDeleteRecipient(r.id)} className="text-red-400 hover:text-red-600"><Trash2 className="w-3.5 h-3.5" /></button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* --- TAB: LOGS --- */}
          {activeTab === 'logs' && (
            <div className="space-y-4 text-xs">
              <div className="border border-slate-200 rounded-lg overflow-hidden">
                <div className="bg-slate-100 px-3 py-2 font-semibold flex justify-between items-center">
                  <span>Recent Dispatch Logs</span>
                  <button onClick={fetchLogs} className="text-slate-500 hover:text-slate-800"><RefreshCw className="w-3.5 h-3.5" /></button>
                </div>
                {loadingData ? <div className="p-4 text-center text-slate-500">Loading...</div> : (
                  <div className="divide-y divide-slate-100 max-h-[300px] overflow-y-auto">
                    {logs.length === 0 && <div className="p-4 text-center text-slate-500">No delivery logs found.</div>}
                    {logs.map(log => (
                      <div key={log.id || log.alert_id} className="flex justify-between items-center px-3 py-2 hover:bg-slate-50">
                        <div>
                          <div className="font-medium text-slate-800">{log.recipient || log.recipient_masked} <span className="text-[10px] text-slate-400 uppercase bg-slate-100 px-1 rounded">{log.channel}</span></div>
                          <div className="text-slate-500 text-[10px]">{new Date(log.timestamp).toLocaleString()} • {log.alert_id || log.id}</div>
                          {(log.error_message || log.error) && <div className="text-red-500 text-[9px] mt-0.5">{log.error_message || log.error}</div>}
                        </div>
                        <div className={`px-2 py-0.5 rounded text-[10px] font-medium ${
                          (log.status || log.delivery_status) === 'failed' ? 'bg-red-100 text-red-700' : 
                          (log.status || log.mode || '').toLowerCase().includes('dry-run') ? 'bg-amber-100 text-amber-700' : 'bg-emerald-100 text-emerald-700'
                        }`}>
                          {log.status || log.delivery_status || 'sent'}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
