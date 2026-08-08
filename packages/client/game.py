"""Client state."""

from packages.client.input import Input
from packages.shared.cards import Card
from packages.shared.game import CombatStep, Game, GamePhase, State
from packages.shared.pdu import PDU
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
        self.__library_count = library_count

    @property
    def library_count(self):
        """Player library count.

        Returns:
            int: Player library count
        """
        return self.__library_count


class CurrentClientPlayer(ClientPlayer):
    """Current player."""

    def __init__(self, id: PlayerID, library_count: int) -> None:  # noqa: D107
        super().__init__(id, library_count)
        self.__hand: set[Card] = set()

    @property
    def hand(self):
        """Player hand.

        Returns:
            set[Card]: Player hand.
        """
        return self.__hand


class OpponentClientPlayer(ClientPlayer):
    """Opponent player."""

    def __init__(self, id: PlayerID, library_count: int) -> None:  # noqa: D107
        super().__init__(id, library_count)
        self.__hand_count = 0

    @property
    def hand_count(self):
        """Player hand count.

        Returns:
            set[Card]: Player hand count.
        """
        return self.__hand_count


class ClientGame(Game):
    """Client-side game."""

    def __init__(self) -> None:
        """Creates a client game instance."""
        super().__init__()
        self.__input = Input()

    @property
    def input(self):
        """Get game input."""
        return self.__input

    def run(self, pdu: PDU):
        """Run on receive.

        Args:
            pdu (PDU): PDU received

        Returns:
            PDU: PDUs to send
        """
        match self.state:
            case State.LOBBY:
                return self.__lobby(pdu)
            case State.GAME_SETUP:
                return self.__game_setup(pdu)
            case State.MULLIGAN:
                return self.__mulligan(pdu)
            case GamePhase.UNTAP:
                return self.__untap(pdu)
            case GamePhase.UPKEEP:
                return self.__upkeep(pdu)
            case GamePhase.DRAW:
                return self.__draw(pdu)
            case GamePhase.PRECOMBAT_MAIN:
                return self.__precombat_main(pdu)
            case CombatStep.BEGIN_COMBAT:
                return self.__begin_combat(pdu)
            case CombatStep.DECLARE_ATTACKERS:
                return self.__declare_attackers(pdu)
            case CombatStep.DECLARE_BLOCKERS:
                return self.__declare_blockers(pdu)
            case CombatStep.ASSIGN_DAMAGE_ORDER:
                return self.__assign_damage_order(pdu)
            case CombatStep.FIRST_STRIKE_DAMAGE:
                return self.__first_strike_damage(pdu)
            case CombatStep.COMBAT_DAMAGE:
                return self.__combat_damage(pdu)
            case CombatStep.END_OF_COMBAT:
                return self.__end_of_combat(pdu)
            case GamePhase.POSTCOMBAT_MAIN:
                return self.__postcombat_main(pdu)
            case GamePhase.END_STEP:
                return self.__end_step(pdu)
            case GamePhase.CLEANUP:
                return self.__cleanup(pdu)
            case State.GAME_OVER:
                return self.__game_over(pdu)

    def ready(self):
        """Initial player ready prompt."""
        raise NotImplementedError

    def __lobby(self, pdu: PDU):
        raise NotImplementedError

    def __game_setup(self, pdu: PDU):
        raise NotImplementedError

    def __mulligan(self, pdu: PDU):
        raise NotImplementedError

    def __game_over(self, pdu: PDU):
        raise NotImplementedError

    def __untap(self, pdu: PDU):
        raise NotImplementedError

    def __upkeep(self, pdu: PDU):
        raise NotImplementedError

    def __draw(self, pdu: PDU):
        raise NotImplementedError

    def __precombat_main(self, pdu: PDU):
        raise NotImplementedError

    def __postcombat_main(self, pdu: PDU):
        raise NotImplementedError

    def __end_step(self, pdu: PDU):
        raise NotImplementedError

    def __cleanup(self, pdu: PDU):
        raise NotImplementedError

    def __begin_combat(self, pdu: PDU):
        raise NotImplementedError

    def __declare_attackers(self, pdu: PDU):
        raise NotImplementedError

    def __declare_blockers(self, pdu: PDU):
        raise NotImplementedError

    def __assign_damage_order(self, pdu: PDU):
        raise NotImplementedError

    def __first_strike_damage(self, pdu: PDU):
        raise NotImplementedError

    def __combat_damage(self, pdu: PDU):
        raise NotImplementedError

    def __end_of_combat(self, pdu: PDU):
        raise NotImplementedError
