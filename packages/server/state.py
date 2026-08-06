"""Server state."""

from packages.shared.game import CombatStep, Game, GamePhase, State
from packages.shared.pdu import PDU
from packages.shared.player import Player

game = Game()


def run(pdu: PDU) -> dict[Player, PDU]:
    """Run on receive.

    Args:
        pdu (PDU): PDU received

    Returns:
        dict[Player, PDU]: PDUs to send
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


def lobby(pdu: PDU) -> dict[Player, PDU]:
    """Lobby state.

    Args:
        pdu (PDU): PDU received

    Returns:
        dict[Player, PDU]: PDUs to send
    """
    raise NotImplementedError


def game_setup(pdu: PDU) -> dict[Player, PDU]:
    """Game Setup state.

    Args:
        pdu (PDU): PDU received

    Returns:
        dict[Player, PDU]: PDUs to send
    """
    raise NotImplementedError


def mulligan(pdu: PDU) -> dict[Player, PDU]:
    """Mulligan state.

    Args:
        pdu (PDU): PDU received

    Returns:
        dict[Player, PDU]: PDUs to send
    """
    raise NotImplementedError


def game_over(pdu: PDU) -> dict[Player, PDU]:
    """Game Over State.

    Args:
        pdu (PDU): PDU received

    Returns:
        dict[Player, PDU]: PDUs to send
    """
    raise NotImplementedError


def untap(pdu: PDU) -> dict[Player, PDU]:
    """In-Game Untap Phase.

    Args:
        pdu (PDU): PDU received

    Returns:
        dict[Player, PDU]: PDUs to send
    """
    raise NotImplementedError


def upkeep(pdu: PDU) -> dict[Player, PDU]:
    """In-Game Upkeep Phase.

    Args:
        pdu (PDU): PDU received

    Returns:
        dict[Player, PDU]: PDUs to send
    """
    raise NotImplementedError


def draw(pdu: PDU) -> dict[Player, PDU]:
    """In-Game Draw Phase.

    Args:
        pdu (PDU): PDU received

    Returns:
        dict[Player, PDU]: PDUs to send
    """
    raise NotImplementedError


def precombat_main(pdu: PDU) -> dict[Player, PDU]:
    """In-Game Precombat Main Phase.

    Args:
        pdu (PDU): PDU received

    Returns:
        dict[Player, PDU]: PDUs to send
    """
    raise NotImplementedError


def postcombat_main(pdu: PDU) -> dict[Player, PDU]:
    """In-Game Postcombat Main Phase.

    Args:
        pdu (PDU): PDU received

    Returns:
        dict[Player, PDU]: PDUs to send
    """
    raise NotImplementedError


def end_step(pdu: PDU) -> dict[Player, PDU]:
    """In-Game End Step Phase.

    Args:
        pdu (PDU): PDU received

    Returns:
        dict[Player, PDU]: PDUs to send
    """
    raise NotImplementedError


def cleanup(pdu: PDU) -> dict[Player, PDU]:
    """In-Game Cleanup Phase.

    Args:
        pdu (PDU): PDU received

    Returns:
        dict[Player, PDU]: PDUs to send
    """
    raise NotImplementedError


def begin_combat(pdu: PDU) -> dict[Player, PDU]:
    """Combat Begin Combat Step.

    Args:
        pdu (PDU): PDU received

    Returns:
        dict[Player, PDU]: PDUs to send
    """
    raise NotImplementedError


def declare_attackers(pdu: PDU) -> dict[Player, PDU]:
    """Combat Declare Attackers Step.

    Args:
        pdu (PDU): PDU received

    Returns:
        dict[Player, PDU]: PDUs to send
    """
    raise NotImplementedError


def declare_blockers(pdu: PDU) -> dict[Player, PDU]:
    """Combat Declare Blockers Step.

    Args:
        pdu (PDU): PDU received

    Returns:
        dict[Player, PDU]: PDUs to send
    """
    raise NotImplementedError


def assign_damage_order(pdu: PDU) -> dict[Player, PDU]:
    """Combat Assign Damage Order Step.

    Args:
        pdu (PDU): PDU received

    Returns:
        dict[Player, PDU]: PDUs to send
    """
    raise NotImplementedError


def first_strike_damage(pdu: PDU) -> dict[Player, PDU]:
    """Combat First Strike Damage Step.

    Args:
        pdu (PDU): PDU received

    Returns:
        dict[Player, PDU]: PDUs to send
    """
    raise NotImplementedError


def combat_damage(pdu: PDU) -> dict[Player, PDU]:
    """Combat Damage Step.

    Args:
        pdu (PDU): PDU received

    Returns:
        dict[Player, PDU]: PDUs to send
    """
    raise NotImplementedError


def end_of_combat(pdu: PDU) -> dict[Player, PDU]:
    """Combat End of Combat Step.

    Args:
        pdu (PDU): PDU received

    Returns:
        dict[Player, PDU]: PDUs to send
    """
    raise NotImplementedError
