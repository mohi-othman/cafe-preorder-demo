import pytest

from app.order_status import InvalidTransition, after_payment


def test_payment_moves_awaiting_payment_to_pending():
    assert after_payment("awaiting_payment") == "pending"


@pytest.mark.parametrize("status", ["pending", "preparing", "ready", "completed"])
def test_an_order_cannot_be_paid_twice(status):
    with pytest.raises(InvalidTransition):
        after_payment(status)
