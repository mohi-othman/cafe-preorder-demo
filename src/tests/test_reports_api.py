"""Daily report: paid Orders of one Café on one Asia/Riyadh day (by paid_at). Riyadh is UTC+3, no DST.

Day 2026-10-20 in Riyadh runs from 2026-10-19 21:00 UTC to 2026-10-20 21:00 UTC.
"""

from datetime import datetime, timezone

import pytest

from app.auth import hash_password
from app.models import Cafe, Category, Order, OrderLine, Product, User
from app.ordering import cafe_day


def utc(*args):
    return datetime(*args, tzinfo=timezone.utc)


@pytest.fixture
def cafes(session):
    """Two Cafés with Products, a Barista and the Super Admin."""
    ids = {}
    for slug in ("demo-roasters", "other"):
        cafe = Cafe(slug=slug, name_ar=slug, name_en=slug)
        session.add(cafe)
        session.commit()
        cat = Category(cafe_id=cafe.id, name_ar="مشروبات", name_en="Drinks")
        session.add(cat)
        session.commit()
        ids[slug] = {"cafe": cafe.id}
        for key, name_ar, name_en, price in [
            ("cortado", "كورتادو", "Cortado", 1500), ("latte", "لاتيه", "Latte", 1800),
            ("mocha", "موكا", "Mocha", 2000), ("tea", "شاي", "Tea", 1006),
            ("juice", "عصير", "Juice", 1006), ("water", "ماء", "Water", 498),
        ]:
            p = Product(cafe_id=cafe.id, category_id=cat.id, name_ar=name_ar, name_en=name_en, price=price)
            session.add(p)
            session.commit()
            ids[slug][key] = p
    session.add(User(username="barista", password_hash=hash_password("pw"), role="barista", cafe_id=ids["demo-roasters"]["cafe"]))
    session.add(User(username="admin", password_hash=hash_password("pw"), role="admin"))
    session.commit()
    return ids


def _login(client, username):
    res = client.post("/api/auth/login", json={"username": username, "password": "pw"})
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


@pytest.fixture
def admin(client, cafes):
    return _login(client, "admin")


def _add_order(session, cafe_id, lines, paid_at, status="pending"):
    """lines: [(Product, qty)]. Snapshots the Product name and price like checkout does."""
    order = Order(cafe_id=cafe_id, status=status, customer_name="Sara", pickup_type="table", table_number="1",
                  total=sum(p.price * qty for p, qty in lines), paid_at=paid_at,
                  created_at=paid_at or utc(2026, 10, 20, 6, 0))
    session.add(order)
    session.commit()
    for p, qty in lines:
        session.add(OrderLine(order_id=order.id, product_id=p.id, name_ar=p.name_ar, name_en=p.name_en,
                              unit_price=p.price, qty=qty))
    session.commit()
    return order


@pytest.fixture
def day_orders(session, cafes):
    """Four paid Orders on Riyadh day 2026-10-20 at Demo Roasters, and five that must not count."""
    c = cafes["demo-roasters"]
    cid = c["cafe"]
    # counted: 3000 + 3300 + 6000 + 4310 = 16610 halalas
    _add_order(session, cid, [(c["cortado"], 2)], utc(2026, 10, 19, 21, 30))  # 00:30 Riyadh
    _add_order(session, cid, [(c["latte"], 1), (c["cortado"], 1)], utc(2026, 10, 20, 5, 10), "completed")  # 08:10
    _add_order(session, cid, [(c["mocha"], 3)], utc(2026, 10, 20, 5, 50), "preparing")  # 08:50
    _add_order(session, cid, [(c["latte"], 1), (c["tea"], 1), (c["juice"], 1), (c["water"], 1)],
               utc(2026, 10, 20, 20, 59, 59), "ready")  # 23:59:59
    # not counted
    _add_order(session, cid, [(c["water"], 10)], utc(2026, 10, 19, 20, 59, 59))  # 23:59:59 on the 19th
    _add_order(session, cid, [(c["water"], 10)], utc(2026, 10, 20, 21, 0))  # 00:00 on the 21st
    _add_order(session, cid, [(c["water"], 10)], None, "awaiting_payment")
    o = cafes["other"]
    _add_order(session, o["cafe"], [(o["water"], 10)], utc(2026, 10, 20, 6, 0))
    return cid


def _report(client, headers, cafe_id, day="2026-10-20"):
    url = f"/api/admin/cafes/{cafe_id}/reports/daily" + (f"?date={day}" if day else "")
    return client.get(url, headers=headers)


def test_counts_paid_orders_and_revenue_of_the_riyadh_day(client, admin, day_orders):
    res = _report(client, admin, day_orders)

    assert res.status_code == 200
    body = res.json()
    assert body["date"] == "2026-10-20"
    assert body["orders"] == 4
    assert body["revenue"] == 16610


def test_average_order_value_rounds_half_up_to_whole_halalas(client, admin, day_orders):
    # 16610 / 4 = 4152.5 -> 4153 (banker's rounding would give 4152)
    assert _report(client, admin, day_orders).json()["average_order_value"] == 4153


def test_top_five_products_by_quantity_then_revenue_then_name(client, admin, day_orders):
    top = _report(client, admin, day_orders).json()["top_products"]

    assert [(p["name_en"], p["qty"], p["revenue"]) for p in top] == [
        ("Mocha", 3, 6000),  # ties Cortado on qty, wins on revenue
        ("Cortado", 3, 4500),
        ("Latte", 2, 3600),
        ("Tea", 1, 1006),  # ties Juice on qty and revenue; شاي sorts before عصير
        ("Juice", 1, 1006),
    ]  # Water (1, 498) is sixth; its 10s on uncounted Orders are ignored
    assert top[0]["name_ar"] == "موكا"


def test_orders_per_riyadh_hour(client, admin, day_orders):
    expected = [0] * 24
    expected[0] = 1  # 00:30
    expected[8] = 2  # 08:10, 08:50
    expected[23] = 1  # 23:59:59
    assert _report(client, admin, day_orders).json()["orders_per_hour"] == expected


def test_a_day_without_paid_orders_is_all_zero_with_no_average(client, admin, day_orders):
    body = _report(client, admin, day_orders, "2026-10-22").json()

    assert body == {
        "cafe_id": day_orders, "date": "2026-10-22", "orders": 0, "revenue": 0, "average_order_value": None,
        "top_products": [], "orders_per_hour": [0] * 24,
    }


def test_the_date_defaults_to_today_in_riyadh(client, admin, session, cafes):
    c = cafes["demo-roasters"]
    now = datetime.now(timezone.utc)
    _add_order(session, c["cafe"], [(c["latte"], 1)], now)

    body = _report(client, admin, c["cafe"], day=None).json()

    assert body["date"] == cafe_day(now).isoformat()
    assert (body["orders"], body["revenue"]) == (1, 1800)


# ---------- access and input ----------

def test_the_report_needs_a_login(client, day_orders):
    assert _report(client, {}, day_orders).status_code == 401


def test_a_barista_cannot_see_reports_even_for_their_own_cafe(client, day_orders):
    assert _report(client, _login(client, "barista"), day_orders).status_code == 403


def test_an_unknown_cafe_is_404(client, admin):
    assert _report(client, admin, 999999).status_code == 404


def test_a_malformed_date_is_422(client, admin, day_orders):
    assert _report(client, admin, day_orders, "20-10-2026").status_code == 422
