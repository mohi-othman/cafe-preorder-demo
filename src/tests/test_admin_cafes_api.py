import pytest

from app.auth import hash_password
from app.models import Cafe, User


@pytest.fixture
def seeded(session):
    """One Café with its Barista, and the Super Admin."""
    cafe = Cafe(slug="demo-roasters", name_ar="محمصة التجربة", name_en="Demo Roasters")
    session.add(cafe)
    session.commit()
    session.add(User(username="barista", password_hash=hash_password("pw"), role="barista", cafe_id=cafe.id))
    session.add(User(username="admin", password_hash=hash_password("pw"), role="admin"))
    session.commit()


def _login(client, username, password="pw"):
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


@pytest.fixture
def admin(client, seeded):
    return _login(client, "admin")


NEW_CAFE = {
    "name_ar": "بن الشمال", "name_en": "North Beans", "slug": "north-beans",
    "barista_username": "north", "barista_password": "north-pass-1",
}


def _create(client, headers, **changes):
    return client.post("/api/admin/cafes", json={**NEW_CAFE, **changes}, headers=headers)


def test_new_cafe_has_an_empty_menu_and_a_working_barista_login(client, admin):
    res = _create(client, admin)
    assert res.status_code == 201
    created = res.json()
    assert {k: created[k] for k in ("slug", "name_ar", "name_en")} == {
        "slug": "north-beans", "name_ar": "بن الشمال", "name_en": "North Beans",
    }

    assert client.get("/api/cafes/north-beans/menu").json()["categories"] == []

    login = client.post("/api/auth/login", json={"username": "north", "password": "north-pass-1"}).json()
    assert login["role"] == "barista"
    assert login["cafe"]["slug"] == "north-beans"
    board = client.get("/api/kds/orders", headers={"Authorization": f"Bearer {login['access_token']}"})
    assert board.status_code == 200
    assert board.json()["cafe"]["slug"] == "north-beans"
    assert board.json()["orders"] == []

    assert "north-beans" in [c["slug"] for c in client.get("/api/admin/cafes", headers=admin).json()]


def test_a_taken_slug_is_refused(client, admin):
    res = _create(client, admin, slug="demo-roasters")
    assert res.status_code == 409
    assert res.json()["detail"] == "slug_taken"
    assert client.post("/api/auth/login", json={"username": "north", "password": "north-pass-1"}).status_code == 401


def test_a_taken_barista_username_is_refused_and_no_cafe_is_added(client, admin):
    res = _create(client, admin, barista_username="barista")
    assert res.status_code == 409
    assert res.json()["detail"] == "username_taken"
    assert client.get("/api/cafes/north-beans/menu").status_code == 404


@pytest.mark.parametrize("changes", [
    {"slug": "North-Beans"},
    {"slug": "north beans"},
    {"slug": "north_beans"},
    {"slug": "-north"},
    {"slug": "north-"},
    {"slug": "قهوة"},
    {"slug": ""},
    {"barista_password": "short"},
    {"barista_username": "  "},
    {"name_ar": ""},
])
def test_bad_input_is_refused(client, admin, changes):
    assert _create(client, admin, **changes).status_code == 422
    assert client.get("/api/cafes/north-beans/menu").status_code == 404


def test_slug_and_username_are_trimmed(client, admin):
    res = _create(client, admin, slug=" north-beans ", barista_username=" north ")
    assert res.json()["slug"] == "north-beans"
    assert client.post("/api/auth/login", json={"username": "north", "password": "north-pass-1"}).status_code == 200


def test_only_the_super_admin_can_add_a_cafe(client, seeded):
    assert _create(client, {}).status_code == 401
    assert _create(client, _login(client, "barista")).status_code == 403
    assert client.get("/api/cafes/north-beans/menu").status_code == 404
