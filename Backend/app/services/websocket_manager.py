import asyncio
import json
import logging
import threading
from typing import Dict, Optional, Set

from fastapi import WebSocket

from app.config import settings
from app.utils.redis_client import get_redis_client

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Manager for WebSocket connections and organization-scoped alert broadcasting.
    
    Responsibilities:
    - Store active client connections with organization context
    - Broadcast alerts only to sockets in the same organization
    - Add/remove connections on event
    
    Thread-safe for concurrent connections.
    """

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self._connection_to_user: Dict[WebSocket, int] = {}  # Maps WebSocket → user_id
        self._connection_to_organization: Dict[WebSocket, int] = {}  # Maps WebSocket → organization_id
        self._event_loop: asyncio.AbstractEventLoop | None = None
        self._redis_relay_stop = threading.Event()
        self._redis_relay_thread: threading.Thread | None = None

    def set_event_loop(self, event_loop: asyncio.AbstractEventLoop) -> None:
        """
        Store the main application event loop for thread-safe scheduling.

        Args:
            event_loop: Running FastAPI event loop
        """
        self._event_loop = event_loop

    def start_redis_relay(self) -> None:
        """Start a background thread that relays Redis broadcasts to connected clients."""
        if self._redis_relay_thread and self._redis_relay_thread.is_alive():
            return

        self._redis_relay_stop.clear()
        self._redis_relay_thread = threading.Thread(
            target=self._redis_relay_loop,
            name="websocket-redis-relay",
            daemon=True,
        )
        self._redis_relay_thread.start()

    def stop_redis_relay(self) -> None:
        """Stop the Redis relay thread during shutdown."""
        self._redis_relay_stop.set()
        thread = self._redis_relay_thread
        if thread and thread.is_alive():
            thread.join(timeout=2)

    def _redis_relay_loop(self) -> None:
        """Listen for Redis broadcasts and forward them onto the app event loop."""
        try:
            redis_client = get_redis_client()
            pubsub = redis_client.pubsub()
            pubsub.subscribe(settings.websocket_broadcast_channel)
        except Exception as exc:
            logger.warning("WebSocket Redis relay could not start: %s", exc)
            return

        logger.info(
            "WebSocket Redis relay started on channel '%s'",
            settings.websocket_broadcast_channel,
        )

        try:
            while not self._redis_relay_stop.is_set():
                try:
                    message = pubsub.get_message(timeout=1.0)
                except Exception as exc:
                    logger.warning("WebSocket Redis relay read failed: %s", exc)
                    continue

                if not message or message.get("type") != "message":
                    continue

                raw_payload = message.get("data")
                if raw_payload is None:
                    continue

                try:
                    payload = json.loads(raw_payload)
                except Exception as exc:
                    logger.warning("WebSocket Redis relay received invalid payload: %s", exc)
                    continue

                if self._event_loop is None or self._event_loop.is_closed():
                    logger.debug("Skipping Redis relay delivery because the event loop is unavailable")
                    continue

                future = asyncio.run_coroutine_threadsafe(self.broadcast(payload), self._event_loop)
                future.add_done_callback(self._log_broadcast_error)
        finally:
            try:
                pubsub.close()
            except Exception:
                pass

    async def connect(
        self,
        websocket: WebSocket,
        organization_id: int,
        user_id: Optional[int] = None,
    ) -> None:
        """
        Accept a client WebSocket connection and register it with organization context.
        
        Args:
            websocket: The WebSocket connection to register
            organization_id: The authenticated user's organization ID
            user_id: The authenticated user ID (used for logging only)
        """
        await websocket.accept()
        self.active_connections.add(websocket)
        self._connection_to_organization[websocket] = organization_id
        if user_id is not None:
            self._connection_to_user[websocket] = user_id
        logger.info(
            f"Client connected. User: {user_id or 'anonymous'}, Organization: {organization_id}, Active connections: {len(self.active_connections)}"
        )

    def disconnect(self, websocket: WebSocket) -> None:
        """
        Remove a disconnected client from active connections.
        
        Args:
            websocket: The WebSocket connection to remove
        """
        self.active_connections.discard(websocket)
        self._connection_to_user.pop(websocket, None)
        self._connection_to_organization.pop(websocket, None)
        logger.info(f"Client disconnected. Active connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict) -> None:
        """
        Broadcast a message to all connected clients in the same organization.

        The payload must include `organization_id` so the relay can target the
        correct tenant without doing per-user ownership checks.
        
        Args:
            message: Dictionary to broadcast as JSON. Must include 'organization_id'.
        """
        if not self.active_connections:
            logger.debug("No active connections to broadcast to")
            return

        organization_id = message.get("organization_id")
        if organization_id is None:
            logger.warning("Cannot broadcast alert: organization_id is missing")
            return

        recipients = []
        for websocket in list(self.active_connections):
            connection_organization_id = self._connection_to_organization.get(websocket)
            if connection_organization_id == organization_id:
                recipients.append(websocket)
        
        if not recipients:
            logger.debug(f"No authorized recipients for organization {organization_id}")
            return
        
        # Optimization 2: Send to all recipients in parallel (not sequential)
        async def send_to_recipient(ws: WebSocket) -> tuple[WebSocket, bool]:
            try:
                await ws.send_json(message)
                return (ws, True)
            except Exception as e:
                logger.warning(f"Failed to broadcast to client: {e}")
                return (ws, False)
        
        # Gather all sends concurrently
        results = await asyncio.gather(
            *[send_to_recipient(ws) for ws in recipients],
            return_exceptions=False
        )
        
        # Clean up dead connections
        for ws, success in results:
            if not success:
                self.disconnect(ws)

    def broadcast_sync(self, message: dict) -> None:
        """
        Broadcast a message from synchronous context (non-blocking).
        
        Publishes to Redis so any running API process can relay the message to
        connected WebSocket clients. Falls back to the local event loop when
        Redis is unavailable.
        
        Args:
            message: Dictionary to broadcast as JSON
        """
        try:
            redis_client = get_redis_client()
            redis_client.publish(settings.websocket_broadcast_channel, json.dumps(message, default=str))
            return
        except Exception as exc:
            logger.debug("Redis broadcast publish failed, falling back to local event loop: %s", exc)

        if self._event_loop is None:
            logger.warning("Cannot broadcast: WebSocket event loop is not configured")
            return

        if self._event_loop.is_closed():
            logger.warning("Cannot broadcast: WebSocket event loop is closed")
            return

        future = asyncio.run_coroutine_threadsafe(self.broadcast(message), self._event_loop)
        future.add_done_callback(self._log_broadcast_error)

    @staticmethod
    def _log_broadcast_error(future) -> None:
        """Log uncaught exceptions from background broadcast tasks."""
        try:
            future.result()
        except Exception as e:
            logger.warning(f"Background broadcast failed: {e}")

    def get_connection_count(self) -> int:
        """Get the current number of active connections."""
        return len(self.active_connections)


# Global instance for use across the application
ws_manager = WebSocketManager()
