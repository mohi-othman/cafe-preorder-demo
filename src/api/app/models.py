from datetime import date, datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import DateTime, UniqueConstraint
from sqlmodel import Field, SQLModel


class Cafe(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    slug: str = Field(unique=True, index=True)
    name_ar: str
    name_en: str = ""


class Category(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    cafe_id: int = Field(foreign_key="cafe.id", index=True)
    name_ar: str
    name_en: str = ""
    position: int = 0


class Product(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    cafe_id: int = Field(foreign_key="cafe.id", index=True)
    category_id: int = Field(foreign_key="category.id", index=True)
    name_ar: str
    name_en: str = ""
    description_ar: str | None = None
    description_en: str | None = None
    price: int  # halalas, VAT included
    available: bool = True
    image_url: str | None = None
    position: int = 0


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Order(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("cafe_id", "cafe_day", "order_number"),)

    id: int | None = Field(default=None, primary_key=True)
    public_id: UUID = Field(default_factory=uuid4, unique=True, index=True)  # used in /o/<uuid>
    cafe_id: int = Field(foreign_key="cafe.id", index=True)
    status: str = "awaiting_payment"
    order_number: int | None = None  # set when paid
    cafe_day: date | None = None  # Riyadh date the Order was paid on
    customer_name: str
    phone: str | None = None
    pickup_type: str  # "table" or "car"
    table_number: str | None = None
    car_model: str | None = None
    car_color: str | None = None
    car_plate: str | None = None
    total: int  # halalas
    created_at: datetime = Field(default_factory=_utcnow, sa_type=DateTime(timezone=True))
    paid_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))


class OrderLine(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="order.id", index=True)
    product_id: int = Field(foreign_key="product.id")
    name_ar: str  # snapshot at order time
    name_en: str = ""
    unit_price: int  # halalas
    qty: int
    note: str | None = None
