import React from 'react';
import {
  LayoutDashboard,
  Activity,
  Terminal,
  AlertTriangle,
  ScrollText,
  Calendar,
  FlaskConical,
  HeartPulse,
  Workflow,
  CheckCircle2,
  FileSpreadsheet,
  Info,
} from 'lucide-react';

export type NavTab =
  | 'overview'
  | 'telemetry'
  | 'commands'
  | 'incidents'
  | 'events'
  | 'planning'
  | 'scenarios'
  | 'health'
  | 'systems'
  | 'verification'
  | 'reports'
  | 'settings';

interface NavigationProps {
  activeTab: NavTab;
  onTabChange: (tab: NavTab) => void;
  openIncidentsCount: number;
}

export const Navigation: React.FC<NavigationProps> = ({
  activeTab,
  onTabChange,
  openIncidentsCount,
}) => {
  const tabs = [
    { id: 'overview' as NavTab, label: 'Overview', icon: LayoutDashboard },
    { id: 'telemetry' as NavTab, label: 'Telemetry', icon: Activity },
    { id: 'commands' as NavTab, label: 'Command Centre', icon: Terminal },
    {
      id: 'incidents' as NavTab,
      label: 'Faults & Incidents',
      icon: AlertTriangle,
      badge: openIncidentsCount > 0 ? openIncidentsCount : undefined,
    },
    { id: 'events' as NavTab, label: 'Event Log & Replay', icon: ScrollText },
    { id: 'planning' as NavTab, label: 'Mission Planning', icon: Calendar },
    { id: 'scenarios' as NavTab, label: 'Scenario Lab', icon: FlaskConical },
    { id: 'health' as NavTab, label: 'Health Intel', icon: HeartPulse },
    { id: 'systems' as NavTab, label: 'Systems Eng', icon: Workflow },
    { id: 'verification' as NavTab, label: 'Verification', icon: CheckCircle2 },
    { id: 'reports' as NavTab, label: 'Reports & Exports', icon: FileSpreadsheet },
    { id: 'settings' as NavTab, label: 'About & Setup', icon: Info },
  ];

  return (
    <nav className="border-b border-space-700 bg-space-850 px-4 overflow-x-auto scrollbar-none">
      <div className="flex space-x-1 py-1.5 min-w-max">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => onTabChange(tab.id)}
              className={`flex items-center space-x-2 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                isActive
                  ? 'bg-cyan-500/15 text-cyan-300 border border-cyan-500/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-space-700/50'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{tab.label}</span>
              {tab.badge !== undefined && (
                <span className="bg-red-500/80 text-white text-[10px] font-bold px-1.5 py-0.2 rounded-full">
                  {tab.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>
    </nav>
  );
};
