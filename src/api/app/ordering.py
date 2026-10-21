"""Order rules: totals, the Café day and Order Numbers."""

from collections.abc import Iterable
from datetime import date, datetime
from zoneinfo import ZoneInfo

from sqlalchemy import func
from sqlmodel import Session, select

from app.models import Cafe, Order
from app.order_status import after_payment

CAFE_TZ = ZoneInfo("Asia/Riyadh")


def order_total(lines: Iterable[tuple[int, int]]) -> int:
    """Total in halalas of (unit_price, qty) pairs."""
    return sum(price * qty for price, qty in lines)


def cafe_day(moment: datetime) -> date:
    """The Café's local date (Asia/Riyadh) for a timezone-aware moment."""
    return moment.astimezone(CAFE_TZ).date()


def mark_paid(session: Session, order: Order, now: datetime) -> Order:
    """Make a paid Order pending and give it the next Order Number of its Café's day. Commits."""
    # Lock the Order (no double payment) and the Café (no duplicate number) until commit.
    locked = select(Order).where(Order.id == order.id).with_for_update().execution_options(populate_existing=True)
    order = session.exec(locked).one()
    status = after_payment(order.status)
    session.exec(select(Cafe).where(Cafe.id == order.cafe_id).with_for_update()).one()
    day = cafe_day(now)
    last = session.exec(
        select(func.max(Order.order_number)).where(Order.cafe_id == order.cafe_id, Order.cafe_day == day)
    ).one()
    order.status = status
    order.cafe_day = day
    order.order_number = (last or 0) + 1
    order.paid_at = now
    session.add(order)
    session.commit()
    session.refresh(order)
    return order
