"""Player states."""

from abc import ABC

from packages.shared.cards import Card
from packages.shared.types import ID

PlayerID = ID


class Player(ABC):
    """Player class."""

    def __init__(self, id: PlayerID) -> None:
        """Creates a player.

        Args:
            id (ID): Player ID
        """
        self.__id = id
        self.__life_total = 20
        self.__battlefield: set[Card] = set()
        self.__graveyard: set[Card] = set()

    @property
    def id(self):
        """Player ID.

        Returns:
            str: Player ID
        """
        return self.__id

    @property
    def life_total(self):
        """Player life total.

        Returns:
            int: Player life total
        """
        return self.__life_total

    @property
    def battlefield(self):
        """Player battlefield.

        Returns:
            _type_: Player battlefield
        """
        return self.__battlefield

    @property
    def graveyard(self):
        """Plaayer graveyard.

        Returns:
            set[Card]: Player graveyard
        """
        return self.__graveyard

    def __eq__(self, value: object) -> bool:
        """Checks object equality.

        Args:
            value (object): Object to compare

        Returns:
            bool: Is equal
        """
        return isinstance(value, Player) and self.id == value.id

    def __hash__(self) -> int:
        """Hashes the object.

        Returns:
            int: Object hash
        """
        return hash(self.id)
