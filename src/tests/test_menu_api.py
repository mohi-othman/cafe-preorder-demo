from app.models import Cafe, Category, Product


def _add_cafe(session, slug="demo-roasters"):
    cafe = Cafe(slug=slug, name_ar="محمصة التجربة", name_en="Demo Roasters")
    session.add(cafe)
    session.commit()
    session.refresh(cafe)
    return cafe


def test_menu_lists_categories_with_available_products(client, session):
    cafe = _add_cafe(session)
    hot = Category(cafe_id=cafe.id, name_ar="مشروبات حارة", name_en="Hot drinks", position=0)
    cold = Category(cafe_id=cafe.id, name_ar="مشروبات باردة", name_en="Cold drinks", position=1)
    session.add_all([hot, cold])
    session.commit()
    session.add_all([
        Product(cafe_id=cafe.id, category_id=hot.id, name_ar="كورتادو", name_en="Cortado",
                price=1500, available=True, image_url="/menu/cortado.svg", position=0),
        Product(cafe_id=cafe.id, category_id=cold.id, name_ar="كولد برو", name_en="Cold brew",
                price=2000, available=False, position=0),
        Product(cafe_id=cafe.id, category_id=cold.id, name_ar="آيس لاتيه", name_en="Iced latte",
                price=1800, available=True, position=1),
    ])
    session.commit()

    res = client.get("/api/cafes/demo-roasters/menu")

    assert res.status_code == 200
    body = res.json()
    assert body["cafe"]["name_en"] == "Demo Roasters"
    assert [c["name_en"] for c in body["categories"]] == ["Hot drinks", "Cold drinks"]
    hot_products, cold_products = (c["products"] for c in body["categories"])
    assert [p["name_en"] for p in hot_products] == ["Cortado"]
    assert hot_products[0]["price"] == 1500
    assert hot_products[0]["image_url"] == "/menu/cortado.svg"
    assert [p["name_en"] for p in cold_products] == ["Iced latte"]


def test_menu_only_shows_the_requested_cafe(client, session):
    _add_cafe(session)
    other = _add_cafe(session, slug="other-cafe")
    cat = Category(cafe_id=other.id, name_ar="حلى", name_en="Desserts", position=0)
    session.add(cat)
    session.commit()

    res = client.get("/api/cafes/demo-roasters/menu")

    assert res.status_code == 200
    assert res.json()["categories"] == []


def test_unknown_cafe_is_404(client):
    res = client.get("/api/cafes/nope/menu")

    assert res.status_code == 404
