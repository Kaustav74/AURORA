import json
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.models import IncidentRecord, EventRecord
from app.schemas.incident import IncidentStatus, IncidentSeverity
from app.services.simulation_engine import simulator

class IncidentService:
    @staticmethod
    def get_incidents(
        db: Session,
        run_id: Optional[str] = None,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[IncidentRecord]:
        query = db.query(IncidentRecord)
        if run_id:
            query = query.filter(IncidentRecord.run_id == run_id)
        if status:
            query = query.filter(IncidentRecord.status == status)
        if severity:
            query = query.filter(IncidentRecord.severity == severity)
        return query.order_by(IncidentRecord.first_seen_sim.desc()).offset(offset).limit(limit).all()

    @staticmethod
    def get_incident_by_id(db: Session, incident_id: str) -> Optional[IncidentRecord]:
        return db.query(IncidentRecord).filter(IncidentRecord.id == incident_id).first()

    @staticmethod
    def acknowledge_incident(
        db: Session, incident_id: str, acknowledged_by: str = "OPERATOR"
    ) -> IncidentRecord:
        incident = db.query(IncidentRecord).filter(IncidentRecord.id == incident_id).first()
        if not incident:
            raise ValueError(f"Incident with ID {incident_id} not found.")

        incident.status = IncidentStatus.ACKNOWLEDGED.value
        incident.acknowledged_at = datetime.utcnow()
        incident.acknowledged_by = acknowledged_by

        # Record event
        event = EventRecord(
            id=f"EVT-INC-ACK-{incident_id}",
            run_id=incident.run_id,
            event_type="INCIDENT_ACKNOWLEDGED",
            category="OPERATIONS",
            severity="INFO",
            message=f"Incident '{incident.summary}' acknowledged by {acknowledged_by}. (Investigation ongoing; fault not cleared).",
            details_json=json.dumps({"incident_id": incident_id, "acknowledged_by": acknowledged_by}),
            timestamp_sim=simulator.sim_time_seconds,
            timestamp_wall=datetime.utcnow(),
        )
        db.add(event)
        db.commit()
        db.refresh(incident)
        return incident

    @staticmethod
    def resolve_incident(
        db: Session, incident_id: str, reason: str, resolved_by: str = "OPERATOR"
    ) -> IncidentRecord:
        incident = db.query(IncidentRecord).filter(IncidentRecord.id == incident_id).first()
        if not incident:
            raise ValueError(f"Incident with ID {incident_id} not found.")

        incident.status = IncidentStatus.RESOLVED.value
        incident.resolved_at = datetime.utcnow()
        incident.resolution_reason = reason

        event = EventRecord(
            id=f"EVT-INC-RES-{incident_id}",
            run_id=incident.run_id,
            event_type="INCIDENT_RESOLVED",
            category="OPERATIONS",
            severity="INFO",
            message=f"Incident '{incident.summary}' resolved: {reason}",
            details_json=json.dumps({"incident_id": incident_id, "reason": reason, "resolved_by": resolved_by}),
            timestamp_sim=simulator.sim_time_seconds,
            timestamp_wall=datetime.utcnow(),
        )
        db.add(event)
        db.commit()
        db.refresh(incident)
        return incident
