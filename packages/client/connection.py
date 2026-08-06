"""Client connection module."""

from collections.abc import Callable
from socket import AF_INET, SOCK_STREAM, socket
from struct import pack

from packages.shared.connection import HOST, PORT, send, recv
from packages.shared.pdu import PDU, PlayerReady
from packages.shared.player import Player


def connect(run: Callable[[PDU], PDU | None], verbose=False):
    """TCP Connection.

    Args:
        run (Callable[[PDU], dict[Player, PDU]]): Function to run when :class:`PDU` is received
        verbose (bool, optional): Verbose mode. Defaults to False.
    """
    with socket(AF_INET, SOCK_STREAM) as client_socket:
        client_socket.connect((HOST, PORT))
        print("Connected to", HOST, PORT)

        send(
            PlayerReady(seq_num=1, player_id=Player("4"), deck_list=set([])),
            client_socket,
            verbose,
        )

        while True:
            payload = run(recv(client_socket, verbose))

            if payload:
                send(payload, client_socket, verbose)
