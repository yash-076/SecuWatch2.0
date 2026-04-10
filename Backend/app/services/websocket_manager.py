import asyncio
import logging
from typing import Set

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Manager for WebSocket connections and alert broadcasting.
    
    Responsibilities:
    - Store active client connections
    - Add/remove connections on event
    - Broadcast alerts to all connected clients
    
    Thread-safe for concurrent connections.
    """

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self._event_loop: asyncio.AbstractEventLoop | None = None

    def set_event_loop(self, event_loop: asyncio.AbstractEventLoop) -> None:
        """
        Store the main application event loop for thread-safe scheduling.

        Args:
            event_loop: Running FastAPI event loop
        """
        self._event_loop = event_loop

    async def connect(self, websocket: WebSocket) -> None:
        """
        Accept a client WebSocket connection and register it.
        
        Args:
            websocket: The WebSocket connection to register
        """
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"Client connected. Active connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        """
        Remove a disconnected client from active connections.
        
        Args:
            websocket: The WebSocket connection to remove
        """
        self.active_connections.discard(websocket)
        logger.info(f"Client disconnected. Active connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict) -> None:
        """
        Broadcast a message to all connected clients.
        
        Removes dead connections gracefully if sending fails.
        
        Args:
            message: Dictionary to broadcast as JSON
        """
        if not self.active_connections:
            logger.debug("No active connections to broadcast to")
            return

        dead_connections = []

        # Snapshot the connection set in case it changes during broadcast.
        for websocket in list(self.active_connections):
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to broadcast to client: {e}")
                dead_connections.append(websocket)

        # Clean up dead connections
        for websocket in dead_connections:
            self.disconnect(websocket)

    def broadcast_sync(self, message: dict) -> None:
        """
        Broadcast a message from synchronous context (non-blocking).
        
        Schedules the async broadcast as a background task if event loop exists.
        This allows synchronous code to trigger broadcasts without blocking.
        
        Args:
            message: Dictionary to broadcast as JSON
        """
        if self._event_loop is None:
            logger.warning("Cannot broadcast: WebSocket event loop is not configured")
            return

        if self._event_loop.is_closed():
            logger.warning("Cannot broadcast: WebSocket event loop is closed")
            return

        # Schedule broadcast from sync/threaded contexts without blocking.
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
