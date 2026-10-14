import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import { api } from '../lib/api-client';
import { TelemetryWebSocketClient, ConnectionStatus, WebSocketEnvelope } from '../lib/websocket';
import {
  TelemetryFrame,
  SimulationStatusResponse,
  SpacecraftStateResponse,
  IncidentItem,
  EventItem,
} from '../types';

interface AuroraContextValue {
  connectionStatus: ConnectionStatus;
  telemetry: TelemetryFrame | null;
  telemetryHistory: TelemetryFrame[];
  simStatus: SimulationStatusResponse | null;
  spacecraftState: SpacecraftStateResponse | null;
  incidents: IncidentItem[];
  events: EventItem[];
  isLoading: boolean;
  error: string | null;
  isStale: boolean;
  lastUpdated: Date | null;
  refreshAll: () => Promise<void>;
  startSim: (name: string, seed?: number, cadence?: number) => Promise<void>;
  pauseSim: () => Promise<void>;
  resumeSim: () => Promise<void>;
  stopSim: () => Promise<void>;
  stepSim: (dt?: number) => Promise<void>;
  recoverSpacecraft: (reason: string) => Promise<void>;
}

const AuroraContext = createContext<AuroraContextValue | undefined>(undefined);

export const AuroraProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('RECONNECTING');
  const [telemetry, setTelemetry] = useState<TelemetryFrame | null>(null);
  const [telemetryHistory, setTelemetryHistory] = useState<TelemetryFrame[]>([]);
  const [simStatus, setSimStatus] = useState<SimulationStatusResponse | null>(null);
  const [spacecraftState, setSpacecraftState] = useState<SpacecraftStateResponse | null>(null);
  const [incidents, setIncidents] = useState<IncidentItem[]>([]);
  const [events, setEvents] = useState<EventItem[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [isStale, setIsStale] = useState<boolean>(false);

  const wsClientRef = useRef<TelemetryWebSocketClient | null>(null);
  const lastPacketTimeRef = useRef<number>(Date.now());

  // Polling fallback / periodic refresh
  const refreshAll = useCallback(async () => {
    try {
      const [tel, hist, status, state, incs, evts] = await Promise.all([
        api.getCurrentTelemetry().catch(() => null),
        api.getTelemetryHistory(50).catch(() => []),
        api.getSimulationStatus().catch(() => null),
        api.getCurrentState().catch(() => null),
        api.getIncidents().catch(() => []),
        api.getEvents(undefined, 50).catch(() => []),
      ]);

      if (tel) {
        setTelemetry(tel);
        lastPacketTimeRef.current = Date.now();
        setLastUpdated(new Date());
        setIsStale(false);
      }
      if (hist && hist.length > 0) setTelemetryHistory(hist);
      if (status) setSimStatus(status);
      if (state) setSpacecraftState(state);
      setIncidents(incs);
      setEvents(evts);
      setConnectionStatus('CONNECTED');
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to connect to backend.');
      setConnectionStatus('DISCONNECTED');
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Staleness watchdog check: runs every 2 seconds
  useEffect(() => {
    const staleInterval = setInterval(() => {
      const elapsed = Date.now() - lastPacketTimeRef.current;
      if (elapsed > 6000 && connectionStatus === 'CONNECTED') {
        setIsStale(true);
      } else {
        setIsStale(false);
      }
    }, 2000);
    return () => clearInterval(staleInterval);
  }, [connectionStatus]);

  // Initial load and WebSocket setup
  useEffect(() => {
    refreshAll();

    const ws = new TelemetryWebSocketClient();
    wsClientRef.current = ws;

    ws.connect(
      (envelope: WebSocketEnvelope) => {
        if (envelope.type === 'TELEMETRY_FRAME' && envelope.payload) {
          const frame = envelope.payload as TelemetryFrame;
          setTelemetry(frame);
          lastPacketTimeRef.current = Date.now();
          setLastUpdated(new Date());
          setIsStale(false);
          setTelemetryHistory((prev) => {
            const next = [...prev, frame];
            return next.length > 60 ? next.slice(next.length - 60) : next;
          });
        }
      },
      (status: ConnectionStatus) => {
        setConnectionStatus(status);
      }
    );

    // Periodic poll for events, incidents, state
    const pollInterval = setInterval(() => {
      api.getCurrentState().then(setSpacecraftState).catch(() => {});
      api.getIncidents().then(setIncidents).catch(() => {});
      api.getEvents(undefined, 30).then(setEvents).catch(() => {});
      api.getSimulationStatus().then(setSimStatus).catch(() => {});
    }, 3000);

    return () => {
      clearInterval(pollInterval);
      ws.disconnect();
    };
  }, [refreshAll]);

  const startSim = async (name: string, seed = 42, cadence = 1.0) => {
    try {
      await api.startSimulation(name, seed, cadence);
      await refreshAll();
    } catch (err: any) {
      setError(err.message);
      throw err;
    }
  };

  const pauseSim = async () => {
    try {
      await api.pauseSimulation();
      await refreshAll();
    } catch (err: any) {
      setError(err.message);
      throw err;
    }
  };

  const resumeSim = async () => {
    try {
      await api.resumeSimulation();
      await refreshAll();
    } catch (err: any) {
      setError(err.message);
      throw err;
    }
  };

  const stopSim = async () => {
    try {
      await api.stopSimulation();
      await refreshAll();
    } catch (err: any) {
      setError(err.message);
      throw err;
    }
  };

  const stepSim = async (dt = 1.0) => {
    try {
      await api.stepSimulation(dt);
      await refreshAll();
    } catch (err: any) {
      setError(err.message);
      throw err;
    }
  };

  const recoverSpacecraft = async (reason: string) => {
    try {
      await api.requestRecovery('LEAD_FLIGHT_CONTROLLER', reason);
      await refreshAll();
    } catch (err: any) {
      setError(err.message);
      throw err;
    }
  };

  return (
    <AuroraContext.Provider
      value={{
        connectionStatus,
        telemetry,
        telemetryHistory,
        simStatus,
        spacecraftState,
        incidents,
        events,
        isLoading,
        error,
        isStale,
        lastUpdated,
        refreshAll,
        startSim,
        pauseSim,
        resumeSim,
        stopSim,
        stepSim,
        recoverSpacecraft,
      }}
    >
      {children}
    </AuroraContext.Provider>
  );
};

export const useAurora = () => {
  const context = useContext(AuroraContext);
  if (!context) {
    throw new Error('useAurora must be used within an AuroraProvider');
  }
  return context;
};
