"""Payment providers. Only a fake one for the demo; Moyasar or Tap would implement the same interface."""

from dataclasses import dataclass
from typing import Protocol
from uuid import uuid4

METHODS = ("apple_pay", "mada")


@dataclass(frozen=True)
class PaymentResult:
    ok: bool
    reference: str | None = None
    error: str | None = None


class PaymentProvider(Protocol):
    def charge(self, amount: int, method: str, source: str) -> PaymentResult:
        """Charge `amount` halalas. `source` is the token the payment page got from the provider."""
        ...


class FakeProvider:
    """Succeeds for Apple Pay and mada unless the source is "fail"."""

    def charge(self, amount: int, method: str, source: str) -> PaymentResult:
        if method not in METHODS:
            return PaymentResult(ok=False, error="unsupported_method")
        if source == "fail":
            return PaymentResult(ok=False, error="declined")
        return PaymentResult(ok=True, reference=f"fake_{uuid4().hex[:12]}")


def get_payment_provider() -> PaymentProvider:
    return FakeProvider()
