"""Order Status flow: awaiting_payment -> pending -> preparing -> ready -> completed. Pure, no I/O."""

AWAITING_PAYMENT = "awaiting_payment"
PENDING = "pending"
PREPARING = "preparing"
READY = "ready"
COMPLETED = "completed"

FLOW = (AWAITING_PAYMENT, PENDING, PREPARING, READY, COMPLETED)
ON_KDS = (PENDING, PREPARING, READY)  # paid and not yet picked up


class InvalidTransition(ValueError):
    pass


def after_payment(status: str) -> str:
    """The status an Order takes when its Payment succeeds."""
    if status != AWAITING_PAYMENT:
        raise InvalidTransition(f"cannot pay an order that is {status}")
    return PENDING


def next_status(status: str) -> str:
    """The status after one KDS step: Accept, Ready or Complete."""
    if status not in ON_KDS:
        raise InvalidTransition(f"an order that is {status} cannot be moved on the KDS")
    return FLOW[FLOW.index(status) + 1]
