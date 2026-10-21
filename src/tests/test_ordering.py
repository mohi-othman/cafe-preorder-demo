from datetime import date, datetime, timezone

from app.models import Cafe, Order
from app.ordering import cafe_day, mark_paid, order_total

UTC = timezone.utc


def test_total_sums_unit_price_times_quantity_in_halalas():
    assert order_total([(1800, 2), (1250, 1)]) == 4850


def test_total_of_no_lines_is_zero():
    assert order_total([]) == 0


def test_cafe_day_uses_riyadh_local_date():
    # 20:59 UTC is 23:59 in Riyadh; 21:00 UTC is already the next day there.
    assert cafe_day(datetime(2026, 10, 21, 20, 59, tzinfo=timezone.utc)) == date(2026, 10, 21)
    assert cafe_day(datetime(2026, 10, 21, 21, 0, tzinfo=timezone.utc)) == date(2026, 10, 22)


def _cafe(session, slug):
    cafe = Cafe(slug=slug, name_ar=slug, name_en=slug)
    session.add(cafe)
    session.commit()
    return cafe


def _paid_number(session, cafe, at):
    order = Order(cafe_id=cafe.id, customer_name="Sara", pickup_type="table", table_number="4", total=1500)
    session.add(order)
    session.commit()
    mark_paid(session, order, now=at)
    return order.order_number


def test_order_numbers_count_up_per_cafe_and_restart_each_riyadh_day(session):
    a = _cafe(session, "a")
    b = _cafe(session, "b")
    day1 = datetime(2026, 10, 21, 8, 0, tzinfo=UTC)
    day1_late = datetime(2026, 10, 21, 20, 59, tzinfo=UTC)  # 23:59 Riyadh
    day2 = datetime(2026, 10, 21, 21, 0, tzinfo=UTC)  # 00:00 Riyadh next day

    assert _paid_number(session, a, day1) == 1
    assert _paid_number(session, a, day1_late) == 2
    assert _paid_number(session, b, day1) == 1
    assert _paid_number(session, a, day2) == 1
    assert _paid_number(session, b, day2) == 1
    assert _paid_number(session, a, day2) == 2


def test_mark_paid_makes_the_order_pending_with_paid_time(session):
    cafe = _cafe(session, "a")
    order = Order(cafe_id=cafe.id, customer_name="Sara", pickup_type="table", table_number="4", total=1500)
    session.add(order)
    session.commit()
    at = datetime(2026, 10, 21, 8, 0, tzinfo=UTC)

    mark_paid(session, order, now=at)

    assert order.status == "pending"
    assert order.paid_at == at
