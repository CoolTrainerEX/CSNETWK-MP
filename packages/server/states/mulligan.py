"""Mulligan state handler."""

from typing import TYPE_CHECKING
from packages.shared.pdu import PDU, MulliganChoice, Error, Type
from packages.shared.player import PlayerID

if TYPE_CHECKING:
    from packages.server.game import ServerGame


def handle_mulligan(
    game: "ServerGame", pdu: PDU, player: PlayerID
) -> dict[PlayerID, list[PDU]]:
    result: dict[PlayerID, list[PDU]] = {p.id: [] for p in game._players}
    player_obj = game._player_map.get(player)

    if pdu.type != Type.MULLIGAN_CHOICE:
        result[player].append(
            game._make_error(Error.Code.WRONG_PHASE, "Expecting MULLIGAN_CHOICE.", pdu)
        )
        return result

    if game._mulligan_done.get(player, False):
        return result  # already decided; ignore

    mc: MulliganChoice = pdu
    expected = game._mulligan_gsu_seq.get(player, 0)
    if mc.seq_num != expected:
        result[player].append(
            game._make_error(
                Error.Code.STALE_ACTION, f"Stale. Expected {expected}.", pdu
            )
        )
        return result

    if not mc.keep:
        # Take mulligan
        game._mulligan_counts[player] = game._mulligan_counts.get(player, 0) + 1
        player_obj.return_hand_to_library()
        for _ in range(7):
            player_obj.draw_card()
        game._seq_num += 1
        game._mulligan_gsu_seq[player] = game._seq_num
        result[player].append(game._build_game_gsu(player_obj))
    else:
        # Keep hand
        count = game._mulligan_counts.get(player, 0)
        if len(mc.cards_to_bottom) != count:
            result[player].append(
                game._make_error(
                    Error.Code.ILLEGAL_ACTION,
                    f"Must bottom exactly {count} card(s).",
                    pdu,
                )
            )
            return result
        for cid in mc.cards_to_bottom:
            if not player_obj.card_in_hand(cid):
                result[player].append(
                    game._make_error(
                        Error.Code.ILLEGAL_ACTION, f"Card {cid} not in hand.", pdu
                    )
                )
                return result

        player_obj.bottom_cards(mc.cards_to_bottom)
        game._mulligan_done[player] = True
        game._seq_num += 1
        result[player].append(game._build_game_gsu(player_obj))

        if all(game._mulligan_done.get(p.id, False) for p in game._players):
            for pid, pdus in game._begin_game().items():
                result.setdefault(pid, []).extend(pdus)

    return result
