import asyncio
import json
from datetime import datetime
from typing import Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.simulation_engine import simulator
from app.core.logging import logger

router = APIRouter(prefix="/v1/ws", tags=["WebSockets"])

class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket client connected. Active connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket client disconnected. Active connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        if not self.active_connections:
            return
        dead_connections = set()
        text = json.dumps(message)
        for connection in self.active_connections:
            try:
                await connection.send_text(text)
            except Exception:
                dead_connections.add(connection)
        for dead in dead_connections:
            self.active_connections.discard(dead)

manager = ConnectionManager()

@router.websocket("/telemetry")
async def websocket_telemetry_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Initial greeting with current simulation state
        await websocket.send_text(json.dumps({
            "type": "CONNECTION_ESTABLISHED",
            "run_id": simulator.active_run_id,
            "timestamp_sim": simulator.sim_time_seconds,
            "timestamp_wall": datetime.utcnow().isoformat(),
            "payload": {
                "message": "Connected to AURORA Telemetry Stream",
                "cadence_hz": simulator.cadence_hz,
            }
        }))

        while True:
            # Send live telemetry frame at simulation cadence
            tel = simulator.latest_telemetry or {}
            envelope = {
                "type": "TELEMETRY_FRAME",
                "run_id": simulator.active_run_id,
                "timestamp_sim": simulator.sim_time_seconds,
                "timestamp_wall": datetime.utcnow().isoformat(),
                "payload": tel,
            }
            await websocket.send_text(json.dumps(envelope))
            
            # Non-blocking sleep for 1.0 / cadence_hz
            sleep_time = max(0.2, 1.0 / simulator.cadence_hz) if simulator.cadence_hz > 0 else 1.0
            await asyncio.sleep(sleep_time)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.warning(f"WebSocket error: {e}")
        manager.disconnect(websocket)
