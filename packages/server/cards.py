"""Server-side card effects."""

from typing import TYPE_CHECKING, Any
from packages.shared.cards import Card
from packages.shared.player import PlayerID
from packages.shared.pdu import StackItem

if TYPE_CHECKING:
    from packages.server.game import ServerPlayer

def validate_targets(
    card: Card,
    targets: set[str],
    player_map: dict[PlayerID, 'ServerPlayer'],
    players: list['ServerPlayer'],
    stack: list[StackItem],
) -> bool:
    """Validate targets for a card cast/activation.
    
    TODO: Implement target validation logic for all cards. 
    This function is called by ServerGame in game.py before putting a spell on the stack.
    """
    return True


def apply_effect(
    card_obj: Card,
    targets: set[str],
    controller: PlayerID,
    is_permanent: bool,
    player_map: dict[PlayerID, 'ServerPlayer'],
    players: list['ServerPlayer'],
    stack: list[StackItem],
    eot_pumps: dict[str, list[tuple[int, int]]],
) -> dict[PlayerID, list[Any]]:
    """Resolve a card's effect or enter-the-battlefield abilities.
    
    TODO: Implement the specific resolution logic for all card effects.
    This function is called by ServerGame in game.py during stack resolution.
    It should return a dict mapping PlayerID to a list of PDUs to send as a result.
    """
    return {p.id: [] for p in players}
