"""Server-side trigger engine."""

# this ano, this is for handling triggered abilitiess, i forgot to consider this pala

from typing import TYPE_CHECKING, Any, Dict, Optional
from pydantic import BaseModel

from packages.shared.cards import Card
from packages.shared.pdu import StackItem, TriggerOrder, TriggerChoice
from packages.shared.player import PlayerID

if TYPE_CHECKING:
    from packages.server.game import ServerGame


class PendingTrigger(BaseModel):
    """Internal representation of a triggered ability waiting to be stacked."""

    trigger_id: str
    source_id: str
    controller_id: PlayerID
    effect_summary: str
    requires_target: bool = False
    is_optional: bool = False
    targets: list[str] = []


class TriggerEngine:
    """Detects and manages triggered abilities according to MTGNP specs."""

    def __init__(self, game: "ServerGame"):
        self.game = game
        self._trigger_counter = 0

        # Queue of triggers waiting for player ordering (by player)
        self.pending_ordering: dict[PlayerID, list[PendingTrigger]] = {}
        # Queue of triggers waiting for optional "you may" or target selection (by player)
        self.pending_choices: dict[PlayerID, list[PendingTrigger]] = {}

        # Triggers waiting to be pushed to the stack (already ordered/accepted)
        # Format: (controller_id, trigger_obj)
        self.ready_triggers: list[tuple[PlayerID, PendingTrigger]] = []

    def dispatch(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Scan all permanents for triggered abilities matching event_type.
        Known event types:
        - "ETB": data={"source_id": CardID, "controller_id": PlayerID}
        - "ATTACKS": data={"source_id": CardID, "controller_id": PlayerID}
        - "CAST_SPELL": data={"source_id": CardID, "controller_id": PlayerID, "card": Card}
        - "TARGETED": data={"source_id": CardID, "controller_id": PlayerID}
        """
        new_triggers = []

        # Scan all battlefields
        for p in self.game._players:
            for cid, entry in p.battlefield.items():
                card = entry.card
                abilities = card.abilities_details()
                if not abilities:
                    continue

                for idx, ab in enumerate(abilities):
                    text = ab.text.lower()

                    # ETB Triggers ("When this enters" or "When [Name] enters")
                    if event_type == "ETB" and data["source_id"] == cid:
                        if "enters" in text and ("when" in text or "whenever" in text):
                            new_triggers.append(
                                self._create_trigger(cid, p.id, ab.text)
                            )

                    # Attack Triggers
                    elif event_type == "ATTACKS" and data["source_id"] == cid:
                        if "attacks" in text and ("when" in text or "whenever" in text):
                            new_triggers.append(
                                self._create_trigger(cid, p.id, ab.text)
                            )

                    # Cast Spell Triggers (e.g. Prowess)
                    elif event_type == "CAST_SPELL" and data["controller_id"] == p.id:
                        if "whenever you cast" in text:
                            new_triggers.append(
                                self._create_trigger(cid, p.id, ab.text)
                            )

                    # Targeted Triggers (e.g. Phantasmal Bear)
                    elif event_type == "TARGETED" and data["source_id"] == cid:
                        if "becomes the target" in text:
                            new_triggers.append(
                                self._create_trigger(cid, p.id, ab.text)
                            )

        if new_triggers:
            self._queue_triggers(new_triggers)

    def _create_trigger(
        self, source_id: str, controller: PlayerID, text: str
    ) -> PendingTrigger:
        self._trigger_counter += 1
        tid = Card.from_id(source_id).trigger_details()[0]

        # Check if optional
        is_optional = "you may" in text.lower()
        requires_target = (
            "target" in text.lower() and "becomes the target" not in text.lower()
        )

        return PendingTrigger(
            trigger_id=tid,
            source_id=source_id,
            controller_id=controller,
            effect_summary=text,
            is_optional=is_optional,
            requires_target=requires_target,
        )

    def _queue_triggers(self, triggers: list[PendingTrigger]) -> None:
        """Group triggers by controller. Single triggers bypass ordering."""
        # Group by player
        grouped = {}
        for t in triggers:
            grouped.setdefault(t.controller_id, []).append(t)

        for player_id, p_triggers in grouped.items():
            if len(p_triggers) > 1:
                # Need ordering
                if player_id not in self.pending_ordering:
                    self.pending_ordering[player_id] = []
                self.pending_ordering[player_id].extend(p_triggers)
            else:
                # Only 1 trigger, goes straight to choices (or ready)
                self._queue_for_choice(p_triggers[0])

    def _queue_for_choice(self, trigger: PendingTrigger) -> None:
        """Queue a trigger for optional accept/decline or target selection."""
        if trigger.is_optional or trigger.requires_target:
            if trigger.controller_id not in self.pending_choices:
                self.pending_choices[trigger.controller_id] = []
            self.pending_choices[trigger.controller_id].append(trigger)
        else:
            self.ready_triggers.append((trigger.controller_id, trigger))

    def get_pending_interaction(self, result: dict) -> Optional[Any]:
        """
        Called by game.py before granting priority.
        Returns the next PDU (player_id, TRIGGER_ORDER or TRIGGER_CHOICE) to send, or None.
        If it pushes to stack, it populates `result` with STACK_PUSH messages and returns True.
        """
        # Check for Pending Ordering
        for player_id, triggers in self.pending_ordering.items():
            if triggers:
                self.game._seq_num += 1
                self.game._priority_seq_num = self.game._seq_num

                return (
                    player_id,
                    TriggerOrder(
                        seq_num=self.game._seq_num,
                        player_id=player_id,
                        trigger_ids=[t.trigger_id for t in triggers],
                    ),
                )

        # Check for Pending Choices
        for player_id, triggers in self.pending_choices.items():
            if triggers:
                t = triggers[0]
                self.game._seq_num += 1
                self.game._priority_seq_num = self.game._seq_num

                return (
                    player_id,
                    TriggerChoice(
                        seq_num=self.game._seq_num,
                        trigger_id=t.trigger_id,
                        source_id=t.source_id,
                        effect_summary=t.effect_summary,
                        legal_targets={},
                        requires_target=t.requires_target,
                    ),
                )

        # Push Ready Triggers to Stack
        # Triggers are placed: AP first (resolves last), NAP last (resolves first)
        if self.ready_triggers:
            ap_id = self.game._ap().id

            # Sort: AP triggers first, then NAP
            self.ready_triggers.sort(key=lambda item: 0 if item[0] == ap_id else 1)

            from packages.server.game import _StackEntry
            from packages.shared.pdu import StackPush

            for controller, t in self.ready_triggers:
                self.game._stack_counter += 1
                sid = f"stk_{self.game._stack_counter:03d}"

                # Retrieve the card obj
                player_obj = self.game._player_map.get(controller)
                card_obj = (
                    player_obj.battlefield[t.source_id].card
                    if player_obj and t.source_id in player_obj.battlefield
                    else None
                )

                self.game._stack.append(
                    _StackEntry(
                        stack_item_id=sid,
                        item_type=StackItem.ItemType.TRIGGER_ABILITY,
                        source=t.source_id,
                        targets=t.targets,
                        controller=controller,
                        card_obj=card_obj,
                        is_permanent=False,
                    )
                )

                self.game._seq_num += 1
                sp = StackPush(
                    seq_num=self.game._seq_num,
                    stack_item_id=sid,
                    item_type=StackItem.ItemType.TRIGGER_ABILITY,
                    source=t.source_id,
                    targets=t.targets,
                    cotroller=controller,
                )
                for p in self.game._players:
                    result.setdefault(p.id, []).append(sp)

            self.ready_triggers.clear()

            return True

        return None

    def resolve_order(self, player_id: PlayerID, ordered_ids: list[str]) -> bool:
        """Resolve a TRIGGER_ORDER_RESPONSE."""
        if player_id not in self.pending_ordering:
            return False

        triggers = self.pending_ordering[player_id]
        if set(ordered_ids) != set([t.trigger_id for t in triggers]):
            return False

        # Reorder them based on player preference
        ordered_triggers = []
        for tid in reversed(ordered_ids):
            for t in triggers:
                if t.trigger_id == tid:
                    ordered_triggers.append(t)
                    break

        for t in ordered_triggers:
            self._queue_for_choice(t)

        del self.pending_ordering[player_id]
        return True

    def resolve_choice(
        self,
        player_id: PlayerID,
        trigger_id: str,
        accept: bool,
        chosen_target: Optional[str],
    ) -> bool:
        """Resolve a TRIGGER_CHOICE_RESPONSE."""
        if player_id not in self.pending_choices or not self.pending_choices[player_id]:
            return False

        t = self.pending_choices[player_id][0]
        if t.trigger_id != trigger_id:
            return False

        # Remove from pending
        self.pending_choices[player_id].pop(0)

        if accept:
            if t.requires_target and chosen_target:
                t.targets.append(chosen_target)
            self.ready_triggers.append((t.controller_id, t))

        return True
