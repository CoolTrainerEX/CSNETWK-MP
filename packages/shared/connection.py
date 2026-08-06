"""Connection module."""

from socket import socket
from struct import pack, unpack

from packages.shared.pdu import PDUValidator, PDU


HOST = ""
PORT = 4444


def send(pdu: PDU, socket_instance: socket, verbose=False):
    """Send a :class:`PDU`.

    Args:
        pdu (PDU): PDU to send
        socket_instance (socket): Connection to send in
        verbose (bool, optional): Verbose mode. Defaults to False.
    """
    payload = pdu.model_dump_json()

    socket_instance.sendall(pack(">I", len(payload)) + payload.encode())

    if verbose:
        print("Sent:", payload)


def recv(socket_instance: socket, verbose=False) -> PDU:
    """Receive a :class:`PDU`.

    Args:
        socket_instance (socket): Connection to receive in.
        verbose (bool, optional): Verbode mode. Defaults to False.

    Returns:
        PDU: PDU received
    """
    payload = PDUValidator.validate_json(
        socket_instance.recv(unpack(">I", socket_instance.recv(4))[0]).decode()
    )

    if verbose:
        print("Received:", payload)

    return payload
