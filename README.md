# 🛰️ Project AURORA: Spacecraft Mission Operations Simulator & Engineering Workbench

**AURORA** — *Autonomous Unified Reconnaissance, Operations & Reliability Architecture*  
*(Fictional aerospace simulation expansion for educational and engineering portfolio use)*

---

> [!IMPORTANT]  
> **LEGAL & FLIGHT SAFETY DISCLAIMER**  
> Project AURORA is an explicitly fictional, software-only simulation platform designed for educational and portfolio demonstration. It simulates spacecraft subsystem dynamics, telemetry ingestion, flight software state machines, deterministic fault injection, command verification, and systems engineering traceability.  
> **It is NOT connected to real spacecraft, NOT certified for flight operations, NOT qualified for safety-critical aerospace missions, and NOT endorsed by any space agency.**

---

## 🌟 Architecture Overview

AURORA is structured with strict separation between presentation, operational state, domain simulation logic, and database persistence.

```
d:\AURORA\
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/          # REST & WebSocket route handlers
│   │   │   └── router.py        # Versioned API router aggregation (/api/v1, /api/health)
│   │   ├── core/                # Configuration (pydantic), logging
│   │   ├── db/                  # SQLite engine, sessions, SQLAlchemy models
│   │   ├── schemas/             # Typed Pydantic request/response models
│   │   ├── services/            # Pure domain services (state machine, fault rules, sim engine, etc.)
│   │   ├── tests/               # Pytest test suite (15 automated tests)
│   │   └── main.py              # FastAPI application entrypoint with clock ticker lifespan
│   ├── requirements.txt         # Pinned Python dependencies
│   └── .env.example             # Safe environment configuration template
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── common/          # Header with SIMULATION banner, Navigation, TelemetryCard
│   │   │   └── views/           # 12 functional operational views
│   │   ├── context/             # React Context for telemetry, WebSocket, and flight state
│   │   ├── lib/                 # Typed API client and WebSocket reconnect manager
│   │   ├── types/               # TypeScript data contracts matching backend models
│   │   ├── App.tsx              # Master shell and navigation view switcher
│   │   └── main.tsx             # React DOM root entrypoint
│   ├── tests/                   # Vitest & Testing Library tests
│   ├── package.json             # Pinned npm dependencies
│   └── vite.config.ts           # Vite bundler configuration with proxy
└── README.md                    # Project master documentation
```

### 1. Data Ownership & Backend Source of Truth
- The Python backend is the **sole source of truth** for spacecraft telemetry, operating state, command auditing, incident tracking, and simulation time.
- The frontend never fabricates or hardcodes telemetry; if the backend drops, the UI explicitly flags `DISCONNECTED` or `STALE TELEMETRY`.

### 2. Spacecraft State Machine
Explicit permitted and rejected transition matrix:
- **`STANDBY`** ➔ `NOMINAL`, `SIMULATION_STOPPED`
- **`NOMINAL`** ➔ `DEGRADED`, `SAFE_MODE`, `STANDBY`, `SIMULATION_STOPPED`
- **`DEGRADED`** ➔ `NOMINAL`, `SAFE_MODE`, `STANDBY`, `SIMULATION_STOPPED`
- **`SAFE_MODE`** ➔ `RECOVERY`, `SIMULATION_STOPPED` *(Direct transition from `SAFE_MODE` to `NOMINAL` is strictly rejected!)*
- **`RECOVERY`** ➔ `NOMINAL`, `DEGRADED`, `SAFE_MODE`, `SIMULATION_STOPPED`
- **`SIMULATION_STOPPED`** ➔ `STANDBY`

### 3. Fictional Overheating Threshold (75.0°C)
- When simulated core avionics temperature crosses **75.0°C**, the autonomous fault engine transitions the vehicle into **`SAFE_MODE`**, sheds non-essential electrical loads, and generates a persistent critical incident and state history record.
- **Cooling down does not automatically restore `NOMINAL`.** Operators must command a validated recovery procedure, and the backend verifies preconditions (temp < 75°C, battery SoC ≥ 30%, link != LOST) before authorizing recovery.

---

## 🚀 Quickstart & Local Setup

### Prerequisites
- Python 3.10+ (with pip)
- Node.js 18+ & npm

### 1. Backend Setup & Startup
```powershell
# In a terminal:
cd d:\AURORA\backend
pip install -r requirements.txt

# Run the FastAPI server:
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
- Interactive OpenAPI / Swagger API Docs: **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**
- Health Endpoint: **[http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)**

### 2. Frontend Setup & Startup
```powershell
# In a separate terminal:
cd d:\AURORA\frontend
npm install
npm run dev
```
- Open your browser at: **[http://localhost:5173](http://localhost:5173)**

---

## 🧪 Automated Testing & Acceptance Scenarios

### Executing Backend Tests
```powershell
cd d:\AURORA\backend
$env:PYTHONPATH="."
python -m pytest app/tests -v
```
**Test Results: 15 PASSED / 15 TOTAL**
- `test_health.py`: Health & metadata API verification
- `test_state_machine.py`: Permitted vs forbidden transitions, recovery preconditions
- `test_overheating_slice.py`: Phase 1 core vertical slice (75°C threshold, safe hold, persistence)
- `test_commands.py`: Command validation, safe mode lockouts, idempotency deduplication
- `test_incidents.py`: Incident acknowledge and resolve lifecycle
- `test_mission_planning.py`: DAG scheduling heuristic, circular dependency detection
- `test_scenarios.py`: Reproducible scenario lab runs (seed 42, 101)
- `test_acceptance_scenarios.py`: End-to-end verification of Scenarios A, C, D, F, H

### Executing Frontend Tests
```powershell
cd d:\AURORA\frontend
npm run test
```
**Test Results: 4 PASSED / 4 TOTAL across 3 Test Suites**
- `Telemetry.test.tsx`: Telemetry card rendering & nominal thresholds
- `EventLogReplay.test.tsx`: Event log & interactive Mission Replay Scrubber deck (read-only historical playback)
- `App.test.tsx`: Persistent brand identity, navigation tabs, and SIMULATION ONLY indicator

### Acceptance Scenarios Compliance Matrix
| Scenario | Description | Status | Evidence |
| :--- | :--- | :---: | :--- |
| **Scenario A** | Nominal Mission: active run, telemetry generated, state NOMINAL, events persisted | **PASS** | `test_acceptance_scenarios.py::test_scenario_a_nominal_mission` |
| **Scenario B** | Overheating: crosses 75°C, safe mode triggered, events persisted, temp drop does not auto-restore NOMINAL | **PASS** | `test_overheating_slice.py::test_first_vertical_slice_overheating_and_safe_mode` |
| **Scenario C** | Communication Loss: link state reflects LOST, fault incident logged, state remains nominal | **PASS** | `test_acceptance_scenarios.py::test_scenario_c_communication_loss` |
| **Scenario D** | Invalid Command: rejected with consistent error, state unchanged, rejection recorded | **PASS** | `test_commands.py::test_command_execution_and_idempotency` |
| **Scenario E** | Recovery: preconditions enforced, invalid attempts rejected, valid sequence restored | **PASS** | `test_overheating_slice.py` & `test_state_machine.py` |
| **Scenario F** | Persistence: records survive across database sessions and restarts | **PASS** | `test_acceptance_scenarios.py::test_scenario_f_persistence_records` |
| **Scenario G** | Mission Planning: DAG scheduling, dependency cycle detection, conflict reporting | **PASS** | `test_mission_planning.py::test_mission_planning_schedule_and_cycles` |
| **Scenario H** | Verification Reporting: unexecuted tests stay NOT RUN, live evidence changes status to PASS | **PASS** | `test_acceptance_scenarios.py::test_scenario_h_verification_reporting` |
| **Scenario I** | API Disconnection: UI flags DISCONNECTED and STALE TELEMETRY honestly | **PASS** | Verified in React Context watchdog |

---

## 📋 Primary Navigation Modules

1. **Mission Overview**: Spacecraft mode banner with one-click recovery, telemetry KPI cards, live SVG time-series charts, simulation lifecycle controls, active incidents summary, real-time event feed.
2. **Telemetry Operations**: Subsystem channel breakdowns (Thermal, EPS, TTC, ADCS, OBDH), historical queries with pagination, CSV export.
3. **Command Centre**: Validated command dispatcher (`SET_MODE`, `REQUEST_TELEMETRY`, `ADJUST_PARAMETER`, `RECOVERY_REQUEST`, `PING`), SAFE_MODE lockouts, idempotency key auditing.
4. **Faults & Incidents**: Rule-based incident log with two-phase lifecycle (Acknowledge vs Resolve with operator justification).
5. **Event Log & Replay**: Chronological audit trail, search & category filters, interactive **Mission Replay Scrubber** deck with non-mutating historical frame playback (Play/Pause, Step Back/Forward, Jump, 1x/2x/5x speed), timestamp-correlated telemetry snapshot, and CSV export.
6. **Mission Planning**: Task registry, DAG cycle detector, topological Earliest-Deadline-First heuristic scheduler, Gantt timeline visualization.
7. **Scenario Lab**: Reproducible flight anomaly scenarios (`SCN-NOMINAL`, `SCN-OVERHEAT-GRADUAL`, `SCN-COMM-LOSS`, `SCN-BATTERY-CRITICAL`) with observed vs expected comparison.
8. **Health Intelligence**: Subsystem integrity scores, rolling 30-frame statistics, explainable diagnostic decision logs.
9. **Systems Engineering**: Requirements registry with coverage indicator, risk matrix, architecture decision records (ADRs), interface control (ICDs), issue log.
10. **Verification & Test Evidence**: Traceability matrix between requirements and genuine test evidence; unexecuted cases remain `NOT RUN`.
11. **Reports & Exports**: Mission summary overview and one-click downloads for Telemetry CSV, Events CSV, Commands CSV, Traceability CSV.
12. **Settings / About**: Mission architecture details, physical assumptions, SQLite backup guide.

---

## 💾 Local SQLite Database & Backup Instructions

All persistent state is stored in a local SQLite database: `d:\AURORA\backend\aurora.db`.

- **Backup Command (PowerShell):**
  ```powershell
  Copy-Item -Path "d:\AURORA\backend\aurora.db" -Destination "d:\AURORA\backend\aurora_backup.db"
  ```
- **Resetting Database:**
  Simply delete `aurora.db`. Upon startup, the backend automatically initializes tables and re-seeds baseline requirements and scenarios.
