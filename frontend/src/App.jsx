import React, { useState, useEffect } from 'react';
import Header from './components/Header/Header';
import Sidebar from './components/Navigation/Sidebar';
import OpenLayersMap from './components/Map/OpenLayersMap';
import RightPanel from './components/Panels/RightPanel';
import AIAssistantPanel from './components/Panels/AIAssistantPanel';
import GlobalMonitoringView from './components/Panels/GlobalMonitoringView';
import NowcastingView from './components/Panels/NowcastingView';
import StormCellsView from './components/Panels/StormCellsView';
import ModelEvaluationView from './components/Panels/ModelEvaluationView';
import ReplayVerificationModal from './components/Panels/ReplayVerificationModal';
import AlertModal from './components/Panels/AlertModal';
import AboutModal from './components/Panels/AboutModal';
import SettingsModal from './components/Panels/SettingsModal';
import WelcomeIntroModal from './components/Walkthrough/WelcomeIntroModal';
import NoviceWalkthrough from './components/Walkthrough/NoviceWalkthrough';
import LandingPage from './components/Landing/LandingPage';
import CellTrackerPanel from './components/Panels/CellTrackerPanel';
import HistoricalAnalogsPanel from './components/Panels/HistoricalAnalogsPanel';
import { useLiveStorms } from './hooks/useLiveStorms';

export default function App() {
  // Navigation State
  const [activeNav, setActiveNav] = useState('dashboard');

  // Layer States
  const [activeLayer, setActiveLayer] = useState('thunderstorm'); // 'thunderstorm' | 'radar' | 'satellite' | 'lightning'
  const [leadTimeMin, setLeadTimeMin] = useState(30);

  // Layer Toggles
  const [showThunderstormProb, setShowThunderstormProb] = useState(true);
  const [showCells, setShowCells] = useState(true);
  const [showTrajectories, setShowTrajectories] = useState(true);
  const [showImpactZones, setShowImpactZones] = useState(true);
  const [showUncertainty, setShowUncertainty] = useState(false);

  // Region & Active Cell Telemetry
  const [currentRegionName, setCurrentRegionName] = useState('India (Operational)');
  const [hasRadarCoverage, setHasRadarCoverage] = useState(true);
  const [selectedCellId, setSelectedCellId] = useState('SC-2026-0917-03');
  const [fallbackMode, setFallbackMode] = useState(false);
  const [targetMapView, setTargetMapView] = useState(null);

  // AI Assistant & Modals State
  const [isAssistantOpen, setIsAssistantOpen] = useState(false);
  const [rightPanelTab, setRightPanelTab] = useState('details'); // 'details' | 'assistant'
  const [isReplayOpen, setIsReplayOpen] = useState(false);
  const [isAlertModalOpen, setIsAlertModalOpen] = useState(false);
  const [isAboutOpen, setIsAboutOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isWelcomeIntroOpen, setIsWelcomeIntroOpen] = useState(false);
  const [isWalkthroughOpen, setIsWalkthroughOpen] = useState(false);

  // Check if first-time user on mount
  useEffect(() => {
    const hasSeenIntro = localStorage.getItem('stormtrace_seen_intro');
    if (!hasSeenIntro) {
      setIsWelcomeIntroOpen(true);
    }
  }, []);

  // User Settings State (Configurable Preferences)
  const [userSettings, setUserSettings] = useState({
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

  const { liveStorms } = useLiveStorms(10000);

  // Selected cell detail object
  const selectedCellData = (liveStorms || []).find(c => c.cell_id === selectedCellId) || (liveStorms && liveStorms.length > 0 ? liveStorms[0] : null);

  const handleSelectNav = (navId) => {
    setActiveNav(navId);
    if (navId === 'historical') {
      setIsReplayOpen(true);
    } else if (navId === 'impact') {
      setIsAlertModalOpen(true);
    } else if (navId === 'settings') {
      setIsSettingsOpen(true);
    } else if (navId === 'about') {
      setIsAboutOpen(true);
    }
  };

  const handleRegionChange = (reg) => {
    setHasRadarCoverage(reg.isIndia);
    setCurrentRegionName(reg.regionName);
  };

  const handleSelectGlobalRegion = (center, zoom, name) => {
    setActiveNav('dashboard');
    setHasRadarCoverage(name.includes('India'));
    setCurrentRegionName(name);
  };

  const handleSelectCellFromView = (cellId) => {
    setSelectedCellId(cellId);
    setActiveNav('dashboard');
    const cell = (liveStorms || []).find(c => c.cell_id === cellId);
    if (cell) {
      setTargetMapView({
        lon: cell.lon,
        lat: cell.lat,
        zoom: 9.0,
        t: Date.now()
      });
    }
  };

  const handleDismissWelcomeIntro = () => {
    localStorage.setItem('stormtrace_seen_intro', 'true');
    setIsWelcomeIntroOpen(false);
  };

  const handleStartTourFromWelcome = () => {
    localStorage.setItem('stormtrace_seen_intro', 'true');
    setIsWelcomeIntroOpen(false);
    setIsWalkthroughOpen(true);
  };

  const handleToggleAssistant = () => {
    setIsAssistantOpen(prev => !prev);
    if (!isAssistantOpen) {
      setRightPanelTab('assistant');
    }
  };

  // Map Action execution from Assistant tool calls
  const handleExecuteMapAction = (action) => {
    if (!action) return;
    if (action.type === 'SET_MAP_VIEW') {
      setTargetMapView({
        lon: action.payload.lon,
        lat: action.payload.lat,
        zoom: action.payload.zoom || 8.0,
        t: Date.now()
      });
      setActiveNav('dashboard');
    } else if (action.type === 'SELECT_CELL') {
      setSelectedCellId(action.payload);
      setActiveNav('dashboard');
    } else if (action.type === 'SET_LEAD_TIME') {
      setLeadTimeMin(action.payload);
    } else if (action.type === 'SET_LAYER') {
      setActiveLayer(action.payload);
    } else if (action.type === 'SET_LAYER_TOGGLE') {
      if (action.payload.key === 'uncertainty') {
        setShowUncertainty(action.payload.value);
      }
    }
  };

  if (activeNav === 'landing') {
    return (
      <div className="h-screen w-screen overflow-y-auto bg-slate-950">
        <LandingPage
          onNavigate={(nav) => setActiveNav(nav)}
          onOpenAbout={() => setIsAboutOpen(true)}
          onOpenAlerts={() => setIsAlertModalOpen(true)}
          onOpenSettings={() => setIsSettingsOpen(true)}
          onSelectCityOnMap={(loc) => {
            setTargetMapView({
              lon: loc.lon,
              lat: loc.lat,
              zoom: 8.5,
              t: Date.now()
            });
            setActiveNav('dashboard');
          }}
        />

        {/* Feature Modals */}
        <ReplayVerificationModal
          isOpen={isReplayOpen}
          onClose={() => setIsReplayOpen(false)}
          liveStorms={liveStorms || []}
        />

        <AlertModal
          isOpen={isAlertModalOpen}
          onClose={() => setIsAlertModalOpen(false)}
          selectedCellId={selectedCellId}
          liveStorms={liveStorms || []}
        />

        <AboutModal
          isOpen={isAboutOpen}
          onClose={() => setIsAboutOpen(false)}
        />

        <SettingsModal
          isOpen={isSettingsOpen}
          onClose={() => setIsSettingsOpen(false)}
          settings={userSettings}
          onUpdateSettings={(newSettings) => setUserSettings(newSettings)}
        />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-[#f8fafc] text-slate-800 font-sans">
      {/* 1. Full-Width Top Header */}
      <Header
        onOpenAbout={() => setIsAboutOpen(true)}
        onOpenSettings={() => setIsSettingsOpen(true)}
        onOpenWalkthrough={() => setIsWelcomeIntroOpen(true)}
        onToggleAssistant={handleToggleAssistant}
        isAssistantOpen={isAssistantOpen}
        onNavigateHome={() => setActiveNav('landing')}
      />

      {/* 2. Main 3-Column Workspace */}
      <div className="flex-1 flex w-full h-[calc(100vh-3.5rem)] overflow-hidden">
        {/* Left Column: Persistent Navigation Sidebar */}
        <Sidebar
          activeNav={activeNav}
          onSelectNav={handleSelectNav}
        />

        {/* Main Content Area */}
        {activeNav === 'global_monitoring' ? (
          <main className="flex-1 relative h-full bg-[#f8fafc] overflow-hidden">
            <GlobalMonitoringView
              onSelectRegion={handleSelectGlobalRegion}
              onBackToDashboard={() => setActiveNav('dashboard')}
            />
          </main>
        ) : activeNav === 'nowcasting' ? (
          <main className="flex-1 relative h-full bg-[#f8fafc] overflow-hidden">
            <NowcastingView onSelectCellOnMap={handleSelectCellFromView} liveStorms={liveStorms || []} />
          </main>
        ) : activeNav === 'storm_cells' ? (
          <main className="flex-1 relative h-full bg-[#f8fafc] overflow-hidden">
            <StormCellsView onSelectCellOnMap={handleSelectCellFromView} liveStorms={liveStorms || []} />
          </main>
        ) : activeNav === 'model_evaluation' ? (
          <main className="flex-1 relative h-full bg-[#f8fafc] overflow-hidden">
            <ModelEvaluationView />
          </main>
        ) : (
          <>
            {/* Center Column: OpenLayers Map Canvas */}
            <main className="flex-1 relative h-full bg-[#f8fafc] overflow-hidden">
              <OpenLayersMap
                activeLayer={activeLayer}
                setActiveLayer={setActiveLayer}
                leadTimeMin={leadTimeMin}
                setLeadTimeMin={setLeadTimeMin}
                showThunderstormProb={showThunderstormProb}
                showCells={showCells}
                showTrajectories={showTrajectories}
                showImpactZones={showImpactZones}
                showUncertainty={showUncertainty}
                liveStorms={liveStorms || []}
                selectedCellId={selectedCellId}
                onSelectCell={(id) => setSelectedCellId(id)}
                onRegionChange={handleRegionChange}
                mapTheme={userSettings.mapTheme}
                fallbackMode={fallbackMode}
                targetMapView={targetMapView}
              />
              {activeNav === 'impact' && (
                <div className="absolute top-4 left-4 z-20">
                  <CellTrackerPanel
                    activeCellsGeojson={{ features: (liveStorms || []).map(c => ({ properties: c })) }}
                    selectedCellId={selectedCellId}
                    onSelectCell={(id) => setSelectedCellId(id)}
                    onClose={() => setActiveNav('dashboard')}
                  />
                </div>
              )}
              {activeNav === 'historical' && (
                <div className="absolute top-4 left-4 z-20">
                  <HistoricalAnalogsPanel
                    selectedCellId={selectedCellId || (liveStorms && liveStorms.length > 0 ? liveStorms[0].cell_id : null)}
                    onClose={() => setActiveNav('dashboard')}
                  />
                </div>
              )}
            </main>

            {/* Right Column: Persistent Stats / Assistant Sidebar */}
            <div className="w-80 h-full flex flex-col shrink-0 border-l border-slate-200 bg-[#f8fafc]">
              {/* Right Column Tab Switcher */}
              <div className="flex items-center border-b border-slate-200 bg-white px-2 py-1.5 shrink-0">
                <button
                  onClick={() => setRightPanelTab('details')}
                  className={`flex-1 py-1.5 rounded-xl text-xs font-semibold transition ${
                    rightPanelTab === 'details'
                      ? 'bg-blue-50 text-blue-600 border border-blue-100 shadow-xs'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  Storm Overview
                </button>
                <button
                  onClick={() => {
                    setRightPanelTab('assistant');
                    setIsAssistantOpen(true);
                  }}
                  className={`flex-1 py-1.5 rounded-xl text-xs font-semibold transition flex items-center justify-center space-x-1 ${
                    rightPanelTab === 'assistant'
                      ? 'bg-blue-50 text-blue-600 border border-blue-100 shadow-xs'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  <span>AI Assistant</span>
                  <span className="w-1.5 h-1.5 rounded-full bg-blue-600" />
                </button>
              </div>

              {/* Tab Content */}
              <div className="flex-1 overflow-hidden">
                {rightPanelTab === 'assistant' ? (
                  <AIAssistantPanel
                    isOpen={true}
                    onClose={() => setRightPanelTab('details')}
                    onExecuteMapAction={handleExecuteMapAction}
                    selectedCellId={selectedCellId}
                  />
                ) : (
                  <RightPanel
                    liveStorms={hasRadarCoverage ? liveStorms || [] : []}
                    activeCellsCount={hasRadarCoverage ? (liveStorms ? liveStorms.length : 0) : 0}
                    selectedCell={hasRadarCoverage ? selectedCellData : null}
                    showThunderstormProb={showThunderstormProb}
                    setShowThunderstormProb={setShowThunderstormProb}
                    showCells={showCells}
                    setShowCells={setShowCells}
                    showTrajectories={showTrajectories}
                    setShowTrajectories={setShowTrajectories}
                    showImpactZones={showImpactZones}
                    setShowImpactZones={setShowImpactZones}
                    showUncertainty={showUncertainty}
                    setShowUncertainty={setShowUncertainty}
                    currentRegionName={currentRegionName}
                    hasRadarCoverage={hasRadarCoverage}
                  />
                )}
              </div>
            </div>
          </>
        )}
      </div>

      {/* Feature Modals */}
      <ReplayVerificationModal
        isOpen={isReplayOpen}
        onClose={() => {
          setIsReplayOpen(false);
          setActiveNav('dashboard');
        }}
        liveStorms={liveStorms || []}
      />

      <AlertModal
        isOpen={isAlertModalOpen}
        onClose={() => {
          setIsAlertModalOpen(false);
          setActiveNav('dashboard');
        }}
        selectedCellId={selectedCellId}
        liveStorms={liveStorms || []}
      />

      {/* Static Read-Only About Modal */}
      <AboutModal
        isOpen={isAboutOpen}
        onClose={() => {
          setIsAboutOpen(false);
          setActiveNav('dashboard');
        }}
      />

      {/* User Preferences Settings Modal */}
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => {
          setIsSettingsOpen(false);
          setActiveNav('dashboard');
        }}
        settings={userSettings}
        onUpdateSettings={(newSettings) => setUserSettings(newSettings)}
      />

      {/* One-Time Plain-Language Welcome Intro Modal */}
      <WelcomeIntroModal
        isOpen={isWelcomeIntroOpen}
        onClose={handleDismissWelcomeIntro}
        onStartTour={handleStartTourFromWelcome}
      />

      {/* Step-by-step Interactive Walkthrough Guide */}
      <NoviceWalkthrough
        isOpen={isWalkthroughOpen}
        onClose={() => setIsWalkthroughOpen(false)}
      />
    </div>
  );
}
