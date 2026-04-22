import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from app.services.websocket_manager import ws_manager
from app.utils.jwt import TokenType, decode_token

router = APIRouter(prefix="/ws", tags=["WebSocket"])
logger = logging.getLogger(__name__)


@router.websocket("/alerts")
async def websocket_alerts(websocket: WebSocket, token: str = Query(None)):
    """
    WebSocket endpoint for real-time alert streaming with permission-based filtering.
    
    Endpoint: /ws/alerts?token=YOUR_JWT_TOKEN
    Protocol: WebSocket
    
    Authentication:
    - Pass JWT access token as 'token' query parameter
    - Token is validated on connect
    - User receives only alerts for devices they own
    
    Message format:
    {
        "id": <alert_id>,
        "device_id": <device_id>,  # User must own this device to receive alert
        "type": "<alert_type>",
        "severity": "<severity>",
        "description": "<description>",
        "created_at": "<ISO 8601 timestamp>"
    }
    
    Error responses:
    - 1008 (Policy Violation) if token is invalid or missing
    - 1002 (Protocol Error) for unexpected errors
    """
    user_id = None
    organization_id = None

    # Allow browser clients to pass ?token=... and non-browser clients to use Authorization: Bearer ...
    if not token:
        authorization = websocket.headers.get("authorization")
        if authorization and authorization.lower().startswith("bearer "):
            token = authorization.split(" ", 1)[1].strip()
    
    # Validate JWT token
    if token:
        try:
            payload = decode_token(token)
            if payload.get("type") != TokenType.ACCESS:
                await websocket.close(code=1008, reason="Invalid token type")
                logger.warning("WebSocket connection rejected: token is not an access token")
                return
            sub = payload.get("sub")
            if sub is None:
                await websocket.close(code=1008, reason="Token missing subject")
                logger.warning("WebSocket connection rejected: access token missing subject")
                return
            user_id = int(sub)
            org_id = payload.get("org_id")
            if org_id is None:
                await websocket.close(code=1008, reason="Token missing organization")
                logger.warning("WebSocket connection rejected: access token missing organization")
                return
            organization_id = org_id
            logger.info(f"WebSocket authenticated for user_id={user_id} organization_id={organization_id}")
        except ValueError as exc:
            await websocket.close(code=1008, reason="Invalid token")
            logger.warning(f"WebSocket connection rejected: {exc}")
            return
        except Exception as exc:
            await websocket.close(code=1002, reason="Token validation error")
            logger.error(f"WebSocket token validation error: {exc}")
            return
    else:
        await websocket.close(code=1008, reason="Missing access token")
        logger.warning("WebSocket connection rejected: missing access token")
        return

    logger.info(
        "WebSocket authenticated for user_id=%s organization_id=%s",
        user_id,
        organization_id,
    )
    
    await ws_manager.connect(websocket, organization_id=organization_id, user_id=user_id)
    try:
        # Keep connection alive and consume incoming frames.
        while True:
            await websocket.receive()
    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected (user_id={user_id})")
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error (user_id={user_id}): {e}")
        ws_manager.disconnect(websocket)
