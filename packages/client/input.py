"""Async user input."""

from asyncio import Event, create_task
from collections.abc import Callable
from typing import Any, Coroutine, Sequence

from rich.console import Console


from packages.shared.pdu import PDU


class Input(object):
    """Async input."""

    def __init__(self):
        """Creates a new input session."""
        self.__event = Event()

    def run(self, func: Callable[[], Coroutine[Any, Any, Sequence[PDU]]]):
        """Run the async input function.

        Args:
            func (Callable[[], Coroutine[Any, Any, Sequence[PDU]]]): Input function
        """
        try:
            self.__task.cancel()
        except AttributeError:
            pass

        self.__task = create_task(self.__worker(func))

    async def __worker(self, func: Callable[[], Coroutine[Any, Any, Sequence[PDU]]]):
        self.__result = await func()
        self.__event.set()

    async def subscribe(self):
        """Yields user inputs as they are completed."""
        while True:
            await self.__event.wait()
            yield self.__result
            self.__event.clear()


def rich_parse(text: str):
    """Parse rich text.

    Args:
        text (str): text to parse

    Returns:
        str: Parsed text
    """
    console = Console()

    with console.capture() as capture:
        console.print(text)

    return capture.get()
