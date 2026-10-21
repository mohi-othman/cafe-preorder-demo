import pytest
from starlette.websockets import WebSocketDisconnect

from tests.test_kds_api import _advance, _board, _login, _order, cafes  # noqa: F401  (fixture)


def _token(client, username):
    return _login(client, username)["Authorization"].removeprefix("Bearer ")


def _kds_socket(client, username):
    return client.websocket_connect(f"/api/ws/kds?token={_token(client, username)}")


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
    with client.websocket_connect(f"/api/ws/orders/{order['id']}") as tracking, \
            _kds_socket(client, "barista-demo-roasters") as kds:
        assert _advance(client, headers, order["id"], "pending").status_code == 200

        for socket in (tracking, kds):
            message = socket.receive_json()
            assert message["type"] == "status_changed"
            assert message["order"]["id"] == order["id"]
            assert message["order"]["status"] == "preparing"
            assert message["order"] == client.get(f"/api/orders/{order['id']}").json()


def test_the_tracking_page_hears_its_own_order_being_paid(client, cafes):
    order = _order(client, cafes, pay=False)
    with client.websocket_connect(f"/api/ws/orders/{order['id']}") as tracking:
        client.post(f"/api/orders/{order['id']}/pay", json={"method": "mada"})

        message = tracking.receive_json()
        assert message["type"] == "order_created"
        assert message["order"]["status"] == "pending"


@pytest.mark.parametrize("token", ["", "junk", "admin"])
def test_the_kds_socket_needs_a_barista_login(client, cafes, token):
    if token == "admin":
        token = _token(client, "admin")
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(f"/api/ws/kds?token={token}") as ws:
            ws.receive_json()


def test_an_unknown_order_has_no_tracking_socket(client, cafes):
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/api/ws/orders/00000000-0000-0000-0000-000000000000") as ws:
            ws.receive_json()
