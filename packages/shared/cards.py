"""Game cards."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum, auto
from inspect import isabstract
from typing import Literal

from rich.console import Console


from packages.shared.types import ID

console = Console()

CardID = ID
CreatureCardID = CardID
LandCardID = CardID

# TODO Please add the ability  and cast text and cost ()


class Card(ABC):
    """Base card class."""

    __registry: dict[CardID, type[Card]] = {}

    class Color(StrEnum):
        """Card color."""

        W = auto()
        U = auto()
        B = auto()
        R = auto()
        G = auto()
        C = "x"

        def __format__(self, format_spec: str) -> str:
            """Format object.

            Args:
                format_spec (str): Format specifier

            Returns:
                str: Formatted string
            """
            match self:
                case Card.Color.W:
                    style = "bold black on white"
                case Card.Color.U:
                    style = "bold bright_blue on dark_blue"
                case Card.Color.B:
                    style = "bold white on black"
                case Card.Color.R:
                    style = "bold bright_red on dark_red"
                case Card.Color.G:
                    style = "bold bright_green on dark_green"
                case Card.Color.C:
                    style = "bold grey30 on grey70"

            with console.capture() as capture:
                console.print(
                    f"[{style}] {super().__format__(format_spec).upper()} [/]"
                )

            return capture.get()

    @dataclass
    class AbilityDetails(object):
        """Details of abilities.

        Attributes:
            mana_cost (dict[Card.Color, int]): Mana cost
            text (str): Ability description
        """

        mana_cost: dict[Card.Color, int] = field(default_factory=dict, compare=False)
        text: str = field(default="")

    def __init__(self, id: CardID) -> None:
        """Creates a card instance.

        Args:
            id (ID): Card ID

        Raises:
            ValueError: Id is not valid
        """
        if id in self._ids():
            self.__id = id
        else:
            raise ValueError(f"{id} is not in {self._ids()}.")

    def __init_subclass__(cls, **kwargs) -> None:
        """Registers cards into the master registry."""
        super().__init_subclass__(**kwargs)

        if not isabstract(cls):
            for id in cls._ids():
                cls.__registry[id] = cls

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
    def cast_details() -> AbilityDetails:
        """Card cast details.

        Returns:
            AbilityDetails: Card cast details
        """
        pass

    @property
    def id(self):
        """Card ID.

        Returns:
            str: Card ID
        """
        return self.__id

    @classmethod
    def from_id(cls, id: str):
        """Gets the card class from the id.

        Args:
            id (str): Card ID

        Returns:
            type[Card]: Card class
        """
        return cls.__registry[id]

    @staticmethod
    def _gen_ids(base: str, copies: int) -> set[str]:
        return {f"{base}_{i:03d}" for i in range(1, copies + 1)}

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


class BattlefieldCard(Card):
    """Card that are placed on the battlefield."""

    @dataclass(unsafe_hash=True)
    class BattlefieldAbilityDetails(Card.AbilityDetails):
        """Ability including tap cost.

        Attriibutes:
            tap_cost (Literal[True] | None) Tap cost
        """

        tap_cost: Literal[True] | None = field(default=None, compare=False)

    def __init__(self, id: ID) -> None:
        """Creates a battlefield card instance.

        Args:
            id (ID): Card ID
        """
        super().__init__(id)
        self._tapped = False

    @property
    def tapped(self) -> bool:
        """Tapped.

        Returns:
            bool: Tapped
        """
        return self._tapped

    @staticmethod
    @abstractmethod
    def abilities_details() -> set[BattlefieldAbilityDetails]:
        """Card abilities details.

        Returns:
            set[Card.AbilityDetails]: List of abilities details
        """
        pass


class ArtifactCard(BattlefieldCard):
    """Artifact Card."""

    pass


class CreatureCard(BattlefieldCard, Subtype):
    """Creature Card."""

    class Modifier(StrEnum):
        """Creature modifier."""

        HASTE = auto()
        TRAMPLE = auto()
        FLYING = auto()
        HEXPROOF = auto()
        DEFENDER = auto()
        FIRST_STRIKE = auto()
        VIGILANCE = auto()

    def __init__(self, id: ID) -> None:  # noqa: D107
        super().__init__(id)
        self.__modifiers = self.base_modifiers()
        self._summoning_sick = False

    @staticmethod
    @abstractmethod
    def power() -> int:  # noqa: D102
        """Creature power.

        Returns:
            int: Creature power
        """
        pass

    @staticmethod
    @abstractmethod
    def toughness() -> int:  # noqa: D102
        """Creature toughness.

        Returns:
            int: Creature toughnesss
        """
        pass

    @staticmethod
    @abstractmethod
    def base_modifiers() -> set[Modifier]:
        """Creature base modifiers.

        Returns:
            set[str]: List of modifiers
        """
        pass

    def modifiers(self) -> set[Modifier]:
        """Creature current modifiers.

        Returns:
            set[str]: List of modifiers
        """
        return self.__modifiers

    @property
    def summoning_sick(self):
        """Cast creature summoning sickness.

        Returns:
            bool: Summoning sickness
        """
        return self._summoning_sick


class TriggerCreatureCard(CreatureCard):
    """Creature with trigger."""

    @staticmethod
    @abstractmethod
    def trigger_details() -> str:
        """Trigger details.

        Returns:
            str: Trigger description
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


class LandCard(BattlefieldCard, Subtype):
    """Land Card."""

    pass


class SorceryCard(Card):
    """Sorcery Card."""

    pass


class Mountain(LandCard):  # noqa: D101
    """Mountain."""

    @staticmethod
    def _ids() -> set[str]:
        return Card._gen_ids("mountain", 20)

    @staticmethod
    def name() -> str:  # noqa: D102
        return "Mountain"

    @staticmethod
    def color() -> Card.Color:  # noqa: D102  # noqa: D102
        return Card.Color.R

    @staticmethod
    def cast_details() -> Card.AbilityDetails:  # noqa: D102
        return Card.AbilityDetails({}, "")

    @staticmethod
    def subtype() -> str:  # noqa: D102
        return "Basic Mountain"

    @staticmethod
    def abilities_details() -> set[BattlefieldCard.BattlefieldAbilityDetails]:  # noqa: D102
        return {
            BattlefieldCard.BattlefieldAbilityDetails(
                text=f"Add {Card.Color.G}", tap_cost=True
            )
        }


class Forest(LandCard):
    """Forest."""

    @staticmethod
    def _ids() -> set[str]:
        return Card._gen_ids("forest", 20)

    @staticmethod
    def name() -> str:  # noqa: D102
        return "Forest"

    @staticmethod
    def color() -> Card.Color:  # noqa: D102
        return Card.Color.G

    @staticmethod
    def cast_details() -> Card.AbilityDetails:  # noqa: D102
        return Card.AbilityDetails({}, "")

    @staticmethod
    def subtype() -> str:  # noqa: D102
        return "Basic Forest"


class Plains(LandCard):
    """Plains."""

    @staticmethod
    def _ids() -> set[str]:
        return Card._gen_ids("plains", 20)

    @staticmethod
    def name() -> str:  # noqa: D102
        return "Plains"

    @staticmethod
    def color() -> Card.Color:  # noqa: D102
        return Card.Color.W

    @staticmethod
    def cast_details() -> Card.AbilityDetails:  # noqa: D102
        return Card.AbilityDetails({}, "")

    @staticmethod
    def subtype() -> str:  # noqa: D102
        return "Basic Plains"


class Island(LandCard):
    """Island."""

    @staticmethod
    def _ids() -> set[str]:
        return Card._gen_ids("island", 20)

    @staticmethod
    def name() -> str:  # noqa: D102
        return "Island"

    @staticmethod
    def color() -> Card.Color:  # noqa: D102
        return Card.Color.U

    @staticmethod
    def cast_details() -> Card.AbilityDetails:  # noqa: D102
        return Card.AbilityDetails({}, "")

    @staticmethod
    def subtype() -> str:  # noqa: D102
        return "Basic Island"


class Swamp(LandCard):
    """Swamp."""

    @staticmethod
    def _ids() -> set[str]:
        return Card._gen_ids("swamp", 20)

    @staticmethod
    def name() -> str:  # noqa: D102
        return "Swamp"

    @staticmethod
    def color() -> Card.Color:  # noqa: D102
        return Card.Color.B

    @staticmethod
    def cast_details() -> Card.AbilityDetails:  # noqa: D102
        return Card.AbilityDetails({}, "")

    @staticmethod
    def subtype() -> str:  # noqa: D102
        return "Basic Swamp"


class LightningBolt(InstantCard):
    """Lightning Bolt."""

    @staticmethod
    def _ids() -> set[str]:
        return Card._gen_ids("lightning_bolt", 4)

    @staticmethod
    def name() -> str:  # noqa: D102
        return "Lightning Bolt"

    @staticmethod
    def color() -> Card.Color:  # noqa: D102
        return Card.Color.R

    @staticmethod
    def cast_details() -> Card.AbilityDetails:  # noqa: D102
        return Card.AbilityDetails({Card.Color.R: 1}, "")


class Shock(InstantCard):
    """Shock."""

    @staticmethod
    def _ids() -> set[str]:
        return Card._gen_ids("shock", 4)

    @staticmethod
    def name() -> str:  # noqa: D102
        return "Shock"

    @staticmethod
    def color() -> Card.Color:  # noqa: D102
        return Card.Color.R

    @staticmethod
    def cast_details() -> Card.AbilityDetails:  # noqa: D102
        return Card.AbilityDetails({Card.Color.R: 1}, "")


class LavaSpike(SorceryCard):
    """Lava Spike."""

    @staticmethod
    def _ids() -> set[str]:
        return Card._gen_ids("lava_spike", 4)

    @staticmethod
    def name() -> str:  # noqa: D102
        return "Lava Spike"

    @staticmethod
    def color() -> Card.Color:  # noqa: D102
        return Card.Color.R

    @staticmethod
    def cast_details() -> Card.AbilityDetails:  # noqa: D102
        return Card.AbilityDetails({Card.Color.R: 1}, "")


class FlameSlash(SorceryCard):
    """Flame Slash."""

    @staticmethod
    def _ids() -> set[str]:
        return Card._gen_ids("flame_slash", 4)

    @staticmethod
    def name() -> str:  # noqa: D102
        return "Flame Slash"

    @staticmethod
    def color() -> Card.Color:  # noqa: D102
        return Card.Color.R

    @staticmethod
    def cast_details() -> Card.AbilityDetails:  # noqa: D102
        return Card.AbilityDetails({Card.Color.R: 1}, "")


class SearingSpear(InstantCard):
    """Searing Spear."""

    @staticmethod
    def _ids() -> set[str]:
        return Card._gen_ids("searing_spear", 4)

    @staticmethod
    def name() -> str:  # noqa: D102
        return "Searing Spear"

    @staticmethod
    def color() -> Card.Color:  # noqa: D102
        return Card.Color.R

    @staticmethod
    def cast_details() -> Card.AbilityDetails:  # noqa: D102
        return Card.AbilityDetails({Card.Color.R: 1, Card.Color.C: 1}, "")


class Skullcrack(InstantCard):
    """Skullcrack."""

    @staticmethod
    def _ids() -> set[str]:
        return Card._gen_ids("skullcrack", 4)

    @staticmethod
    def name() -> str:  # noqa: D102
        return "Skullcrack"

    @staticmethod
    def color() -> Card.Color:  # noqa: D102
        return Card.Color.R

    @staticmethod
    def cast_details() -> Card.AbilityDetails:  # noqa: D102
        return Card.AbilityDetails({Card.Color.R: 1, Card.Color.C: 1}, "")


class RiftBolt(SorceryCard):
    """Rift Bolt."""

    @staticmethod
    def _ids() -> set[str]:
        return Card._gen_ids("rift_bolt", 4)

    @staticmethod
    def name() -> str:  # noqa: D102
        return "Rift Bolt"

    @staticmethod
    def color() -> Card.Color:  # noqa: D102
        return Card.Color.R

    @staticmethod
    def cast_details() -> Card.AbilityDetails:  # noqa: D102
        return Card.AbilityDetails({Card.Color.R: 1, Card.Color.C: 2}, "")


class Incinerate(InstantCard):
    """Incinerate."""

    @staticmethod
    def _ids() -> set[str]:
        return Card._gen_ids("incinerate", 4)

    @staticmethod
    def name() -> str:  # noqa: D102
        return "Incinerate"

    @staticmethod
    def color() -> Card.Color:  # noqa: D102
        return Card.Color.R

    @staticmethod
    def cast_details() -> Card.AbilityDetails:  # noqa: D102
        return Card.AbilityDetails({Card.Color.R: 1, Card.Color.C: 1}, "")


class GoblinGuide(TriggerCreatureCard):
    """Goblin Guide."""

    @staticmethod
    def _ids() -> set[str]:
        return Card._gen_ids("goblin_guide", 4)

    @staticmethod
    def name() -> str:  # noqa: D102
        return "Goblin Guide"

    @staticmethod
    def color() -> Card.Color:  # noqa: D102
        return Card.Color.R

    @staticmethod
    def cast_details() -> Card.AbilityDetails:  # noqa: D102
        return Card.AbilityDetails({Card.Color.R: 1}, "")

    @staticmethod
    def subtype() -> str:  # noqa: D102
        return "Goblin Scout"

    @staticmethod
    def power() -> int:  # noqa: D102
        return 2

    @staticmethod
    def toughness() -> int:  # noqa: D102
        return 2

    @staticmethod
    def base_modifiers() -> set[CreatureCard.Modifier]:  # noqa: D102
        return {CreatureCard.Modifier.HASTE}

    @staticmethod
    def trigger_details() -> str:  # noqa: D102
        return "Whenever Goblin Guide attacks, defending player reveals top card of library. If it's a land, that player puts it into their hand."


class GoblinBushwhacker(CreatureCard):
    """Goblin Bushwhacker."""

    @staticmethod
    def _ids() -> set[str]:
        return Card._gen_ids("goblin_bushwhacker", 4)

    @staticmethod
    def name() -> str:  # noqa: D102
        return "Goblin Bushwhacker"

    @staticmethod
    def color() -> Card.Color:  # noqa: D102
        return Card.Color.R

    @staticmethod
    def cast_details() -> Card.AbilityDetails:  # noqa: D102
        return Card.AbilityDetails({Card.Color.R: 1}, "")

    @staticmethod
    def subtype() -> str:  # noqa: D102
        return "Goblin Warrior"

    @staticmethod
    def power() -> int:  # noqa: D102
        return 1

    @staticmethod
    def toughness() -> int:  # noqa: D102
        return 1


class RecklessWurm(CreatureCard):
    """Reckless Wurm."""

    @staticmethod
    def _ids() -> set[str]:
        return Card._gen_ids("reckless_wurm", 4)

    @staticmethod
    def name() -> str:  # noqa: D102
        return "Reckless Wurm"

    @staticmethod
    def color() -> Card.Color:  # noqa: D102
        return Card.Color.R

    @staticmethod
    def cast_details() -> Card.AbilityDetails:  # noqa: D102
        return Card.AbilityDetails({Card.Color.R: 1, Card.Color.C: 3}, "")

    @staticmethod
    def subtype() -> str:  # noqa: D102
        return "Wurm"

    @staticmethod
    def power() -> int:  # noqa: D102
        return 4

    @staticmethod
    def toughness() -> int:  # noqa: D102
        return 4


class MonasterySwiftspear(CreatureCard):
    """Monastery Swiftspear."""

    @staticmethod
    def _ids() -> set[str]:
        return Card._gen_ids("monastery_swiftspear", 4)

    @staticmethod
    def name() -> str:  # noqa: D102
        return "Monastery Swiftspear"

    @staticmethod
    def color() -> Card.Color:  # noqa: D102
        return Card.Color.R

    @staticmethod
    def cast_details() -> Card.AbilityDetails:  # noqa: D102
        return Card.AbilityDetails({Card.Color.R: 1}, "")

    @staticmethod
    def subtype() -> str:  # noqa: D102
        return "Human Monk"

    @staticmethod
    def power() -> int:  # noqa: D102
        return 1

    @staticmethod
    def toughness() -> int:  # noqa: D102
        return 2


class Counterspell(InstantCard):
    """Counterspell."""

    @staticmethod
    def _ids() -> set[str]:
        return Card._gen_ids("counterspell", 4)

    @staticmethod
    def name() -> str:  # noqa: D102
        return "Counterspell"

    @staticmethod
    def color() -> Card.Color:  # noqa: D102
        return Card.Color.U

    @staticmethod
    def cast_details() -> Card.AbilityDetails:  # noqa: D102
        return Card.AbilityDetails({Card.Color.U: 2}, "")


class Cancel(InstantCard):
    """Cancel."""

    @staticmethod
    def _ids() -> set[str]:
        return Card._gen_ids("cancel", 4)

    @staticmethod
    def name() -> str:  # noqa: D102
        return "Cancel"

    @staticmethod
    def color() -> Card.Color:  # noqa: D102
        return Card.Color.U

    @staticmethod
    def cast_details() -> Card.AbilityDetails:  # noqa: D102
        return Card.AbilityDetails({Card.Color.U: 2, Card.Color.C: 1}, "")


class Unsummon(InstantCard):
    """Unsummon."""

    @staticmethod
    def _ids() -> set[str]:
        return Card._gen_ids("unsummon", 4)

    @staticmethod
    def name() -> str:  # noqa: D102
        return "Unsummon"

    @staticmethod
    def color() -> Card.Color:  # noqa: D102
        return Card.Color.U

    @staticmethod
    def cast_details() -> Card.AbilityDetails:  # noqa: D102
        return Card.AbilityDetails({Card.Color.U: 1}, "")


class Ponder(SorceryCard):
    """Ponder."""

    @staticmethod
    def _ids() -> set[str]:
        return Card._gen_ids("ponder", 4)

    @staticmethod
    def name() -> str:  # noqa: D102
        return "Ponder"

    @staticmethod
    def color() -> Card.Color:  # noqa: D102
        return Card.Color.U

    @staticmethod
    def cast_details() -> Card.AbilityDetails:  # noqa: D102
        return Card.AbilityDetails({Card.Color.U: 1}, "")


class Negate(InstantCard):
    """Negate."""

    @staticmethod
    def _ids() -> set[str]:
        return Card._gen_ids("negate", 4)

    @staticmethod
    def name() -> str:  # noqa: D102
        return "Negate"

    @staticmethod
    def color() -> Card.Color:  # noqa: D102
        return Card.Color.U

    @staticmethod
    def cast_details() -> Card.AbilityDetails:  # noqa: D102
        return Card.AbilityDetails({Card.Color.U: 1, Card.Color.C: 1}, "")


class ManaLeak(InstantCard):
    """Mana Leak."""

    @staticmethod
    def _ids() -> set[str]:
        return Card._gen_ids("mana_leak", 4)

    @staticmethod
    def name() -> str:  # noqa: D102
        return "Mana Leak"

    @staticmethod
    def color() -> Card.Color:  # noqa: D102
        return Card.Color.U

    @staticmethod
    def cast_details() -> Card.AbilityDetails:  # noqa: D102
        return Card.AbilityDetails({Card.Color.U: 1, Card.Color.C: 1}, "")


class MerfolkLooter(CreatureCard):
    """Merfolk Looter."""

    @staticmethod
    def _ids() -> set[str]:
        return Card._gen_ids("merfolk_looter", 4)

    @staticmethod
    def name() -> str:  # noqa: D102
        return "Merfolk Looter"

    @staticmethod
    def color() -> Card.Color:  # noqa: D102
        return Card.Color.U

    @staticmethod
    def cast_details() -> Card.AbilityDetails:  # noqa: D102
        return Card.AbilityDetails({Card.Color.U: 1, Card.Color.C: 1}, "")

    @staticmethod
    def subtype() -> str:  # noqa: D102
        return "Merfolk Rogue"

    @staticmethod
    def power() -> int:  # noqa: D102
        return 1

    @staticmethod
    def toughness() -> int:  # noqa: D102
        return 1


class ProdigalSorcerer(CreatureCard):
    """Prodigal Sorcerer."""

    @staticmethod
    def _ids() -> set[str]:
        return Card._gen_ids("prodigal_sorcerer", 4)

    @staticmethod
    def name() -> str:  # noqa: D102
        return "Prodigal Sorcerer"

    @staticmethod
    def color() -> Card.Color:  # noqa: D102
        return Card.Color.U

    @staticmethod
    def cast_details() -> Card.AbilityDetails:  # noqa: D102
        return Card.AbilityDetails({Card.Color.U: 1, Card.Color.C: 2}, "")

    @staticmethod
    def subtype() -> str:  # noqa: D102
        return "Human Wizard"

    @staticmethod
    def power() -> int:  # noqa: D102
        return 1

    @staticmethod
    def toughness() -> int:  # noqa: D102
        return 1


class AirElemental(CreatureCard):
    """Air Elemental."""

    @staticmethod
    def _ids() -> set[str]:
        return Card._gen_ids("air_elemental", 4)

    @staticmethod
    def name() -> str:  # noqa: D102
        return "Air Elemental"

    @staticmethod
    def color() -> Card.Color:  # noqa: D102
        return Card.Color.U

    @staticmethod
    def cast_details() -> Card.AbilityDetails:  # noqa: D102
        return Card.AbilityDetails({Card.Color.U: 2, Card.Color.C: 3}, "")

    @staticmethod
    def subtype() -> str:  # noqa: D102
        return "Elemental"

    @staticmethod
    def power() -> int:  # noqa: D102
        return 4

    @staticmethod
    def toughness() -> int:  # noqa: D102
        return 4


class PhantasmalBear(CreatureCard):
    """Phantasmal Bear."""

    @staticmethod
    def _ids() -> set[str]:
        return Card._gen_ids("phantasmal_bear", 4)

    @staticmethod
    def name() -> str:  # noqa: D102
        return "Phantasmal Bear"

    @staticmethod
    def color() -> Card.Color:  # noqa: D102
        return Card.Color.U

    @staticmethod
    def cast_details() -> Card.AbilityDetails:  # noqa: D102
        return Card.AbilityDetails({Card.Color.U: 1}, "")

    @staticmethod
    def subtype() -> str:  # noqa: D102
        return "Bear Illusion"

    @staticmethod
    def power() -> int:  # noqa: D102
        return 2

    @staticmethod
    def toughness() -> int:  # noqa: D102
        return 2


class GiantGrowth(InstantCard):
    """Giant Growth."""

    @staticmethod
    def _ids() -> set[str]:
        return Card._gen_ids("giant_growth", 4)

    @staticmethod
    def name() -> str:  # noqa: D102
        return "Giant Growth"

    @staticmethod
    def color() -> Card.Color:  # noqa: D102
        return Card.Color.G

    @staticmethod
    def cast_details() -> Card.AbilityDetails:  # noqa: D102
        return Card.AbilityDetails({Card.Color.G: 1}, "")


class RampantGrowth(SorceryCard):
    """Rampant Growth."""

    @staticmethod
    def _ids() -> set[str]:
        return Card._gen_ids("rampant_growth", 4)

    @staticmethod
    def name() -> str:  # noqa: D102
        return "Rampant Growth"

    @staticmethod
    def color() -> Card.Color:  # noqa: D102
        return Card.Color.G

    @staticmethod
    def cast_details() -> Card.AbilityDetails:  # noqa: D102
        return Card.AbilityDetails({Card.Color.G: 1, Card.Color.C: 1}, "")


class Naturalize(InstantCard):
    """Naturalize."""

    @staticmethod
    def _ids() -> set[str]:
        return Card._gen_ids("naturalize", 4)

    @staticmethod
    def name() -> str:  # noqa: D102
        return "Naturalize"

    @staticmethod
    def color() -> Card.Color:  # noqa: D102
        return Card.Color.G

    @staticmethod
    def cast_details() -> Card.AbilityDetails:  # noqa: D102
        return Card.AbilityDetails({Card.Color.G: 1, Card.Color.C: 1}, "")


class VinesOfVastwood(InstantCard):
    """Vines of Vastwood."""

    @staticmethod
    def _ids() -> set[str]:
        return Card._gen_ids("vines_of_vastwood", 4)

    @staticmethod
    def name() -> str:  # noqa: D102
        return "Vines of Vastwood"

    @staticmethod
    def color() -> Card.Color:  # noqa: D102
        return Card.Color.G

    @staticmethod
    def cast_details() -> Card.AbilityDetails:  # noqa: D102
        return Card.AbilityDetails({Card.Color.G: 1}, "")


class LlanowarElves(CreatureCard):
    """Llanowar Elves."""

    @staticmethod
    def _ids() -> set[str]:
        return Card._gen_ids("llanowar_elves", 4)

    @staticmethod
    def name() -> str:  # noqa: D102
        return "Llanowar Elves"

    @staticmethod
    def color() -> Card.Color:  # noqa: D102
        return Card.Color.G

    @staticmethod
    def cast_details() -> Card.AbilityDetails:  # noqa: D102
        return Card.AbilityDetails({Card.Color.G: 1}, "")

    @staticmethod
    def subtype() -> str:  # noqa: D102
        return "Elf Druid"

    @staticmethod
    def power() -> int:  # noqa: D102
        return 1

    @staticmethod
    def toughness() -> int:  # noqa: D102
        return 1


class ElvishMystic(CreatureCard):
    """Elvish Mystic."""

    @staticmethod
    def _ids() -> set[str]:
        return Card._gen_ids("elvish_mystic", 4)

    @staticmethod
    def name() -> str:  # noqa: D102
        return "Elvish Mystic"

    @staticmethod
    def color() -> Card.Color:  # noqa: D102
        return Card.Color.G

    @staticmethod
    def cast_details() -> Card.AbilityDetails:  # noqa: D102
        return Card.AbilityDetails({Card.Color.G: 1}, "")

    @staticmethod
    def subtype() -> str:  # noqa: D102
        return "Elf Druid"

    @staticmethod
    def power() -> int:  # noqa: D102
        return 1

    @staticmethod
    def toughness() -> int:  # noqa: D102
        return 1


class GrizzlyBears(CreatureCard):
    """Grizzly Bears."""

    @staticmethod
    def _ids() -> set[str]:
        return Card._gen_ids("grizzly_bears", 4)

    @staticmethod
    def name() -> str:  # noqa: D102
        return "Grizzly Bears"

    @staticmethod
    def color() -> Card.Color:  # noqa: D102
        return Card.Color.G

    @staticmethod
    def cast_details() -> Card.AbilityDetails:  # noqa: D102
        return Card.AbilityDetails({Card.Color.G: 1, Card.Color.C: 1}, "")

    @staticmethod
    def subtype() -> str:  # noqa: D102
        return "Bear"

    @staticmethod
    def power() -> int:  # noqa: D102
        return 2

    @staticmethod
    def toughness() -> int:  # noqa: D102
        return 2


class LeatherbackBaloth(CreatureCard):
    """Leatherback Baloth."""

    @staticmethod
    def _ids() -> set[str]:
        return Card._gen_ids("leatherback_baloth", 4)

    @staticmethod
    def name() -> str:  # noqa: D102
        return "Leatherback Baloth"

    @staticmethod
    def color() -> Card.Color:  # noqa: D102
        return Card.Color.G

    @staticmethod
    def cast_details() -> Card.AbilityDetails:  # noqa: D102
        return Card.AbilityDetails({Card.Color.G: 3}, "")

    @staticmethod
    def subtype() -> str:  # noqa: D102
        return "Beast"

    @staticmethod
    def power() -> int:  # noqa: D102
        return 4

    @staticmethod
    def toughness() -> int:  # noqa: D102
        return 5


class TrollAscetic(CreatureCard):
    """Troll Ascetic."""

    @staticmethod
    def _ids() -> set[str]:
        return Card._gen_ids("troll_ascetic", 4)

    @staticmethod
    def name() -> str:  # noqa: D102
        return "Troll Ascetic"

    @staticmethod
    def color() -> Card.Color:  # noqa: D102
        return Card.Color.G

    @staticmethod
    def cast_details() -> Card.AbilityDetails:  # noqa: D102
        return Card.AbilityDetails({Card.Color.G: 2, Card.Color.C: 1}, "")

    @staticmethod
    def subtype() -> str:  # noqa: D102
        return "Troll Shaman"

    @staticmethod
    def power() -> int:  # noqa: D102
        return 3

    @staticmethod
    def toughness() -> int:  # noqa: D102
        return 2


class WallOfStone(CreatureCard):
    """Wall of Stone."""

    @staticmethod
    def _ids() -> set[str]:
        return Card._gen_ids("wall_of_stone", 4)

    @staticmethod
    def name() -> str:  # noqa: D102
        return "Wall of Stone"

    @staticmethod
    def color() -> Card.Color:  # noqa: D102
        return Card.Color.R

    @staticmethod
    def cast_details() -> Card.AbilityDetails:  # noqa: D102
        return Card.AbilityDetails({Card.Color.R: 2, Card.Color.C: 1}, "")

    @staticmethod
    def subtype() -> str:  # noqa: D102
        return "Wall"

    @staticmethod
    def power() -> int:  # noqa: D102
        return 0

    @staticmethod
    def toughness() -> int:  # noqa: D102
        return 8


class SwordsToPlowshares(InstantCard):
    """Swords to Plowshares."""

    @staticmethod
    def _ids() -> set[str]:
        return Card._gen_ids("swords_to_plowshares", 4)

    @staticmethod
    def name() -> str:  # noqa: D102
        return "Swords to Plowshares"

    @staticmethod
    def color() -> Card.Color:  # noqa: D102
        return Card.Color.W

    @staticmethod
    def cast_details() -> Card.AbilityDetails:  # noqa: D102
        return Card.AbilityDetails({Card.Color.W: 1}, "")


class PathToExile(InstantCard):
    """Path to Exile."""

    @staticmethod
    def _ids() -> set[str]:
        return Card._gen_ids("path_to_exile", 4)

    @staticmethod
    def name() -> str:  # noqa: D102
        return "Path to Exile"

    @staticmethod
    def color() -> Card.Color:  # noqa: D102
        return Card.Color.W

    @staticmethod
    def cast_details() -> Card.AbilityDetails:  # noqa: D102
        return Card.AbilityDetails({Card.Color.W: 1}, "")


class HealingSalve(InstantCard):
    """Healing Salve."""

    @staticmethod
    def _ids() -> set[str]:
        return Card._gen_ids("healing_salve", 4)

    @staticmethod
    def name() -> str:  # noqa: D102
        return "Healing Salve"

    @staticmethod
    def color() -> Card.Color:  # noqa: D102
        return Card.Color.W

    @staticmethod
    def cast_details() -> Card.AbilityDetails:  # noqa: D102
        return Card.AbilityDetails({Card.Color.W: 1}, "")


class Pacifism(EnchantmentCard):
    """Pacifism."""

    @staticmethod
    def _ids() -> set[str]:
        return Card._gen_ids("pacifism", 4)

    @staticmethod
    def name() -> str:  # noqa: D102
        return "Pacifism"

    @staticmethod
    def color() -> Card.Color:  # noqa: D102
        return Card.Color.W

    @staticmethod
    def cast_details() -> Card.AbilityDetails:  # noqa: D102
        return Card.AbilityDetails({Card.Color.W: 1, Card.Color.C: 1}, "")

    @staticmethod
    def subtype() -> str:  # noqa: D102
        return "Aura"


class WhiteKnight(CreatureCard):
    """White Knight."""

    @staticmethod
    def _ids() -> set[str]:
        return Card._gen_ids("white_knight", 4)

    @staticmethod
    def name() -> str:  # noqa: D102
        return "White Knight"

    @staticmethod
    def color() -> Card.Color:  # noqa: D102
        return Card.Color.W

    @staticmethod
    def cast_details() -> Card.AbilityDetails:  # noqa: D102
        return Card.AbilityDetails({Card.Color.W: 2}, "")

    @staticmethod
    def subtype() -> str:  # noqa: D102
        return "Human Knight"

    @staticmethod
    def power() -> int:  # noqa: D102
        return 2

    @staticmethod
    def toughness() -> int:  # noqa: D102
        return 2


class SerraAngel(CreatureCard):
    """Serra Angel."""

    @staticmethod
    def _ids() -> set[str]:
        return Card._gen_ids("serra_angel", 4)

    @staticmethod
    def name() -> str:  # noqa: D102
        return "Serra Angel"

    @staticmethod
    def color() -> Card.Color:  # noqa: D102
        return Card.Color.W

    @staticmethod
    def cast_details() -> Card.AbilityDetails:  # noqa: D102
        return Card.AbilityDetails({Card.Color.W: 2, Card.Color.C: 3}, "")

    @staticmethod
    def subtype() -> str:  # noqa: D102
        return "Angel"

    @staticmethod
    def power() -> int:  # noqa: D102
        return 4

    @staticmethod
    def toughness() -> int:  # noqa: D102
        return 4


class SavannahLions(CreatureCard):
    """Savannah Lions."""

    @staticmethod
    def _ids() -> set[str]:
        return Card._gen_ids("savannah_lions", 4)

    @staticmethod
    def name() -> str:  # noqa: D102
        return "Savannah Lions"

    @staticmethod
    def color() -> Card.Color:  # noqa: D102
        return Card.Color.W

    @staticmethod
    def cast_details() -> Card.AbilityDetails:  # noqa: D102
        return Card.AbilityDetails({Card.Color.W: 1}, "")

    @staticmethod
    def subtype() -> str:  # noqa: D102
        return "Cat"

    @staticmethod
    def power() -> int:  # noqa: D102
        return 2

    @staticmethod
    def toughness() -> int:  # noqa: D102
        return 1


class MotherOfRunes(CreatureCard):
    """Mother of Runes."""

    @staticmethod
    def _ids() -> set[str]:
        return Card._gen_ids("mother_of_runes", 4)

    @staticmethod
    def name() -> str:  # noqa: D102
        return "Mother of Runes"

    @staticmethod
    def color() -> Card.Color:  # noqa: D102
        return Card.Color.W

    @staticmethod
    def cast_details() -> Card.AbilityDetails:  # noqa: D102
        return Card.AbilityDetails({Card.Color.W: 1}, "")

    @staticmethod
    def subtype() -> str:  # noqa: D102
        return "Human Cleric"

    @staticmethod
    def power() -> int:  # noqa: D102
        return 1

    @staticmethod
    def toughness() -> int:  # noqa: D102
        return 1


class DarkRitual(InstantCard):
    """Dark Ritual."""

    @staticmethod
    def _ids() -> set[str]:
        return Card._gen_ids("dark_ritual", 4)

    @staticmethod
    def name() -> str:  # noqa: D102
        return "Dark Ritual"

    @staticmethod
    def color() -> Card.Color:  # noqa: D102
        return Card.Color.B

    @staticmethod
    def cast_details() -> Card.AbilityDetails:  # noqa: D102
        return Card.AbilityDetails({Card.Color.B: 1}, "")


class Terror(InstantCard):
    """Terror."""

    @staticmethod
    def _ids() -> set[str]:
        return Card._gen_ids("terror", 4)

    @staticmethod
    def name() -> str:  # noqa: D102
        return "Terror"

    @staticmethod
    def color() -> Card.Color:  # noqa: D102
        return Card.Color.B

    @staticmethod
    def cast_details() -> Card.AbilityDetails:  # noqa: D102
        return Card.AbilityDetails({Card.Color.B: 1, Card.Color.C: 1}, "")


class DoomBlade(InstantCard):
    """Doom Blade."""

    @staticmethod
    def _ids() -> set[str]:
        return Card._gen_ids("doom_blade", 4)

    @staticmethod
    def name() -> str:  # noqa: D102
        return "Doom Blade"

    @staticmethod
    def color() -> Card.Color:  # noqa: D102
        return Card.Color.B

    @staticmethod
    def cast_details() -> Card.AbilityDetails:  # noqa: D102
        return Card.AbilityDetails({Card.Color.B: 1, Card.Color.C: 1}, "")


class RaiseDead(SorceryCard):
    """Raise Dead."""

    @staticmethod
    def _ids() -> set[str]:
        return Card._gen_ids("raise_dead", 4)

    @staticmethod
    def name() -> str:  # noqa: D102
        return "Raise Dead"

    @staticmethod
    def color() -> Card.Color:  # noqa: D102
        return Card.Color.B

    @staticmethod
    def cast_details() -> Card.AbilityDetails:  # noqa: D102
        return Card.AbilityDetails({Card.Color.B: 1}, "")


class MindRot(SorceryCard):
    """Mind Rot."""

    @staticmethod
    def _ids() -> set[str]:
        return Card._gen_ids("mind_rot", 4)

    @staticmethod
    def name() -> str:  # noqa: D102
        return "Mind Rot"

    @staticmethod
    def color() -> Card.Color:  # noqa: D102
        return Card.Color.B

    @staticmethod
    def cast_details() -> Card.AbilityDetails:  # noqa: D102
        return Card.AbilityDetails({Card.Color.B: 1, Card.Color.C: 2}, "")


class GrayMerchantOfAsphodel(CreatureCard):
    """Gray Merchant of Asphodel."""

    @staticmethod
    def _ids() -> set[str]:
        return Card._gen_ids("gray_merchant", 4)

    @staticmethod
    def name() -> str:  # noqa: D102
        return "Gray Merchant of Asphodel"

    @staticmethod
    def color() -> Card.Color:  # noqa: D102
        return Card.Color.B

    @staticmethod
    def cast_details() -> Card.AbilityDetails:  # noqa: D102
        return Card.AbilityDetails({Card.Color.B: 2, Card.Color.C: 3}, "")

    @staticmethod
    def subtype() -> str:  # noqa: D102
        return "Zombie"

    @staticmethod
    def power() -> int:  # noqa: D102
        return 2

    @staticmethod
    def toughness() -> int:  # noqa: D102
        return 4


class Gravedigger(CreatureCard):
    """Gravedigger."""

    @staticmethod
    def _ids() -> set[str]:
        return Card._gen_ids("gravedigger", 4)

    @staticmethod
    def name() -> str:  # noqa: D102
        return "Gravedigger"

    @staticmethod
    def color() -> Card.Color:  # noqa: D102
        return Card.Color.B

    @staticmethod
    def cast_details() -> Card.AbilityDetails:  # noqa: D102
        return Card.AbilityDetails({Card.Color.B: 1, Card.Color.C: 3}, "")

    @staticmethod
    def subtype() -> str:  # noqa: D102
        return "Zombie"

    @staticmethod
    def power() -> int:  # noqa: D102
        return 2

    @staticmethod
    def toughness() -> int:  # noqa: D102
        return 2


class RoyalAssassin(CreatureCard):
    """Royal Assassin."""

    @staticmethod
    def _ids() -> set[str]:
        return Card._gen_ids("royal_assassin", 4)

    @staticmethod
    def name() -> str:  # noqa: D102
        return "Royal Assassin"

    @staticmethod
    def color() -> Card.Color:  # noqa: D102
        return Card.Color.B

    @staticmethod
    def cast_details() -> Card.AbilityDetails:  # noqa: D102
        return Card.AbilityDetails({Card.Color.B: 2, Card.Color.C: 1}, "")

    @staticmethod
    def subtype() -> str:  # noqa: D102
        return "Human Assassin"

    @staticmethod
    def power() -> int:  # noqa: D102
        return 1

    @staticmethod
    def toughness() -> int:  # noqa: D102
        return 1


class BlackKnight(CreatureCard):
    """Black Knight."""

    @staticmethod
    def _ids() -> set[str]:
        return Card._gen_ids("black_knight", 4)

    @staticmethod
    def name() -> str:  # noqa: D102
        return "Black Knight"

    @staticmethod
    def color() -> Card.Color:  # noqa: D102
        return Card.Color.B

    @staticmethod
    def cast_details() -> Card.AbilityDetails:  # noqa: D102
        return Card.AbilityDetails({Card.Color.B: 2}, "")

    @staticmethod
    def subtype() -> str:  # noqa: D102
        return "Human Knight"

    @staticmethod
    def power() -> int:  # noqa: D102
        return 2

    @staticmethod
    def toughness() -> int:  # noqa: D102
        return 2


class SolRing(ArtifactCard):
    """Sol Ring."""

    @staticmethod
    def _ids() -> set[str]:
        return Card._gen_ids("sol_ring", 4)

    @staticmethod
    def name() -> str:  # noqa: D102
        return "Sol Ring"

    @staticmethod
    def color() -> Card.Color:  # noqa: D102
        return Card.Color.C

    @staticmethod
    def cast_details() -> Card.AbilityDetails:  # noqa: D102
        return Card.AbilityDetails({Card.Color.C: 1}, "")


class Ornithopter(ArtifactCreatureCard):
    """Ornithopter."""

    @staticmethod
    def _ids() -> set[str]:
        return Card._gen_ids("ornithopter", 4)

    @staticmethod
    def name() -> str:  # noqa: D102
        return "Ornithopter"

    @staticmethod
    def color() -> Card.Color:  # noqa: D102
        return Card.Color.C

    @staticmethod
    def cast_details() -> Card.AbilityDetails:  # noqa: D102
        return Card.AbilityDetails({}, "")

    @staticmethod
    def subtype() -> str:  # noqa: D102
        return "Thopter"

    @staticmethod
    def power() -> int:  # noqa: D102
        return 0

    @staticmethod
    def toughness() -> int:  # noqa: D102
        return 2


class Millstone(ArtifactCard):
    """Millstone."""

    @staticmethod
    def _ids() -> set[str]:
        return Card._gen_ids("millstone", 4)

    @staticmethod
    def name() -> str:  # noqa: D102
        return "Millstone"

    @staticmethod
    def color() -> Card.Color:  # noqa: D102
        return Card.Color.C

    @staticmethod
    def cast_details() -> Card.AbilityDetails:  # noqa: D102
        return Card.AbilityDetails({Card.Color.C: 2}, "")


class RodOfRuin(ArtifactCard):
    """Rod of Ruin."""

    @staticmethod
    def _ids() -> set[str]:
        return Card._gen_ids("rod_of_ruin", 4)

    @staticmethod
    def name() -> str:  # noqa: D102
        return "Rod of Ruin"

    @staticmethod
    def color() -> Card.Color:  # noqa: D102
        return Card.Color.C

    @staticmethod
    def cast_details() -> Card.AbilityDetails:  # noqa: D102
        return Card.AbilityDetails({Card.Color.C: 4}, "")
