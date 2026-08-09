"""Server logic implementation."""

import random
from dataclasses import dataclass
from typing import Any, Sequence

from packages.shared.cards import (
    ArtifactCard,
    Card,
    CardID,
    CreatureCard,
    EnchantmentCard,
    LandCard,
    SorceryCard,
    # Mana-producing lands
    Mountain,
    Forest,
    Plains,
    Island,
    Swamp,
    # Mana-producing creatures
    LlanowarElves,
    ElvishMystic,
)
from packages.shared.game import CombatStep, Game, GamePhase, State
from packages.shared.pdu import (
    PDU,
    ActivateAbility,
    AssignDamageOrder,
    CastSpell,
    CombatDamageResult,
    Concede,
    DeclareAttackers,
    DeclareBlockers,
    Discard,
    Error,
    GameOver,
    GameStateUpdate,
    MulliganChoice,
    PhaseTransition,
    PlayLand,
    PlayerReady,
    PriorityGrant,
    PriorityPass,
    StackItem,
    StackPush,
    StackResolve,
    Type,
)
from packages.shared.player import Player, PlayerID
from packages.server.cards import apply_effect, validate_targets

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_MANA_PRODUCERS: dict[type[Card], Card.Color] = {
    Mountain: Card.Color.R,
    Forest: Card.Color.G,
    Plains: Card.Color.W,
    Island: Card.Color.U,
    Swamp: Card.Color.B,
    LlanowarElves: Card.Color.G,
    ElvishMystic: Card.Color.G,
}


# ---------------------------------------------------------------------------
# Internal data classes
# ---------------------------------------------------------------------------


@dataclass
class _BFEntry:
    """A card placed on the battlefield (server-only view)."""

    card: Card
    tapped: bool = False
    summoning_sick: bool = False
    damage: int = 0


@dataclass
class _StackEntry:
    """An item sitting on the stack (server-only view)."""

    stack_item_id: str
    item_type: StackItem.ItemType
    source: CardID
    targets: list[str]
    controller: PlayerID
    card_obj: Card
    is_permanent: bool


@dataclass
class _PumpEffect:
    """A +N/+N pump lasting until end of turn."""

    card_id: CardID
    power_bonus: int
    toughness_bonus: int


@dataclass
class _AttackerInfo:
    """One declared attacker."""

    creature_id: CardID
    target_player: PlayerID
    is_blocked: bool = False


# ---------------------------------------------------------------------------
# ServerPlayer
# ---------------------------------------------------------------------------


class ServerPlayer(Player):
    """Server player view."""

    def __init__(self, id: PlayerID, deck: list[Card]) -> None:
        """Creates a server player.

        Args:
            id (PlayerID): Player ID
            deck (list[Card]): Shuffled deck (index 0 = top of library)
        """
        super().__init__(id)
        self._library: list[Card] = deck
        self._hand: set[Card] = set()
        self._battlefield: dict[CardID, _BFEntry] = {}
        self._graveyard: list[CardID] = []
        self._life: int = 20

    # --- Properties ---

    @property
    def life_total(self) -> int:
        return self._life

    @property
    def library(self) -> list[Card]:
        """Player library (index 0 = top)."""
        return self._library

    @property
    def hand(self) -> set[Card]:
        return self._hand

    @property
    def battlefield(self) -> dict[CardID, _BFEntry]:
        return self._battlefield

    @property
    def graveyard(self) -> list[CardID]:
        return self._graveyard

    # --- Mutators ---

    def draw_card(self) -> Card | None:
        """Draw the top card into hand. Returns the card or None if library empty."""
        if not self._library:
            return None
        card = self._library.pop(0)
        self._hand.add(card)
        return card

    def card_in_hand(self, card_id: CardID) -> Card | None:
        """Return the Card object with *card_id* from hand, or None."""
        for c in self._hand:
            if c.id == card_id:
                return c
        return None

    def remove_from_hand(self, card: Card) -> None:
        """Remove *card* from hand (no-op if not present)."""
        self._hand.discard(card)

    def put_to_battlefield(self, card: Card, *, summoning_sick: bool = False) -> None:
        """Move *card* to this player's battlefield."""
        self._battlefield[card.id] = _BFEntry(
            card=card, tapped=False, summoning_sick=summoning_sick, damage=0
        )

    def remove_from_battlefield(self, card_id: CardID) -> _BFEntry | None:
        """Remove and return the battlefield entry for *card_id*."""
        return self._battlefield.pop(card_id, None)

    def send_to_graveyard_from_battlefield(self, card_id: CardID) -> None:
        """Move *card_id* from battlefield to graveyard (insertion-ordered)."""
        if card_id in self._battlefield:
            del self._battlefield[card_id]
            self._graveyard.append(card_id)

    def bounce_to_hand(self, card_id: CardID) -> None:
        """Return *card_id* from battlefield to hand."""
        entry = self.remove_from_battlefield(card_id)
        if entry:
            self._hand.add(entry.card)

    def untap_all(self) -> None:
        """Untap every permanent on this player's battlefield."""
        for e in self._battlefield.values():
            e.tapped = False

    def clear_summoning_sickness(self) -> None:
        """Remove summoning sickness from all permanents."""
        for e in self._battlefield.values():
            e.summoning_sick = False

    def tap(self, card_id: CardID) -> bool:
        """Tap *card_id*. Returns True on success, False if absent or already tapped."""
        entry = self._battlefield.get(card_id)
        if entry and not entry.tapped:
            entry.tapped = True
            return True
        return False

    def bottom_cards(self, card_ids: set[CardID]) -> None:
        """Put *card_ids* from hand to the bottom of the library."""
        to_bottom: list[Card] = []
        for cid in card_ids:
            card = self.card_in_hand(cid)
            if card:
                self._hand.discard(card)
                to_bottom.append(card)
        self._library.extend(to_bottom)

    def shuffle_library(self) -> None:
        """Shuffle the library in place."""
        random.shuffle(self._library)

    def return_hand_to_library(self) -> None:
        """Return all hand cards to library and shuffle."""
        self._library.extend(self._hand)
        self._hand.clear()
        self.shuffle_library()


# ---------------------------------------------------------------------------
# ServerGame
# ---------------------------------------------------------------------------


from packages.server.priority import PriorityMixin
from packages.server.utilities import UtilitiesMixin


class ServerGame(PriorityMixin, UtilitiesMixin, Game):
    """Server-side game implementing RFC 0001 MTGNP v1.0."""

    def __init__(self) -> None:
        """Create a game instance."""
        super().__init__()

        # Players
        self._players: list[ServerPlayer] = []
        self._player_map: dict[PlayerID, ServerPlayer] = {}

        # Turn / phase
        self._active_player_idx: int = 0
        self._first_player_idx: int = 0
        self._turn: int = 0
        self._is_first_turn: bool = True
        self._land_played_this_turn: bool = False

        # Priority
        self._priority_holder_idx: int | None = None
        self._priority_seq_num: int = 0
        self._consecutive_passes: int = 0

        # Stack
        self._stack: list[_StackEntry] = []
        self._stack_counter: int = 0

        # Mulligan
        self._mulligan_counts: dict[PlayerID, int] = {}
        self._mulligan_done: dict[PlayerID, bool] = {}
        self._mulligan_gsu_seq: dict[PlayerID, int] = {}

        # Combat
        self._attackers: list[_AttackerInfo] = []
        self._blockers: dict[CardID, list[CardID]] = {}
        self._damage_order: dict[CardID, list[CardID]] = {}
        self._pending_damage_orders: set[CardID] = set()
        self._declare_attackers_seq_num: int = 0
        self._declare_blockers_seq_num: int = 0
        self._assign_damage_order_seq_num: int = 0

        # End-of-turn pump effects
        self._eot_pumps: list[_PumpEffect] = []

        # Cleanup discard sub-state
        self._discard_player: PlayerID | None = None
        self._discard_gsu_seq: int = 0

    # -----------------------------------------------------------------------
    # Public interface
    # -----------------------------------------------------------------------

    def run(self, pdu: PDU, player: PlayerID) -> dict[PlayerID, Sequence[PDU]]:
        """Run on receive.

        Args:
            pdu (PDU): PDU received
            player (PlayerID): Player who sent

        Returns:
            dict[PlayerID, Sequence[PDU]]: PDUs to send
        """
        # CONCEDE is valid at any time
        if pdu.type == Type.CONCEDE:
            return self._handle_concede(pdu, player)

        if self._priority_holder_idx is not None:
            return self._handle_priority_pdu(pdu, player)

        match self.state:
            case State.LOBBY:
                from packages.server.states.lobby import handle_lobby

                return handle_lobby(self, pdu, player)
            case State.GAME_SETUP:
                from packages.server.states.game_setup import handle_game_setup

                return handle_game_setup(self, pdu, player)
            case State.MULLIGAN:
                from packages.server.states.mulligan import handle_mulligan

                return handle_mulligan(self, pdu, player)
            case GamePhase.UNTAP:
                return self._untap(pdu, player)
            case GamePhase.UPKEEP:
                return self._upkeep(pdu, player)
            case GamePhase.DRAW:
                return self._draw(pdu, player)
            case GamePhase.PRECOMBAT_MAIN:
                return self._precombat_main(pdu, player)
            case CombatStep.BEGIN_COMBAT:
                return self._begin_combat(pdu, player)
            case CombatStep.DECLARE_ATTACKERS:
                return self._declare_attackers(pdu, player)
            case CombatStep.DECLARE_BLOCKERS:
                return self._declare_blockers(pdu, player)
            case CombatStep.ASSIGN_DAMAGE_ORDER:
                return self._assign_damage_order(pdu, player)
            case CombatStep.FIRST_STRIKE_DAMAGE:
                return self._first_strike_damage(pdu, player)
            case CombatStep.COMBAT_DAMAGE:
                return self._combat_damage(pdu, player)
            case CombatStep.END_OF_COMBAT:
                return self._end_of_combat(pdu, player)
            case GamePhase.POSTCOMBAT_MAIN:
                return self._postcombat_main(pdu, player)
            case GamePhase.END_STEP:
                return self._end_step(pdu, player)
            case GamePhase.CLEANUP:
                return self._cleanup(pdu, player)
            case State.GAME_OVER:
                from packages.server.states.game_over import handle_game_over

                return handle_game_over(self, pdu, player)
            case _:
                return {}

    def disconnect(self, player: PlayerID) -> dict[PlayerID, Sequence[PDU]]:
        """Player disconnected.

        Args:
            player (PlayerID): Player who disconnected

        Returns:
            dict[PlayerID, Sequence[PDU]]: PDUs to send
        """
        result: dict[PlayerID, list[PDU]] = {p.id: [] for p in self._players}

        if self.state not in (State.LOBBY, State.GAME_OVER) and len(self._players) == 2:
            winner = self._opponent_of_id(player)
            if winner:
                self._seq_num += 1
                go = GameOver(
                    seq_num=self._seq_num,
                    winner_id=winner.id,
                    loser_id=player,
                    reason=GameOver.Reason.DISCONNECT,
                )
                result[winner.id].append(go)

        self._reset_to_lobby()
        return result

    # -----------------------------------------------------------------------
    # Phase-advance dispatcher
    # -----------------------------------------------------------------------

    def _advance_phase(self, result: dict) -> None:
        """Advance to the next step/phase after both players pass with an empty stack."""
        cur = self.state
        if cur == GamePhase.UPKEEP:
            self._do_draw(result)
        elif cur == GamePhase.DRAW:
            self._do_precombat_main(result)
        elif cur == GamePhase.PRECOMBAT_MAIN:
            self._do_begin_combat(result)
        elif cur == CombatStep.BEGIN_COMBAT:
            self._do_declare_attackers_step(result)
        elif cur == CombatStep.DECLARE_ATTACKERS:
            self._do_declare_blockers_step(result)
        elif cur == CombatStep.DECLARE_BLOCKERS:
            has_multi = any(len(bs) >= 2 for bs in self._blockers.values())
            if has_multi:
                self._do_assign_damage_order_step(result)
            else:
                self._do_transition_to_damage(result)
        elif cur == CombatStep.ASSIGN_DAMAGE_ORDER:
            self._do_transition_to_damage(result)
        elif cur == CombatStep.FIRST_STRIKE_DAMAGE:
            self._do_combat_damage(result)
        elif cur == CombatStep.END_OF_COMBAT:
            self._do_postcombat_main(result)
        elif cur == GamePhase.POSTCOMBAT_MAIN:
            self._do_end_step(result)
        elif cur == GamePhase.END_STEP:
            self._do_cleanup(result)

    # -----------------------------------------------------------------------
    # Phase transition helpers
    # -----------------------------------------------------------------------

    def _do_draw(self, result: dict) -> None:
        from_phase = self.state
        self.state = GamePhase.DRAW
        self._broadcast_pt(from_phase, GamePhase.DRAW, result)
        ap = self._ap()
        # First player skips drawing on turn 1
        skip = self._is_first_turn and self._active_player_idx == self._first_player_idx
        if not skip:
            drawn = ap.draw_card()
            if drawn is None:
                self._emit_game_over(
                    self._nap(), ap, GameOver.Reason.DECK_EMPTY, result
                )
                return
        self._broadcast_gsu(result)
        self._open_priority(result)

    def _do_precombat_main(self, result: dict) -> None:
        from_phase = self.state
        self.state = GamePhase.PRECOMBAT_MAIN
        self._broadcast_pt(from_phase, GamePhase.PRECOMBAT_MAIN, result)
        self._open_priority(result)

    def _do_begin_combat(self, result: dict) -> None:
        from_phase = self.state
        self.state = CombatStep.BEGIN_COMBAT
        self._broadcast_pt(from_phase, CombatStep.BEGIN_COMBAT, result)
        self._open_priority(result)

    def _do_declare_attackers_step(self, result: dict) -> None:
        from_phase = self.state
        self.state = CombatStep.DECLARE_ATTACKERS
        self._priority_holder_idx = None
        self._seq_num += 1
        self._declare_attackers_seq_num = self._seq_num
        pt = PhaseTransition(
            seq_num=self._seq_num,
            from_phase=from_phase,
            to_phase=CombatStep.DECLARE_ATTACKERS,
            active_player=self._ap().id,
            turn=self._turn,
        )
        for p in self._players:
            result[p.id].append(pt)

    def _do_declare_blockers_step(self, result: dict) -> None:
        from_phase = self.state
        self.state = CombatStep.DECLARE_BLOCKERS
        self._priority_holder_idx = None
        self._seq_num += 1
        self._declare_blockers_seq_num = self._seq_num
        pt = PhaseTransition(
            seq_num=self._seq_num,
            from_phase=from_phase,
            to_phase=CombatStep.DECLARE_BLOCKERS,
            active_player=self._ap().id,
            turn=self._turn,
        )
        for p in self._players:
            result[p.id].append(pt)

    def _do_assign_damage_order_step(self, result: dict) -> None:
        from_phase = self.state
        self.state = CombatStep.ASSIGN_DAMAGE_ORDER
        self._priority_holder_idx = None
        self._pending_damage_orders = {
            a.creature_id
            for a in self._attackers
            if len(self._blockers.get(a.creature_id, [])) >= 2
        }
        self._seq_num += 1
        self._assign_damage_order_seq_num = self._seq_num
        pt = PhaseTransition(
            seq_num=self._seq_num,
            from_phase=from_phase,
            to_phase=CombatStep.ASSIGN_DAMAGE_ORDER,
            active_player=self._ap().id,
            turn=self._turn,
        )
        for p in self._players:
            result[p.id].append(pt)

    def _do_transition_to_damage(self, result: dict) -> None:
        """Skip FIRST_STRIKE_DAMAGE (no first-strike cards in set) → COMBAT_DAMAGE."""
        self._do_combat_damage(result)

    def _do_combat_damage(self, result: dict) -> None:
        from_phase = self.state
        self.state = CombatStep.COMBAT_DAMAGE
        self._broadcast_pt(from_phase, CombatStep.COMBAT_DAMAGE, result)
        self._resolve_combat_damage(result)

    def _do_skip_to_end_of_combat(self, result: dict) -> None:
        """Jump straight to END_OF_COMBAT when no attackers are declared."""
        from_phase = self.state
        self.state = CombatStep.END_OF_COMBAT
        self._broadcast_pt(from_phase, CombatStep.END_OF_COMBAT, result)
        self._open_priority(result)

    def _do_postcombat_main(self, result: dict) -> None:
        # Clear all combat state
        self._attackers.clear()
        self._blockers.clear()
        self._damage_order.clear()
        self._pending_damage_orders.clear()
        from_phase = self.state
        self.state = GamePhase.POSTCOMBAT_MAIN
        self._broadcast_pt(from_phase, GamePhase.POSTCOMBAT_MAIN, result)
        self._open_priority(result)

    def _do_end_step(self, result: dict) -> None:
        from_phase = self.state
        self.state = GamePhase.END_STEP
        self._broadcast_pt(from_phase, GamePhase.END_STEP, result)
        self._open_priority(result)

    def _do_cleanup(self, result: dict) -> None:
        from_phase = self.state
        self.state = GamePhase.CLEANUP
        self._priority_holder_idx = None
        self._broadcast_pt(from_phase, GamePhase.CLEANUP, result)

        ap = self._ap()
        if len(ap.hand) > 7:
            self._discard_player = ap.id
            self._seq_num += 1
            self._discard_gsu_seq = self._seq_num
            result[ap.id].append(self._build_game_gsu(ap))
        else:
            self._finish_cleanup(result)

    def _finish_cleanup(self, result: dict) -> None:
        """Complete cleanup after discard (or if no discard needed)."""
        self._discard_player = None

        self._eot_pumps.clear()

        for p in self._players:
            for e in p.battlefield.values():
                e.damage = 0

        self._broadcast_gsu(result)

        # Advance turn
        self._turn += 1
        self._active_player_idx = 1 - self._active_player_idx
        self._land_played_this_turn = False
        self._is_first_turn = False

        self._run_untap_sequence(result)

    # -----------------------------------------------------------------------
    # Game lifecycle
    # -----------------------------------------------------------------------

    def _start_game(self) -> dict[PlayerID, list[PDU]]:
        """Both players ready → GAME_SETUP → MULLIGAN."""
        result: dict[PlayerID, list[PDU]] = {p.id: [] for p in self._players}
        self.state = State.GAME_SETUP

        for p in self._players:
            for _ in range(7):
                p.draw_card()

        self._active_player_idx = random.randint(0, 1)
        self._first_player_idx = self._active_player_idx
        self._turn = 0
        self._is_first_turn = True

        for p in self._players:
            self._mulligan_counts[p.id] = 0
            self._mulligan_done[p.id] = False

        self.state = State.MULLIGAN

        for p in self._players:
            self._seq_num += 1
            self._mulligan_gsu_seq[p.id] = self._seq_num
            result[p.id].append(self._build_game_gsu(p))

        return result

    def _begin_game(self) -> dict[PlayerID, list[PDU]]:
        """Both players kept → start turn 1."""
        result: dict[PlayerID, list[PDU]] = {p.id: [] for p in self._players}
        self._turn = 1
        self._is_first_turn = True
        self._run_untap_sequence(result)
        return result

    def _run_untap_sequence(self, result: dict) -> None:
        """Execute UNTAP step then open UPKEEP priority."""
        ap = self._ap()

        # --- UNTAP ---
        self.state = GamePhase.UNTAP
        self._seq_num += 1
        pt_untap = PhaseTransition(
            seq_num=self._seq_num,
            from_phase=GamePhase.CLEANUP,
            to_phase=GamePhase.UNTAP,
            active_player=ap.id,
            turn=self._turn,
        )
        for p in self._players:
            result[p.id].append(pt_untap)

        ap.untap_all()
        ap.clear_summoning_sickness()
        self._land_played_this_turn = False

        self._broadcast_gsu(result)

        # --- UPKEEP ---
        self.state = GamePhase.UPKEEP
        self._seq_num += 1
        pt_upkeep = PhaseTransition(
            seq_num=self._seq_num,
            from_phase=GamePhase.UNTAP,
            to_phase=GamePhase.UPKEEP,
            active_player=ap.id,
            turn=self._turn,
        )
        for p in self._players:
            result[p.id].append(pt_upkeep)

        self._open_priority(result)

    # -----------------------------------------------------------------------
    # Combat damage
    # -----------------------------------------------------------------------

    def _resolve_combat_damage(self, result: dict) -> None:
        """Compute and apply simultaneous combat damage per RFC §9.7."""
        ap = self._ap()
        nap = self._nap()
        damage_events: list[dict] = []
        creatures_died: list[str] = []

        # --- Attacker → blocker/player ---
        for ai in self._attackers:
            attacker_entry = ap.battlefield.get(ai.creature_id)
            if not attacker_entry or not isinstance(attacker_entry.card, CreatureCard):
                continue
            pb, _ = self._pump_bonuses(ai.creature_id)
            power = attacker_entry.card.power() + pb

            blockers = self._blockers.get(ai.creature_id, [])
            if not ai.is_blocked:
                target_p = self._player_map.get(ai.target_player)
                if target_p:
                    target_p._life -= power
                    damage_events.append(
                        {
                            "source": ai.creature_id,
                            "target": ai.target_player,
                            "amount": power,
                        }
                    )
            else:
                order = self._damage_order.get(ai.creature_id, blockers)
                dmg_left = power
                for i, blk_id in enumerate(order):
                    if dmg_left <= 0:
                        break
                    blk_entry = nap.battlefield.get(blk_id)
                    if not blk_entry or not isinstance(blk_entry.card, CreatureCard):
                        continue
                    _, tb = self._pump_bonuses(blk_id)
                    effective_tough = blk_entry.card.toughness() + tb
                    lethal = max(0, effective_tough - blk_entry.damage)
                    if i == len(order) - 1:
                        assign = dmg_left
                    else:
                        assign = lethal if dmg_left >= lethal else dmg_left
                    blk_entry.damage += assign
                    damage_events.append(
                        {"source": ai.creature_id, "target": blk_id, "amount": assign}
                    )
                    dmg_left -= assign

        # --- Blocker → attacker ---
        for att_id, blk_ids in self._blockers.items():
            att_entry = ap.battlefield.get(att_id)
            if not att_entry or not isinstance(att_entry.card, CreatureCard):
                continue
            for blk_id in blk_ids:
                blk_entry = nap.battlefield.get(blk_id)
                if not blk_entry or not isinstance(blk_entry.card, CreatureCard):
                    continue
                pb, _ = self._pump_bonuses(blk_id)
                blk_power = blk_entry.card.power() + pb
                att_entry.damage += blk_power
                damage_events.append(
                    {"source": blk_id, "target": att_id, "amount": blk_power}
                )

        # --- State-based actions: lethal damage → graveyard ---
        for p in self._players:
            for cid in list(p.battlefield.keys()):
                e = p.battlefield.get(cid)
                if not e or not isinstance(e.card, CreatureCard):
                    continue
                _, tb = self._pump_bonuses(cid)
                if e.damage >= e.card.toughness() + tb:
                    p.send_to_graveyard_from_battlefield(cid)
                    creatures_died.append(cid)

        life_totals = {p.id: p.life_total for p in self._players}

        # Broadcast COMBAT_DAMAGE_RESULT
        self._seq_num += 1
        cdr = CombatDamageResult.model_validate(
            {
                "type": Type.COMBAT_DAMAGE_RESULT,
                "seq_num": self._seq_num,
                "damage_events": damage_events,
                "life_totals": life_totals,
                "creatures_died": creatures_died,
            }
        )
        for p in self._players:
            result[p.id].append(cdr)

        # Check win conditions
        losers = [p for p in self._players if p.life_total <= 0]
        if losers:
            loser = losers[0] if len(losers) == 1 else self._ap()
            winner = self._opponent_of(loser)
            self._emit_game_over(winner, loser, GameOver.Reason.LIFE_ZERO, result)
            return

        # Personalized GSU then transition to END_OF_COMBAT
        self._broadcast_gsu(result)
        self.state = CombatStep.END_OF_COMBAT
        self._broadcast_pt(CombatStep.COMBAT_DAMAGE, CombatStep.END_OF_COMBAT, result)
        self._open_priority(result)

    # -----------------------------------------------------------------------
    # Stack resolution
    # -----------------------------------------------------------------------

    def _resolve_top_of_stack(self, result: dict) -> bool:
        """Pop and resolve the top stack item. Returns True if the game ended."""
        if not self._stack:
            return False

        entry = self._stack.pop()

        # Target validity check
        all_invalid = bool(entry.targets) and not any(
            self._is_target_still_valid(t) for t in entry.targets
        )

        self._seq_num += 1

        if all_invalid:
            fizzle = StackResolve(
                seq_num=self._seq_num,
                stack_item_id=entry.stack_item_id,
                result=StackResolve.Result.FIZZLED,
                state_changes=[],
            )
            for p in self._players:
                result[p.id].append(fizzle)
            return False

        state_changes = self._apply_effect(entry, result)

        resolve_pdu = StackResolve(
            seq_num=self._seq_num,
            stack_item_id=entry.stack_item_id,
            result=StackResolve.Result.RESOLVED,
            state_changes=state_changes,
        )
        for p in self._players:
            result[p.id].append(resolve_pdu)

        # SBAs after resolution
        ended = self._check_sbas(result)
        if ended:
            return True

        self._broadcast_gsu(result)
        return False

    def _apply_effect(self, entry: _StackEntry, result: dict) -> list:
        """Delegate effect resolution to effects.py and return state_changes.

        Permanent spells (creatures, enchantments, artifacts) enter the
        battlefield on resolution.  All other logic is in effects.py.
        """
        return apply_effect(
            card_obj=entry.card_obj,
            targets=entry.targets,
            controller=entry.controller,
            is_permanent=entry.is_permanent,
            player_map=self._player_map,
            players=self._players,
            stack=self._stack,
            eot_pumps=self._eot_pumps,
        )

    # -----------------------------------------------------------------------
    # State-based actions
    # -----------------------------------------------------------------------

    def _check_sbas(self, result: dict) -> bool:
        """Apply SBAs. Returns True if game ended."""
        changed = True
        while changed:
            changed = False
            for p in self._players:
                for cid in list(p.battlefield.keys()):
                    e = p.battlefield.get(cid)
                    if not e or not isinstance(e.card, CreatureCard):
                        continue
                    _, tb = self._pump_bonuses(cid)
                    if e.damage >= e.card.toughness() + tb:
                        p.send_to_graveyard_from_battlefield(cid)
                        changed = True

            losers = [p for p in self._players if p.life_total <= 0]
            if losers:
                loser = losers[0] if len(losers) == 1 else self._ap()
                winner = self._opponent_of(loser)
                self._emit_game_over(winner, loser, GameOver.Reason.LIFE_ZERO, result)
                return True

        return False

    # -----------------------------------------------------------------------
    # Mana validation
    # -----------------------------------------------------------------------

    def _validate_and_pay_mana(
        self,
        player_obj: ServerPlayer,
        mana_payment: dict[Card.Color, int],
        card_cost: dict[Card.Color, int],
    ) -> tuple[bool, list[CardID]]:
        """Validate *mana_payment* satisfies *card_cost* using untapped sources.

        Returns (ok, list_of_card_ids_to_tap).
        """
        # Payment must cover all coloured requirements
        for color, needed in card_cost.items():
            if color == Card.Color.C:
                continue
            if mana_payment.get(color, 0) < needed:
                return False, []

        total_cost = sum(card_cost.values())
        total_paid = sum(mana_payment.values())
        if total_paid < total_cost:
            return False, []

        # Build pool of untapped mana sources
        pool: dict[CardID, Card.Color] = {}
        for cid, bf_e in player_obj.battlefield.items():
            if bf_e.tapped:
                continue
            if isinstance(bf_e.card, CreatureCard) and bf_e.summoning_sick:
                continue
            cls = type(bf_e.card)
            if cls in _MANA_PRODUCERS:
                pool[cid] = _MANA_PRODUCERS[cls]

        used: set[CardID] = set()

        # Satisfy coloured requirements first
        for color, amount in mana_payment.items():
            if color == Card.Color.C:
                continue
            matching = [
                cid for cid, c in pool.items() if c == color and cid not in used
            ]
            if len(matching) < amount:
                return False, []
            used.update(matching[:amount])

        # Satisfy generic requirement
        generic = mana_payment.get(Card.Color.C, 0)
        remaining = [cid for cid in pool if cid not in used]
        if len(remaining) < generic:
            return False, []
        used.update(remaining[:generic])

        return True, list(used)

    # -----------------------------------------------------------------------
    # Target validation
    # -----------------------------------------------------------------------

    def _validate_targets(self, card: Card, targets: set[str]) -> bool:
        """Return True if *targets* are legal for *card* at cast time.

        Delegates per-card checks to effects.py; the server checks
        structural rules (e.g. targets must reference an existing object).
        """
        return validate_targets(
            card=card,
            targets=targets,
            player_map=self._player_map,
            players=self._players,
            stack=self._stack,
        )

    def _is_target_still_valid(self, target: str) -> bool:
        """Check if *target* is still a legal object just before resolution."""
        if target in self._player_map:
            return True
        for p in self._players:
            if target in p.battlefield:
                return True
        return any(e.stack_item_id == target for e in self._stack)

    # -----------------------------------------------------------------------
    # GSU / PDU construction helpers
    # -----------------------------------------------------------------------

    def _build_lobby_gsu(self) -> GameStateUpdate:
        return GameStateUpdate.model_validate(
            {
                "type": Type.GAME_STATE_UPDATE,
                "seq_num": self._seq_num,
                "state": {
                    "phase": State.LOBBY,
                    "players_ready": len(self._players),
                    "waiting_for": [],
                },
            }
        )

    def _build_game_gsu(self, for_player: ServerPlayer) -> GameStateUpdate:
        """Build a personalized in-game GAME_STATE_UPDATE for *for_player*."""
        opponent = self._opponent_of(for_player)

        battlefield: dict[str, list] = {}
        for p in self._players:
            bf_list = []
            for cid, e in p.battlefield.items():
                d: dict = {"id": cid, "tapped": e.tapped}
                if isinstance(e.card, CreatureCard):
                    pb, tb = self._pump_bonuses(cid)
                    d.update(
                        {
                            "damage": e.damage,
                            "power": e.card.power() + pb,
                            "toughness": e.card.toughness() + tb,
                            "summoning_sick": e.summoning_sick,
                        }
                    )
                bf_list.append(d)
            battlefield[p.id] = bf_list

        priority_holder = (
            self._players[self._priority_holder_idx].id
            if self._priority_holder_idx is not None
            else None
        )

        stack_list = [
            {
                "stack_item_id": e.stack_item_id,
                "item_type": e.item_type,
                "source": e.source,
                "targets": list(e.targets),
                "cotroller": e.controller,
            }
            for e in self._stack
        ]

        state_dict: dict = {
            "turn": self._turn,
            "active_player": self._ap().id,
            "phase": self.state,
            "priority_holder": priority_holder,
            "life_totals": {p.id: p.life_total for p in self._players},
            "stack": stack_list,
            "battlefield": battlefield,
            "graveyard": {p.id: p.graveyard for p in self._players},
            "hand": {for_player.id: [c.id for c in for_player.hand]},
            "hand_counts": {opponent.id: len(opponent.hand)},
            "library_counts": {p.id: len(p.library) for p in self._players},
            "land_played_this_turn": self._land_played_this_turn,
        }

        self._seq_num += 1
        return GameStateUpdate.model_validate(
            {
                "type": Type.GAME_STATE_UPDATE,
                "seq_num": self._seq_num,
                "state": state_dict,
            }
        )

    def _broadcast_gsu(self, result: dict) -> None:
        """Send a personalized GSU to every player."""
        for p in self._players:
            result[p.id].append(self._build_game_gsu(p))

    def _broadcast_pt(self, from_phase: Any, to_phase: Any, result: dict) -> None:
        """Broadcast a PHASE_TRANSITION to all players."""
        self._seq_num += 1
        pt = PhaseTransition(
            seq_num=self._seq_num,
            from_phase=from_phase,
            to_phase=to_phase,
            active_player=self._ap().id,
            turn=self._turn,
        )
        for p in self._players:
            result[p.id].append(pt)

    def _make_error(self, code: Error.Code, message: str, rejected: PDU) -> Error:
        """Construct an Error PDU (increments seq_num)."""
        self._seq_num += 1
        return Error(
            seq_num=self._seq_num,
            code=code,
            message=message,
            rejected_action=rejected,
        )

    def _emit_game_over(
        self,
        winner: ServerPlayer,
        loser: ServerPlayer,
        reason: GameOver.Reason,
        result: dict,
    ) -> None:
        """Broadcast GAME_OVER and reset to LOBBY."""
        self._seq_num += 1
        go = GameOver(
            seq_num=self._seq_num,
            winner_id=winner.id,
            loser_id=loser.id,
            reason=reason,
        )
        for p in self._players:
            result.setdefault(p.id, []).append(go)
        self._reset_to_lobby()

    # -----------------------------------------------------------------------
    # Phase handlers
    # -----------------------------------------------------------------------

    def _generic_wrong_phase(
        self, pdu: PDU, player: PlayerID
    ) -> dict[PlayerID, list[PDU]]:
        result: dict[PlayerID, list[PDU]] = {p.id: [] for p in self._players}
        result[player].append(
            self._make_error(
                Error.Code.WRONG_PHASE,
                "No special actions expected during this phase.",
                pdu,
            )
        )
        return result

    def _untap(self, pdu: PDU, player: PlayerID) -> dict[PlayerID, list[PDU]]:
        return self._generic_wrong_phase(pdu, player)

    def _upkeep(self, pdu: PDU, player: PlayerID) -> dict[PlayerID, list[PDU]]:
        return self._generic_wrong_phase(pdu, player)

    def _draw(self, pdu: PDU, player: PlayerID) -> dict[PlayerID, list[PDU]]:
        return self._generic_wrong_phase(pdu, player)

    def _precombat_main(self, pdu: PDU, player: PlayerID) -> dict[PlayerID, list[PDU]]:
        return self._generic_wrong_phase(pdu, player)

    def _begin_combat(self, pdu: PDU, player: PlayerID) -> dict[PlayerID, list[PDU]]:
        return self._generic_wrong_phase(pdu, player)

    def _first_strike_damage(
        self, pdu: PDU, player: PlayerID
    ) -> dict[PlayerID, list[PDU]]:
        return self._generic_wrong_phase(pdu, player)

    def _combat_damage(self, pdu: PDU, player: PlayerID) -> dict[PlayerID, list[PDU]]:
        return self._generic_wrong_phase(pdu, player)

    def _end_of_combat(self, pdu: PDU, player: PlayerID) -> dict[PlayerID, list[PDU]]:
        return self._generic_wrong_phase(pdu, player)

    def _postcombat_main(self, pdu: PDU, player: PlayerID) -> dict[PlayerID, list[PDU]]:
        return self._generic_wrong_phase(pdu, player)

    def _end_step(self, pdu: PDU, player: PlayerID) -> dict[PlayerID, list[PDU]]:
        return self._generic_wrong_phase(pdu, player)

    def _declare_attackers(
        self, pdu: PDU, player: PlayerID
    ) -> dict[PlayerID, list[PDU]]:
        result: dict[PlayerID, list[PDU]] = {p.id: [] for p in self._players}
        ap = self._ap()
        if player != ap.id:
            result[player].append(
                self._make_error(
                    Error.Code.NOT_YOUR_PRIORITY,
                    "Only the Active Player declares attackers.",
                    pdu,
                )
            )
            return result
        if pdu.type != Type.DECLARE_ATTACKERS:
            result[player].append(
                self._make_error(
                    Error.Code.WRONG_PHASE, "Expecting DECLARE_ATTACKERS.", pdu
                )
            )
            return result

        da: DeclareAttackers = pdu
        if da.seq_num != self._declare_attackers_seq_num:
            result[player].append(
                self._make_error(Error.Code.STALE_ACTION, "Stale action.", pdu)
            )
            return result

        for att in da.attackers:
            entry = ap.battlefield.get(att.creature_id)
            if not entry or not isinstance(entry.card, CreatureCard):
                result[player].append(
                    self._make_error(
                        Error.Code.ILLEGAL_ACTION, f"{att.creature_id} invalid.", pdu
                    )
                )
                return result
            if entry.tapped or entry.summoning_sick:
                result[player].append(
                    self._make_error(
                        Error.Code.ILLEGAL_ACTION,
                        f"{att.creature_id} cannot attack.",
                        pdu,
                    )
                )
                return result

        self._attackers = []
        for att in da.attackers:
            ap.tap(att.creature_id)
            self._attackers.append(
                _AttackerInfo(creature_id=att.creature_id, target_player=att.target)
            )

        self._broadcast_gsu(result)
        if not self._attackers:
            self._do_skip_to_end_of_combat(result)
        else:
            self._open_priority(result)
        return result

    def _declare_blockers(
        self, pdu: PDU, player: PlayerID
    ) -> dict[PlayerID, list[PDU]]:
        result: dict[PlayerID, list[PDU]] = {p.id: [] for p in self._players}
        nap = self._nap()
        if player != nap.id:
            result[player].append(
                self._make_error(
                    Error.Code.NOT_YOUR_PRIORITY, "Only NAP declares blockers.", pdu
                )
            )
            return result
        if pdu.type != Type.DECLARE_BLOCKERS:
            result[player].append(
                self._make_error(
                    Error.Code.WRONG_PHASE, "Expecting DECLARE_BLOCKERS.", pdu
                )
            )
            return result

        db: DeclareBlockers = pdu
        if db.seq_num != self._declare_blockers_seq_num:
            result[player].append(
                self._make_error(Error.Code.STALE_ACTION, "Stale action.", pdu)
            )
            return result

        attacker_ids = {a.creature_id for a in self._attackers}
        for blk in db.blockers:
            entry = nap.battlefield.get(blk.creature_id)
            if not entry or not isinstance(entry.card, CreatureCard):
                result[player].append(
                    self._make_error(
                        Error.Code.ILLEGAL_ACTION, f"{blk.creature_id} invalid.", pdu
                    )
                )
                return result
            if entry.tapped:
                result[player].append(
                    self._make_error(
                        Error.Code.ILLEGAL_ACTION, f"{blk.creature_id} is tapped.", pdu
                    )
                )
                return result
            if blk.blocking_id not in attacker_ids:
                result[player].append(
                    self._make_error(
                        Error.Code.ILLEGAL_ACTION,
                        f"{blk.blocking_id} invalid target.",
                        pdu,
                    )
                )
                return result
            self._blockers.setdefault(blk.blocking_id, []).append(blk.creature_id)

        for ai in self._attackers:
            if ai.creature_id in self._blockers:
                ai.is_blocked = True

        self._broadcast_gsu(result)
        self._open_priority(result)
        return result

    def _assign_damage_order(
        self, pdu: PDU, player: PlayerID
    ) -> dict[PlayerID, list[PDU]]:
        result: dict[PlayerID, list[PDU]] = {p.id: [] for p in self._players}
        ap = self._ap()
        if player != ap.id:
            result[player].append(
                self._make_error(
                    Error.Code.NOT_YOUR_PRIORITY, "AP assigns damage order.", pdu
                )
            )
            return result
        if pdu.type != Type.ASSIGN_DAMAGE_ORDER:
            result[player].append(
                self._make_error(
                    Error.Code.WRONG_PHASE, "Expecting ASSIGN_DAMAGE_ORDER.", pdu
                )
            )
            return result

        ado: AssignDamageOrder = pdu
        if ado.seq_num != self._assign_damage_order_seq_num:
            result[player].append(
                self._make_error(Error.Code.STALE_ACTION, "Stale action.", pdu)
            )
            return result

        self._damage_order[ado.attacker_id] = ado.blocker_order
        self._pending_damage_orders.discard(ado.attacker_id)

        if not self._pending_damage_orders:
            self._do_transition_to_damage(result)
        return result

    def _cleanup(self, pdu: PDU, player: PlayerID) -> dict[PlayerID, list[PDU]]:
        result: dict[PlayerID, list[PDU]] = {p.id: [] for p in self._players}
        ap = self._ap()
        if player != ap.id or self._discard_player != ap.id:
            result[player].append(
                self._make_error(
                    Error.Code.WRONG_PHASE, "Not waiting for your discard.", pdu
                )
            )
            return result
        if pdu.type != Type.DISCARD:
            result[player].append(
                self._make_error(Error.Code.WRONG_PHASE, "Expecting DISCARD.", pdu)
            )
            return result

        disc: Discard = pdu
        if disc.seq_num != self._discard_gsu_seq:
            result[player].append(
                self._make_error(Error.Code.STALE_ACTION, "Stale discard.", pdu)
            )
            return result

        needed = len(ap.hand) - 7
        if len(disc.card_ids) != needed:
            result[player].append(
                self._make_error(
                    Error.Code.ILLEGAL_ACTION,
                    f"Must discard exactly {needed} cards.",
                    pdu,
                )
            )
            return result

        for cid in disc.card_ids:
            if not ap.card_in_hand(cid):
                result[player].append(
                    self._make_error(
                        Error.Code.ILLEGAL_ACTION, f"{cid} not in hand.", pdu
                    )
                )
                return result

        for cid in disc.card_ids:
            card = ap.card_in_hand(cid)
            if card:
                ap.remove_from_hand(card)
                ap._graveyard.append(cid)

        if len(ap.hand) > 7:
            self._seq_num += 1
            self._discard_gsu_seq = self._seq_num
            result[ap.id].append(self._build_game_gsu(ap))
        else:
            self._discard_player = None
            self._finish_cleanup(result)

        return result
