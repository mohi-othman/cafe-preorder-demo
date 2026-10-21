"""In-process broadcaster: open WebSocket connections per channel, and fan-out of events to them.

Channels are `cafe:<id>` (KDS screens) and `order:<uuid>` (tracking pages). Connections live in this
process's memory, so the API must run as one instance (ADR 0001).
"""

from collections import defaultdict
from typing import Any, Protocol


class Connection(Protocol):
    async def send_json(self, data: Any) -> None: ...

    async def close(self, code: int = 1000) -> None: ...


def cafe_channel(cafe_id: int) -> str:
    return f"cafe:{cafe_id}"


def order_channel(public_id) -> str:
    return f"order:{public_id}"


class Broadcaster:
    def __init__(self) -> None:
        self._channels: dict[str, set[Connection]] = defaultdict(set)

    def subscribe(self, channel: str, conn: Connection) -> None:
        self._channels[channel].add(conn)

    def unsubscribe(self, channel: str, conn: Connection) -> None:
        conns = self._channels.get(channel)
        if conns is not None:
            conns.discard(conn)
            if not conns:
                del self._channels[channel]

    async def publish(self, channels: list[str], message: Any) -> None:
        """Send `message` to every connection on `channels`; drop and close connections that fail.

        Closing tells a client that missed a message to reconnect and reload, instead of waiting forever.
        """
        for channel in channels:
            for conn in list(self._channels.get(channel, ())):
                try:
                    await conn.send_json(message)
                except Exception:
                    self.unsubscribe(channel, conn)
                    try:
                        await conn.close(code=1011)  # internal error: the client reconnects
                    except Exception:
                        pass  # already gone


broadcaster = Broadcaster()
