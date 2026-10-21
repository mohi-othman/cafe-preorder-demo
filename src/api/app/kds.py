"""KDS: a Barista's board of their Café's paid Orders and the one-step status buttons."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.auth import require_barista
from app.db import get_session
from app.menu import CafeOut
from app.models import Cafe, Order
from app.order_status import ON_KDS, InvalidTransition, next_status
from app.orders import OrderOut, _out

router = APIRouter(prefix="/api/kds")


class BoardOut(BaseModel):
    cafe: CafeOut
    orders: list[OrderOut]  # pending, preparing and ready; oldest paid first


class AdvanceIn(BaseModel):
    from_status: str  # the status the Barista saw; a stale tap gets 409 instead of skipping a step


@router.get("/orders", response_model=BoardOut)
def board(cafe: Cafe = Depends(require_barista), session: Session = Depends(get_session)):
    orders = session.exec(
        select(Order).where(Order.cafe_id == cafe.id, Order.status.in_(ON_KDS)).order_by(Order.paid_at, Order.id)
    ).all()
    return BoardOut(cafe=CafeOut.model_validate(cafe, from_attributes=True), orders=[_out(session, o) for o in orders])


@router.post("/orders/{public_id}/advance", response_model=OrderOut)
def advance(
    public_id: UUID,
    body: AdvanceIn,
    cafe: Cafe = Depends(require_barista),
    session: Session = Depends(get_session),
):
    order = session.exec(select(Order).where(Order.public_id == public_id).with_for_update()).first()
    if order is None or order.cafe_id != cafe.id:  # another Café's Order looks like no Order
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != body.from_status:
        raise HTTPException(status_code=409, detail=f"Order is already {order.status}")
    try:
        order.status = next_status(order.status)
    except InvalidTransition as e:
        raise HTTPException(status_code=409, detail=str(e))
    session.add(order)
    session.commit()
    session.refresh(order)
    return _out(session, order)
