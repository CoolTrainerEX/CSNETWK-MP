"""Server state."""

from packages.shared.game import CombatStep, Game, GamePhase, State
from packages.shared.pdu import PDU

game = Game()


def run(pdu: PDU) -> PDU | None:
    """Run on receive.

    Args:
        pdu (PDU): PDU received

    Returns:
        PDU: PDUs to send
    """
    match game.state:
        case State.LOBBY:
            return lobby(pdu)
        case State.GAME_SETUP:
            return game_setup(pdu)
        case State.MULLIGAN:
            return mulligan(pdu)
        case GamePhase.UNTAP:
            return untap(pdu)
        case GamePhase.UPKEEP:
            return upkeep(pdu)
        case GamePhase.DRAW:
            return draw(pdu)
        case GamePhase.PRECOMBAT_MAIN:
            return precombat_main(pdu)
        case CombatStep.BEGIN_COMBAT:
            return begin_combat(pdu)
        case CombatStep.DECLARE_ATTACKERS:
            return declare_attackers(pdu)
        case CombatStep.DECLARE_BLOCKERS:
            return declare_blockers(pdu)
        case CombatStep.ASSIGN_DAMAGE_ORDER:
            return assign_damage_order(pdu)
        case CombatStep.FIRST_STRIKE_DAMAGE:
            return first_strike_damage(pdu)
        case CombatStep.COMBAT_DAMAGE:
            return combat_damage(pdu)
        case CombatStep.END_OF_COMBAT:
            return end_of_combat(pdu)
        case GamePhase.POSTCOMBAT_MAIN:
            return postcombat_main(pdu)
        case GamePhase.END_STEP:
            return end_step(pdu)
        case GamePhase.CLEANUP:
            return cleanup(pdu)
        case State.GAME_OVER:
            return game_over(pdu)


def lobby(pdu: PDU) -> PDU | None:
    """Lobby state.

    Args:
        pdu (PDU): PDU received

    Returns:
        PDU: PDUs to send
    """
    raise NotImplementedError


def game_setup(pdu: PDU) -> PDU | None:
    """Game Setup state.

    Args:
        pdu (PDU): PDU received

    Returns:
        PDU: PDUs to send
    """
    raise NotImplementedError


def mulligan(pdu: PDU) -> PDU | None:
    """Mulligan state.

    Args:
        pdu (PDU): PDU received

    Returns:
        PDU: PDUs to send
    """
    raise NotImplementedError


def game_over(pdu: PDU) -> PDU | None:
    """Game Over State.

    Args:
        pdu (PDU): PDU received

    Returns:
        PDU: PDUs to send
    """
    raise NotImplementedError


def untap(pdu: PDU) -> PDU | None:
    """In-Game Untap Phase.

    Args:
        pdu (PDU): PDU received

    Returns:
        PDU: PDUs to send
    """
    raise NotImplementedError


def upkeep(pdu: PDU) -> PDU | None:
    """In-Game Upkeep Phase.

    Args:
        pdu (PDU): PDU received

    Returns:
        PDU: PDUs to send
    """
    raise NotImplementedError


def draw(pdu: PDU) -> PDU | None:
    """In-Game Draw Phase.

    Args:
        pdu (PDU): PDU received

    Returns:
        PDU: PDUs to send
    """
    raise NotImplementedError


def precombat_main(pdu: PDU) -> PDU | None:
    """In-Game Precombat Main Phase.

    Args:
        pdu (PDU): PDU received

    Returns:
        PDU: PDUs to send
    """
    raise NotImplementedError


def postcombat_main(pdu: PDU) -> PDU | None:
    """In-Game Postcombat Main Phase.

    Args:
        pdu (PDU): PDU received

    Returns:
        PDU: PDUs to send
    """
    raise NotImplementedError


def end_step(pdu: PDU) -> PDU | None:
    """In-Game End Step Phase.

    Args:
        pdu (PDU): PDU received

    Returns:
        PDU: PDUs to send
    """
    raise NotImplementedError


def cleanup(pdu: PDU) -> PDU | None:
    """In-Game Cleanup Phase.

    Args:
        pdu (PDU): PDU received

    Returns:
        PDU: PDUs to send
    """
    raise NotImplementedError


def begin_combat(pdu: PDU) -> PDU | None:
    """Combat Begin Combat Step.

    Args:
        pdu (PDU): PDU received

    Returns:
        PDU: PDUs to send
    """
    raise NotImplementedError


def declare_attackers(pdu: PDU) -> PDU | None:
    """Combat Declare Attackers Step.

    Args:
        pdu (PDU): PDU received

    Returns:
        PDU: PDUs to send
    """
    raise NotImplementedError


def declare_blockers(pdu: PDU) -> PDU | None:
    """Combat Declare Blockers Step.

    Args:
        pdu (PDU): PDU received

    Returns:
        PDU: PDUs to send
    """
    raise NotImplementedError


def assign_damage_order(pdu: PDU) -> PDU | None:
    """Combat Assign Damage Order Step.

    Args:
        pdu (PDU): PDU received

    Returns:
        PDU: PDUs to send
    """
    raise NotImplementedError


def first_strike_damage(pdu: PDU) -> PDU | None:
    """Combat First Strike Damage Step.

    Args:
        pdu (PDU): PDU received

    Returns:
        PDU: PDUs to send
    """
    raise NotImplementedError


def combat_damage(pdu: PDU) -> PDU | None:
    """Combat Damage Step.

    Args:
        pdu (PDU): PDU received

    Returns:
        PDU: PDUs to send
    """
    raise NotImplementedError


def end_of_combat(pdu: PDU) -> PDU | None:
    """Combat End of Combat Step.

    Args:
        pdu (PDU): PDU received

    Returns:
        PDU: PDUs to send
    """
    raise NotImplementedError
