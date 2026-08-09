"""Utilities mixin for ServerGame."""

from typing import TYPE_CHECKING

from packages.shared.pdu import State
from packages.shared.player import PlayerID
from packages.shared.cards import CardID

if TYPE_CHECKING:
    from packages.server.game import ServerGame, ServerPlayer


class UtilitiesMixin:
    """Provides internal utility helpers for ServerGame."""

    def _ap(self: "ServerGame") -> "ServerPlayer":
        return self._players[self._active_player_idx]

    def _nap(self: "ServerGame") -> "ServerPlayer":
        return self._players[1 - self._active_player_idx]

    def _opponent_of(self: "ServerGame", player: "ServerPlayer") -> "ServerPlayer":
        return self._players[1 - self._players.index(player)]

    def _opponent_of_id(
        self: "ServerGame", player_id: PlayerID
    ) -> "ServerPlayer | None":
        return next((p for p in self._players if p.id != player_id), None)

    def _pump_bonuses(self: "ServerGame", card_id: CardID) -> tuple[int, int]:
        """Return (power_bonus, toughness_bonus) from active EOT pumps."""
        pb = sum(e.power_bonus for e in self._eot_pumps if e.card_id == card_id)
        tb = sum(e.toughness_bonus for e in self._eot_pumps if e.card_id == card_id)
        return pb, tb

    def _reset_to_lobby(self: "ServerGame") -> None:
        """Reset all game state and return to LOBBY."""
        self._players.clear()
        self._player_map.clear()
        self._stack.clear()
        self._stack_counter = 0
        self._active_player_idx = 0
        self._first_player_idx = 0
        self._turn = 0
        self._is_first_turn = True
        self._priority_holder_idx = None
        self._priority_seq_num = 0
        self._consecutive_passes = 0
        self._land_played_this_turn = False
        self._attackers.clear()
        self._blockers.clear()
        self._damage_order.clear()
        self._pending_damage_orders.clear()
        self._eot_pumps.clear()
        self._discard_player = None
        self._discard_gsu_seq = 0
        self._mulligan_counts.clear()
        self._mulligan_done.clear()
        self._mulligan_gsu_seq.clear()
        self._declare_attackers_seq_num = 0
        self._declare_blockers_seq_num = 0
        self._assign_damage_order_seq_num = 0
        self._seq_num = 0
        self.state = State.LOBBY
