"""Async user input."""

from asyncio import CancelledError, Queue, Task, create_task

from prompt_toolkit import PromptSession


class Input(object):
    """Async input."""

    def __init__(self):
        self.__session = PromptSession()
        self.__queue: Queue[str] = Queue()
        self.__prompt_task: Task | None = None

    def start_prompt(self, prompt_text: str = "<> "):
        """Starts an async prompt task in the background.

        Args:
            prompt_text (str, optional): Text to display. Defaults to "<> ".
        """
        if self.__prompt_task and not self.__prompt_task.done():
            return  # Already prompting

        async def prompt_worker():
            try:
                # Prompt runs natively on the asyncio event loop
                user_str = await self.__session.prompt_async(prompt_text)
                await self.__queue.put(user_str)
            except CancelledError, KeyboardInterrupt:
                pass

        self.__prompt_task = create_task(prompt_worker())

    def interrupt(self):
        """Immediately cancels and erases the active prompt."""
        if self.__prompt_task and not self.__prompt_task.done():
            self.__prompt_task.cancel()
            self.__prompt_task = None

    async def subscribe(self):
        """Yields user inputs as they are completed."""
        while True:
            val = await self.__queue.get()
            yield val
            self.__queue.task_done()
