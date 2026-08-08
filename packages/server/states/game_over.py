"""Game over state handler."""

from typing import TYPE_CHECKING
from packages.shared.pdu import PDU
from packages.shared.player import PlayerID

if TYPE_CHECKING:
    from packages.server.game import ServerGame

def handle_game_over(game: "ServerGame", pdu: PDU, player: PlayerID) -> dict[PlayerID, list[PDU]]:
    # After GAME_OVER the server is back in LOBBY; PDUs are handled there.
    return {}
