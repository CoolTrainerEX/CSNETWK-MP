"""Game module."""

from abc import ABC
from enum import StrEnum, auto

from packages.shared.player import Player


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


class Game(ABC):
    """Game instance.

    Attributes:
        _seq_num (int): Sequence number
        _players list[Player]: List of players
    """

    def __init__(self) -> None:
        """Create a game instance."""
        self.__state = State.LOBBY
        self.__game_phase = GamePhase.UNTAP
        self.__combat_step = CombatStep.BEGIN_COMBAT
        self._seq_num = 0
        self._players: list[Player] = []

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

    @state.setter
    def state(self, value: State | GamePhase | CombatStep):
        """Set current game state.

        Args:
            value (State | GamePhase | CombatStep): Current game state.
        """
        if isinstance(value, CombatStep):
            self.__combat_step = value
            self.__game_phase = GamePhase.COMBAT
            self.__state = State.IN_GAME
        elif isinstance(value, GamePhase):
            self.__combat_step = CombatStep.BEGIN_COMBAT
            self.__game_phase = value
            self.__state = State.IN_GAME
        else:
            self.__combat_step = CombatStep.BEGIN_COMBAT
            self.__game_phase = GamePhase.UNTAP
            self.__state = value
