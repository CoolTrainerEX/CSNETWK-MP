"""Server state."""

from packages.shared.game import CombatStep, Game, GamePhase, State
from packages.shared.pdu import PDU
from packages.shared.player import PlayerID

game = Game()


def run(pdu: PDU, player: PlayerID) -> dict[PlayerID, list[PDU]]:
    """Run on receive.

    Args:
        pdu (PDU): PDU received
        player (PlayerID): Player who sent

    Returns:
        dict[PlayerID, list[PDU]]: PDUs to send
    """
    match game.state:
        case State.LOBBY:
            return lobby(pdu, player)
        case State.GAME_SETUP:
            return game_setup(pdu, player)
        case State.MULLIGAN:
            return mulligan(pdu, player)
        case GamePhase.UNTAP:
            return untap(pdu, player)
        case GamePhase.UPKEEP:
            return upkeep(pdu, player)
        case GamePhase.DRAW:
            return draw(pdu, player)
        case GamePhase.PRECOMBAT_MAIN:
            return precombat_main(pdu, player)
        case CombatStep.BEGIN_COMBAT:
            return begin_combat(pdu, player)
        case CombatStep.DECLARE_ATTACKERS:
            return declare_attackers(pdu, player)
        case CombatStep.DECLARE_BLOCKERS:
            return declare_blockers(pdu, player)
        case CombatStep.ASSIGN_DAMAGE_ORDER:
            return assign_damage_order(pdu, player)
        case CombatStep.FIRST_STRIKE_DAMAGE:
            return first_strike_damage(pdu, player)
        case CombatStep.COMBAT_DAMAGE:
            return combat_damage(pdu, player)
        case CombatStep.END_OF_COMBAT:
            return end_of_combat(pdu, player)
        case GamePhase.POSTCOMBAT_MAIN:
            return postcombat_main(pdu, player)
        case GamePhase.END_STEP:
            return end_step(pdu, player)
        case GamePhase.CLEANUP:
            return cleanup(pdu, player)
        case State.GAME_OVER:
            return game_over(pdu, player)


def disconnect(player: PlayerID) -> dict[PlayerID, list[PDU]]:
    """Player disconnected.

    Args:
        player (PlayerID): PLayer who disconnected

    Returns:
        dict[PlayerID, list[PDU]]: PDUs to send
    """
    raise NotImplementedError


def lobby(pdu: PDU, player: PlayerID) -> dict[PlayerID, list[PDU]]:
    """Lobby state.

    Args:
        pdu (PDU): PDU received
        player (PlayerID): Player who sent

    Returns:
        dict[PlayerID, list[PDU]]: PDUs to send
    """
    raise NotImplementedError


def game_setup(pdu: PDU, player: PlayerID) -> dict[PlayerID, list[PDU]]:
    """Game Setup state.

    Args:
        pdu (PDU): PDU received
        player (Player): Player who sent

    Returns:
        dict[PlayerID, list[PDU]]: PDUs to send
    """
    raise NotImplementedError


def mulligan(pdu: PDU, player: PlayerID) -> dict[PlayerID, list[PDU]]:
    """Mulligan state.

    Args:
        pdu (PDU): PDU received
        player (Player): Player who sent

    Returns:
        dict[PlayerID, list[PDU]]: PDUs to send
    """
    raise NotImplementedError


def game_over(pdu: PDU, player: PlayerID) -> dict[PlayerID, list[PDU]]:
    """Game Over State.

    Args:
        pdu (PDU): PDU received
        player (Player): Player who sent

    Returns:
        dict[PlayerID, list[PDU]]: PDUs to send
    """
    raise NotImplementedError


def untap(pdu: PDU, player: PlayerID) -> dict[PlayerID, list[PDU]]:
    """In-Game Untap Phase.

    Args:
        pdu (PDU): PDU received
        player (Player): Player who sent

    Returns:
        dict[PlayerID, list[PDU]]: PDUs to send
    """
    raise NotImplementedError


def upkeep(pdu: PDU, player: PlayerID) -> dict[PlayerID, list[PDU]]:
    """In-Game Upkeep Phase.

    Args:
        pdu (PDU): PDU received
        player (Player): Player who sent

    Returns:
        dict[PlayerID, list[PDU]]: PDUs to send
    """
    raise NotImplementedError


def draw(pdu: PDU, player: PlayerID) -> dict[PlayerID, list[PDU]]:
    """In-Game Draw Phase.

    Args:
        pdu (PDU): PDU received
        player (Player): Player who sent

    Returns:
        dict[PlayerID, list[PDU]]: PDUs to send
    """
    raise NotImplementedError


def precombat_main(pdu: PDU, player: PlayerID) -> dict[PlayerID, list[PDU]]:
    """In-Game Precombat Main Phase.

    Args:
        pdu (PDU): PDU received
        player (Player): Player who sent

    Returns:
        dict[PlayerID, list[PDU]]: PDUs to send
    """
    raise NotImplementedError


def postcombat_main(pdu: PDU, player: PlayerID) -> dict[PlayerID, list[PDU]]:
    """In-Game Postcombat Main Phase.

    Args:
        pdu (PDU): PDU received
        player (Player): Player who sent

    Returns:
        dict[PlayerID, list[PDU]]: PDUs to send
    """
    raise NotImplementedError


def end_step(pdu: PDU, player: PlayerID) -> dict[PlayerID, list[PDU]]:
    """In-Game End Step Phase.

    Args:
        pdu (PDU): PDU received
        player (Player): Player who sent

    Returns:
        dict[PlayerID, list[PDU]]: PDUs to send
    """
    raise NotImplementedError


def cleanup(pdu: PDU, player: PlayerID) -> dict[PlayerID, list[PDU]]:
    """In-Game Cleanup Phase.

    Args:
        pdu (PDU): PDU received
        player (Player): Player who sent

    Returns:
        dict[PlayerID, list[PDU]]: PDUs to send
    """
    raise NotImplementedError


def begin_combat(pdu: PDU, player: PlayerID) -> dict[PlayerID, list[PDU]]:
    """Combat Begin Combat Step.

    Args:
        pdu (PDU): PDU received
        player (Player): Player who sent

    Returns:
        dict[PlayerID, list[PDU]]: PDUs to send
    """
    raise NotImplementedError


def declare_attackers(pdu: PDU, player: PlayerID) -> dict[PlayerID, list[PDU]]:
    """Combat Declare Attackers Step.

    Args:
        pdu (PDU): PDU received
        player (Player): Player who sent

    Returns:
        dict[PlayerID, list[PDU]]: PDUs to send
    """
    raise NotImplementedError


def declare_blockers(pdu: PDU, player: PlayerID) -> dict[PlayerID, list[PDU]]:
    """Combat Declare Blockers Step.

    Args:
        pdu (PDU): PDU received
        player (Player): Player who sent

    Returns:
        dict[PlayerID, list[PDU]]: PDUs to send
    """
    raise NotImplementedError


def assign_damage_order(pdu: PDU, player: PlayerID) -> dict[PlayerID, list[PDU]]:
    """Combat Assign Damage Order Step.

    Args:
        pdu (PDU): PDU received
        player (Player): Player who sent

    Returns:
        dict[PlayerID, list[PDU]]: PDUs to send
    """
    raise NotImplementedError


def first_strike_damage(pdu: PDU, player: PlayerID) -> dict[PlayerID, list[PDU]]:
    """Combat First Strike Damage Step.

    Args:
        pdu (PDU): PDU received
        player (Player): Player who sent

    Returns:
        dict[PlayerID, list[PDU]]: PDUs to send
    """
    raise NotImplementedError


def combat_damage(pdu: PDU, player: PlayerID) -> dict[PlayerID, list[PDU]]:
    """Combat Damage Step.

    Args:
        pdu (PDU): PDU received
        player (Player): Player who sent

    Returns:
        dict[PlayerID, list[PDU]]: PDUs to send
    """
    raise NotImplementedError


def end_of_combat(pdu: PDU, player: PlayerID) -> dict[PlayerID, list[PDU]]:
    """Combat End of Combat Step.

    Args:
        pdu (PDU): PDU received
        player (Player): Player who sent

    Returns:
        dict[PlayerID, list[PDU]]: PDUs to send
    """
    raise NotImplementedError
