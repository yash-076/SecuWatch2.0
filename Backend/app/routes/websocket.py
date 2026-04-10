import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.websocket_manager import ws_manager

router = APIRouter(prefix="/ws", tags=["WebSocket"])
logger = logging.getLogger(__name__)


@router.websocket("/alerts")
async def websocket_alerts(websocket: WebSocket):
    """
    WebSocket endpoint for real-time alert streaming.
    
    Endpoint: /ws/alerts
    Protocol: WebSocket
    
    Clients can connect and will receive JSON-formatted alerts
    whenever they are generated in the system.
    
    Message format:
    {
        "id": <alert_id>,
        "device_id": <device_id>,
        "type": "<alert_type>",
        "severity": "<severity>",
        "description": "<description>",
        "created_at": "<ISO 8601 timestamp>"
    }
    """
    await ws_manager.connect(websocket)
    try:
        # Keep connection alive and consume incoming frames.
        while True:
            await websocket.receive()
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)
