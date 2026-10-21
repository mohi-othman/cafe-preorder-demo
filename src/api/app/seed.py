"""Load the demo Café, its Menu and the admin and Barista logins. Safe to run more than once.

Run from src/api:  python -m app.seed
"""

from sqlmodel import Session, select

from app.auth import ADMIN, BARISTA, hash_password
from app.config import settings
from app.db import create_schema, engine
from app.models import Cafe, Category, Product, User

# Logins; passwords come from ADMIN_PASSWORD and BARISTA_PASSWORD.
ADMIN_USERNAME = "admin"
BARISTA_USERNAME = "barista"  # Demo Roasters

CAFE ={"slug": "demo-roasters", "name_ar": "محمصة التجربة", "name_en": "Demo Roasters"}

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
    missing = [name for name, value in (("ADMIN_PASSWORD", settings.admin_password),
                                         ("BARISTA_PASSWORD", settings.barista_password)) if not value]
    if missing:
        raise RuntimeError(f"Set {' and '.join(missing)} (env var or src/api/.env) before seeding")

    cafe =_upsert(session, Cafe, {"slug": CAFE["slug"]}, {"name_ar": CAFE["name_ar"], "name_en": CAFE["name_en"]})
    for c_pos, (c_ar, c_en, products) in enumerate(MENU):
        cat = _upsert(session, Category, {"cafe_id": cafe.id, "name_en": c_en}, {"name_ar": c_ar, "position": c_pos})
        for p_pos, (p_ar, p_en, d_ar, d_en, price, available, image) in enumerate(products):
            _upsert(session, Product, {"cafe_id": cafe.id, "name_en": p_en}, {
                "category_id": cat.id, "name_ar": p_ar, "description_ar": d_ar, "description_en": d_en,
                "price": price, "available": available, "image_url": f"/menu/{image}.svg", "position": p_pos,
            })
    _upsert(session, User, {"username": ADMIN_USERNAME}, {
        "role": ADMIN, "cafe_id": None, "password_hash": hash_password(settings.admin_password)})
    _upsert(session, User, {"username": BARISTA_USERNAME}, {
        "role": BARISTA, "cafe_id": cafe.id, "password_hash": hash_password(settings.barista_password)})
    session.commit()


if __name__ == "__main__":
    create_schema()
    with Session(engine) as s:
        seed(s)
    print("Seeded Demo Roasters.")
