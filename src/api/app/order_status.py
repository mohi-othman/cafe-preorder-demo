"""Order Status flow: awaiting_payment -> pending -> preparing -> ready -> completed. Pure, no I/O."""

AWAITING_PAYMENT = "awaiting_payment"
PENDING = "pending"
PREPARING = "preparing"
READY = "ready"
COMPLETED = "completed"

FLOW = (AWAITING_PAYMENT, PENDING, PREPARING, READY, COMPLETED)


class InvalidTransition(ValueError):
    pass


def after_payment(status: str) -> str:
    """The status an Order takes when its Payment succeeds."""
    if status != AWAITING_PAYMENT:
        raise InvalidTransition(f"cannot pay an order that is {status}")
    return PENDING
