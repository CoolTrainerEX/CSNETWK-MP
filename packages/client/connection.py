"""Client connection module."""

from collections.abc import Callable

from packages.shared.pdu import PDU, PlayerReady
from packages.shared.player import Player


def connect(run: Callable[[PDU], PDU], verbose=False):
    """TCP Connection.

    Args:
        run (Callable[[PDU], dict[Player, PDU]]): Function to run when :class:`PDU` is received
        verbose (bool, optional): Verbose mode. Defaults to False.
    """
    req_pdu = PlayerReady(seq_num=1, player_id=Player("4"), deck_list=set([]))

    if verbose:
        print(req_pdu)

    res_pdu = run(req_pdu)

    if verbose:
        print(res_pdu)
