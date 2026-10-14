from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.db.models import TelemetryRecord
from app.schemas.health import SubsystemHealth, SubsystemTrend, SpacecraftHealthOverview
from app.services.simulation_engine import simulator
from app.core.config import settings

class HealthService:
    @staticmethod
    def get_health_overview(db: Session, run_id: Optional[str] = None) -> SpacecraftHealthOverview:
        effective_run_id = run_id or simulator.active_run_id

        # Fetch last 30 telemetry records for rolling stats
        records = []
        if effective_run_id:
            records = (
                db.query(TelemetryRecord)
                .filter(TelemetryRecord.run_id == effective_run_id)
                .order_by(TelemetryRecord.timestamp_sim.desc())
                .limit(30)
                .all()
            )

        # Fallback to current simulator telemetry if no DB records yet
        latest = simulator.latest_telemetry or {}

        temp = float(latest.get("temperature_c", 24.0))
        soc = float(latest.get("battery_soc_pct", 95.0))
        voltage = float(latest.get("bus_voltage_v", 28.0))
        comm = str(latest.get("comm_status", "NOMINAL"))
        signal = float(latest.get("signal_quality_pct", 98.0))
        att_err = float(latest.get("attitude_error_deg", 0.15))
        storage = float(latest.get("storage_used_pct", 35.0))
        sensors_valid = bool(latest.get("sensors_valid", True))

        rule_explanations = []

        # 1. Thermal Subsystem
        thermal_warnings = []
        if temp >= settings.OVERHEAT_THRESHOLD_C:
            thermal_status = "CRITICAL"
            thermal_score = max(10.0, 100.0 - (temp - settings.OVERHEAT_THRESHOLD_C) * 5.0)
            thermal_warnings.append(f"Temperature {temp:.1f}°C exceeds critical threshold {settings.OVERHEAT_THRESHOLD_C}°C.")
            rule_explanations.append(f"[RULE TH-01] Critical overheating detected ({temp:.1f}°C >= {settings.OVERHEAT_THRESHOLD_C}°C). Autonomous safe mode activated.")
        elif temp > 50.0:
            thermal_status = "DEGRADED"
            thermal_score = 65.0
            thermal_warnings.append(f"Elevated temperature {temp:.1f}°C approaching safety boundary.")
            rule_explanations.append(f"[RULE TH-02] Elevated temperature ({temp:.1f}°C > 50.0°C). Increased thermal radiator dissipation advised.")
        else:
            thermal_status = "NOMINAL"
            thermal_score = 100.0 - abs(temp - 22.0) * 0.8
            rule_explanations.append(f"[RULE TH-00] Thermal control nominal ({temp:.1f}°C within 0–50°C band).")

        thermal_subsystem = SubsystemHealth(
            name="Thermal Control",
            status=thermal_status,
            score_pct=round(max(0.0, min(100.0, thermal_score)), 1),
            summary=f"Core avionics package at {temp:.1f}°C.",
            active_warnings=thermal_warnings,
        )

        # 2. Electrical Power Subsystem (EPS)
        power_warnings = []
        if soc < 20.0 or voltage < 22.0:
            power_status = "CRITICAL"
            power_score = max(15.0, soc)
            power_warnings.append(f"Critical power drain (SoC {soc:.1f}%, Bus {voltage:.2f}V).")
            rule_explanations.append(f"[RULE EPS-01] Battery reserve critical (< 20%). Non-essential loads shed.")
        elif soc < 40.0:
            power_status = "DEGRADED"
            power_score = 60.0
            power_warnings.append(f"Low battery reserve (SoC {soc:.1f}%).")
            rule_explanations.append(f"[RULE EPS-02] Battery reserve caution ({soc:.1f}% < 40%).")
        else:
            power_status = "NOMINAL"
            power_score = min(100.0, soc)
            rule_explanations.append(f"[RULE EPS-00] Power generation balance nominal (SoC: {soc:.1f}%, Bus: {voltage:.2f}V).")

        power_subsystem = SubsystemHealth(
            name="Electrical Power (EPS)",
            status=power_status,
            score_pct=round(power_score, 1),
            summary=f"Battery {soc:.1f}%, Bus {voltage:.2f}V.",
            active_warnings=power_warnings,
        )

        # 3. Communications (TTC)
        comm_warnings = []
        if comm == "LOST":
            comm_status = "CRITICAL"
            comm_score = 0.0
            comm_warnings.append("Ground RF carrier lost. Autonomous link search active.")
            rule_explanations.append("[RULE COM-01] RF carrier acquisition failure. Uplink/downlink offline.")
        elif comm == "DEGRADED" or signal < 50.0:
            comm_status = "DEGRADED"
            comm_score = signal
            comm_warnings.append(f"Link margin degraded (Signal {signal:.1f}%).")
            rule_explanations.append(f"[RULE COM-02] Signal margin degraded ({signal:.1f}%). High bit-error rate expected.")
        else:
            comm_status = "NOMINAL"
            comm_score = signal
            rule_explanations.append("[RULE COM-00] High-gain transponder locked with ground tracking station.")

        comm_subsystem = SubsystemHealth(
            name="Communications (TTC)",
            status=comm_status,
            score_pct=round(comm_score, 1),
            summary=f"Status: {comm}, Signal: {signal:.1f}%.",
            active_warnings=comm_warnings,
        )

        # 4. ADCS
        adcs_warnings = []
        if att_err > 15.0:
            adcs_status = "CRITICAL"
            adcs_score = 30.0
            adcs_warnings.append(f"Excessive pointing error ({att_err:.2f}° > 15°).")
            rule_explanations.append(f"[RULE ADCS-01] Reaction wheel desaturation or sun-sensor loss ({att_err:.2f}° error).")
        elif att_err > 1.0:
            adcs_status = "DEGRADED"
            adcs_score = 75.0
            adcs_warnings.append(f"Minor pointing error ({att_err:.2f}°).")
            rule_explanations.append(f"[RULE ADCS-02] ADCS pointing error ({att_err:.2f}°) outside fine pointing budget.")
        else:
            adcs_status = "NOMINAL"
            adcs_score = 98.0
            rule_explanations.append("[RULE ADCS-00] Fine attitude hold locked within 1° error budget.")

        adcs_subsystem = SubsystemHealth(
            name="Attitude Control (ADCS)",
            status=adcs_status,
            score_pct=round(adcs_score, 1),
            summary=f"Pointing error: {att_err:.3f}°.",
            active_warnings=adcs_warnings,
        )

        # 5. OBDH / Data
        obdh_warnings = []
        if storage > 90.0 or not sensors_valid:
            obdh_status = "CRITICAL" if storage > 95.0 or not sensors_valid else "DEGRADED"
            obdh_score = 45.0
            if storage > 90.0:
                obdh_warnings.append(f"Mass memory buffer nearing capacity ({storage:.1f}%).")
            if not sensors_valid:
                obdh_warnings.append("Telemetry parity check failed / sensor invalid.")
            rule_explanations.append(f"[RULE OBDH-01] Solid-state recorder buffer at {storage:.1f}%. Downlink required.")
        else:
            obdh_status = "NOMINAL"
            obdh_score = 100.0 - storage * 0.2
            rule_explanations.append("[RULE OBDH-00] Telemetry frame encoder and memory recorder nominal.")

        obdh_subsystem = SubsystemHealth(
            name="Data Handling (OBDH)",
            status=obdh_status,
            score_pct=round(obdh_score, 1),
            summary=f"Storage used: {storage:.1f}%, Parity: OK.",
            active_warnings=obdh_warnings,
        )

        subsystems = [thermal_subsystem, power_subsystem, comm_subsystem, adcs_subsystem, obdh_subsystem]

        # Calculate Rolling Stats
        key_metrics = []
        if records:
            temps = [r.temperature_c for r in records]
            socs = [r.battery_soc_pct for r in records]
            key_metrics.append(SubsystemTrend(
                metric_name="Core Temperature (°C)",
                current_value=temp,
                rolling_avg=round(sum(temps) / len(temps), 2),
                min_value=round(min(temps), 2),
                max_value=round(max(temps), 2),
                trend_direction="INCREASING" if temps[0] > temps[-1] + 0.5 else ("DECREASING" if temps[0] < temps[-1] - 0.5 else "STABLE"),
                is_anomalous=temp >= settings.OVERHEAT_THRESHOLD_C,
                explanation="Monitors thermal equilibrium across avionics bays.",
            ))
            key_metrics.append(SubsystemTrend(
                metric_name="Battery State of Charge (%)",
                current_value=soc,
                rolling_avg=round(sum(socs) / len(socs), 2),
                min_value=round(min(socs), 2),
                max_value=round(max(socs), 2),
                trend_direction="INCREASING" if socs[0] > socs[-1] + 1.0 else ("DECREASING" if socs[0] < socs[-1] - 1.0 else "STABLE"),
                is_anomalous=soc < 20.0,
                explanation="Monitors energy storage balance between eclipse and insolation.",
            ))

        # Overall Status
        if any(s.status == "CRITICAL" for s in subsystems):
            overall_status = "CRITICAL"
        elif any(s.status == "DEGRADED" for s in subsystems):
            overall_status = "DEGRADED"
        else:
            overall_status = "NOMINAL"

        avg_score = sum(s.score_pct for s in subsystems) / len(subsystems)

        return SpacecraftHealthOverview(
            overall_status=overall_status,
            overall_health_pct=round(avg_score, 1),
            subsystems=subsystems,
            key_metrics=key_metrics,
            rule_explanations=rule_explanations,
        )
