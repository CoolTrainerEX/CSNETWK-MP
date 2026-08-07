"""Player states."""

from typing import Annotated

from pydantic import PlainSerializer

from packages.shared.game import ID


# TODO Add player data
class Player(object):
    """Player class."""

    def __init__(self, id: ID) -> None:
        """Creates a player.

        Args:
            id (ID): Player ID
        """
        self.__id = id

    @property
    def id(self):
        """Player ID.

        Returns:
            str: Player ID
        """
        return self.__id

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


def serialize_player(player: Player):
    """Serialize :class:`Player` for Pydantic.

    Args:
        player (Player): Player to serialize

    Returns:
        ID: Serialized player
    """
    return player.id


PlayerID = ID
