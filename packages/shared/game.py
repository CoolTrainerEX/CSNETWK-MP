"""Game module."""

from enum import StrEnum, auto


ID = str


class State(StrEnum):
    """Game states."""

    LOBBY = auto()
    GAME_SETUP = auto()
    MULLIGAN = auto()
    IN_GAME = auto()
    GAME_OVER = auto()


class GamePhase(StrEnum):
    """:attr:`State.IN_GAME` phases."""

    UNTAP = auto()

    UPKEEP = auto()
    """Priority window"""

    DRAW = auto()
    """Priority window"""

    PRECOMBAT_MAIN = auto()
    """Priority window (sorcery speed for AP)"""

    COMBAT = auto()
    """See :class:`CombatStep` for sub-steps"""

    POSTCOMBAT_MAIN = auto()
    """Priority window (sorcery speed for AP)"""

    END_STEP = auto()
    """Priority window"""

    CLEANUP = auto()


class CombatStep(StrEnum):
    """:attr:`GamePhase.COMBAT` steps."""

    BEGIN_COMBAT = auto()

    DECLARE_ATTACKERS = auto()
    """AP declares; priority window follows"""

    DECLARE_BLOCKERS = auto()
    """NAP assigns blockers; priority window follows"""

    ASSIGN_DAMAGE_ORDER = auto()
    """AP orders multi-blockers; priority window"""

    FIRST_STRIKE_DAMAGE = auto()
    """OPTIONAL: only if first/double strike present"""
    COMBAT_DAMAGE = auto()
    """Server resolves damage; priority window"""

    END_OF_COMBAT = auto()
    """Priority window; combat concludes"""
