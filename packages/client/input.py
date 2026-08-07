"""Async user input."""

from asyncio import Event, Future, Queue, create_task, get_running_loop
from collections.abc import Callable
from typing import Any, Sequence

from prompt_toolkit import PromptSession

from packages.shared.pdu import PDU


class Input(object):
    """Async input."""

    def __init__(self):
        """Creates a new input session."""
        self.__session = PromptSession()
        self.__event = Event()

    @property
    def active(self):
        """`True` if there is currently an active input.

        Returns:
            bool: Active input
        """
        try:
            return bool(self.__task)
        except AttributeError:
            return False

    def prompt(self, prompts: list[str], parse: Callable[[list[str]], Sequence[PDU]]):
        """Starts an async prompt task in the background.

        Args:
            prompts (str, optional): Text to display
            parse (Callable[[str], PDU]): Parsing function to send PDU
        """
        self.interrupt()

        self.__prompts = prompts
        self.__parse = parse
        self.__task = create_task(self.__prompt_worker())

    async def __prompt_worker(self):
        result = []

        for prompt in self.__prompts:
            result.append(await self.__session.prompt_async(prompt))

        self.__result = self.__parse(result)

    def interrupt(self):
        """Immediately cancels and erases the active prompt."""
        try:
            if self.__task and not self.__task.done():
                self.__task.cancel()
                self.__task = None
        except AttributeError:
            pass

    async def subscribe(self):
        """Yields user inputs as they are completed."""
        while True:
            await self.__event.wait()
            yield self.__result
            self.__event.clear()
