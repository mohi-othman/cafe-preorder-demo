from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

import pytest
from sqlmodel import select
from starlette.websockets import WebSocketDisconnect

from app.auth import TOKEN_LIFETIME, create_token
from app.live import UNAUTHORIZED
from app.config import settings
from app.models import User
from tests.test_kds_api import _advance, _board, _login, _order, cafes  # noqa: F401  (fixture)


def _token(client, username):
    return _login(client, username)["Authorization"].removeprefix("Bearer ")


@contextmanager
def _kds_socket_with(client, token):
    """Open the KDS socket, log in with the first message and wait until the server is listening."""
    with client.websocket_connect("/api/ws/kds") as ws:
        ws.send_json({"token": token})
        assert ws.receive_json() == {"type": "ready"}
        yield ws


def _kds_socket(client, username):
    return _kds_socket_with(client, _token(client, username))


@contextmanager
def _tracking_socket(client, order_id):
    with client.websocket_connect(f"/api/ws/orders/{order_id}") as ws:
        assert ws.receive_json() == {"type": "ready"}
        yield ws


def _close_code(client, token) -> int:
    with client.websocket_connect("/api/ws/kds") as ws:
        ws.send_json({"token": token})
        with pytest.raises(WebSocketDisconnect) as e:
            ws.receive_json()
    return e.value.code


def test_a_paid_order_reaches_its_cafes_kds_and_not_another_cafes(client, cafes):
    with _kds_socket(client, "barista-demo-roasters") as kds, _kds_socket(client, "barista-other") as other_kds:
        _order(client, cafes, pay=False)  # unpaid: not on the KDS yet
        paid = _order(client, cafes, name="Sara")
        other = _order(client, cafes, slug="other", name="Other café")

        message = kds.receive_json()
        assert message["type"] == "order_created"
        assert message["order"]["id"] == paid["id"]
        assert message["order"] == _board(client, _login(client, "barista-demo-roasters"))["orders"][0]
        # The other Café's first message is its own Order: it never saw Sara's.
        assert other_kds.receive_json()["order"]["id"] == other["id"]


def test_a_status_change_reaches_the_tracking_page_and_the_kds(client, cafes):
    headers = _login(client, "barista-demo-roasters")
    order = _order(client, cafes)
    with _tracking_socket(client, order["id"]) as tracking, _kds_socket(client, "barista-demo-roasters") as kds:
        assert _advance(client, headers, order["id"], "pending").status_code == 200

        for socket in (tracking, kds):
            message = socket.receive_json()
            assert message["type"] == "status_changed"
            assert message["order"]["id"] == order["id"]
            assert message["order"]["status"] == "preparing"
            assert message["order"] == client.get(f"/api/orders/{order['id']}").json()


def test_the_tracking_page_hears_its_own_order_being_paid(client, cafes):
    order = _order(client, cafes, pay=False)
    with _tracking_socket(client, order["id"]) as tracking:
        client.post(f"/api/orders/{order['id']}/pay", json={"method": "mada"})

        message = tracking.receive_json()
        assert message["type"] == "order_created"
        assert message["order"]["status"] == "pending"


@pytest.mark.parametrize("token", ["", "junk", "admin", "expired"])
def test_the_kds_socket_needs_a_barista_login(client, cafes, token):
    if token == "admin":
        token = _token(client, "admin")
    if token == "expired":
        token = create_token(1, "barista", 1, settings.jwt_secret, now=datetime.now(timezone.utc) - TOKEN_LIFETIME * 2)

    assert _close_code(client, token) == UNAUTHORIZED


def test_the_kds_socket_needs_the_token_in_a_message_not_the_url(client, cafes):
    token = _token(client, "barista-demo-roasters")
    with client.websocket_connect(f"/api/ws/kds?token={token}") as ws:
        ws.send_json({"hello": "there"})
        with pytest.raises(WebSocketDisconnect) as e:
            ws.receive_json()

    assert e.value.code == UNAUTHORIZED


def test_the_kds_socket_closes_when_the_token_expires(client, cafes, session):
    barista = session.exec(select(User).where(User.username == "barista-demo-roasters")).one()
    # A token issued almost a full lifetime ago: one second left.
    issued = datetime.now(timezone.utc) - TOKEN_LIFETIME + timedelta(seconds=1)
    token = create_token(barista.id, "barista", barista.cafe_id, settings.jwt_secret, now=issued)

    with _kds_socket_with(client, token) as ws:
        with pytest.raises(WebSocketDisconnect) as e:
            ws.receive_json()

    assert e.value.code == UNAUTHORIZED


def test_an_unknown_order_has_no_tracking_socket(client, cafes):
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/api/ws/orders/00000000-0000-0000-0000-000000000000") as ws:
            ws.receive_json()
