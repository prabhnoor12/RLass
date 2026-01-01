from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any
from ..database import get_db
from ..services.usage_dashboard_service import get_realtime_usage_stats

router = APIRouter()

active_connections: Dict[str, WebSocket] = {}

@router.websocket("/ws/usage-dashboard/{user_id}")
async def websocket_usage_dashboard(websocket: WebSocket, user_id: str, db: Session = Depends(get_db)):
    await websocket.accept()
    active_connections[user_id] = websocket
    try:
        while True:
            stats = get_realtime_usage_stats(db, user_id)
            await websocket.send_json(stats)
            await asyncio.sleep(2)  # Send updates every 2 seconds
    except WebSocketDisconnect:
        del active_connections[user_id]
