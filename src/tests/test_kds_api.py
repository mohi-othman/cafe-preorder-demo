import pytest

from app.auth import hash_password
from app.models import Cafe, Category, Product, User


@pytest.fixture
def cafes(session):
    """Two Cafés with one Product each, a Barista for each, and the Super Admin."""
    ids = {}
    for slug in ("demo-roasters", "other"):
        cafe = Cafe(slug=slug, name_ar=slug, name_en=slug)
        session.add(cafe)
        session.commit()
        cat = Category(cafe_id=cafe.id, name_ar="مشروبات", name_en="Drinks")
        session.add(cat)
        session.commit()
        product = Product(cafe_id=cafe.id, category_id=cat.id, name_ar="كورتادو", name_en="Cortado", price=1500)
        session.add(product)
        session.add(User(username=f"barista-{slug}", password_hash=hash_password("pw"), role="barista", cafe_id=cafe.id))
        session.commit()
        ids[slug] = product.id
    session.add(User(username="admin", password_hash=hash_password("pw"), role="admin"))
    session.commit()
    return ids


def _login(client, username):
    res = client.post("/api/auth/login", json={"username": username, "password": "pw"})
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def _order(client, cafes, slug="demo-roasters", pay=True, name="Sara"):
    body = {
        "customer_name": name, "pickup_type": "car", "car_model": "Camry", "car_color": "White", "car_plate": "1234 ABJ",
        "lines": [{"product_id": cafes[slug], "qty": 2, "note": "oat milk"}],
    }
    order = client.post(f"/api/cafes/{slug}/orders", json=body).json()
    if pay:
        order = client.post(f"/api/orders/{order['id']}/pay", json={"method": "mada"}).json()
    return order


def _board(client, headers):
    res = client.get("/api/kds/orders", headers=headers)
    assert res.status_code == 200
    return res.json()


def _advance(client, headers, order_id, from_status):
    return client.post(f"/api/kds/orders/{order_id}/advance", json={"from_status": from_status}, headers=headers)


def test_full_status_run_from_pending_to_completed(client, cafes):
    headers = _login(client, "barista-demo-roasters")
    order = _order(client, cafes)

    board = _board(client, headers)
    assert board["cafe"]["slug"] == "demo-roasters"
    assert [(o["id"], o["status"]) for o in board["orders"]] == [(order["id"], "pending")]
    card = board["orders"][0]
    assert card["order_number"] == 1
    assert card["car_plate"] == "1234 ABJ"
    assert card["lines"][0]["note"] == "oat milk"

    for current, after in (("pending", "preparing"), ("preparing", "ready"), ("ready", "completed")):
        res = _advance(client, headers, order["id"], current)
        assert res.status_code == 200
        assert res.json()["status"] == after
        assert client.get(f"/api/orders/{order['id']}").json()["status"] == after  # the Customer sees it too

    assert _board(client, headers)["orders"] == []  # completed Orders leave the board


def test_a_repeated_tap_does_not_skip_a_status(client, cafes):
    headers = _login(client, "barista-demo-roasters")
    order = _order(client, cafes)
    assert _advance(client, headers, order["id"], "pending").status_code == 200

    again = _advance(client, headers, order["id"], "pending")  # second tablet, stale board

    assert again.status_code == 409
    assert client.get(f"/api/orders/{order['id']}").json()["status"] == "preparing"


def test_completed_and_unpaid_orders_cannot_be_moved(client, cafes):
    headers = _login(client, "barista-demo-roasters")
    unpaid = _order(client, cafes, pay=False)
    done = _order(client, cafes)
    for step in ("pending", "preparing", "ready"):
        _advance(client, headers, done["id"], step)

    assert _advance(client, headers, unpaid["id"], "awaiting_payment").status_code == 409
    assert _advance(client, headers, done["id"], "completed").status_code == 409
    assert client.get(f"/api/orders/{unpaid['id']}").json()["status"] == "awaiting_payment"


def test_the_board_shows_only_paid_orders_of_the_baristas_cafe_oldest_first(client, cafes):
    first = _order(client, cafes, name="First")
    _order(client, cafes, pay=False, name="Unpaid")
    _order(client, cafes, slug="other", name="Other café")
    second = _order(client, cafes, name="Second")

    board = _board(client, _login(client, "barista-demo-roasters"))

    assert [o["id"] for o in board["orders"]] == [first["id"], second["id"]]


def test_a_barista_cannot_move_another_cafes_order(client, cafes):
    foreign = _order(client, cafes, slug="other")

    res = _advance(client, _login(client, "barista-demo-roasters"), foreign["id"], "pending")

    assert res.status_code == 404
    assert client.get(f"/api/orders/{foreign['id']}").json()["status"] == "pending"


def test_the_kds_needs_a_barista_login(client, cafes):
    order = _order(client, cafes)

    assert client.get("/api/kds/orders").status_code == 401
    assert client.get("/api/kds/orders", headers={"Authorization": "Bearer junk"}).status_code == 401
    assert client.get("/api/kds/orders", headers=_login(client, "admin")).status_code == 403
    assert client.post(f"/api/kds/orders/{order['id']}/advance", json={"from_status": "pending"}).status_code == 401
