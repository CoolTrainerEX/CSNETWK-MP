"""Client state."""

from packages.client.input import Input
from packages.shared.cards import Card
from packages.shared.game import CombatStep, Game, GamePhase, State
from packages.shared.pdu import PDU, Type
from packages.shared.player import Player, PlayerID


class ClientPlayer(Player):
    """Client player view."""

    def __init__(self, id: PlayerID, library_count: int) -> None:
        """Creates a client player.

        Args:
            id (PlayerID): Player ID
            library_count (int): Library count
        """
        super().__init__(id)
        self._library_count = library_count
        self._life_total = 20
        self._battlefield = set()
        self._graveyard = set()

    @property
    def library_count(self):
        """Player library count.

        Returns:
            int: Player library count
        """
        return self._library_count

    @library_count.setter
    def library_count(self, value):
        self._library_count = value

    @property
    def life_total(self):
        """Player life total."""
        return self._life_total

    @life_total.setter
    def life_total(self, value):
        self._life_total = value

    @property
    def battlefield(self):
        """Player battlefield."""
        return self._battlefield

    @battlefield.setter
    def battlefield(self, value):
        self._battlefield = value

    @property
    def graveyard(self):
        """Player graveyard."""
        return self._graveyard

    @graveyard.setter
    def graveyard(self, value):
        self._graveyard = value


class CurrentClientPlayer(ClientPlayer):
    """Current player."""

    def __init__(self, id: PlayerID, library_count: int) -> None:  # noqa: D107
        super().__init__(id, library_count)
        self._hand: set[Card] = set()

    @property
    def hand(self):
        """Player hand.

        Returns:
            set[Card]: Player hand.
        """
        return self._hand

    @hand.setter
    def hand(self, value):
        self._hand = value


class OpponentClientPlayer(ClientPlayer):
    """Opponent player."""

    def __init__(self, id: PlayerID, library_count: int) -> None:  # noqa: D107
        super().__init__(id, library_count)
        self._hand_count = 0

    @property
    def hand_count(self):
        """Player hand count.

        Returns:
            int: Player hand count.
        """
        return self._hand_count

    @hand_count.setter
    def hand_count(self, value):
        self._hand_count = value


class ClientGame(Game):
    """Client-side game."""

    def __init__(self) -> None:
        """Creates a client game instance."""
        super().__init__()
        self.__input = Input()

        # state tracking
        self.game_state_data = None
        self.priority_player = None
        self.priority_seq_num = 0
        self.time_limit_ms = 0
        self.stack = []
        self.error_msg = None
        self.active_player = None
        self.turn = 0
        self.game_over_data = None
        self.last_combat_result = None
        self.pending_trigger_order = None
        self.pending_trigger_choice = None

    @property
    def input(self):
        """Get game input."""
        return self.__input

    def _parse_phase(self, phase_value: str):
        for enum_type in (State, GamePhase, CombatStep):
            try:
                return enum_type(phase_value)
            except ValueError:
                continue

        return None

    def run(self, pdu: PDU):
        """Run on receive.

        Args:
            pdu (PDU): PDU received
        """
        if hasattr(pdu, "seq_num"):
            self._seq_num = pdu.seq_num

        match pdu.type:
            case Type.GAME_STATE_UPDATE:
                self.game_state_data = pdu.state

                if hasattr(pdu.state, "phase"):
                    parsed_phase = self._parse_phase(pdu.state.phase)

                    if parsed_phase:
                        self.state = parsed_phase

                if hasattr(pdu.state, "active_player"):
                    self.active_player = pdu.state.active_player

                if hasattr(pdu.state, "turn"):
                    self.turn = pdu.state.turn

                if hasattr(pdu.state, "stack"):
                    self.stack = pdu.state.stack

                self._update_players(pdu.state)

            case Type.PHASE_TRANSITION:
                parsed_phase = self._parse_phase(pdu.to_phase)

                if parsed_phase:
                    self.state = parsed_phase

                self.active_player = pdu.active_player
                self.turn = pdu.turn

            case Type.PRIORITY_GRANT:
                self.priority_player = pdu.player_id
                self.priority_seq_num = pdu.seq_num
                self.time_limit_ms = pdu.time_limit_ms

            case Type.STACK_PUSH:
                self.stack.append(pdu)

            case Type.STACK_RESOLVE:
                self.stack = [
                    item
                    for item in self.stack
                    if getattr(item, "stack_item_id", None) != pdu.stack_item_id
                ]

            case Type.GAME_OVER:
                self.state = State.GAME_OVER
                self.game_over_data = pdu

            case Type.ERROR:
                self.error_msg = pdu.message

            case Type.COMBAT_DAMAGE_RESULT:
                self.last_combat_result = pdu

            case Type.TRIGGER_ORDER:
                self.pending_trigger_order = pdu

            case Type.TRIGGER_CHOICE:
                self.pending_trigger_choice = pdu

    def ready(self):
        """Initial player ready prompt."""
        pass

    def _update_players(self, state):
        if not hasattr(state, "life_totals"):
            return  # lobby state

        our_id = None
        opponent_id = None

        for pid in getattr(state, "hand", {}).keys():
            our_id = pid

        for pid in getattr(state, "hand_counts", {}).keys():
            if pid != our_id:
                opponent_id = pid

        if not self._players and our_id and opponent_id:
            self._players = [
                CurrentClientPlayer(our_id, state.library_counts.get(our_id, 0)),
                OpponentClientPlayer(
                    opponent_id, state.library_counts.get(opponent_id, 0)
                ),
            ]

        for p in self._players:
            if isinstance(p, CurrentClientPlayer) and p.id == our_id:
                p.life_total = state.life_totals.get(our_id, p.life_total)
                p.graveyard = state.graveyard.get(our_id, p.graveyard)
                p.hand = state.hand.get(our_id, p.hand)
                p.library_count = state.library_counts.get(our_id, p.library_count)
                p.battlefield = state.battlefield.get(our_id, p.battlefield)
            elif isinstance(p, OpponentClientPlayer) and p.id == opponent_id:
                p.life_total = state.life_totals.get(opponent_id, p.life_total)
                p.graveyard = state.graveyard.get(opponent_id, p.graveyard)
                p.hand_count = state.hand_counts.get(opponent_id, p.hand_count)
                p.library_count = state.library_counts.get(opponent_id, p.library_count)
                p.battlefield = state.battlefield.get(opponent_id, p.battlefield)
