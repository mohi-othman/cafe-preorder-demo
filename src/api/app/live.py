"""Live updates over WebSockets: the KDS listens per Café, the tracking page per Order.

Server-to-client, except the KDS's first message, which logs in: {"token": "<JWT>"} (never in the URL, so it
stays out of access logs). Once the socket is subscribed the server sends {"type": "ready"}; clients reload
current state over REST then, on every (re)connect. After that each message is
{"type": "order_created" | "status_changed", "order": <OrderOut>}.

The KDS socket closes with code 4401 (UNAUTHORIZED) on a bad login or when the token expires; the client
sends the Barista back to the login form instead of reconnecting.
"""

import asyncio
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, WebSocket, WebSocketDisconnect, status
from sqlmodel import Session, select
from starlette.concurrency import run_in_threadpool

from app.auth import BARISTA, Claims, InvalidToken, _secret, decode_token
from app.broadcaster import broadcaster, cafe_channel, order_channel
from app.db import engine
from app.models import Cafe, Order

ORDER_CREATED = "order_created"
STATUS_CHANGED = "status_changed"
READY = {"type": "ready"}
UNAUTHORIZED = 4401  # close code: log in again
LOGIN_TIMEOUT_S = 10  # how long the KDS socket waits for its login message

router = APIRouter(prefix="/api/ws")


def publish_after_response(tasks: BackgroundTasks, event: str, cafe_id: int, order) -> None:
    """Queue the event to go out after the response, so it always follows the DB commit.

    `order` is the OrderOut the REST endpoints return, so clients get the same shape.
    """
    message = {"type": event, "order": order.model_dump(mode="json")}
    tasks.add_task(broadcaster.publish, [cafe_channel(cafe_id), order_channel(order.id)], message)


async def _listen(websocket: WebSocket, channel: str, until: datetime | None = None) -> None:
    """Subscribe an accepted socket to `channel` until it disconnects or `until` passes."""
    broadcaster.subscribe(channel, websocket)
    try:
        await websocket.send_json(READY)
        timeout = None if until is None else max(0.0, (until - datetime.now(timezone.utc)).total_seconds())
        try:
            await asyncio.wait_for(_drain(websocket), timeout)
        except TimeoutError:
            await websocket.close(code=UNAUTHORIZED)
    except WebSocketDisconnect:
        pass
    finally:
        broadcaster.unsubscribe(channel, websocket)


async def _drain(websocket: WebSocket) -> None:
    while True:
        await websocket.receive_text()  # ignore client messages; wait for the disconnect


def _barista_claims(token: str) -> Claims | None:
    try:
        claims = decode_token(token, _secret(), now=datetime.now(timezone.utc))
    except InvalidToken:
        return None
    if claims.role != BARISTA or claims.cafe_id is None:
        return None
    with Session(engine) as session:
        return claims if session.get(Cafe, claims.cafe_id) else None


def _order_exists(public_id: UUID) -> bool:
    with Session(engine) as session:
        return session.exec(select(Order.id).where(Order.public_id == public_id)).first() is not None


async def _login_message(websocket: WebSocket) -> str:
    try:
        message = await asyncio.wait_for(websocket.receive_json(), LOGIN_TIMEOUT_S)
    except (TimeoutError, ValueError):
        return ""
    token = message.get("token") if isinstance(message, dict) else None
    return token if isinstance(token, str) else ""


@router.websocket("/kds")
async def kds_socket(websocket: WebSocket):
    await websocket.accept()
    try:
        claims = await run_in_threadpool(_barista_claims, await _login_message(websocket))
    except WebSocketDisconnect:
        return
    if claims is None:
        await websocket.close(code=UNAUTHORIZED)
        return
    await _listen(websocket, cafe_channel(claims.cafe_id), until=claims.expires_at)


@router.websocket("/orders/{public_id}")
async def order_socket(websocket: WebSocket, public_id: UUID):
    if not await run_in_threadpool(_order_exists, public_id):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    await websocket.accept()
    await _listen(websocket, order_channel(public_id))
