import json
import csv
import io
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.db.models import EventRecord, TelemetryRecord, SpacecraftStateRecord, IncidentRecord

class EventService:
    @staticmethod
    def get_events(
        db: Session,
        run_id: Optional[str] = None,
        category: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[EventRecord]:
        query = db.query(EventRecord)
        if run_id:
            query = query.filter(EventRecord.run_id == run_id)
        if category:
            query = query.filter(EventRecord.category == category)
        if severity:
            query = query.filter(EventRecord.severity == severity)
        return query.order_by(EventRecord.timestamp_sim.desc(), EventRecord.timestamp_wall.desc()).offset(offset).limit(limit).all()

    @staticmethod
    def get_event_by_id(db: Session, event_id: str) -> Optional[EventRecord]:
        return db.query(EventRecord).filter(EventRecord.id == event_id).first()

    @staticmethod
    def get_replay_timeline(db: Session, run_id: str) -> List[Dict[str, Any]]:
        events = (
            db.query(EventRecord)
            .filter(EventRecord.run_id == run_id)
            .order_by(EventRecord.timestamp_sim.asc(), EventRecord.timestamp_wall.asc())
            .all()
        )
        timeline = []
        for e in events:
            details = json.loads(e.details_json) if e.details_json else {}
            timeline.append({
                "id": e.id,
                "sim_time": e.timestamp_sim,
                "wall_time": e.timestamp_wall.isoformat() if e.timestamp_wall else None,
                "type": e.event_type,
                "category": e.category,
                "severity": e.severity,
                "message": e.message,
                "details": details,
            })
        return timeline

    @staticmethod
    def get_replay_frames(db: Session, run_id: str) -> Dict[str, Any]:
        """
        Fetch all historical telemetry frames and events for this run to power the client-side replay scrubber.
        Read-only query; strictly does not mutate active simulation state.
        """
        frames = (
            db.query(TelemetryRecord)
            .filter(TelemetryRecord.run_id == run_id)
            .order_by(TelemetryRecord.timestamp_sim.asc())
            .all()
        )
        events = (
            db.query(EventRecord)
            .filter(EventRecord.run_id == run_id)
            .order_by(EventRecord.timestamp_sim.asc())
            .all()
        )

        frame_data = [
            {
                "timestamp_sim": round(f.timestamp_sim, 2),
                "mode": f.mode,
                "temperature_c": round(f.temperature_c, 2),
                "battery_soc_pct": round(f.battery_soc_pct, 2),
                "bus_voltage_v": round(f.bus_voltage_v, 2),
                "current_draw_a": round(f.current_draw_a, 2),
                "comm_status": f.comm_status,
                "signal_quality_pct": round(f.signal_quality_pct, 1),
                "attitude_error_deg": round(f.attitude_error_deg, 3),
                "angular_rate_deg_s": round(f.angular_rate_deg_s, 4),
                "storage_used_pct": round(f.storage_used_pct, 2),
                "sensors_valid": f.sensors_valid,
            }
            for f in frames
        ]

        min_time = frame_data[0]["timestamp_sim"] if frame_data else 0.0
        max_time = frame_data[-1]["timestamp_sim"] if frame_data else 0.0

        return {
            "run_id": run_id,
            "min_sim_time": min_time,
            "max_sim_time": max_time,
            "total_frames": len(frame_data),
            "frames": frame_data,
            "events_count": len(events),
        }

    @staticmethod
    def export_events_csv(db: Session, run_id: Optional[str] = None) -> str:
        events = EventService.get_events(db=db, run_id=run_id, limit=5000)
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "run_id", "sim_time_s", "wall_time", "event_type", "category", "severity", "message"])
        for e in events:
            writer.writerow([
                e.id,
                e.run_id or "",
                f"{e.timestamp_sim:.2f}",
                e.timestamp_wall.isoformat() if e.timestamp_wall else "",
                e.event_type,
                e.category,
                e.severity,
                e.message,
            ])
        return output.getvalue()
