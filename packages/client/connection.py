"""Client connection module."""

from asyncio import IncompleteReadError, TaskGroup, open_connection, sleep
from time import time

from packages.client.game import ClientGame
from packages.shared.connection import HOST, PORT, write, read
from packages.shared.pdu import Ping, Type

PING_INTERVAL = 30
PING_TIMEOUT = 10

assert PING_INTERVAL > PING_TIMEOUT


class ClientConnection(object):
    """Client TCP Connection."""

    def __init__(self, game: ClientGame, verbose=False):
        """TCP Connection.

        Args:
            game (ClientGame): Game to run
            verbose (bool, optional): Verbose mode. Defaults to False.
        """
        self.__game = game
        self.__verbose = verbose
        self.__pong = False

    async def connect(self):
        """Connect the client."""
        try:
            self.__reader, self.__writer = await open_connection(HOST, PORT)

            print("Connected to", HOST, PORT)

            async with TaskGroup() as tg:
                tg.create_task(self.__handle_write())
                tg.create_task(self.__ping())
                tg.create_task(self.__handle_read())
        except* (
            IncompleteReadError,
            ConnectionRefusedError,
            ConnectionResetError,
            BrokenPipeError,
        ):
            # Disconnect
            pass

        try:
            self.__writer.close()
            await self.__writer.wait_closed()
        except AttributeError:
            pass

    async def __handle_read(self):
        self.__game.ready()

        while True:
            res = await read(self.__reader, self.__verbose)

            if res.type == Type.PONG:
                self.__pong = True
            else:
                self.__game.run(res)

    async def __handle_write(self):
        while True:
            async for payload in self.__game.input.subscribe():
                for pdu in payload:
                    await write(pdu, self.__writer, self.__verbose)

    async def __ping(self):
        seq_num = 1

        while True:
            self.__pong = False
            await write(
                Ping(seq_num=seq_num, timestamp=time()), self.__writer, self.__verbose
            )
            seq_num += 1
            await sleep(PING_TIMEOUT)

            if not self.__pong:
                print("Timeout")
                self.__writer.close()
                break

            await sleep(PING_INTERVAL - PING_TIMEOUT)
