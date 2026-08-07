"""Connection module."""

from asyncio import StreamReader, StreamWriter
from struct import pack, unpack

from packages.shared.pdu import PDUValidator, PDU


HOST = "localhost"
PORT = 4444


async def write(pdu: PDU, writer: StreamWriter, verbose=False):
    """Send a :class:`PDU`.

    Args:
        pdu (PDU): PDU to send
        writer (StreamWriter): Connection to send in
        verbose (bool, optional): Verbose mode. Defaults to False.
    """
    payload = pdu.model_dump_json()

    writer.write(pack(">I", len(payload)) + payload.encode())
    await writer.drain()

    if verbose:
        print("Sent:", payload)


async def read(reader: StreamReader, verbose=False) -> PDU:
    """Receive a :class:`PDU`.

    Args:
        reader (StreamReader): Connection to receive in.
        verbose (bool, optional): Verbode mode. Defaults to False.

    Returns:
        PDU: PDU received
    """
    payload = (
        await reader.readexactly(unpack(">I", await reader.readexactly(4))[0])
    ).decode()

    if verbose:
        print("Received:", payload)

    return PDUValidator.validate_json(payload)
