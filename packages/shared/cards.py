"""Game cards."""

from abc import ABC, abstractmethod
from enum import StrEnum, auto

from packages.shared.game import ID


CardID = ID
CreatureCardID = CardID
LandCardID = CardID

# TODO Card cast and ability logic


class Card(ABC):
    """Base card class."""

    class Color(StrEnum):
        """Card color."""

        W = auto()
        U = auto()
        B = auto()
        R = auto()
        G = auto()
        C = "x"

    def __init__(self, id: CardID) -> None:
        """Creates a card instance.

        Args:
            id (ID): Card ID
        """
        self.__id = id

    @staticmethod
    @abstractmethod
    def _ids() -> set[str]:
        """Valid card IDs.

        Returns:
            set[str]: Set of valid card IDs
        """
        pass

    @staticmethod
    @abstractmethod
    def name() -> str:
        """Card name.

        Returns:
            str: Card name
        """
        pass

    @staticmethod
    @abstractmethod
    def color() -> Color:
        """Card color.

        Returns:
            Color: Card color
        """
        pass

    @staticmethod
    @abstractmethod
    def cost() -> dict[Color, int]:
        """Card cost.

        Returns:
            dict[Color, int]: Card cost
        """
        pass

    @property
    def id(self):
        """Card ID.

        Returns:
            str: Card ID
        """
        return self.__id

    def __eq__(self, value: object) -> bool:
        """Checks object equality.

        Args:
            value (object): Object to compare

        Returns:
            bool: Is equal
        """
        return isinstance(value, Card) and self.id == value.id

    def __hash__(self) -> int:
        """Hashes the object.

        Returns:
            int: Object hash
        """
        return hash(self.id)


class Subtype(ABC):
    """Subtype interface."""

    @staticmethod
    @abstractmethod
    def subtype() -> str:
        """Card subtype.

        Returns:
            str: Card subtype
        """
        pass


class TapCard(Card):
    """Card that can tap."""

    def __init__(self, id: ID) -> None:
        """Creates a tap card instance.

        Args:
            id (ID): Card ID
        """
        super().__init__(id)
        self._tapped = False

    @property
    @abstractmethod
    def tapped(self) -> bool:
        """Tapped.

        Returns:
            bool: Tapped
        """
        return self._tapped


class ArtifactCard(TapCard):
    """Artifact Card."""

    pass


class CreatureCard(TapCard, Subtype):
    """Creature Card."""

    @staticmethod
    @abstractmethod
    def power() -> int:
        """Creature power.

        Returns:
            int: Creature power
        """
        pass

    @staticmethod
    @abstractmethod
    def toughness() -> int:
        """Creature toughness.

        Returns:
            int: Creature toughnesss
        """
        pass


class ArtifactCreatureCard(ArtifactCard, CreatureCard):
    """Artifact Creature Card."""

    pass


class EnchantmentCard(Card, Subtype):
    """Enchantment Card."""

    pass


class InstantCard(Card):
    """Instant Card."""

    pass


class LandCard(TapCard, Subtype):
    """Land Card."""

    pass


class SorceryCard(Card):
    """Sorcery Card."""

    pass
