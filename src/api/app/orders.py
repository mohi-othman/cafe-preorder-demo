import logging
from datetime import datetime, timezone
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field, StringConstraints, model_validator
from sqlmodel import Session, select

from app import live
from app.db import get_session
from app.menu import CafeOut
from app.models import Cafe, Order, OrderLine, Product
from app.order_status import AWAITING_PAYMENT
from app.ordering import mark_paid, order_total
from app.payments import PaymentProvider, get_payment_provider

router = APIRouter(prefix="/api")
log = logging.getLogger(__name__)

Text = Annotated[str, StringConstraints(strip_whitespace=True, max_length=80)]


class LineIn(BaseModel):
    product_id: int
    qty: int = Field(ge=1, le=99)
    note: Annotated[str, StringConstraints(strip_whitespace=True, max_length=140)] | None = None


class OrderIn(BaseModel):
    customer_name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)]
    phone: Annotated[str, StringConstraints(strip_whitespace=True, max_length=20)] | None = None
    pickup_type: Literal["table", "car"]
    table_number: Annotated[str, StringConstraints(strip_whitespace=True, max_length=10)] | None = None
    car_model: Text | None = None
    car_color: Text | None = None
    car_plate: Text | None = None
    lines: list[LineIn] = Field(min_length=1, max_length=50)

    @model_validator(mode="after")
    def pickup_details(self):
        if self.pickup_type == "table":
            if not self.table_number:
                raise ValueError("Table pickup needs a table number")
            self.car_model = self.car_color = self.car_plate = None
        else:
            if not (self.car_model and self.car_color and self.car_plate):
                raise ValueError("Car pickup needs car model, color and plate")
            self.table_number = None
        return self


class PaymentIn(BaseModel):
    method: Literal["apple_pay", "mada"]
    source: str = "ok"


class LineOut(BaseModel):
    product_id: int
    name_ar: str
    name_en: str
    unit_price: int
    qty: int
    note: str | None


class OrderOut(BaseModel):
    id: UUID
    cafe: CafeOut
    status: str
    order_number: int | None
    customer_name: str
    phone: str | None
    pickup_type: str
    table_number: str | None
    car_model: str | None
    car_color: str | None
    car_plate: str | None
    total: int
    created_at: datetime
    paid_at: datetime | None
    lines: list[LineOut]


def order_out(session: Session, order: Order) -> OrderOut:
    cafe = session.get(Cafe, order.cafe_id)
    lines = session.exec(select(OrderLine).where(OrderLine.order_id == order.id).order_by(OrderLine.id)).all()
    return OrderOut(
        **order.model_dump(exclude={"id", "public_id", "cafe_id", "cafe_day"}),
        id=order.public_id,
        cafe=CafeOut.model_validate(cafe, from_attributes=True),
        lines=[LineOut.model_validate(line, from_attributes=True) for line in lines],
    )


def _get_order(session: Session, public_id: UUID, lock: bool = False) -> Order:
    query = select(Order).where(Order.public_id == public_id)
    order = session.exec(query.with_for_update() if lock else query).first()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.post("/cafes/{slug}/orders", response_model=OrderOut, status_code=201)
def create_order(slug: str, body: OrderIn, session: Session = Depends(get_session)):
    cafe = session.exec(select(Cafe).where(Cafe.slug == slug)).first()
    if cafe is None:
        raise HTTPException(status_code=404, detail="Café not found")
    ids = {line.product_id for line in body.lines}
    products = {
        p.id: p
        for p in session.exec(
            select(Product).where(Product.id.in_(ids), Product.cafe_id == cafe.id, Product.available)
        ).all()
    }
    if missing := ids - products.keys():
        raise HTTPException(status_code=422, detail={"code": "products_unavailable", "product_ids": sorted(missing)})

    order = Order(
        cafe_id=cafe.id,
        status=AWAITING_PAYMENT,
        total=order_total((products[line.product_id].price, line.qty) for line in body.lines),
        **body.model_dump(exclude={"lines"}),
    )
    session.add(order)
    session.flush()
    for line in body.lines:
        p = products[line.product_id]
        session.add(OrderLine(
            order_id=order.id, product_id=p.id, name_ar=p.name_ar, name_en=p.name_en,
            unit_price=p.price, qty=line.qty, note=line.note or None,
        ))
    session.commit()
    session.refresh(order)
    return order_out(session, order)


@router.post("/orders/{public_id}/pay", response_model=OrderOut)
def pay_order(
    public_id: UUID,
    body: PaymentIn,
    tasks: BackgroundTasks,
    session: Session = Depends(get_session),
    provider: PaymentProvider = Depends(get_payment_provider),
):
    # The row lock is held through the charge until mark_paid commits, so a second pay of the
    # same Order waits here and then sees it paid: one charge only.
    order = _get_order(session, public_id, lock=True)
    if order.status != AWAITING_PAYMENT:
        raise HTTPException(status_code=409, detail="Order is already paid")
    result = provider.charge(amount=order.total, method=body.method, source=body.source)
    if not result.ok:
        raise HTTPException(status_code=402, detail=result.error or "payment_failed")
    try:
        mark_paid(session, order, now=datetime.now(timezone.utc))
    except Exception:
        # Charged but not marked paid: leave a trace so staff can mark it paid or refund it.
        log.exception("Order %s was charged %s halalas (payment %s) but could not be marked paid",
                      order.public_id, order.total, result.reference)
        raise
    out = order_out(session, order)
    live.publish_after_response(tasks, live.ORDER_CREATED, order.cafe_id, out)
    return out


@router.get("/orders/{public_id}", response_model=OrderOut)
def get_order(public_id: UUID, session: Session = Depends(get_session)):
    return order_out(session, _get_order(session, public_id))
