"""Load the demo Café and its Menu. Safe to run more than once.

Run from src/api:  python -m app.seed
"""

from sqlmodel import Session, select

from app.db import create_schema, engine
from app.models import Cafe, Category, Product

CAFE = {"slug": "demo-roasters", "name_ar": "محمصة التجربة", "name_en": "Demo Roasters"}

# (name_ar, name_en, [(name_ar, name_en, desc_ar, desc_en, price_halalas, available, image)])
MENU = [
    ("مشروبات حارة", "Hot drinks", [
        ("قهوة مقطرة V60", "V60 pour-over", "إثيوبيا، نكهات توت وياسمين", "Ethiopia, berry and jasmine notes", 1800, True, "v60"),
        ("سبانش لاتيه", "Spanish latte", "إسبريسو مع حليب مكثف", "Espresso with condensed milk", 1900, True, "spanish-latte"),
        ("كورتادو", "Cortado", "إسبريسو مزدوج وحليب", "Double espresso and milk", 1500, True, "cortado"),
        ("فلات وايت", "Flat white", "حليب ناعم ورغوة خفيفة", "Silky milk, thin foam", 1700, True, "flat-white"),
    ]),
    ("مشروبات باردة", "Cold drinks", [
        ("كولد برو", "Cold brew", "منقوع ١٢ ساعة", "Steeped for 12 hours", 2000, False, "cold-brew"),
        ("آيس لاتيه", "Iced latte", "إسبريسو وحليب وثلج", "Espresso, milk and ice", 1800, True, "iced-latte"),
        ("آيس سبانش", "Iced Spanish latte", "حليب مكثف وثلج", "Condensed milk over ice", 2100, True, "iced-spanish"),
    ]),
    ("حلى", "Desserts", [
        ("تشيز كيك", "Cheesecake", "سان سباستيان", "San Sebastián style", 2600, True, "cheesecake"),
        ("كروسان زبدة", "Butter croissant", "مخبوز يومياً", "Baked daily", 1200, True, "croissant"),
        ("كيكة التمر", "Date cake", "مع صوص الكراميل", "With caramel sauce", 2200, True, "date-cake"),
    ]),
    ("بن", "Beans", [
        ("بن إثيوبي ٢٥٠غ", "Ethiopian beans 250g", "يرغاتشيفي، تحميص فاتح", "Yirgacheffe, light roast", 7500, True, "beans-ethiopia"),
        ("بن كولومبي ٢٥٠غ", "Colombian beans 250g", "هويلا، تحميص متوسط", "Huila, medium roast", 6800, True, "beans-colombia"),
    ]),
]


def _upsert(session: Session, model, keys: dict, values: dict):
    row = session.exec(select(model).filter_by(**keys)).first()
    if row is None:
        row = model(**keys, **values)
    else:
        for k, v in values.items():
            setattr(row, k, v)
    session.add(row)
    session.flush()
    return row


def seed(session: Session) -> None:
    cafe = _upsert(session, Cafe, {"slug": CAFE["slug"]}, {"name_ar": CAFE["name_ar"], "name_en": CAFE["name_en"]})
    for c_pos, (c_ar, c_en, products) in enumerate(MENU):
        cat = _upsert(session, Category, {"cafe_id": cafe.id, "name_en": c_en}, {"name_ar": c_ar, "position": c_pos})
        for p_pos, (p_ar, p_en, d_ar, d_en, price, available, image) in enumerate(products):
            _upsert(session, Product, {"cafe_id": cafe.id, "name_en": p_en}, {
                "category_id": cat.id, "name_ar": p_ar, "description_ar": d_ar, "description_en": d_en,
                "price": price, "available": available, "image_url": f"/menu/{image}.svg", "position": p_pos,
            })
    session.commit()


if __name__ == "__main__":
    create_schema()
    with Session(engine) as s:
        seed(s)
    print("Seeded Demo Roasters.")
