"""Server connection module."""

from collections.abc import Callable

from packages.shared.pdu import PDU, PlayerReady
from packages.shared.player import Player


def connect(run: Callable[[PDU], dict[Player, PDU]], verbose=False):
    """TCP Connection.

    Args:
        run (Callable[[PDU], dict[Player, PDU]]): Function to run when :class:`PDU` is received
        verbose (bool, optional): Verbose mode. Defaults to False.
    """
    req_pdu = PlayerReady(seq_num=1, player_id=Player("4"), deck_list=set([]))

    if verbose:
        print(req_pdu)

    res_pdu = run(req_pdu)

    for player, pdu in res_pdu.items():
        data = pdu.model_dump_json()

        if verbose:
            print(player, data)
