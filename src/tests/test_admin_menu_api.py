import pytest

from app.auth import hash_password
from app.models import Cafe, Category, Product, User


@pytest.fixture
def cafes(session):
    """Two Cafés with one Category and Product each, a Barista, and the Super Admin."""
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
        session.commit()
        ids[slug] = {"cafe": cafe.id, "category": cat.id, "product": product.id}
    session.add(User(username="barista", password_hash=hash_password("pw"), role="barista", cafe_id=ids["demo-roasters"]["cafe"]))
    session.add(User(username="admin", password_hash=hash_password("pw"), role="admin"))
    session.commit()
    return ids


def _login(client, username):
    res = client.post("/api/auth/login", json={"username": username, "password": "pw"})
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


@pytest.fixture
def admin(client):
    return _login(client, "admin")


def _base(cafes, slug="demo-roasters"):
    return f"/api/admin/cafes/{cafes[slug]['cafe']}"


def _public_menu(client, slug="demo-roasters"):
    res = client.get(f"/api/cafes/{slug}/menu")
    assert res.status_code == 200
    return res.json()


def _public_products(client, slug="demo-roasters"):
    return {p["name_en"]: p for c in _public_menu(client, slug)["categories"] for p in c["products"]}


NEW_PRODUCT = {
    "name_ar": "موكا", "name_en": "Mocha", "description_ar": "شوكولاتة", "description_en": "Chocolate",
    "price_sar": "18.50", "available": True, "image_url": "/menu/mocha.svg",
}


# ---------- role checks ----------

ADMIN_ROUTES = [
    ("get", "/api/admin/cafes"),
    ("get", "{base}/menu"),
    ("post", "{base}/categories"),
    ("patch", "{base}/categories/{category}"),
    ("delete", "{base}/categories/{category}"),
    ("post", "{base}/products"),
    ("patch", "{base}/products/{product}"),
    ("delete", "{base}/products/{product}"),
]


def _url(template, cafes):
    ids = cafes["demo-roasters"]
    return template.format(base=_base(cafes), category=ids["category"], product=ids["product"])


@pytest.mark.parametrize("method, template", ADMIN_ROUTES)
def test_admin_routes_need_a_login(client, cafes, method, template):
    assert getattr(client, method)(_url(template, cafes)).status_code == 401


@pytest.mark.parametrize("method, template", ADMIN_ROUTES)
def test_a_barista_cannot_use_admin_routes(client, cafes, method, template):
    res = client.request(method.upper(), _url(template, cafes), headers=_login(client, "barista"), json={})
    assert res.status_code == 403
    assert "Cortado" in _public_products(client)  # nothing was deleted


def test_the_admin_lists_cafes(client, cafes, admin):
    res = client.get("/api/admin/cafes", headers=admin)

    assert res.status_code == 200
    assert [(c["id"], c["slug"]) for c in res.json()] == [
        (cafes["demo-roasters"]["cafe"], "demo-roasters"), (cafes["other"]["cafe"], "other")]


def test_an_unknown_cafe_is_404(client, cafes, admin):
    assert client.get("/api/admin/cafes/999999/menu", headers=admin).status_code == 404


# ---------- reading the Menu ----------

def test_the_admin_menu_includes_unavailable_products(client, cafes, admin, session):
    ids = cafes["demo-roasters"]
    session.add(Product(cafe_id=ids["cafe"], category_id=ids["category"], name_ar="كولد برو", name_en="Cold brew",
                        price=2000, available=False))
    session.commit()

    menu = client.get(f"{_base(cafes)}/menu", headers=admin).json()

    assert menu["cafe"]["slug"] == "demo-roasters"
    assert [(c["id"], c["name_en"]) for c in menu["categories"]] == [(ids["category"], "Drinks")]
    assert [(p["name_en"], p["available"], p["price"], p["price_sar"], p["category_id"]) for p in menu["products"]] == [
        ("Cortado", True, 1500, "15.00", ids["category"]),
        ("Cold brew", False, 2000, "20.00", ids["category"]),
    ]


def test_the_admin_menu_shows_only_that_cafes_menu(client, cafes, admin):
    menu = client.get(f"{_base(cafes, 'other')}/menu", headers=admin).json()

    assert [p["id"] for p in menu["products"]] == [cafes["other"]["product"]]


# ---------- Categories ----------

def test_create_rename_and_delete_a_category(client, cafes, admin):
    created = client.post(f"{_base(cafes)}/categories", headers=admin, json={"name_ar": "حلى", "name_en": "Desserts"})
    assert created.status_code == 201
    cat_id = created.json()["id"]
    assert "Desserts" in [c["name_en"] for c in _public_menu(client)["categories"]]

    renamed = client.patch(f"{_base(cafes)}/categories/{cat_id}", headers=admin, json={"name_en": "Sweets"})
    assert renamed.status_code == 200
    assert renamed.json()["name_ar"] == "حلى"  # untouched
    assert [c["name_en"] for c in _public_menu(client)["categories"]] == ["Drinks", "Sweets"]  # new ones go last

    assert client.delete(f"{_base(cafes)}/categories/{cat_id}", headers=admin).status_code == 204
    assert [c["name_en"] for c in _public_menu(client)["categories"]] == ["Drinks"]


def test_a_category_needs_an_arabic_name(client, cafes, admin):
    res = client.post(f"{_base(cafes)}/categories", headers=admin, json={"name_ar": "  ", "name_en": "Desserts"})
    assert res.status_code == 422


def test_a_category_with_products_cannot_be_deleted(client, cafes, admin):
    res = client.delete(f"{_base(cafes)}/categories/{cafes['demo-roasters']['category']}", headers=admin)

    assert res.status_code == 409
    assert "Cortado" in _public_products(client)


def test_another_cafes_category_is_404(client, cafes, admin):
    foreign = cafes["other"]["category"]
    assert client.patch(f"{_base(cafes)}/categories/{foreign}", headers=admin, json={"name_en": "x"}).status_code == 404
    assert client.delete(f"{_base(cafes)}/categories/{foreign}", headers=admin).status_code == 404


# ---------- Products ----------

def _create_product(client, cafes, admin, **changes):
    body = {**NEW_PRODUCT, "category_id": cafes["demo-roasters"]["category"], **changes}
    return client.post(f"{_base(cafes)}/products", headers=admin, json=body)


def test_a_new_product_shows_on_the_customer_menu_with_its_price_in_halalas(client, cafes, admin):
    res = _create_product(client, cafes, admin)

    assert res.status_code == 201
    assert (res.json()["price"], res.json()["price_sar"]) == (1850, "18.50")
    mocha = _public_products(client)["Mocha"]
    assert (mocha["name_ar"], mocha["description_en"], mocha["price"], mocha["image_url"]) == (
        "موكا", "Chocolate", 1850, "/menu/mocha.svg")
    assert list(_public_products(client)) == ["Cortado", "Mocha"]  # new ones go last


def test_edit_a_products_names_and_price(client, cafes, admin):
    product_id = cafes["demo-roasters"]["product"]

    res = client.patch(f"{_base(cafes)}/products/{product_id}", headers=admin,
                       json={"name_en": "Big cortado", "price_sar": "16.75", "description_ar": "مزدوج"})

    assert res.status_code == 200
    item = _public_products(client)["Big cortado"]
    assert (item["name_ar"], item["price"], item["description_ar"]) == ("كورتادو", 1675, "مزدوج")


def test_an_unavailable_product_is_hidden_from_the_customer_but_kept_for_the_admin(client, cafes, admin):
    product_id = cafes["demo-roasters"]["product"]

    off = client.patch(f"{_base(cafes)}/products/{product_id}", headers=admin, json={"available": False})

    assert off.status_code == 200
    assert "Cortado" not in _public_products(client)
    admin_menu = client.get(f"{_base(cafes)}/menu", headers=admin).json()
    assert [(p["id"], p["available"]) for p in admin_menu["products"]] == [(product_id, False)]

    client.patch(f"{_base(cafes)}/products/{product_id}", headers=admin, json={"available": True})
    assert "Cortado" in _public_products(client)


def test_a_product_can_move_to_another_category(client, cafes, admin):
    cat = client.post(f"{_base(cafes)}/categories", headers=admin, json={"name_ar": "حلى", "name_en": "Desserts"}).json()

    client.patch(f"{_base(cafes)}/products/{cafes['demo-roasters']['product']}", headers=admin,
                 json={"category_id": cat["id"]})

    by_category = {c["name_en"]: [p["name_en"] for p in c["products"]] for c in _public_menu(client)["categories"]}
    assert by_category == {"Drinks": [], "Desserts": ["Cortado"]}


def test_blank_optional_texts_are_stored_as_empty(client, cafes, admin):
    res = _create_product(client, cafes, admin, name_en="", description_ar=" ", description_en="", image_url="")

    assert res.status_code == 201
    body = res.json()
    assert (body["name_en"], body["description_ar"], body["description_en"], body["image_url"]) == ("", None, None, None)


@pytest.mark.parametrize("changes", [
    {"price_sar": "-1"},
    {"price_sar": "18.505"},
    {"price_sar": "abc"},
    {"price_sar": 18.5},  # numbers are refused: SAR travels as text
    {"name_ar": " "},
    {"category_id": None},
])
def test_invalid_products_are_rejected(client, cafes, admin, changes):
    assert _create_product(client, cafes, admin, **changes).status_code == 422
    assert "Mocha" not in _public_products(client)


@pytest.mark.parametrize("changes", [{"price_sar": "1.234"}, {"name_ar": ""}, {"available": None}, {"price_sar": None}])
def test_invalid_edits_are_rejected(client, cafes, admin, changes):
    res = client.patch(f"{_base(cafes)}/products/{cafes['demo-roasters']['product']}", headers=admin, json=changes)

    assert res.status_code == 422
    assert _public_products(client)["Cortado"]["price"] == 1500


def test_a_product_cannot_use_another_cafes_category(client, cafes, admin):
    foreign = cafes["other"]["category"]

    assert _create_product(client, cafes, admin, category_id=foreign).status_code == 422
    res = client.patch(f"{_base(cafes)}/products/{cafes['demo-roasters']['product']}", headers=admin,
                       json={"category_id": foreign})
    assert res.status_code == 422


def test_another_cafes_product_is_404(client, cafes, admin):
    foreign = cafes["other"]["product"]
    assert client.patch(f"{_base(cafes)}/products/{foreign}", headers=admin, json={"available": False}).status_code == 404
    assert client.delete(f"{_base(cafes)}/products/{foreign}", headers=admin).status_code == 404
    assert "Cortado" in _public_products(client, "other")


def test_delete_a_product(client, cafes, admin):
    product_id = _create_product(client, cafes, admin).json()["id"]

    assert client.delete(f"{_base(cafes)}/products/{product_id}", headers=admin).status_code == 204
    assert "Mocha" not in _public_products(client)


def test_a_product_on_an_order_cannot_be_deleted_but_can_be_hidden(client, cafes, admin):
    product_id = cafes["demo-roasters"]["product"]
    order = client.post("/api/cafes/demo-roasters/orders", json={
        "customer_name": "Sara", "pickup_type": "table", "table_number": "4",
        "lines": [{"product_id": product_id, "qty": 1}],
    }).json()

    assert client.delete(f"{_base(cafes)}/products/{product_id}", headers=admin).status_code == 409

    client.patch(f"{_base(cafes)}/products/{product_id}", headers=admin, json={"available": False, "price_sar": "99"})
    line = client.get(f"/api/orders/{order['id']}").json()["lines"][0]
    assert (line["name_en"], line["unit_price"]) == ("Cortado", 1500)  # the Order keeps its snapshot
