from app.payments import FakeProvider


def test_fake_provider_succeeds_with_apple_pay_and_mada():
    provider = FakeProvider()

    for method in ("apple_pay", "mada"):
        result = provider.charge(amount=4850, method=method, source="ok")
        assert result.ok
        assert result.reference


def test_fake_provider_fails_when_asked_to():
    result = FakeProvider().charge(amount=4850, method="mada", source="fail")

    assert not result.ok
    assert result.reference is None


def test_fake_provider_rejects_unknown_method():
    result = FakeProvider().charge(amount=4850, method="cash", source="ok")

    assert not result.ok
