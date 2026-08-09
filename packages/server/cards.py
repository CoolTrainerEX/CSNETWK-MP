"""Server-side card effects."""

import re
from typing import TYPE_CHECKING, Any, Set, Optional

from packages.shared.cards import Card, CreatureCard
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
) -> bool:
    """Validate targets for a card cast/activation."""
    if not targets:
        return True
        
    ability_details = card.cast_details()
    effect_text = ability_details.text.lower()
    
    target_player = "target player" in effect_text
    target_creature = "target creature" in effect_text
    any_target = "any target" in effect_text
    
    # did a simple validation here, but we could do more complex validation if needed
    for target in targets:
        is_player = target in player_map
        
        is_creature = False
        if not is_player:
            for p in players:
                if target in p.battlefield:
                    if isinstance(p.battlefield[target].card, CreatureCard):
                        is_creature = True
                    break
                    
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
    eot_pumps: dict[str, list[tuple[int, int]]],
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
        eot_pumps: dict[str, list[tuple[int, int]]],
    ):
        self.player_map = player_map
        self.players = players
        self.stack = stack
        self.eot_pumps = eot_pumps

    def resolve(self, card_obj: Card, player: PlayerID, targets: Set[str]) -> list[dict]:
        """Main entry point for spell resolution."""
        return self._apply_cast_details(card_obj, player, targets)

    def activate(
        self,
        card_obj: Card,
        player: PlayerID,
        targets: Set[str],
    ) -> list[dict]:
        """Main entry point for ability resolution."""
        return self._apply_ability_details(card_obj, player, targets)

    # added this trigger method to handle triggered abilities, 
    # the routing is just different sa priority.py, its to make it kinda organized
    def trigger(
        self,
        card_obj: Card,
        player: PlayerID,
        targets: Set[str],
    ) -> list[dict]:
        """Main entry point for trigger resolution."""
        return self._apply_ability_details(card_obj, player, targets)

    # ----------------- PRIVATE EFFECT HANDLERS -----------------

    def _apply_cast_details(
        self,
        card_obj: Card,
        player: PlayerID,
        targets: Set[str],
    ) -> list[dict]:
        """Parse the spell's cast details and apply the effect."""
        ability_details = card_obj.cast_details()
        effect_text = ability_details.text
        
        effect = self._extract_effect_from_text(effect_text)
        
        if effect == "damage":
            return self._apply_damage_spell(effect_text, targets, player)
        elif effect == "exile":
            return self._apply_exile_spell(targets, player)
        elif effect == "heal":
            return self._apply_heal_spell(effect_text, targets, player)
        elif effect == "draw":
            return self._apply_draw_spell(effect_text, player)
        elif effect == "counter":
            return self._apply_counter_spell(targets)
        elif effect == "return":
            return self._apply_bounce_spell(targets)
        elif effect == "gets":
            return self._apply_pump_spell(effect_text, targets, card_obj.id)
            
        return []

    def _apply_ability_details(
        self,
        card_obj: Card,
        player: PlayerID,
        targets: Set[str],
    ) -> list[dict]:
        """Parse ability details and apply the effect."""
        state_changes = []
        if not hasattr(card_obj, "abilities_details"):
            return state_changes
            
        for ability in card_obj.abilities_details():
            effect_text = ability.text
            if not effect_text:
                continue
                
            effect = self._extract_effect_from_text(effect_text)
            
            if effect == "damage":
                state_changes.extend(self._apply_damage_spell(effect_text, targets, player))
            elif effect == "exile":
                state_changes.extend(self._apply_exile_spell(targets, player))
            elif effect == "heal":
                state_changes.extend(self._apply_heal_spell(effect_text, targets, player))
            elif effect == "draw":
                state_changes.extend(self._apply_draw_spell(effect_text, player))
            elif effect == "counter":
                state_changes.extend(self._apply_counter_spell(targets))
            elif effect == "return":
                state_changes.extend(self._apply_bounce_spell(targets))
            elif effect == "gets":
                state_changes.extend(self._apply_pump_spell(effect_text, targets, card_obj.id))
                
        return state_changes

    # Specific Effect Handlers

    def _apply_counter_spell(self, targets: Set[str]) -> list[dict]:
        """Apply counter spell effect."""
        state_changes = []
        for target_id in targets:
            # target_id should be a stack_item_id
            for i, item in enumerate(self.stack):
                if item.stack_item_id == target_id:
                    # Remove from stack
                    self.stack.pop(i)
                    state_changes.append({
                        "change_type": "destroy",
                        "target": target_id,
                        "amount": None
                    })
                    break
        return state_changes

    def _apply_bounce_spell(self, targets: Set[str]) -> list[dict]:
        """Apply bounce (return to hand) effect."""
        state_changes = []
        for target_id in targets:
            for p in self.players:
                if target_id in p.battlefield:
                    entry = p.battlefield.pop(target_id)
                    p.hand.add(entry.card)
                    state_changes.append({
                        "change_type": "destroy", # "destroy" is the only removal change_type in StackResolve
                        "target": target_id,
                        "amount": None
                    })
                    break
        return state_changes

    def _apply_pump_spell(self, effect_text: str, targets: Set[str], source_id: str) -> list[dict]:
        """Apply stat pump (e.g., +3/+3) effect."""
        state_changes = []
        
        # e.g., "gets +3/+3"
        match = re.search(r"\+([0-9]+)/\+([0-9]+)", effect_text)
        if match:
            power_bonus = int(match.group(1))
            toughness_bonus = int(match.group(2))
            
            for target_id in targets:
                if target_id not in self.eot_pumps:
                    self.eot_pumps[target_id] = []
                self.eot_pumps[target_id].append((power_bonus, toughness_bonus))
                # State change for pump? StackResolve.__StateChange doesn't have STAT_CHANGE.
                # The GSU will naturally update it.

        return state_changes

    def _apply_damage_spell(
        self, effect_text: str, targets: Set[str], player: PlayerID
    ) -> list[dict]:
        """Apply damage based on spell effect text."""
        state_changes = []
        damage = self._extract_number_from_text(effect_text)

        if damage is None:
            return state_changes

        # Apply damage to each target
        for target_id in targets:
            target = self.find_target(target_id)
            if not target:
                continue

            if hasattr(target, "life_total"):
                target._life -= damage
            else:
                target.damage += damage
                
            state_changes.append({
                "change_type": "damage", 
                "target": target_id,
                "amount": damage
            })
            
        return state_changes

    def _apply_draw_spell(self, effect_text: str, player: PlayerID) -> list[dict]:
        """Apply card draw effect."""
        cards_to_draw = self._extract_number_from_text(effect_text) or 1
        
        target_player = self.player_map.get(player)
        if target_player:
            for _ in range(cards_to_draw):
                target_player.draw_card()
                
        return []

    def _apply_exile_spell(self, targets: Set[str], player: PlayerID) -> list[dict]:
        """Apply exile effect."""
        state_changes = []
        for target_id in targets:
            for p in self.players:
                if target_id in p.battlefield:
                    del p.battlefield[target_id]
                    state_changes.append({
                        "change_type": "destroy", 
                        "target": target_id,
                        "amount": None
                    })
                    break
        return state_changes

    def _apply_heal_spell(
        self, effect_text: str, targets: Set[str], player: PlayerID
    ) -> list[dict]:
        """Apply healing effect."""
        state_changes = []
        heal_amount = self._extract_number_from_text(effect_text) or 0

        for target_id in targets:
            target = self.find_target(target_id)
            if target and hasattr(target, "life_total"):
                target._life += heal_amount
                state_changes.append({
                    "change_type": "life_gain",
                    "target": target_id,
                    "amount": heal_amount
                })
                
        return state_changes

    # Helper Methods

    def find_target(self, target_id: str) -> Any:
        """Find a target player or creature entry."""
        if target_id in self.player_map:
            return self.player_map[target_id]
            
        for p in self.players:
            if target_id in p.battlefield:
                return p.battlefield[target_id]
                
        return None

    def _extract_number_from_text(self, text: str) -> Optional[int]:
        """Extract the first number from text."""
        match = re.search(r"\d+", text)
        if match:
            return int(match.group())
        return None

    def _extract_effect_from_text(self, text: str) -> str:
        """Extract the first occurrence of effect keywords from text."""
        match = re.search(r"\b(damage|heal|exile|draw|counter|return|gets)\b", text, re.IGNORECASE)
        if match:
            return match.group().lower()
        return ""
