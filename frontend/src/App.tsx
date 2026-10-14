import React, { useState } from 'react';
import { useAurora } from './context/AuroraContext';
import { Header } from './components/common/Header';
import { Navigation, NavTab } from './components/common/Navigation';
import { MissionOverview } from './components/views/MissionOverview';
import { TelemetryOperations } from './components/views/TelemetryOperations';
import { CommandCentre } from './components/views/CommandCentre';
import { IncidentsView } from './components/views/IncidentsView';
import { EventLogView } from './components/views/EventLogView';
import { MissionPlanningView } from './components/views/MissionPlanningView';
import { ScenarioLabView } from './components/views/ScenarioLabView';
import { HealthIntelligenceView } from './components/views/HealthIntelligenceView';
import { SystemsEngineeringView } from './components/views/SystemsEngineeringView';
import { VerificationView } from './components/views/VerificationView';
import { ReportsView } from './components/views/ReportsView';
import { SettingsAboutView } from './components/views/SettingsAboutView';
import { PhysicsLabContainer } from './components/views/physics_lab/PhysicsLabContainer';
import { AlertCircle } from 'lucide-react';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<NavTab>('overview');
  const { incidents, error } = useAurora();

  const openIncidentsCount = incidents.filter(
    (i) => i.status === 'OPEN' || i.status === 'ACKNOWLEDGED'
  ).length;

  return (
    <div className="min-h-screen bg-space-900 text-slate-100 flex flex-col font-sans">
      {/* Top Application Header */}
      <Header />

      {/* Global Module Navigation Bar */}
      <Navigation
        activeTab={activeTab}
        onTabChange={setActiveTab}
        openIncidentsCount={openIncidentsCount}
      />

      {/* Global Connection / Backend Error Alert */}
      {error && (
        <div className="bg-red-950/80 border-b border-red-500/50 px-4 py-2 text-xs font-mono text-red-200 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
            <span>BACKEND COMMUNICATION FAULT: {error}</span>
          </div>
          <span className="text-[11px] text-red-400">Showing last cached telemetry state</span>
        </div>
      )}

      {/* Primary Main Content View */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 space-y-6">
        {activeTab === 'overview' && (
          <MissionOverview onNavigateToTab={(tab) => setActiveTab(tab)} />
        )}
        {activeTab === 'physics' && <PhysicsLabContainer />}
        {activeTab === 'telemetry' && <TelemetryOperations />}
        {activeTab === 'commands' && <CommandCentre />}
        {activeTab === 'incidents' && <IncidentsView />}
        {activeTab === 'events' && <EventLogView />}
        {activeTab === 'planning' && <MissionPlanningView />}
        {activeTab === 'scenarios' && <ScenarioLabView />}
        {activeTab === 'health' && <HealthIntelligenceView />}
        {activeTab === 'systems' && <SystemsEngineeringView />}
        {activeTab === 'verification' && <VerificationView />}
        {activeTab === 'reports' && <ReportsView />}
        {activeTab === 'settings' && <SettingsAboutView />}
      </main>

      {/* Aerospace Engineering Footer */}
      <footer className="border-t border-space-700 bg-space-850 px-4 py-3 text-center text-xs font-mono text-slate-400">
        <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-2">
          <span>PROJECT AURORA • AUTONOMOUS MISSION OPERATIONS SIMULATOR v1.0.0</span>
          <span className="text-amber-400/90 font-semibold">
            EDUCATIONAL & PORTFOLIO SIMULATION ONLY — NOT FLIGHT CERTIFIED
          </span>
          <span className="text-slate-400">LOCAL-FIRST SQLITE & FASTAPI</span>
        </div>
      </footer>
    </div>
  );
};

export default App;
