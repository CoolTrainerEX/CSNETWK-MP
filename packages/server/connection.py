"""Server connection module."""

from asyncio import Semaphore
from collections.abc import Callable
from socket import AF_INET, SOCK_STREAM, socket
from threading import Thread

from packages.shared.connection import HOST, PORT
from packages.shared.pdu import PDU
from packages.shared.player import Player

semaphore = Semaphore(2)


def connect(run: Callable[[PDU], dict[Player, PDU]], verbose=False):
    """TCP Connection.

    Args:
        run (Callable[[PDU], dict[Player, PDU]]): Function to run when :class:`PDU` is received
        verbose (bool, optional): Verbose mode. Defaults to False.
    """
    with socket(AF_INET, SOCK_STREAM) as server_socket:
        server_socket.bind((HOST, PORT))
        server_socket.listen()
        print("Listening to", HOST, PORT)

        while True:
            with server_socket.accept()[0] as conn:
                if not semaphore.locked():
                    
