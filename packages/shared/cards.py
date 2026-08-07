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


# card_id
def _gen_ids(base: str, copies: int) -> set[str]:
    return {f"{base}_{i:03d}" for i in range(1, copies + 1)}

class Mountain(LandCard):
    @staticmethod
    def _ids() -> set[str]: return _gen_ids("mountain", 20)
    @staticmethod
    def name() -> str: return "Mountain"
    @staticmethod
    def color() -> Card.Color: return Card.Color.R
    @staticmethod
    def cost() -> dict[Card.Color, int]: return {}
    @staticmethod
    def subtype() -> str: return "Basic Mountain"

class Forest(LandCard):
    @staticmethod
    def _ids() -> set[str]: return _gen_ids("forest", 20)
    @staticmethod
    def name() -> str: return "Forest"
    @staticmethod
    def color() -> Card.Color: return Card.Color.G
    @staticmethod
    def cost() -> dict[Card.Color, int]: return {}
    @staticmethod
    def subtype() -> str: return "Basic Forest"

class Plains(LandCard):
    @staticmethod
    def _ids() -> set[str]: return _gen_ids("plains", 20)
    @staticmethod
    def name() -> str: return "Plains"
    @staticmethod
    def color() -> Card.Color: return Card.Color.W
    @staticmethod
    def cost() -> dict[Card.Color, int]: return {}
    @staticmethod
    def subtype() -> str: return "Basic Plains"

class Island(LandCard):
    @staticmethod
    def _ids() -> set[str]: return _gen_ids("island", 20)
    @staticmethod
    def name() -> str: return "Island"
    @staticmethod
    def color() -> Card.Color: return Card.Color.U
    @staticmethod
    def cost() -> dict[Card.Color, int]: return {}
    @staticmethod
    def subtype() -> str: return "Basic Island"

class Swamp(LandCard):
    @staticmethod
    def _ids() -> set[str]: return _gen_ids("swamp", 20)
    @staticmethod
    def name() -> str: return "Swamp"
    @staticmethod
    def color() -> Card.Color: return Card.Color.B
    @staticmethod
    def cost() -> dict[Card.Color, int]: return {}
    @staticmethod
    def subtype() -> str: return "Basic Swamp"

class LightningBolt(InstantCard):
    @staticmethod
    def _ids() -> set[str]: return _gen_ids("lightning_bolt", 4)
    @staticmethod
    def name() -> str: return "Lightning Bolt"
    @staticmethod
    def color() -> Card.Color: return Card.Color.R
    @staticmethod
    def cost() -> dict[Card.Color, int]: return {Card.Color.R: 1}

class Shock(InstantCard):
    @staticmethod
    def _ids() -> set[str]: return _gen_ids("shock", 4)
    @staticmethod
    def name() -> str: return "Shock"
    @staticmethod
    def color() -> Card.Color: return Card.Color.R
    @staticmethod
    def cost() -> dict[Card.Color, int]: return {Card.Color.R: 1}

class LavaSpike(SorceryCard):
    @staticmethod
    def _ids() -> set[str]: return _gen_ids("lava_spike", 4)
    @staticmethod
    def name() -> str: return "Lava Spike"
    @staticmethod
    def color() -> Card.Color: return Card.Color.R
    @staticmethod
    def cost() -> dict[Card.Color, int]: return {Card.Color.R: 1}

class FlameSlash(SorceryCard):
    @staticmethod
    def _ids() -> set[str]: return _gen_ids("flame_slash", 4)
    @staticmethod
    def name() -> str: return "Flame Slash"
    @staticmethod
    def color() -> Card.Color: return Card.Color.R
    @staticmethod
    def cost() -> dict[Card.Color, int]: return {Card.Color.R: 1}

class SearingSpear(InstantCard):
    @staticmethod
    def _ids() -> set[str]: return _gen_ids("searing_spear", 4)
    @staticmethod
    def name() -> str: return "Searing Spear"
    @staticmethod
    def color() -> Card.Color: return Card.Color.R
    @staticmethod
    def cost() -> dict[Card.Color, int]: return {Card.Color.R: 1, Card.Color.C: 1}

class Skullcrack(InstantCard):
    @staticmethod
    def _ids() -> set[str]: return _gen_ids("skullcrack", 4)
    @staticmethod
    def name() -> str: return "Skullcrack"
    @staticmethod
    def color() -> Card.Color: return Card.Color.R
    @staticmethod
    def cost() -> dict[Card.Color, int]: return {Card.Color.R: 1, Card.Color.C: 1}

class RiftBolt(SorceryCard):
    @staticmethod
    def _ids() -> set[str]: return _gen_ids("rift_bolt", 4)
    @staticmethod
    def name() -> str: return "Rift Bolt"
    @staticmethod
    def color() -> Card.Color: return Card.Color.R
    @staticmethod
    def cost() -> dict[Card.Color, int]: return {Card.Color.R: 1, Card.Color.C: 2}

class Incinerate(InstantCard):
    @staticmethod
    def _ids() -> set[str]: return _gen_ids("incinerate", 4)
    @staticmethod
    def name() -> str: return "Incinerate"
    @staticmethod
    def color() -> Card.Color: return Card.Color.R
    @staticmethod
    def cost() -> dict[Card.Color, int]: return {Card.Color.R: 1, Card.Color.C: 1}

class GoblinGuide(CreatureCard):
    @staticmethod
    def _ids() -> set[str]: return _gen_ids("goblin_guide", 4)
    @staticmethod
    def name() -> str: return "Goblin Guide"
    @staticmethod
    def color() -> Card.Color: return Card.Color.R
    @staticmethod
    def cost() -> dict[Card.Color, int]: return {Card.Color.R: 1}
    @staticmethod
    def subtype() -> str: return "Goblin Scout"
    @staticmethod
    def power() -> int: return 2
    @staticmethod
    def toughness() -> int: return 2

class GoblinBushwhacker(CreatureCard):
    @staticmethod
    def _ids() -> set[str]: return _gen_ids("goblin_bushwhacker", 4)
    @staticmethod
    def name() -> str: return "Goblin Bushwhacker"
    @staticmethod
    def color() -> Card.Color: return Card.Color.R
    @staticmethod
    def cost() -> dict[Card.Color, int]: return {Card.Color.R: 1}
    @staticmethod
    def subtype() -> str: return "Goblin Warrior"
    @staticmethod
    def power() -> int: return 1
    @staticmethod
    def toughness() -> int: return 1

class RecklessWurm(CreatureCard):
    @staticmethod
    def _ids() -> set[str]: return _gen_ids("reckless_wurm", 4)
    @staticmethod
    def name() -> str: return "Reckless Wurm"
    @staticmethod
    def color() -> Card.Color: return Card.Color.R
    @staticmethod
    def cost() -> dict[Card.Color, int]: return {Card.Color.R: 1, Card.Color.C: 3}
    @staticmethod
    def subtype() -> str: return "Wurm"
    @staticmethod
    def power() -> int: return 4
    @staticmethod
    def toughness() -> int: return 4

class MonasterySwiftspear(CreatureCard):
    @staticmethod
    def _ids() -> set[str]: return _gen_ids("monastery_swiftspear", 4)
    @staticmethod
    def name() -> str: return "Monastery Swiftspear"
    @staticmethod
    def color() -> Card.Color: return Card.Color.R
    @staticmethod
    def cost() -> dict[Card.Color, int]: return {Card.Color.R: 1}
    @staticmethod
    def subtype() -> str: return "Human Monk"
    @staticmethod
    def power() -> int: return 1
    @staticmethod
    def toughness() -> int: return 2

class Counterspell(InstantCard):
    @staticmethod
    def _ids() -> set[str]: return _gen_ids("counterspell", 4)
    @staticmethod
    def name() -> str: return "Counterspell"
    @staticmethod
    def color() -> Card.Color: return Card.Color.U
    @staticmethod
    def cost() -> dict[Card.Color, int]: return {Card.Color.U: 2}

class Cancel(InstantCard):
    @staticmethod
    def _ids() -> set[str]: return _gen_ids("cancel", 4)
    @staticmethod
    def name() -> str: return "Cancel"
    @staticmethod
    def color() -> Card.Color: return Card.Color.U
    @staticmethod
    def cost() -> dict[Card.Color, int]: return {Card.Color.U: 2, Card.Color.C: 1}

class Unsummon(InstantCard):
    @staticmethod
    def _ids() -> set[str]: return _gen_ids("unsummon", 4)
    @staticmethod
    def name() -> str: return "Unsummon"
    @staticmethod
    def color() -> Card.Color: return Card.Color.U
    @staticmethod
    def cost() -> dict[Card.Color, int]: return {Card.Color.U: 1}

class Ponder(SorceryCard):
    @staticmethod
    def _ids() -> set[str]: return _gen_ids("ponder", 4)
    @staticmethod
    def name() -> str: return "Ponder"
    @staticmethod
    def color() -> Card.Color: return Card.Color.U
    @staticmethod
    def cost() -> dict[Card.Color, int]: return {Card.Color.U: 1}

class Negate(InstantCard):
    @staticmethod
    def _ids() -> set[str]: return _gen_ids("negate", 4)
    @staticmethod
    def name() -> str: return "Negate"
    @staticmethod
    def color() -> Card.Color: return Card.Color.U
    @staticmethod
    def cost() -> dict[Card.Color, int]: return {Card.Color.U: 1, Card.Color.C: 1}

class ManaLeak(InstantCard):
    @staticmethod
    def _ids() -> set[str]: return _gen_ids("mana_leak", 4)
    @staticmethod
    def name() -> str: return "Mana Leak"
    @staticmethod
    def color() -> Card.Color: return Card.Color.U
    @staticmethod
    def cost() -> dict[Card.Color, int]: return {Card.Color.U: 1, Card.Color.C: 1}

class MerfolkLooter(CreatureCard):
    @staticmethod
    def _ids() -> set[str]: return _gen_ids("merfolk_looter", 4)
    @staticmethod
    def name() -> str: return "Merfolk Looter"
    @staticmethod
    def color() -> Card.Color: return Card.Color.U
    @staticmethod
    def cost() -> dict[Card.Color, int]: return {Card.Color.U: 1, Card.Color.C: 1}
    @staticmethod
    def subtype() -> str: return "Merfolk Rogue"
    @staticmethod
    def power() -> int: return 1
    @staticmethod
    def toughness() -> int: return 1

class ProdigalSorcerer(CreatureCard):
    @staticmethod
    def _ids() -> set[str]: return _gen_ids("prodigal_sorcerer", 4)
    @staticmethod
    def name() -> str: return "Prodigal Sorcerer"
    @staticmethod
    def color() -> Card.Color: return Card.Color.U
    @staticmethod
    def cost() -> dict[Card.Color, int]: return {Card.Color.U: 1, Card.Color.C: 2}
    @staticmethod
    def subtype() -> str: return "Human Wizard"
    @staticmethod
    def power() -> int: return 1
    @staticmethod
    def toughness() -> int: return 1

class AirElemental(CreatureCard):
    @staticmethod
    def _ids() -> set[str]: return _gen_ids("air_elemental", 4)
    @staticmethod
    def name() -> str: return "Air Elemental"
    @staticmethod
    def color() -> Card.Color: return Card.Color.U
    @staticmethod
    def cost() -> dict[Card.Color, int]: return {Card.Color.U: 2, Card.Color.C: 3}
    @staticmethod
    def subtype() -> str: return "Elemental"
    @staticmethod
    def power() -> int: return 4
    @staticmethod
    def toughness() -> int: return 4

class PhantasmalBear(CreatureCard):
    @staticmethod
    def _ids() -> set[str]: return _gen_ids("phantasmal_bear", 4)
    @staticmethod
    def name() -> str: return "Phantasmal Bear"
    @staticmethod
    def color() -> Card.Color: return Card.Color.U
    @staticmethod
    def cost() -> dict[Card.Color, int]: return {Card.Color.U: 1}
    @staticmethod
    def subtype() -> str: return "Bear Illusion"
    @staticmethod
    def power() -> int: return 2
    @staticmethod
    def toughness() -> int: return 2

class GiantGrowth(InstantCard):
    @staticmethod
    def _ids() -> set[str]: return _gen_ids("giant_growth", 4)
    @staticmethod
    def name() -> str: return "Giant Growth"
    @staticmethod
    def color() -> Card.Color: return Card.Color.G
    @staticmethod
    def cost() -> dict[Card.Color, int]: return {Card.Color.G: 1}

class RampantGrowth(SorceryCard):
    @staticmethod
    def _ids() -> set[str]: return _gen_ids("rampant_growth", 4)
    @staticmethod
    def name() -> str: return "Rampant Growth"
    @staticmethod
    def color() -> Card.Color: return Card.Color.G
    @staticmethod
    def cost() -> dict[Card.Color, int]: return {Card.Color.G: 1, Card.Color.C: 1}

class Naturalize(InstantCard):
    @staticmethod
    def _ids() -> set[str]: return _gen_ids("naturalize", 4)
    @staticmethod
    def name() -> str: return "Naturalize"
    @staticmethod
    def color() -> Card.Color: return Card.Color.G
    @staticmethod
    def cost() -> dict[Card.Color, int]: return {Card.Color.G: 1, Card.Color.C: 1}

class VinesOfVastwood(InstantCard):
    @staticmethod
    def _ids() -> set[str]: return _gen_ids("vines_of_vastwood", 4)
    @staticmethod
    def name() -> str: return "Vines of Vastwood"
    @staticmethod
    def color() -> Card.Color: return Card.Color.G
    @staticmethod
    def cost() -> dict[Card.Color, int]: return {Card.Color.G: 1}

class LlanowarElves(CreatureCard):
    @staticmethod
    def _ids() -> set[str]: return _gen_ids("llanowar_elves", 4)
    @staticmethod
    def name() -> str: return "Llanowar Elves"
    @staticmethod
    def color() -> Card.Color: return Card.Color.G
    @staticmethod
    def cost() -> dict[Card.Color, int]: return {Card.Color.G: 1}
    @staticmethod
    def subtype() -> str: return "Elf Druid"
    @staticmethod
    def power() -> int: return 1
    @staticmethod
    def toughness() -> int: return 1

class ElvishMystic(CreatureCard):
    @staticmethod
    def _ids() -> set[str]: return _gen_ids("elvish_mystic", 4)
    @staticmethod
    def name() -> str: return "Elvish Mystic"
    @staticmethod
    def color() -> Card.Color: return Card.Color.G
    @staticmethod
    def cost() -> dict[Card.Color, int]: return {Card.Color.G: 1}
    @staticmethod
    def subtype() -> str: return "Elf Druid"
    @staticmethod
    def power() -> int: return 1
    @staticmethod
    def toughness() -> int: return 1

class GrizzlyBears(CreatureCard):
    @staticmethod
    def _ids() -> set[str]: return _gen_ids("grizzly_bears", 4)
    @staticmethod
    def name() -> str: return "Grizzly Bears"
    @staticmethod
    def color() -> Card.Color: return Card.Color.G
    @staticmethod
    def cost() -> dict[Card.Color, int]: return {Card.Color.G: 1, Card.Color.C: 1}
    @staticmethod
    def subtype() -> str: return "Bear"
    @staticmethod
    def power() -> int: return 2
    @staticmethod
    def toughness() -> int: return 2

class LeatherbackBaloth(CreatureCard):
    @staticmethod
    def _ids() -> set[str]: return _gen_ids("leatherback_baloth", 4)
    @staticmethod
    def name() -> str: return "Leatherback Baloth"
    @staticmethod
    def color() -> Card.Color: return Card.Color.G
    @staticmethod
    def cost() -> dict[Card.Color, int]: return {Card.Color.G: 3}
    @staticmethod
    def subtype() -> str: return "Beast"
    @staticmethod
    def power() -> int: return 4
    @staticmethod
    def toughness() -> int: return 5

class TrollAscetic(CreatureCard):
    @staticmethod
    def _ids() -> set[str]: return _gen_ids("troll_ascetic", 4)
    @staticmethod
    def name() -> str: return "Troll Ascetic"
    @staticmethod
    def color() -> Card.Color: return Card.Color.G
    @staticmethod
    def cost() -> dict[Card.Color, int]: return {Card.Color.G: 2, Card.Color.C: 1}
    @staticmethod
    def subtype() -> str: return "Troll Shaman"
    @staticmethod
    def power() -> int: return 3
    @staticmethod
    def toughness() -> int: return 2

class WallOfStone(CreatureCard):
    @staticmethod
    def _ids() -> set[str]: return _gen_ids("wall_of_stone", 4)
    @staticmethod
    def name() -> str: return "Wall of Stone"
    @staticmethod
    def color() -> Card.Color: return Card.Color.R
    @staticmethod
    def cost() -> dict[Card.Color, int]: return {Card.Color.R: 2, Card.Color.C: 1}
    @staticmethod
    def subtype() -> str: return "Wall"
    @staticmethod
    def power() -> int: return 0
    @staticmethod
    def toughness() -> int: return 8

class SwordsToPlowshares(InstantCard):
    @staticmethod
    def _ids() -> set[str]: return _gen_ids("swords_to_plowshares", 4)
    @staticmethod
    def name() -> str: return "Swords to Plowshares"
    @staticmethod
    def color() -> Card.Color: return Card.Color.W
    @staticmethod
    def cost() -> dict[Card.Color, int]: return {Card.Color.W: 1}

class PathToExile(InstantCard):
    @staticmethod
    def _ids() -> set[str]: return _gen_ids("path_to_exile", 4)
    @staticmethod
    def name() -> str: return "Path to Exile"
    @staticmethod
    def color() -> Card.Color: return Card.Color.W
    @staticmethod
    def cost() -> dict[Card.Color, int]: return {Card.Color.W: 1}

class HealingSalve(InstantCard):
    @staticmethod
    def _ids() -> set[str]: return _gen_ids("healing_salve", 4)
    @staticmethod
    def name() -> str: return "Healing Salve"
    @staticmethod
    def color() -> Card.Color: return Card.Color.W
    @staticmethod
    def cost() -> dict[Card.Color, int]: return {Card.Color.W: 1}

class Pacifism(EnchantmentCard):
    @staticmethod
    def _ids() -> set[str]: return _gen_ids("pacifism", 4)
    @staticmethod
    def name() -> str: return "Pacifism"
    @staticmethod
    def color() -> Card.Color: return Card.Color.W
    @staticmethod
    def cost() -> dict[Card.Color, int]: return {Card.Color.W: 1, Card.Color.C: 1}
    @staticmethod
    def subtype() -> str: return "Aura"

class WhiteKnight(CreatureCard):
    @staticmethod
    def _ids() -> set[str]: return _gen_ids("white_knight", 4)
    @staticmethod
    def name() -> str: return "White Knight"
    @staticmethod
    def color() -> Card.Color: return Card.Color.W
    @staticmethod
    def cost() -> dict[Card.Color, int]: return {Card.Color.W: 2}
    @staticmethod
    def subtype() -> str: return "Human Knight"
    @staticmethod
    def power() -> int: return 2
    @staticmethod
    def toughness() -> int: return 2

class SerraAngel(CreatureCard):
    @staticmethod
    def _ids() -> set[str]: return _gen_ids("serra_angel", 4)
    @staticmethod
    def name() -> str: return "Serra Angel"
    @staticmethod
    def color() -> Card.Color: return Card.Color.W
    @staticmethod
    def cost() -> dict[Card.Color, int]: return {Card.Color.W: 2, Card.Color.C: 3}
    @staticmethod
    def subtype() -> str: return "Angel"
    @staticmethod
    def power() -> int: return 4
    @staticmethod
    def toughness() -> int: return 4

class SavannahLions(CreatureCard):
    @staticmethod
    def _ids() -> set[str]: return _gen_ids("savannah_lions", 4)
    @staticmethod
    def name() -> str: return "Savannah Lions"
    @staticmethod
    def color() -> Card.Color: return Card.Color.W
    @staticmethod
    def cost() -> dict[Card.Color, int]: return {Card.Color.W: 1}
    @staticmethod
    def subtype() -> str: return "Cat"
    @staticmethod
    def power() -> int: return 2
    @staticmethod
    def toughness() -> int: return 1

class MotherOfRunes(CreatureCard):
    @staticmethod
    def _ids() -> set[str]: return _gen_ids("mother_of_runes", 4)
    @staticmethod
    def name() -> str: return "Mother of Runes"
    @staticmethod
    def color() -> Card.Color: return Card.Color.W
    @staticmethod
    def cost() -> dict[Card.Color, int]: return {Card.Color.W: 1}
    @staticmethod
    def subtype() -> str: return "Human Cleric"
    @staticmethod
    def power() -> int: return 1
    @staticmethod
    def toughness() -> int: return 1

class DarkRitual(InstantCard):
    @staticmethod
    def _ids() -> set[str]: return _gen_ids("dark_ritual", 4)
    @staticmethod
    def name() -> str: return "Dark Ritual"
    @staticmethod
    def color() -> Card.Color: return Card.Color.B
    @staticmethod
    def cost() -> dict[Card.Color, int]: return {Card.Color.B: 1}

class Terror(InstantCard):
    @staticmethod
    def _ids() -> set[str]: return _gen_ids("terror", 4)
    @staticmethod
    def name() -> str: return "Terror"
    @staticmethod
    def color() -> Card.Color: return Card.Color.B
    @staticmethod
    def cost() -> dict[Card.Color, int]: return {Card.Color.B: 1, Card.Color.C: 1}

class DoomBlade(InstantCard):
    @staticmethod
    def _ids() -> set[str]: return _gen_ids("doom_blade", 4)
    @staticmethod
    def name() -> str: return "Doom Blade"
    @staticmethod
    def color() -> Card.Color: return Card.Color.B
    @staticmethod
    def cost() -> dict[Card.Color, int]: return {Card.Color.B: 1, Card.Color.C: 1}

class RaiseDead(SorceryCard):
    @staticmethod
    def _ids() -> set[str]: return _gen_ids("raise_dead", 4)
    @staticmethod
    def name() -> str: return "Raise Dead"
    @staticmethod
    def color() -> Card.Color: return Card.Color.B
    @staticmethod
    def cost() -> dict[Card.Color, int]: return {Card.Color.B: 1}

class MindRot(SorceryCard):
    @staticmethod
    def _ids() -> set[str]: return _gen_ids("mind_rot", 4)
    @staticmethod
    def name() -> str: return "Mind Rot"
    @staticmethod
    def color() -> Card.Color: return Card.Color.B
    @staticmethod
    def cost() -> dict[Card.Color, int]: return {Card.Color.B: 1, Card.Color.C: 2}

class GrayMerchantOfAsphodel(CreatureCard):
    @staticmethod
    def _ids() -> set[str]: return _gen_ids("gray_merchant", 4)
    @staticmethod
    def name() -> str: return "Gray Merchant of Asphodel"
    @staticmethod
    def color() -> Card.Color: return Card.Color.B
    @staticmethod
    def cost() -> dict[Card.Color, int]: return {Card.Color.B: 2, Card.Color.C: 3}
    @staticmethod
    def subtype() -> str: return "Zombie"
    @staticmethod
    def power() -> int: return 2
    @staticmethod
    def toughness() -> int: return 4

class Gravedigger(CreatureCard):
    @staticmethod
    def _ids() -> set[str]: return _gen_ids("gravedigger", 4)
    @staticmethod
    def name() -> str: return "Gravedigger"
    @staticmethod
    def color() -> Card.Color: return Card.Color.B
    @staticmethod
    def cost() -> dict[Card.Color, int]: return {Card.Color.B: 1, Card.Color.C: 3}
    @staticmethod
    def subtype() -> str: return "Zombie"
    @staticmethod
    def power() -> int: return 2
    @staticmethod
    def toughness() -> int: return 2

class RoyalAssassin(CreatureCard):
    @staticmethod
    def _ids() -> set[str]: return _gen_ids("royal_assassin", 4)
    @staticmethod
    def name() -> str: return "Royal Assassin"
    @staticmethod
    def color() -> Card.Color: return Card.Color.B
    @staticmethod
    def cost() -> dict[Card.Color, int]: return {Card.Color.B: 2, Card.Color.C: 1}
    @staticmethod
    def subtype() -> str: return "Human Assassin"
    @staticmethod
    def power() -> int: return 1
    @staticmethod
    def toughness() -> int: return 1

class BlackKnight(CreatureCard):
    @staticmethod
    def _ids() -> set[str]: return _gen_ids("black_knight", 4)
    @staticmethod
    def name() -> str: return "Black Knight"
    @staticmethod
    def color() -> Card.Color: return Card.Color.B
    @staticmethod
    def cost() -> dict[Card.Color, int]: return {Card.Color.B: 2}
    @staticmethod
    def subtype() -> str: return "Human Knight"
    @staticmethod
    def power() -> int: return 2
    @staticmethod
    def toughness() -> int: return 2

class SolRing(ArtifactCard):
    @staticmethod
    def _ids() -> set[str]: return _gen_ids("sol_ring", 4)
    @staticmethod
    def name() -> str: return "Sol Ring"
    @staticmethod
    def color() -> Card.Color: return Card.Color.C
    @staticmethod
    def cost() -> dict[Card.Color, int]: return {Card.Color.C: 1}

class Ornithopter(ArtifactCreatureCard):
    @staticmethod
    def _ids() -> set[str]: return _gen_ids("ornithopter", 4)
    @staticmethod
    def name() -> str: return "Ornithopter"
    @staticmethod
    def color() -> Card.Color: return Card.Color.C
    @staticmethod
    def cost() -> dict[Card.Color, int]: return {}
    @staticmethod
    def subtype() -> str: return "Thopter"
    @staticmethod
    def power() -> int: return 0
    @staticmethod
    def toughness() -> int: return 2

class Millstone(ArtifactCard):
    @staticmethod
    def _ids() -> set[str]: return _gen_ids("millstone", 4)
    @staticmethod
    def name() -> str: return "Millstone"
    @staticmethod
    def color() -> Card.Color: return Card.Color.C
    @staticmethod
    def cost() -> dict[Card.Color, int]: return {Card.Color.C: 2}

class RodOfRuin(ArtifactCard):
    @staticmethod
    def _ids() -> set[str]: return _gen_ids("rod_of_ruin", 4)
    @staticmethod
    def name() -> str: return "Rod of Ruin"
    @staticmethod
    def color() -> Card.Color: return Card.Color.C
    @staticmethod
    def cost() -> dict[Card.Color, int]: return {Card.Color.C: 4}