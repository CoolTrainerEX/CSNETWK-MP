"""Server-side card effects."""

import random
import re
from typing import TYPE_CHECKING, Any, Set, Optional

from packages.shared.cards import Card, CreatureCard, LandCard
from packages.shared.player import PlayerID
from packages.shared.pdu import StackItem

if TYPE_CHECKING:
    from packages.server.game import ServerPlayer


def validate_targets(
    card: Card,
    targets: set[str],
    player_map: dict[PlayerID, "ServerPlayer"],
    players: list["ServerPlayer"],
    stack: list[StackItem],
    controller: PlayerID = None,
) -> bool:
    """Validate targets for a card cast/activation."""
    if not targets:
        return True

    ability_details = card.cast_details()
    effect_text = ability_details.text.lower()
    if not effect_text and hasattr(card, "trigger_details"):
        effect_text = card.trigger_details()[1].lower()

    target_player = "target player" in effect_text or "opponent" in effect_text
    target_creature = "target creature" in effect_text or "tapped creature" in effect_text
    any_target = "any target" in effect_text

    for target in targets:
        is_player = target in player_map
        is_creature = False
        target_card_obj = None
        target_controller = None

        if not is_player:
            for p in players:
                if target in p.battlefield:
                    target_card_obj = p.battlefield[target].card
                    target_controller = p.id

                    if isinstance(target_card_obj, CreatureCard):
                        is_creature = True

                    break

        # Hexproof & Protection
        if target_card_obj:
            # protection from Black
            if target_card_obj.name() == "White Knight" and card.color() == Card.Color.B:
                return False

            # protection from White
            if target_card_obj.name() == "Black Knight" and card.color() == Card.Color.W:
                return False

            # Hexproof
            if CreatureCard.Modifier.HEXPROOF in target_card_obj.modifiers():
                if controller and target_controller != controller:
                    return False

        if any_target:
            if not is_player and not is_creature:
                return False
        elif target_player:
            if not is_player:
                return False
        elif target_creature:
            if not is_creature:
                return False

    return True


def apply_effect(
    card_obj: Card,
    targets: set[str],
    controller: PlayerID,
    player_map: dict[PlayerID, "ServerPlayer"],
    players: list["ServerPlayer"],
    stack: list[StackItem],
    eot_pumps: list[Any],
    is_trigger: bool = False,
    is_ability: bool = False,
) -> list[dict]:
    """Resolve a card's effect or enter-the-battlefield abilities."""
    effects = CardEffects(player_map, players, stack, eot_pumps)
    if is_trigger:
        return effects.trigger(card_obj, controller, targets)
    elif is_ability:
        return effects.activate(card_obj, controller, targets)
    return effects.resolve(card_obj, controller, targets)


class CardEffects:
    """Server-side card effect interpreter."""

    def __init__(
        self,
        player_map: dict[PlayerID, "ServerPlayer"],
        players: list["ServerPlayer"],
        stack: list[StackItem],
        eot_pumps: list[Any],
    ):
        self.player_map = player_map
        self.players = players
        self.stack = stack
        self.eot_pumps = eot_pumps

    def resolve(self, card_obj: Card, player: PlayerID, targets: Set[str]) -> list[dict]:
        """Main entry point for spell resolution."""
        text = card_obj.cast_details().text.lower()
        return self._execute_text(text, targets, player, card_obj)

    def activate(self, card_obj: Card, player: PlayerID, targets: Set[str]) -> list[dict]:
        """Main entry point for ability resolution."""
        state_changes = []

        if hasattr(card_obj, "abilities_details"):
            for ability in card_obj.abilities_details():
                text = ability.text.lower()
                state_changes.extend(self._execute_text(text, targets, player, card_obj))

        return state_changes

    def trigger(self, card_obj: Card, player: PlayerID, targets: Set[str]) -> list[dict]:
        """Main entry point for trigger resolution."""
        state_changes = []

        if hasattr(card_obj, "trigger_details"):
            text = card_obj.trigger_details()[1].lower()
            state_changes.extend(self._execute_text(text, targets, player, card_obj))

        return state_changes

    def _execute_text(self, text: str, targets: Set[str], player: PlayerID, card_obj: Card) -> list[dict]:
        """Parse the specific mechanics of the text and apply them."""
        state_changes = []

        # standard damage
        if "deals" in text and "damage" in text:
            state_changes.extend(self._apply_damage_spell(text, targets, player))

        # removals
        if "destroy" in text:
            state_changes.extend(self._apply_destroy_spell(targets))

        if "exile" in text:
            state_changes.extend(self._apply_exile_spell(text, targets, player))

        # draw and discard
        if "draw" in text and "discard" not in text:
            state_changes.extend(self._apply_draw_spell(text, player))

        if "draw a card, then discard a card" in text:
            self._apply_draw_spell("draw 1", player)
            self._apply_discard_effect("discard 1", {player})

        if "discards" in text:
            state_changes.extend(self._apply_discard_effect(text, targets))

        if "mills" in text:
            state_changes.extend(self._apply_mill_effect(text, targets))

        # life gain & drain
        if "gains" in text and "life" in text and "devotion" not in text:
            state_changes.extend(self._apply_heal_spell(text, targets, player))

        if "devotion to black" in text:
            state_changes.extend(self._apply_devotion_drain(player))

        # stack
        if "counter target spell" in text or "counter target noncreature spell" in text:
            state_changes.extend(self._apply_counter_spell(targets))

        # board & graveyard
        if "return target creature to its owner's hand" in text:
            state_changes.extend(self._apply_bounce_spell(targets))

        if "return target creature card from your graveyard" in text:
            state_changes.extend(self._apply_graveyard_return_spell(targets, player))

        # combat tricks
        if "gets +" in text or "gets -" in text:
            state_changes.extend(self._apply_pump_spell(text, targets, card_obj.id))

        # library searching
        if "search your library for a basic land" in text:
            state_changes.extend(self._apply_search_effect(player))

        # Phantasmal Bear
        if "sacrifice it" in text and card_obj.name() == "Phantasmal Bear":
            state_changes.extend(self._apply_destroy_spell({card_obj.id}))

        return state_changes

    # ----------------- Specific Effect Handlers -----------------

    def _apply_counter_spell(self, targets: Set[str]) -> list[dict]:
        state_changes = []

        for target_id in targets:
            for i, item in enumerate(self.stack):
                if item.stack_item_id == target_id:
                    self.stack.pop(i)
                    state_changes.append({"change_type": "destroy", "target": target_id, "amount": None})
                    break

        return state_changes

    def _apply_bounce_spell(self, targets: Set[str]) -> list[dict]:
        state_changes = []

        for target_id in targets:
            for p in self.players:
                if target_id in p.battlefield:
                    entry = p.battlefield.pop(target_id)
                    p.hand.add(entry.card)
                    state_changes.append({"change_type": "destroy", "target": target_id, "amount": None})
                    break

        return state_changes

    def _apply_pump_spell(self, effect_text: str, targets: Set[str], source_id: str) -> list[dict]:
        state_changes = []
        match = re.search(r"([+-])([0-9]+)/([+-])([0-9]+)", effect_text)

        if match:
            p_sign, p_val, t_sign, t_val = match.groups()
            power_bonus = int(p_val) if p_sign == '+' else -int(p_val)
            toughness_bonus = int(t_val) if t_sign == '+' else -int(t_val)

            from packages.server.game import _PumpEffect
            for target_id in targets:
                self.eot_pumps.append(_PumpEffect(card_id=target_id, power_bonus=power_bonus, toughness_bonus=toughness_bonus))

        return state_changes

    def _apply_damage_spell(self, effect_text: str, targets: Set[str], player: PlayerID) -> list[dict]:
        state_changes = []
        damage = self._extract_number_from_text(effect_text)

        if damage is None:
            return state_changes

        for target_id in targets:
            target = self.find_target(target_id)
            if not target:
                continue

            if hasattr(target, "life_total"):
                target._life -= damage
            else:
                target.damage += damage

            state_changes.append({"change_type": "damage", "target": target_id, "amount": damage})

        return state_changes

    def _apply_draw_spell(self, effect_text: str, player: PlayerID) -> list[dict]:
        cards_to_draw = self._extract_number_from_text(effect_text) or 1
        target_player = self.player_map.get(player)

        if target_player:
            for _ in range(cards_to_draw):
                target_player.draw_card()

        return []

    def _apply_exile_spell(self, text: str, targets: Set[str], player: PlayerID) -> list[dict]:
        state_changes = []
        for target_id in targets:
            for p in self.players:
                if target_id in p.battlefield:
                    entry = p.battlefield[target_id]

                    # Swords to Plowshares healing
                    if "gains life equal to its power" in text:
                        pb = sum(e.power_bonus for e in self.eot_pumps if e.card_id == target_id)
                        power = entry.card.base_power() + pb
                        p._life += power
                        state_changes.append({"change_type": "life_gain", "target": p.id, "amount": power})

                    # Path to Exile search
                    if "search for a basic land" in text:
                        self._apply_search_effect(p.id)

                    del p.battlefield[target_id]
                    state_changes.append({"change_type": "destroy", "target": target_id, "amount": None})
                    break
        return state_changes

    def _apply_heal_spell(self, effect_text: str, targets: Set[str], player: PlayerID) -> list[dict]:
        state_changes = []
        heal_amount = self._extract_number_from_text(effect_text) or 0

        for target_id in targets:
            target = self.find_target(target_id)
            if target and hasattr(target, "life_total"):
                target._life += heal_amount
                state_changes.append({"change_type": "life_gain", "target": target_id, "amount": heal_amount})

        return state_changes

    def _apply_destroy_spell(self, targets: Set[str]) -> list[dict]:
        state_changes = []

        for target_id in targets:
            for p in self.players:
                if target_id in p.battlefield:
                    p.send_to_graveyard_from_battlefield(target_id)
                    state_changes.append({"change_type": "destroy", "target": target_id, "amount": None})
                    break

        return state_changes

    def _apply_graveyard_return_spell(self, targets: Set[str], player: PlayerID) -> list[dict]:
        p = self.player_map.get(player)

        if p:
            for target_id in targets:
                if target_id in p.graveyard:
                    p.graveyard.remove(target_id)
                    card_instance = Card.from_id(target_id)(target_id)
                    p.hand.add(card_instance)

        return []

    def _apply_discard_effect(self, text: str, targets: Set[str]) -> list[dict]:
        amount = self._extract_number_from_text(text) or 1

        for target_id in targets:
            p = self.player_map.get(target_id)

            if p:
                for _ in range(min(amount, len(p.hand))):
                    card = random.choice(list(p.hand))
                    p.hand.remove(card)
                    p.graveyard.append(card.id)

        return []

    def _apply_search_effect(self, player: PlayerID) -> list[dict]:
        p = self.player_map.get(player)

        if p:
            for i, card in enumerate(p._library):
                if isinstance(card, LandCard):
                    land = p._library.pop(i)
                    p.put_to_battlefield(land, summoning_sick=False)
                    p.tap(land.id)
                    p.shuffle_library()
                    break

        return []

    def _apply_mill_effect(self, text: str, targets: Set[str]) -> list[dict]:
        amount = self._extract_number_from_text(text) or 2

        for target_id in targets:
            p = self.player_map.get(target_id)

            if p:
                for _ in range(min(amount, len(p.library))):
                    card = p.library.pop(0)
                    p.graveyard.append(card.id)

        return []

    def _apply_devotion_drain(self, player: PlayerID) -> list[dict]:
        p = self.player_map.get(player)
        if not p: return []
        devotion = 0

        for cid, entry in p.battlefield.items():
            cost = entry.card.cast_details().mana_cost
            devotion += cost.get(Card.Color.B, 0)

        state_changes = []

        for opp in self.players:
            if opp.id != player:
                opp._life -= devotion
                state_changes.append({"change_type": "damage", "target": opp.id, "amount": devotion})

        p._life += devotion
        state_changes.append({"change_type": "life_gain", "target": player, "amount": devotion})
        return state_changes

    # ----------------- Helper Methods -----------------

    def find_target(self, target_id: str) -> Any:
        if target_id in self.player_map:
            return self.player_map[target_id]

        for p in self.players:
            if target_id in p.battlefield:
                return p.battlefield[target_id]

        return None

    def _extract_number_from_text(self, text: str) -> Optional[int]:
        match = re.search(r"\d+", text)
        return int(match.group()) if match else None
