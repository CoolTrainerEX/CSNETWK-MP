"""Server state."""

from packages.shared.game import CombatStep, Game, GamePhase, State
from packages.shared.pdu import PDU
from packages.shared.player import PlayerID


class ServerGame(Game):
    """Server-side game."""

    def run(self, pdu: PDU, player: PlayerID) -> dict[PlayerID, list[PDU]]:
        """Run on receive.

        Args:
            pdu (PDU): PDU received
            player (PlayerID): Player who sent

        Returns:
            dict[PlayerID, list[PDU]]: PDUs to send
        """
        match self.state:
            case State.LOBBY:
                return self.__lobby(pdu, player)
            case State.GAME_SETUP:
                return self.__game_setup(pdu, player)
            case State.MULLIGAN:
                return self.__mulligan(pdu, player)
            case GamePhase.UNTAP:
                return self.__untap(pdu, player)
            case GamePhase.UPKEEP:
                return self.__upkeep(pdu, player)
            case GamePhase.DRAW:
                return self.__draw(pdu, player)
            case GamePhase.PRECOMBAT_MAIN:
                return self.__precombat_main(pdu, player)
            case CombatStep.BEGIN_COMBAT:
                return self.__begin_combat(pdu, player)
            case CombatStep.DECLARE_ATTACKERS:
                return self.__declare_attackers(pdu, player)
            case CombatStep.DECLARE_BLOCKERS:
                return self.__declare_blockers(pdu, player)
            case CombatStep.ASSIGN_DAMAGE_ORDER:
                return self.__assign_damage_order(pdu, player)
            case CombatStep.FIRST_STRIKE_DAMAGE:
                return self.__first_strike_damage(pdu, player)
            case CombatStep.COMBAT_DAMAGE:
                return self.__combat_damage(pdu, player)
            case CombatStep.END_OF_COMBAT:
                return self.__end_of_combat(pdu, player)
            case GamePhase.POSTCOMBAT_MAIN:
                return self.__postcombat_main(pdu, player)
            case GamePhase.END_STEP:
                return self.__end_step(pdu, player)
            case GamePhase.CLEANUP:
                return self.__cleanup(pdu, player)
            case State.GAME_OVER:
                return self.__game_over(pdu, player)

    def disconnect(self, player: PlayerID) -> dict[PlayerID, list[PDU]]:
        """Player disconnected.

        Args:
            player (PlayerID): PLayer who disconnected

        Returns:
            dict[PlayerID, list[PDU]]: PDUs to send
        """
        raise NotImplementedError

    def __lobby(self, pdu: PDU, player: PlayerID) -> dict[PlayerID, list[PDU]]:
        raise NotImplementedError

    def __game_setup(self, pdu: PDU, player: PlayerID) -> dict[PlayerID, list[PDU]]:
        raise NotImplementedError

    def __mulligan(self, pdu: PDU, player: PlayerID) -> dict[PlayerID, list[PDU]]:
        raise NotImplementedError

    def __game_over(self, pdu: PDU, player: PlayerID) -> dict[PlayerID, list[PDU]]:
        raise NotImplementedError

    def __untap(self, pdu: PDU, player: PlayerID) -> dict[PlayerID, list[PDU]]:
        raise NotImplementedError

    def __upkeep(self, pdu: PDU, player: PlayerID) -> dict[PlayerID, list[PDU]]:
        raise NotImplementedError

    def __draw(self, pdu: PDU, player: PlayerID) -> dict[PlayerID, list[PDU]]:
        raise NotImplementedError

    def __precombat_main(self, pdu: PDU, player: PlayerID) -> dict[PlayerID, list[PDU]]:
        raise NotImplementedError

    def __postcombat_main(
        self, pdu: PDU, player: PlayerID
    ) -> dict[PlayerID, list[PDU]]:
        raise NotImplementedError

    def __end_step(self, pdu: PDU, player: PlayerID) -> dict[PlayerID, list[PDU]]:
        raise NotImplementedError

    def __cleanup(self, pdu: PDU, player: PlayerID) -> dict[PlayerID, list[PDU]]:
        raise NotImplementedError

    def __begin_combat(self, pdu: PDU, player: PlayerID) -> dict[PlayerID, list[PDU]]:
        raise NotImplementedError

    def __declare_attackers(
        self, pdu: PDU, player: PlayerID
    ) -> dict[PlayerID, list[PDU]]:
        raise NotImplementedError

    def __declare_blockers(
        self, pdu: PDU, player: PlayerID
    ) -> dict[PlayerID, list[PDU]]:
        raise NotImplementedError

    def __assign_damage_order(
        self, pdu: PDU, player: PlayerID
    ) -> dict[PlayerID, list[PDU]]:
        raise NotImplementedError

    def __first_strike_damage(
        self, pdu: PDU, player: PlayerID
    ) -> dict[PlayerID, list[PDU]]:
        raise NotImplementedError

    def __combat_damage(self, pdu: PDU, player: PlayerID) -> dict[PlayerID, list[PDU]]:
        raise NotImplementedError

    def __end_of_combat(self, pdu: PDU, player: PlayerID) -> dict[PlayerID, list[PDU]]:
        raise NotImplementedError
