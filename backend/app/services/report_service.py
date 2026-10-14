import io
import csv
import json
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.db.models import TelemetryRecord, CommandRecord, IncidentRecord, EventRecord
from app.services.systems_engineering_service import SystemsEngineeringService
from app.services.simulation_engine import simulator
from app.schemas.report import MissionReportSummary

class ReportService:
    @staticmethod
    def get_mission_summary(db: Session) -> MissionReportSummary:
        readiness = SystemsEngineeringService.get_readiness_summary(db)

        run_id = simulator.active_run_id
        tel_count = db.query(TelemetryRecord).filter(TelemetryRecord.run_id == run_id).count() if run_id else 0
        evt_count = db.query(EventRecord).filter(EventRecord.run_id == run_id).count() if run_id else 0
        cmd_count = db.query(CommandRecord).filter(CommandRecord.run_id == run_id).count() if run_id else 0
        open_inc = db.query(IncidentRecord).filter(IncidentRecord.status.in_(["OPEN", "ACKNOWLEDGED"])).count()
        res_inc = db.query(IncidentRecord).filter(IncidentRecord.status == "RESOLVED").count()

        notes = [
            f"Active run: {run_id or 'No active run'}",
            f"Simulation clock: {simulator.sim_time_seconds:.1f}s",
            f"Current mode: {simulator.current_mode.value}",
            f"Requirement coverage: {readiness.requirement_coverage_pct}%",
        ]

        return MissionReportSummary(
            generated_at=datetime.utcnow(),
            run_id=run_id,
            simulation_time_seconds=simulator.sim_time_seconds,
            spacecraft_mode=simulator.current_mode.value,
            total_telemetry_frames=tel_count,
            total_events=evt_count,
            open_incidents=open_inc,
            resolved_incidents=res_inc,
            total_commands=cmd_count,
            readiness_score_pct=readiness.requirement_coverage_pct,
            notes=notes,
        )

    @staticmethod
    def export_telemetry_csv(db: Session, run_id: Optional[str] = None) -> str:
        query = db.query(TelemetryRecord)
        if run_id:
            query = query.filter(TelemetryRecord.run_id == run_id)
        records = query.order_by(TelemetryRecord.timestamp_sim.asc()).limit(5000).all()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "timestamp_sim_s",
            "timestamp_wall",
            "mode",
            "temperature_c",
            "battery_soc_pct",
            "bus_voltage_v",
            "current_draw_a",
            "comm_status",
            "signal_quality_pct",
            "attitude_error_deg",
            "angular_rate_deg_s",
            "storage_used_pct",
            "sensors_valid",
        ])
        for r in records:
            writer.writerow([
                f"{r.timestamp_sim:.2f}",
                r.timestamp_wall.isoformat() if r.timestamp_wall else "",
                r.mode,
                f"{r.temperature_c:.2f}",
                f"{r.battery_soc_pct:.2f}",
                f"{r.bus_voltage_v:.2f}",
                f"{r.current_draw_a:.2f}",
                r.comm_status,
                f"{r.signal_quality_pct:.1f}",
                f"{r.attitude_error_deg:.3f}",
                f"{r.angular_rate_deg_s:.4f}",
                f"{r.storage_used_pct:.2f}",
                r.sensors_valid,
            ])
        return output.getvalue()

    @staticmethod
    def export_commands_csv(db: Session, run_id: Optional[str] = None) -> str:
        query = db.query(CommandRecord)
        if run_id:
            query = query.filter(CommandRecord.run_id == run_id)
        records = query.order_by(CommandRecord.created_at.desc()).limit(2000).all()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "id",
            "run_id",
            "created_at",
            "command_type",
            "status",
            "issued_by",
            "parameters",
            "rejection_reason",
        ])
        for c in records:
            writer.writerow([
                c.id,
                c.run_id or "",
                c.created_at.isoformat() if c.created_at else "",
                c.command_type,
                c.status,
                c.issued_by,
                c.parameters_json,
                c.rejection_reason or "",
            ])
        return output.getvalue()

    @staticmethod
    def export_traceability_matrix_csv(db: Session) -> str:
        reqs = SystemsEngineeringService.get_requirements(db)
        cases = SystemsEngineeringService.get_verification_cases(db)
        case_map = {c.id: c for c in cases}

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "requirement_id",
            "title",
            "category",
            "priority",
            "verification_method",
            "linked_test_cases",
            "test_statuses",
            "overall_verification_status",
        ])
        for r in reqs:
            test_statuses = [case_map[tid].latest_status for tid in r.linked_test_ids if tid in case_map]
            writer.writerow([
                r.id,
                r.title,
                r.category,
                r.priority,
                r.verification_method,
                ";".join(r.linked_test_ids),
                ";".join(test_statuses),
                r.verification_status,
            ])
        return output.getvalue()
