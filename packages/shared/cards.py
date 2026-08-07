"""Game cards."""

from abc import ABC, abstractmethod
from enum import StrEnum, auto
from typing import Annotated

from pydantic import PlainSerializer

from packages.shared.game import ID


# TODO Add Card data and inherit it for Creature, Artifact, etc.
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

    def __init__(self, id: ID) -> None:
        """Creates a card instance.

        Args:
            id (ID): Card ID
        """
        self.__id = id

    @staticmethod
    @abstractmethod
    def valid_ids() -> set[str]:
        """Valid card IDs.

        Returns:
            set[str]: Set of valid card IDs
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


def serialize_card(card: Card):
    """Serialize :class:`Card` for Pydantic.

    Args:
        card (BaseCard): Card to serialize

    Returns:
        ID: Serialized card
    """
    return card.id


CardID = ID
CreatureCardID = CardID
LandCardID = CardID
