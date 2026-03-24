from collections import defaultdict
from typing import Any, DefaultDict

from fastapi import WebSocket
from loguru import logger


class NotificationsWebSocketManager:
    """Simple connection manager for notification websockets."""

    def __init__(self) -> None:
        self._connections: DefaultDict[int, set[WebSocket]] = defaultdict(set)

    async def connect(self, user_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[user_id].add(websocket)
        logger.debug("WebSocket connected for user_id={}", user_id)

    def disconnect(self, user_id: int, websocket: WebSocket) -> None:
        connections = self._connections.get(user_id)
        if connections and websocket in connections:
            connections.remove(websocket)
            logger.debug("WebSocket disconnected for user_id={}", user_id)
        if connections and len(connections) == 0:
            self._connections.pop(user_id, None)

    async def send_to_user(self, user_id: int, payload: Any) -> None:
        """Send payload to all active sockets for the user."""
        if user_id not in self._connections:
            return

        dead_connections: list[WebSocket] = []
        for ws in list(self._connections[user_id]):
            try:
                await ws.send_json(payload)
            except Exception as exc:  # noqa: BLE001
                logger.warning("WebSocket send failed for user_id={}: {}", user_id, exc)
                dead_connections.append(ws)

        for ws in dead_connections:
            self.disconnect(user_id, ws)

    def has_connections(self, user_id: int) -> bool:
        return user_id in self._connections and len(self._connections[user_id]) > 0


notifications_ws_manager = NotificationsWebSocketManager()
