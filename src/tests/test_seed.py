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
