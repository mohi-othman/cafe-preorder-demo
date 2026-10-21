import pytest

from app.order_status import InvalidTransition, after_payment, next_status


def test_payment_moves_awaiting_payment_to_pending():
    assert after_payment("awaiting_payment") == "pending"


@pytest.mark.parametrize("status", ["pending", "preparing", "ready", "completed"])
def test_an_order_cannot_be_paid_twice(status):
    with pytest.raises(InvalidTransition):
        after_payment(status)


@pytest.mark.parametrize("current, expected", [
    ("pending", "preparing"),  # Accept
    ("preparing", "ready"),  # Ready
    ("ready", "completed"),  # Complete
])
def test_each_kds_step_moves_an_order_one_status_forward(current, expected):
    assert next_status(current) == expected


@pytest.mark.parametrize("status", ["awaiting_payment", "completed", "cancelled"])
def test_unpaid_finished_or_unknown_orders_cannot_be_moved_on_the_kds(status):
    with pytest.raises(InvalidTransition):
        next_status(status)
