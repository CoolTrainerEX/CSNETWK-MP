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


class Game(object):
    """Game instance."""

    def __init__(self) -> None:
        """Create a game instance."""
        self.__state = State.LOBBY
        self.__game_phase = GamePhase.UNTAP
        self.__combat_step = CombatStep.BEGIN_COMBAT

    @property
    def state(self):
        """Current game state.

        Returns:
            State | GamePhase | CombatStep: Current game state
        """
        if self.__state == State.IN_GAME:
            if self.__game_phase == GamePhase.COMBAT:
                return self.__combat_step
            return self.__game_phase
        return self.__state
