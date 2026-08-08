"""Lobby state handler."""

import random
from typing import TYPE_CHECKING

from packages.shared.pdu import PDU, PlayerReady, Error, Type
from packages.shared.player import PlayerID
from packages.shared.cards import Card

if TYPE_CHECKING:
    from packages.server.game import ServerGame

def handle_lobby(game: "ServerGame", pdu: PDU, player: PlayerID) -> dict[PlayerID, list[PDU]]:
    from packages.server.game import ServerPlayer

    result: dict[PlayerID, list[PDU]] = {p.id: [] for p in game._players}
    result.setdefault(player, [])

    if pdu.type != Type.PLAYER_READY:
        result[player].append(
            game._make_error(Error.Code.WRONG_PHASE, "Only PLAYER_READY is accepted in LOBBY.", pdu)
        )
        return result

    pr: PlayerReady = pdu

    # Validate player_id non-empty
    if not pr.player_id:
        result[player].append(
            game._make_error(Error.Code.ILLEGAL_DECK, "player_id must be non-empty.", pdu)
        )
        return result

    # Validate deck
    if not pr.deck_list or len(pr.deck_list) > 50:
        msg = (
            "Deck must have 1–50 cards."
            if not pr.deck_list
            else f"Deck contains {len(pr.deck_list)} cards; maximum is 50."
        )
        result[player].append(game._make_error(Error.Code.ILLEGAL_DECK, msg, pdu))
        return result

    deck_cards: list[Card] = []
    try:
        for cid in pr.deck_list:
            cls = Card.from_id(cid)
            deck_cards.append(cls(cid))
    except (KeyError, ValueError):
        result[player].append(
            game._make_error(Error.Code.ILLEGAL_DECK, "Deck contains an unknown card ID.", pdu)
        )
        return result

    # Check duplicate player_id (claimed by the OTHER connected player)
    existing_other = next(
        (p for p in game._players if p.id == pr.player_id and p.id != player), None
    )
    if existing_other:
        result[player].append(
            game._make_error(Error.Code.DUPLICATE_ID, f"'{pr.player_id}' is already taken.", pdu)
        )
        return result

    # Replace previous submission from this same connection (same player)
    old = next((p for p in game._players if p.id == pr.player_id), None)
    if old:
        game._players.remove(old)
        del game._player_map[pr.player_id]

    # Register player
    random.shuffle(deck_cards)
    sp = ServerPlayer(pr.player_id, deck_cards)
    game._players.append(sp)
    game._player_map[pr.player_id] = sp

    # Broadcast lobby update
    game._seq_num += 1
    lobby_gsu = game._build_lobby_gsu()
    for p in game._players:
        result.setdefault(p.id, []).append(lobby_gsu)

    # Both ready → start game
    if len(game._players) == 2:
        for pid, pdus in game._start_game().items():
            result.setdefault(pid, []).extend(pdus)

    return result
