"""Live updates over WebSockets: the KDS listens per Café, the tracking page per Order.

Server-to-client only. Each message is {"type": "order_created" | "status_changed", "order": <OrderOut>}.
Clients reload current state over REST when they (re)connect.
"""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, WebSocket, WebSocketDisconnect, status
from sqlmodel import Session, select
from starlette.concurrency import run_in_threadpool

from app.auth import BARISTA, InvalidToken, _secret, decode_token
from app.broadcaster import broadcaster, cafe_channel, order_channel
from app.db import engine
from app.models import Cafe, Order

ORDER_CREATED = "order_created"
STATUS_CHANGED = "status_changed"

router = APIRouter(prefix="/api/ws")


def publish_after_response(tasks: BackgroundTasks, event: str, cafe_id: int, order) -> None:
    """Queue the event to go out after the response, so it always follows the DB commit.

    `order` is the OrderOut the REST endpoints return, so clients get the same shape.
    """
    message = {"type": event, "order": order.model_dump(mode="json")}
    tasks.add_task(broadcaster.publish, [cafe_channel(cafe_id), order_channel(order.id)], message)


async def _listen(websocket: WebSocket, channel: str) -> None:
    broadcaster.subscribe(channel, websocket)  # before accept, so nothing is missed once the client is open
    try:
        await websocket.accept()
        while True:
            await websocket.receive_text()  # ignore client messages; wait for the disconnect
    except WebSocketDisconnect:
        pass
    finally:
        broadcaster.unsubscribe(channel, websocket)


def _barista_cafe_id(token: str) -> int | None:
    try:
        claims = decode_token(token, _secret(), now=datetime.now(timezone.utc))
    except InvalidToken:
        return None
    if claims.role != BARISTA or claims.cafe_id is None:
        return None
    with Session(engine) as session:
        return claims.cafe_id if session.get(Cafe, claims.cafe_id) else None


def _order_exists(public_id: UUID) -> bool:
    with Session(engine) as session:
        return session.exec(select(Order.id).where(Order.public_id == public_id)).first() is not None


@router.websocket("/kds")
async def kds_socket(websocket: WebSocket, token: str = ""):
    cafe_id = await run_in_threadpool(_barista_cafe_id, token)
    if cafe_id is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    await _listen(websocket, cafe_channel(cafe_id))


@router.websocket("/orders/{public_id}")
async def order_socket(websocket: WebSocket, public_id: UUID):
    if not await run_in_threadpool(_order_exists, public_id):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    await _listen(websocket, order_channel(public_id))
