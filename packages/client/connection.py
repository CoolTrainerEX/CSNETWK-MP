"""Client connection module."""

from asyncio import open_connection

from packages.client.state import run
from packages.shared.connection import HOST, PORT, write, read
from packages.shared.pdu import PDU, PlayerReady
from packages.shared.player import Player


async def connect(verbose=False):
    """TCP Connection.

    Args:
        verbose (bool, optional): Verbose mode. Defaults to False.
    """
    reader, writer = await open_connection(HOST, PORT)

    print("Connected to", HOST, PORT)

    # await write(
    #     PlayerReady(seq_num=1, player_id="4", deck_list=set({})),
    #     writer,
    #     verbose,
    # )

    while True:
        for pdu in run(await read(reader, verbose)):
            await write(pdu, writer, verbose)
