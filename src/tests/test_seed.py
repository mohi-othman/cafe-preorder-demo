import pytest

from app.config import settings
from app.seed import seed


def test_seed_loads_demo_roasters_menu_and_is_idempotent(client, session):
    seed(session)
    seed(session)

    res = client.get("/api/cafes/demo-roasters/menu")

    assert res.status_code == 200
    body = res.json()
    assert body["cafe"]["name_ar"] == "محمصة التجربة"
    assert [c["name_en"] for c in body["categories"]] == ["Hot drinks", "Cold drinks", "Desserts", "Beans"]
    names = [p["name_en"] for c in body["categories"] for p in c["products"]]
    assert len(names) == len(set(names)) == 11  # 12 seeded, Cold brew is unavailable
    assert "Cold brew" not in names
    assert all(p["image_url"] for c in body["categories"] for p in c["products"])


def test_seeded_admin_and_barista_can_log_in_with_the_env_passwords(client, session):
    seed(session)
    seed(session)  # re-seeding keeps one login each

    admin = client.post("/api/auth/login", json={"username": "admin", "password": "admin-test-pass"})
    barista = client.post("/api/auth/login", json={"username": "barista", "password": "barista-test-pass"})

    assert admin.status_code == 200
    assert admin.json()["role"] == "admin"
    assert admin.json()["cafe"] is None
    assert barista.status_code == 200
    assert barista.json()["role"] == "barista"
    assert barista.json()["cafe"]["slug"] == "demo-roasters"
    assert client.post("/api/auth/login", json={"username": "barista", "password": "nope"}).status_code == 401
    assert client.post("/api/auth/login", json={"username": "nobody", "password": "x"}).status_code == 401


def test_reseeding_updates_a_changed_password(client, session, monkeypatch):
    seed(session)
    monkeypatch.setattr(settings, "barista_password", "new-barista-pass")
    seed(session)

    assert client.post("/api/auth/login", json={"username": "barista", "password": "barista-test-pass"}).status_code == 401
    assert client.post("/api/auth/login", json={"username": "barista", "password": "new-barista-pass"}).status_code == 200


def test_seed_refuses_to_run_without_passwords(session, monkeypatch):
    monkeypatch.setattr(settings, "admin_password", "")

    with pytest.raises(RuntimeError, match="ADMIN_PASSWORD"):
        seed(session)
