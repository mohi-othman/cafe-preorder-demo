import pytest

from app.models import Cafe, Category, Product


@pytest.fixture
def menu(session):
    """Demo café with Cortado 15.00, Cheesecake 26.00 and an unavailable Cold brew; plus another café's Product."""
    cafe = Cafe(slug="demo-roasters", name_ar="محمصة التجربة", name_en="Demo Roasters")
    other = Cafe(slug="other", name_ar="آخر", name_en="Other")
    session.add_all([cafe, other])
    session.commit()
    cat = Category(cafe_id=cafe.id, name_ar="مشروبات", name_en="Drinks")
    other_cat = Category(cafe_id=other.id, name_ar="مشروبات", name_en="Drinks")
    session.add_all([cat, other_cat])
    session.commit()
    products = {
        "cortado": Product(cafe_id=cafe.id, category_id=cat.id, name_ar="كورتادو", name_en="Cortado", price=1500),
        "cheesecake": Product(cafe_id=cafe.id, category_id=cat.id, name_ar="تشيز كيك", name_en="Cheesecake", price=2600),
        "cold_brew": Product(cafe_id=cafe.id, category_id=cat.id, name_ar="كولد برو", name_en="Cold brew",
                             price=2000, available=False),
        "foreign": Product(cafe_id=other.id, category_id=other_cat.id, name_ar="لاتيه", name_en="Latte", price=1000),
    }
    session.add_all(products.values())
    session.commit()
    return {k: p.id for k, p in products.items()}


def _table_order(menu, **overrides):
    body = {
        "customer_name": "Sara",
        "phone": "0500000000",
        "pickup_type": "table",
        "table_number": "7",
        "lines": [
            {"product_id": menu["cortado"], "qty": 2, "note": "oat milk"},
            {"product_id": menu["cheesecake"], "qty": 1},
        ],
    }
    return body | overrides


def test_full_checkout_create_fail_retry_pay_and_track(client, menu):
    created = client.post("/api/cafes/demo-roasters/orders", json=_table_order(menu))
    assert created.status_code == 201
    order = created.json()
    assert order["status"] == "awaiting_payment"
    assert order["order_number"] is None
    assert order["total"] == 5600  # 2 x 1500 + 2600
    uuid = order["id"]

    failed = client.post(f"/api/orders/{uuid}/pay", json={"method": "mada", "source": "fail"})
    assert failed.status_code == 402
    assert client.get(f"/api/orders/{uuid}").json()["status"] == "awaiting_payment"

    paid = client.post(f"/api/orders/{uuid}/pay", json={"method": "apple_pay", "source": "ok"})
    assert paid.status_code == 200
    assert paid.json()["status"] == "pending"

    tracked = client.get(f"/api/orders/{uuid}").json()
    assert tracked["status"] == "pending"
    assert tracked["order_number"] == 1
    assert tracked["cafe"]["slug"] == "demo-roasters"
    assert tracked["customer_name"] == "Sara"
    assert tracked["table_number"] == "7"
    assert [(line["name_en"], line["qty"], line["unit_price"], line["note"]) for line in tracked["lines"]] == [
        ("Cortado", 2, 1500, "oat milk"),
        ("Cheesecake", 1, 2600, None),
    ]


def test_second_paid_order_of_the_day_gets_number_two(client, menu):
    numbers = []
    for _ in range(2):
        uuid = client.post("/api/cafes/demo-roasters/orders", json=_table_order(menu)).json()["id"]
        numbers.append(client.post(f"/api/orders/{uuid}/pay", json={"method": "mada", "source": "ok"}).json()["order_number"])

    assert numbers == [1, 2]


def test_a_paid_order_cannot_be_paid_again(client, menu):
    uuid = client.post("/api/cafes/demo-roasters/orders", json=_table_order(menu)).json()["id"]
    client.post(f"/api/orders/{uuid}/pay", json={"method": "mada", "source": "ok"})

    again = client.post(f"/api/orders/{uuid}/pay", json={"method": "mada", "source": "ok"})

    assert again.status_code == 409


def test_car_pickup_order(client, menu):
    body = _table_order(menu, pickup_type="car", table_number=None,
                        car_model="Camry", car_color="White", car_plate="ABC 123")

    res = client.post("/api/cafes/demo-roasters/orders", json=body)

    assert res.status_code == 201
    assert (res.json()["car_model"], res.json()["car_color"], res.json()["car_plate"]) == ("Camry", "White", "ABC 123")


@pytest.mark.parametrize("missing", ["car_model", "car_color", "car_plate"])
def test_car_pickup_needs_model_color_and_plate(client, menu, missing):
    body = _table_order(menu, pickup_type="car", table_number=None,
                        car_model="Camry", car_color="White", car_plate="ABC 123")
    body[missing] = " "

    assert client.post("/api/cafes/demo-roasters/orders", json=body).status_code == 422


def test_table_pickup_needs_a_number(client, menu):
    res = client.post("/api/cafes/demo-roasters/orders", json=_table_order(menu, table_number=""))

    assert res.status_code == 422


def test_name_is_required(client, menu):
    res = client.post("/api/cafes/demo-roasters/orders", json=_table_order(menu, customer_name="  "))

    assert res.status_code == 422


@pytest.mark.parametrize("bad_line", [
    {"product_id": "cold_brew", "qty": 1},  # unavailable
    {"product_id": "foreign", "qty": 1},  # another café's Product
    {"product_id": "cortado", "qty": 0},
])
def test_rejects_bad_lines(client, menu, bad_line):
    line = bad_line | {"product_id": menu[bad_line["product_id"]]}

    res = client.post("/api/cafes/demo-roasters/orders", json=_table_order(menu, lines=[line]))

    assert res.status_code == 422


def test_rejects_an_empty_cart(client, menu):
    assert client.post("/api/cafes/demo-roasters/orders", json=_table_order(menu, lines=[])).status_code == 422


def test_total_ignores_a_price_sent_by_the_client(client, menu):
    lines = [{"product_id": menu["cortado"], "qty": 1, "unit_price": 1}]

    res = client.post("/api/cafes/demo-roasters/orders", json=_table_order(menu, lines=lines, total=1))

    assert res.json()["total"] == 1500


def test_unknown_order_is_404(client, menu):
    assert client.get("/api/orders/00000000-0000-0000-0000-000000000000").status_code == 404
