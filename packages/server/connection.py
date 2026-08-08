"""Server connection module."""

from asyncio import (
    IncompleteReadError,
    Semaphore,
    StreamReader,
    StreamWriter,
    start_server,
    timeout,
)

from packages.server.game import ServerGame
from packages.shared.connection import HOST, PORT, read, write
from packages.shared.pdu import Pong, Type
from packages.shared.player import PlayerID


class ServerConnection(object):
    """Server TCP connection."""

    def __init__(self, game: ServerGame, verbose=False):
        """TCP Connection.

        Args:
            game (ServerGame): Game to run
            verbose (bool, optional): Verbose mode. Defaults to False.
        """
        self.__game = game
        self.__verbose = verbose
        self.__semaphore = Semaphore(2)
        self.__writers: dict[PlayerID, StreamWriter] = {}
        self.__readers: dict[StreamReader, PlayerID] = {}

    async def run(self):
        """Run the server."""
        async with await start_server(self.__handle, HOST, PORT) as server:
            print("Listening to", HOST, PORT)
            await server.serve_forever()

    async def __handle(self, reader: StreamReader, writer: StreamWriter):
        if not self.__semaphore.locked():
            async with self.__semaphore:
                print(writer.get_extra_info("peername"), "Connected")

                try:
                    time_limit = None

                    while True:
                        if time_limit:
                            async with timeout(time_limit / 1000.0):
                                req = await read(reader, self.__verbose)
                        else:
                            req = await read(reader, self.__verbose)

                        if req.type == Type.PING:
                            await write(
                                Pong(seq_num=req.seq_num, timestamp=req.timestamp),
                                writer,
                                self.__verbose,
                            )
                        else:
                            if req.type == Type.PLAYER_READY:
                                self.__readers[reader] = req.player_id
                                self.__writers[req.player_id] = writer

                            for player, payload in self.__game.run(
                                req, self.__readers[reader]
                            ).items():
                                for pdu in payload:
                                    if pdu.type == Type.PRIORITY_GRANT:
                                        time_limit = pdu.time_limit_ms

                                    await write(
                                        pdu, self.__writers[player], self.__verbose
                                    )
                except (TimeoutError, IncompleteReadError, ConnectionResetError):
                    if reader in self.__readers:
                        for player, payload in self.__game.disconnect(
                            self.__readers[reader]
                        ).items():
                            for pdu in payload:
                                await write(pdu, self.__writers[player], self.__verbose)

                        del self.__writers[self.__readers[reader]]
                        del self.__readers[reader]

                print(writer.get_extra_info("peername"), "Disconnected")

        writer.close()
        await writer.wait_closed()
