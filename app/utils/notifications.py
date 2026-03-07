from types import TracebackType
from typing import Self

from faststream.rabbit import RabbitQueue
from faststream.rabbit.annotations import RabbitBroker


class Notifications:
    def __init__(self, broker: RabbitBroker, queue: str) -> None:
        self._broker = broker
        self._queue = queue

    async def __aenter__(self) -> Self:
        await self._broker.connect()
        await self._broker.declare_queue(RabbitQueue(self._queue))
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_val: BaseException | None = None,
        exc_tb: TracebackType | None = None,
    ) -> None:
        await self._broker.stop(exc_type, exc_val, exc_tb)

    async def send_to_rabbit(self, message: list[str]) -> None:
        await self._broker.publish(message=message, queue=self._queue)
