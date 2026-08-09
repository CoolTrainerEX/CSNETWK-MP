"""Game setup state handler."""

from typing import TYPE_CHECKING
from packages.shared.pdu import PDU, Error
from packages.shared.player import PlayerID

if TYPE_CHECKING:
    from packages.server.game import ServerGame


def handle_game_setup(
    game: "ServerGame", pdu: PDU, player: PlayerID
) -> dict[PlayerID, list[PDU]]:
    result: dict[PlayerID, list[PDU]] = {p.id: [] for p in game._players}
    result[player].append(
        game._make_error(Error.Code.WRONG_PHASE, "Game is setting up.", pdu)
    )
    return result
