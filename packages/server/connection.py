"""Server connection module."""

from asyncio import (
    IncompleteReadError,
    Semaphore,
    StreamReader,
    StreamWriter,
    start_server,
    timeout,
)

from packages.server.state import disconnect, run
from packages.shared.connection import HOST, PORT, read, write
from packages.shared.pdu import PDU, Pong, Type
from packages.shared.player import PlayerID

semaphore = Semaphore(2)
writers: dict[PlayerID, StreamWriter] = {}
readers: dict[StreamReader, PlayerID] = {}


async def connect(verbose=False):
    """TCP Connection.

    Args:
        verbose (bool, optional): Verbose mode. Defaults to False.
    """

    async def handle(reader: StreamReader, writer: StreamWriter):
        if not semaphore.locked():
            async with semaphore:
                print(writer.get_extra_info("peername"), "Connected")
                try:
                    time_limit = None

                    while True:
                        if time_limit:
                            async with timeout(time_limit / 1000.0):
                                req = await read(reader, verbose)
                        else:
                            req = await read(reader, verbose)

                        if req.type == Type.PING:
                            await write(
                                Pong(seq_num=req.seq_num, timestamp=req.timestamp),
                                writer,
                                verbose,
                            )
                        else:
                            if req.type == Type.PLAYER_READY:
                                readers[reader] = req.player_id
                                writers[req.player_id] = writer

                            for player, payload in run(req, readers[reader]).items():
                                for pdu in payload:
                                    if pdu.type == Type.PRIORITY_GRANT:
                                        time_limit = pdu.time_limit_ms

                                    await write(pdu, writers[player], verbose)
                except TimeoutError, IncompleteReadError, ConnectionResetError:
                    if reader in readers:
                        for player, payload in disconnect(readers[reader]).items():
                            for pdu in payload:
                                await write(pdu, writers[player], verbose)

                        del writers[readers[reader]]
                        del readers[reader]
        print(writer.get_extra_info("peername"), "Disconnected")
        writer.close()
        await writer.wait_closed()

    async with await start_server(handle, HOST, PORT) as server:
        print("Listening to", HOST, PORT)
        await server.serve_forever()
