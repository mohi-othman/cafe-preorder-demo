"""Super Admin daily report of one Café, computed live with SQL.

Only paid Orders count (any status after awaiting_payment). An Order belongs to the Asia/Riyadh day
and hour of its paid_at, the same rule that gives Order Numbers their Café day.
"""

from datetime import date, datetime, time, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlmodel import Session, select

from app.auth import require_admin
from app.db import get_session
from app.models import Cafe, Order, OrderLine
from app.order_status import AWAITING_PAYMENT
from app.ordering import CAFE_TZ, cafe_day

router = APIRouter(prefix="/api/admin", dependencies=[Depends(require_admin)])


class TopProductOut(BaseModel):
    product_id: int
    name_ar: str  # from the latest Order Line snapshot
    name_en: str
    qty: int
    revenue: int  # halalas


class DailyReportOut(BaseModel):
    cafe_id: int
    date: date
    orders: int
    revenue: int  # halalas
    average_order_value: int | None  # halalas, rounded half up; None when there are no Orders
    top_products: list[TopProductOut]  # at most 5: qty desc, then revenue desc, then Arabic name
    orders_per_hour: list[int]  # 24 counts, index = Riyadh hour of paid_at


def average(revenue: int, orders: int) -> int | None:
    """Average order value in whole halalas, rounded half up (4152.5 -> 4153). None for no Orders."""
    return (2 * revenue + orders) // (2 * orders) if orders else None


def _paid_on(cafe_id: int, day: date):
    """WHERE clause: paid Orders of the Café whose paid_at falls on the Riyadh day."""
    start = datetime.combine(day, time(), CAFE_TZ)
    end = datetime.combine(day + timedelta(days=1), time(), CAFE_TZ)
    return (Order.cafe_id == cafe_id, Order.status != AWAITING_PAYMENT, Order.paid_at >= start, Order.paid_at < end)


def _top_products(session: Session, where) -> list[TopProductOut]:
    totals = (
        select(
            OrderLine.product_id,
            func.sum(OrderLine.qty).label("qty"),
            func.sum(OrderLine.unit_price * OrderLine.qty).label("revenue"),
            func.max(OrderLine.id).label("last_line"),
        )
        .join(Order, Order.id == OrderLine.order_id)
        .where(*where)
        .group_by(OrderLine.product_id)
        .subquery()
    )
    rows = session.exec(
        select(totals.c.product_id, OrderLine.name_ar, OrderLine.name_en, totals.c.qty, totals.c.revenue)
        .join(OrderLine, OrderLine.id == totals.c.last_line)
        .order_by(totals.c.qty.desc(), totals.c.revenue.desc(), OrderLine.name_ar.collate("C"))
        .limit(5)
    ).all()
    return [TopProductOut(product_id=r[0], name_ar=r[1], name_en=r[2], qty=r[3], revenue=r[4]) for r in rows]


def _orders_per_hour(session: Session, where) -> list[int]:
    hour = func.extract("hour", func.timezone(CAFE_TZ.key, Order.paid_at))
    counts = [0] * 24
    for h, n in session.exec(select(hour, func.count(Order.id)).where(*where).group_by(hour)).all():
        counts[int(h)] = n
    return counts


@router.get("/cafes/{cafe_id}/reports/daily", response_model=DailyReportOut)
def daily_report(cafe_id: int, date: date | None = None,  # default: today in Riyadh
                 session: Session = Depends(get_session)):
    if session.get(Cafe, cafe_id) is None:
        raise HTTPException(status_code=404, detail="Café not found")
    if date is None:
        date = cafe_day(datetime.now(timezone.utc))
    where = _paid_on(cafe_id, date)
    orders, revenue = session.exec(select(func.count(Order.id), func.coalesce(func.sum(Order.total), 0)).where(*where)).one()
    return DailyReportOut(cafe_id=cafe_id, date=date, orders=orders, revenue=revenue,
                          average_order_value=average(revenue, orders), top_products=_top_products(session, where),
                          orders_per_hour=_orders_per_hour(session, where))
