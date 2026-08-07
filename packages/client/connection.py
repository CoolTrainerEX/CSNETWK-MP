"""Client connection module."""

from asyncio import IncompleteReadError, TaskGroup, open_connection, sleep
from time import time

from packages.client.state import run
from packages.shared.connection import HOST, PORT, write, read
from packages.shared.pdu import Ping, Type

PING_INTERVAL = 30
PING_TIMEOUT = 10

assert PING_INTERVAL > PING_TIMEOUT


async def connect(verbose=False):
    """TCP Connection.

    Args:
        verbose (bool, optional): Verbose mode. Defaults to False.
    """
    reader, writer = await open_connection(HOST, PORT)

    print("Connected to", HOST, PORT)

    pong = False

    async def handle():
        nonlocal pong

        while True:
            res = await read(reader, verbose)

            if res.type == Type.PONG:
                pong = True
            else:
                for pdu in run(res):
                    await write(pdu, writer, verbose)

    async def ping():
        nonlocal pong
        seq_num = 1

        while True:
            pong = False
            await write(Ping(seq_num=seq_num, timestamp=time()), writer, verbose)
            seq_num += 1
            await sleep(PING_TIMEOUT)

            if not pong:
                print("Timeout")
                writer.close()
                break

            await sleep(PING_INTERVAL - PING_TIMEOUT)

    try:
        async with TaskGroup() as tg:
            tg.create_task(ping())
            await tg.create_task(handle())
    except* IncompleteReadError:
        # Disconnect
        pass

    writer.close()
    await writer.wait_closed()
