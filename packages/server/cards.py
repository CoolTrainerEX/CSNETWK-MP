"""Server-side card effects."""

from typing import TYPE_CHECKING, Any
from packages.shared.cards import Card, CardID
from packages.shared.player import PlayerID
from packages.shared.pdu import StackItem
from packages.server.game import ServerGame
from typing import Set, Optional
import re


if TYPE_CHECKING:
    from packages.server.game import ServerPlayer


def validate_targets(
    card: Card,
    targets: set[str],
    player_map: dict[PlayerID, "ServerPlayer"],
    players: list["ServerPlayer"],
    stack: list[StackItem],
) -> bool:
    """Validate targets for a card cast/activation.

    TODO: Implement target validation logic for all cards.
    This function is called by ServerGame in game.py before putting a spell on the stack.
    """
    return True


def apply_effect(
    card_obj: Card,
    targets: set[str],
    controller: PlayerID,
    is_permanent: bool,
    player_map: dict[PlayerID, "ServerPlayer"],
    players: list["ServerPlayer"],
    stack: list[StackItem],
    eot_pumps: dict[str, list[tuple[int, int]]],
) -> dict[PlayerID, list[Any]]:
    """Resolve a card's effect or enter-the-battlefield abilities.

    TODO: Implement the specific resolution logic for all card effects.
    This function is called by ServerGame in game.py during stack resolution.
    It should return a dict mapping PlayerID to a list of PDUs to send as a result.
    """
    return {p.id: [] for p in players}


"""Server-side card effect interpreter."""

# cast spell (play a card)
# ability (player choice to activate)
# trigger (event based automatic)
# creature modifiers (creature has some special effects)


# compiled TODOs for game.py
# TODO parse effect text here and result in either "damage", "heal", "exile, or more effects"
# parse here
# TODO apply tap in game.py via function
# TODO implement parsing function for effect_text
# TODO implement find_target in game.py
# TODO implement health update in game.py preferably a class getter with target checks
# for specific target types for certain card restrictions
# TODO implement draw_card in game.py
# TODO implement add_to_hand card in game.py
# TODO implement exile_target in game.py

# note that ability text needs to have certain words to trigger certain effects which is handled by the parser
# for now, these are "damage", "heal", "exile"


class CardEffects:
    def __init__(self, game: ServerGame):
        self.game = game

    # resolves automatic effects that do not need to be activated by player
    def resolve(self, card_id: CardID, player: str, targets: Set[str]) -> None:
        """Main entry point for spell resolution."""
        card_cls = Card.from_id(card_id)
        self._apply_cast_details(card_cls, player, targets)

    # resolves effects that need to be activated by player
    def activate(
        self,
        card_id: CardID,
        player: str,
        targets: Set[str],
    ) -> None:
        """Main entry point for ability resolution."""
        card_cls = Card.from_id(card_id)
        self._apply_ability_details(card_cls, player, targets)

    # ----------------- PRIVATE EFFECT HANDLERS -----------------

    def _apply_cast_details(
        self,
        card_cls: type[Card],
        player: str,
        targets: Set[str],
    ) -> None:
        """Parse the spell's cast details and apply the effect."""
        ability_details = card_cls.cast_details()
        effect_text = ability_details.text

        # TODO parse effect text here and result in either "damage", "heal", "exile, or more effects"
        # parse here

        effect = self._extract_effect_from_text(effect_text)

        if effect == "damage" in effect_text.lower():
            self._apply_damage_spell(effect_text, targets, player)
        elif effect == "exile" in effect_text.lower():
            self._apply_exile_spell(targets, player)
        elif effect == "heal" in effect_text.lower():
            self._apply_heal_spell(effect_text, targets, player)

    def _apply_ability_details(
        self,
        card_cls: type[Card],
        player: str,
    ) -> None:
        """Parse ability details and apply the effect."""
        ability_details = card_cls.abilities_details()
        effect_text = ability_details.text

        effect = self._extract_effect_from_text(effect_text)
        # Check if ability requires tapping
        if ability_details.tap_cost:
            # TODO apply tap in game.py via function
            self.game.tap(ability_details.tap_cost, player)

        elif effect == "draw" in effect_text.lower():
            self._apply_draw_on_tap(effect_text, player)

        # Add more ability types...

    # Specific Effect Handlers

    def _apply_damage_spell(
        self, effect_text: str, targets: Set[str], player: str
    ) -> None:
        """Apply damage based on spell effect text."""

        # TODO implement parsing function for effect_text
        damage = self._extract_number_from_text(effect_text)

        if damage is None:
            return

        # Apply damage to each target
        for target_id in targets:
            # TODO implement find_target in game.py
            target = self.game.find_target(target_id, player)

            # TODO implement health update in game.py preferably a class getter with target checks
            # for specific target types for certain card restrictions
            target.life += damage

    def _apply_draw_spell(self, effect_text: str, player: str) -> None:
        """Apply card draw effect."""
        # Extract number of cards to draw (e.g., "Draw 2 cards")
        cards_to_draw = self._extract_number_from_text(effect_text) or 1

        # Draw the cards
        for _ in range(cards_to_draw):
            # TODO implement draw_card in game.py
            drawn_card_id = self.game.draw_card(player)

            # TODO implement add_to_hand card in game.py
            self.game.add_to_hand(player, drawn_card_id)

    def _apply_exile_spell(self, targets: Set[str], player: str) -> None:
        """Apply exile effect."""
        for target_id in targets:
            target = self.game.find_target(target_id, player)
            if target:
                # TODO implement exile_target in game.py
                self.game.exile_target(target.id)

    def _apply_heal_spell(
        self, effect_text: str, targets: Set[str], player: str
    ) -> None:
        """Apply healing effect."""
        heal_amount = self._extract_number_from_text(effect_text) or 0

        for target_id in targets:
            target = self.game.find_target(target_id, player)
            if target and target.type == "PLAYER":
                # TODO implement health update in game.py preferably a class getter with target checks
                # for specific target types for certain card restrictions
                target.life += heal_amount

    def _apply_draw_on_tap(self, effect_text, player: str) -> None:
        """Apply draw-on-tap ability."""

        cards_to_draw = self._extract_number_from_text(effect_text) or 1
        for _ in range(cards_to_draw):
            # TODO implement draw_card in game.py
            drawn_card_id = self.game.draw_card(player)

            # TODO implement add_to_hand card in game.py
            self.game.add_to_hand(player, drawn_card_id)

    # Helper Methods
    # utility methods to help parse and validate effects

    def _extract_number_from_text(self, text: str) -> Optional[int]:
        """Extract the first number from text."""
        match = re.search(r"\d+", text)
        if match:
            return int(match.group())
        return None

    def _extract_effect_from_text(self, text: str) -> str:
        """Extract the first occurrence of 'damage', 'heal', or 'exile' from text."""
        match = re.search(r"\b(damage|heal|exile)\b", text, re.IGNORECASE)
        if match:
            return match.group()
        return None
