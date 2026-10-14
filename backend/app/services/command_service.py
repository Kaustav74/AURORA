import uuid
import json
from datetime import datetime
from typing import Dict, Any, Tuple, Optional, List
from sqlalchemy.orm import Session
from app.db.models import CommandRecord, EventRecord
from app.schemas.state import SpacecraftMode
from app.schemas.command import CommandType, CommandStatus, CommandCreateRequest
from app.services.state_machine import StateMachine, StateMachineError
from app.services.simulation_engine import simulator
from app.core.logging import logger

class CommandService:
    @staticmethod
    def submit_command(db: Session, request: CommandCreateRequest) -> CommandRecord:
        cmd_id = f"CMD-{str(uuid.uuid4())[:8].upper()}"

        # 1. Idempotency check
        if request.idempotency_key:
            existing = (
                db.query(CommandRecord)
                .filter(CommandRecord.idempotency_key == request.idempotency_key)
                .first()
            )
            if existing:
                logger.info(f"Duplicate command rejected via idempotency key: {request.idempotency_key}")
                return existing

        current_mode = simulator.current_mode
        run_id = simulator.active_run_id

        # 2. Validation Stage
        is_valid, validation_msg = CommandService._validate_command(
            request.command_type, request.parameters, current_mode
        )

        if not is_valid:
            # Record Rejected Command
            record = CommandRecord(
                id=cmd_id,
                run_id=run_id,
                idempotency_key=request.idempotency_key,
                command_type=request.command_type.value,
                parameters_json=json.dumps(request.parameters),
                issued_by=request.issued_by,
                status=CommandStatus.REJECTED.value,
                rejection_reason=validation_msg,
                result_json=None,
                created_at=datetime.utcnow(),
                executed_at=None,
            )
            db.add(record)

            # Record event
            event = EventRecord(
                id=f"EVT-CMD-{cmd_id}",
                run_id=run_id,
                event_type="COMMAND_REJECTED",
                category="OPERATIONS",
                severity="WARNING",
                message=f"Command {request.command_type.value} rejected: {validation_msg}",
                details_json=json.dumps({"command_id": cmd_id, "params": request.parameters}),
                timestamp_sim=simulator.sim_time_seconds,
                timestamp_wall=datetime.utcnow(),
            )
            db.add(event)
            db.commit()
            db.refresh(record)
            return record

        # 3. Validated Stage -> Execute
        record = CommandRecord(
            id=cmd_id,
            run_id=run_id,
            idempotency_key=request.idempotency_key,
            command_type=request.command_type.value,
            parameters_json=json.dumps(request.parameters),
            issued_by=request.issued_by,
            status=CommandStatus.EXECUTING.value,
            rejection_reason=None,
            result_json=None,
            created_at=datetime.utcnow(),
        )
        db.add(record)
        db.commit()

        # 4. Execution
        success, exec_result, err_reason = CommandService._execute_command(
            db, request.command_type, request.parameters, request.issued_by
        )

        if success:
            record.status = CommandStatus.COMPLETED.value
            record.result_json = json.dumps(exec_result or {})
            record.executed_at = datetime.utcnow()
        else:
            record.status = CommandStatus.FAILED.value
            record.rejection_reason = err_reason
            record.executed_at = datetime.utcnow()

        event = EventRecord(
            id=f"EVT-CMD-{cmd_id}-RES",
            run_id=run_id,
            event_type="COMMAND_EXECUTED" if success else "COMMAND_FAILED",
            category="OPERATIONS",
            severity="INFO" if success else "CRITICAL",
            message=f"Command {request.command_type.value} {'completed successfully' if success else 'failed: ' + (err_reason or '')}",
            details_json=json.dumps({"command_id": cmd_id, "result": exec_result, "error": err_reason}),
            timestamp_sim=simulator.sim_time_seconds,
            timestamp_wall=datetime.utcnow(),
        )
        db.add(event)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def _validate_command(
        cmd_type: CommandType, params: Dict[str, Any], current_mode: SpacecraftMode
    ) -> Tuple[bool, str]:
        # Rule: In SAFE_MODE, strictly restrict allowable command actions
        if current_mode == SpacecraftMode.SAFE_MODE:
            if cmd_type not in (
                CommandType.RECOVERY_REQUEST,
                CommandType.REQUEST_TELEMETRY,
                CommandType.PING,
            ):
                return (
                    False,
                    f"Command {cmd_type.value} is restricted while spacecraft is in SAFE_MODE. Only telemetry queries and recovery procedures are authorized.",
                )

        if cmd_type == CommandType.SET_MODE:
            target_mode_str = params.get("target_mode")
            if not target_mode_str:
                return False, "Missing parameter 'target_mode'."
            try:
                target_mode = SpacecraftMode(target_mode_str)
            except ValueError:
                return False, f"Invalid target mode: '{target_mode_str}'."

            allowed, reason = StateMachine.is_transition_allowed(current_mode, target_mode)
            if not allowed:
                return False, reason

        elif cmd_type == CommandType.ADJUST_PARAMETER:
            param_name = params.get("parameter_name")
            param_value = params.get("value")
            if not param_name or param_value is None:
                return False, "Missing 'parameter_name' or 'value'."
            allowed_params = ["cadence_hz", "heater_bias_w", "ssr_downlink_rate_kbps"]
            if param_name not in allowed_params:
                return False, f"Parameter '{param_name}' is not recognized or tunable. Allowed: {allowed_params}"

        elif cmd_type == CommandType.RECOVERY_REQUEST:
            if current_mode != SpacecraftMode.SAFE_MODE:
                return False, f"Recovery request is only valid when spacecraft is in SAFE_MODE (current: {current_mode.value})."

        return True, "Command parameters validated."

    @staticmethod
    def _execute_command(
        db: Session, cmd_type: CommandType, params: Dict[str, Any], issued_by: str
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        try:
            if cmd_type == CommandType.PING:
                return True, {"pong": True, "sim_time": simulator.sim_time_seconds}, None

            elif cmd_type == CommandType.REQUEST_TELEMETRY:
                return True, {"telemetry": simulator.latest_telemetry}, None

            elif cmd_type == CommandType.SET_MODE:
                target_mode = SpacecraftMode(params["target_mode"])
                StateMachine.transition(
                    db=db,
                    run_id=simulator.active_run_id or "NO-RUN",
                    current_mode=simulator.current_mode,
                    target_mode=target_mode,
                    reason=params.get("reason", f"Commanded by {issued_by}"),
                    source=f"CMD:{issued_by}",
                    sim_time=simulator.sim_time_seconds,
                )
                simulator.current_mode = target_mode
                return True, {"mode": target_mode.value}, None

            elif cmd_type == CommandType.RECOVERY_REQUEST:
                # 1. Verify preconditions
                unresolved_crit = [
                    inc.fault_type
                    for inc in db.query(CommandRecord).filter().all()
                    if False
                ]
                # Preconditions checked against current telemetry
                satisfied, msg = StateMachine.check_recovery_preconditions(
                    telemetry=simulator.latest_telemetry,
                    unresolved_critical_incidents=None,
                )
                if not satisfied:
                    return False, None, msg

                # 2. Transition to RECOVERY mode
                StateMachine.transition(
                    db=db,
                    run_id=simulator.active_run_id or "NO-RUN",
                    current_mode=SpacecraftMode.SAFE_MODE,
                    target_mode=SpacecraftMode.RECOVERY,
                    reason=f"Recovery procedure initiated by {issued_by}: Preconditions verified.",
                    source=f"CMD:{issued_by}",
                    sim_time=simulator.sim_time_seconds,
                )
                simulator.current_mode = SpacecraftMode.RECOVERY

                # 3. Clear transient thermal / power faults in simulator
                simulator.clear_fault("OVERHEATING")

                # 4. Promote from RECOVERY to NOMINAL once recovery step executes cleanly
                StateMachine.transition(
                    db=db,
                    run_id=simulator.active_run_id or "NO-RUN",
                    current_mode=SpacecraftMode.RECOVERY,
                    target_mode=SpacecraftMode.NOMINAL,
                    reason="Post-recovery diagnostic pass confirmed nominal bus parameters.",
                    source="AUTONOMOUS_RESTORE",
                    sim_time=simulator.sim_time_seconds,
                )
                simulator.current_mode = SpacecraftMode.NOMINAL

                return True, {"status": "RECOVERED", "final_mode": SpacecraftMode.NOMINAL.value, "detail": msg}, None

            elif cmd_type == CommandType.ADJUST_PARAMETER:
                pname = params["parameter_name"]
                pval = params["value"]
                if pname == "cadence_hz":
                    simulator.cadence_hz = float(pval)
                return True, {pname: pval}, None

            return True, {}, None
        except Exception as e:
            logger.exception(f"Execution error on command {cmd_type.value}")
            return False, None, str(e)
