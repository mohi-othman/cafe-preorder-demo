import asyncio

from app.broadcaster import Broadcaster


class FakeConnection:
    def __init__(self, fail=False):
        self.received = []
        self.fail = fail

    async def send_json(self, message):
        if self.fail:
            raise RuntimeError("connection gone")
        self.received.append(message)


def publish(b, channels, message):
    asyncio.run(b.publish(channels, message))


def test_a_message_reaches_every_connection_on_its_channels_only():
    b = Broadcaster()
    kds_a, kds_a2, kds_b, tracking = FakeConnection(), FakeConnection(), FakeConnection(), FakeConnection()
    b.subscribe("cafe:1", kds_a)
    b.subscribe("cafe:1", kds_a2)
    b.subscribe("cafe:2", kds_b)
    b.subscribe("order:x", tracking)

    publish(b, ["cafe:1", "order:x"], {"type": "order_created"})

    assert kds_a.received == [{"type": "order_created"}]
    assert kds_a2.received == [{"type": "order_created"}]
    assert tracking.received == [{"type": "order_created"}]
    assert kds_b.received == []


def test_an_unsubscribed_connection_gets_nothing_more():
    b = Broadcaster()
    conn = FakeConnection()
    b.subscribe("cafe:1", conn)
    publish(b, ["cafe:1"], {"n": 1})

    b.unsubscribe("cafe:1", conn)
    publish(b, ["cafe:1"], {"n": 2})

    assert conn.received == [{"n": 1}]


def test_a_broken_connection_is_dropped_and_does_not_stop_the_others():
    b = Broadcaster()
    broken, ok = FakeConnection(fail=True), FakeConnection()
    b.subscribe("cafe:1", broken)
    b.subscribe("cafe:1", ok)

    publish(b, ["cafe:1"], {"n": 1})
    broken.fail = False
    publish(b, ["cafe:1"], {"n": 2})

    assert ok.received == [{"n": 1}, {"n": 2}]
    assert broken.received == []


def test_publishing_to_a_channel_nobody_listens_on_is_harmless():
    b = Broadcaster()
    b.subscribe("cafe:1", FakeConnection())
    b.unsubscribe("cafe:1", FakeConnection())  # never subscribed

    publish(b, ["cafe:9"], {"n": 1})
