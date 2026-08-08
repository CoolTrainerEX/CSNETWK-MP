"""Handles priority window and action PDUs."""

from typing import TYPE_CHECKING, Any

from packages.shared.pdu import (
    PDU, PriorityPass, CastSpell, ActivateAbility, PlayLand, Concede,
    Error, Type, StackItem, StackPush, PriorityGrant, GameOver
)
from packages.shared.player import PlayerID
from packages.shared.cards import Card, LandCard, SorceryCard, CreatureCard, EnchantmentCard, ArtifactCard

if TYPE_CHECKING:
    from packages.server.game import ServerGame, ServerPlayer, _StackEntry
    from packages.server.game import GamePhase


class PriorityMixin:
    """Handles priority window and action PDUs."""

    # -----------------------------------------------------------------------
    # Priority window core
    # -----------------------------------------------------------------------

    def _handle_priority_pdu(self: "ServerGame", pdu: PDU, player: PlayerID) -> dict[PlayerID, list[PDU]]:
        """Process any PDU arriving during a priority window."""
        result: dict[PlayerID, list[PDU]] = {p.id: [] for p in self._players}

        if self._priority_holder_idx is None:
            result[player].append(
                self._make_error(Error.Code.WRONG_PHASE, "No priority window active.", pdu)
            )
            return result

        holder = self._players[self._priority_holder_idx]
        if holder.id != player:
            result[player].append(
                self._make_error(Error.Code.NOT_YOUR_PRIORITY, "You do not hold priority.", pdu)
            )
            return result

        if pdu.type == Type.PRIORITY_PASS:
            return self._handle_pass(pdu, holder, result)
        elif pdu.type == Type.CAST_SPELL:
            return self._handle_cast_spell(pdu, player, holder, result)
        elif pdu.type == Type.ACTIVATE_ABILITY:
            return self._handle_activate_ability(pdu, player, holder, result)
        elif pdu.type == Type.PLAY_LAND:
            return self._handle_play_land(pdu, player, holder, result)
        else:
            result[player].append(
                self._make_error(Error.Code.WRONG_PHASE, f"Invalid action in priority window: {pdu.type}.", pdu)
            )
            result[player].append(self._reissue_priority(holder))
            return result

    def _handle_pass(
        self: "ServerGame", pdu: PriorityPass, holder: "ServerPlayer", result: dict
    ) -> dict:
        if pdu.seq_num != self._priority_seq_num:
            result[holder.id].append(
                self._make_error(Error.Code.STALE_ACTION, f"Stale. Expected {self._priority_seq_num}, got {pdu.seq_num}.", pdu)
            )
            result[holder.id].append(self._reissue_priority(holder))
            return result

        self._consecutive_passes += 1

        if self._consecutive_passes >= 2:
            self._consecutive_passes = 0
            if self._stack:
                ended = self._resolve_top_of_stack(result)
                if not ended:
                    self._open_priority(result)
            else:
                self._advance_phase(result)
        else:
            other = self._opponent_of(holder)
            self._grant_priority_to(other, result)

        return result

    # -----------------------------------------------------------------------
    # Action handlers
    # -----------------------------------------------------------------------

    def _handle_cast_spell(
        self: "ServerGame", pdu: CastSpell, player: PlayerID, holder: "ServerPlayer", result: dict
    ) -> dict:
        from packages.server.game import _StackEntry, GamePhase

        cs: CastSpell = pdu
        ap = self._ap()
        player_obj = self._player_map.get(player)

        if cs.seq_num != self._priority_seq_num:
            result[player].append(self._make_error(Error.Code.STALE_ACTION, f"Stale. Expected {self._priority_seq_num}.", pdu))
            result[player].append(self._reissue_priority(holder))
            return result

        card = player_obj.card_in_hand(cs.card_id) if player_obj else None
        if not card:
            result[player].append(self._make_error(Error.Code.ILLEGAL_ACTION, f"Card {cs.card_id} not in hand.", pdu))
            result[player].append(self._reissue_priority(holder))
            return result

        # Sorcery-speed restriction
        sorcery_speed = isinstance(card, (SorceryCard, CreatureCard, EnchantmentCard, ArtifactCard))
        if sorcery_speed:
            if player != ap.id:
                result[player].append(self._make_error(Error.Code.WRONG_PHASE, "Sorcery-speed: only the Active Player may cast.", pdu))
                result[player].append(self._reissue_priority(holder))
                return result
            if self.state not in (GamePhase.PRECOMBAT_MAIN, GamePhase.POSTCOMBAT_MAIN):
                result[player].append(self._make_error(Error.Code.WRONG_PHASE, "Sorcery-speed: only castable during Main Phase.", pdu))
                result[player].append(self._reissue_priority(holder))
                return result
            if self._stack:
                result[player].append(self._make_error(Error.Code.WRONG_PHASE, "Sorcery-speed: stack must be empty.", pdu))
                result[player].append(self._reissue_priority(holder))
                return result

        # Target validation
        if not self._validate_targets(card, cs.targets):
            result[player].append(self._make_error(Error.Code.ILLEGAL_TARGET, "One or more targets are illegal.", pdu))
            result[player].append(self._reissue_priority(holder))
            return result

        # Mana validation
        ok, to_tap = self._validate_and_pay_mana(player_obj, cs.mana_payment, card.cost())
        if not ok:
            result[player].append(self._make_error(Error.Code.INSUFFICIENT_MANA, "Insufficient mana to cast spell.", pdu))
            result[player].append(self._reissue_priority(holder))
            return result

        for cid in to_tap:
            player_obj.tap(cid)

        player_obj.remove_from_hand(card)
        is_permanent = isinstance(card, (CreatureCard, EnchantmentCard, ArtifactCard))

        self._stack_counter += 1
        sid = f"stk_{self._stack_counter:03d}"
        self._stack.append(
            _StackEntry(
                stack_item_id=sid,
                item_type=StackItem.ItemType.SPELL,
                source=card.id,
                targets=list(cs.targets),
                controller=player,
                card_obj=card,
                is_permanent=is_permanent,
            )
        )

        self._seq_num += 1
        sp = StackPush(
            seq_num=self._seq_num,
            stack_item_id=sid,
            item_type=StackItem.ItemType.SPELL,
            source=card.id,
            targets=cs.targets,
            cotroller=player,
        )
        for p in self._players:
            result[p.id].append(sp)

        # Caster retains priority; reset consecutive passes
        self._consecutive_passes = 0
        self._grant_priority_to(player_obj, result)
        return result

    def _handle_activate_ability(
        self: "ServerGame", pdu: ActivateAbility, player: PlayerID, holder: "ServerPlayer", result: dict
    ) -> dict:
        from packages.server.game import _StackEntry

        aa: ActivateAbility = pdu
        player_obj = self._player_map.get(player)

        if aa.seq_num != self._priority_seq_num:
            result[player].append(self._make_error(Error.Code.STALE_ACTION, f"Stale. Expected {self._priority_seq_num}.", pdu))
            result[player].append(self._reissue_priority(holder))
            return result

        entry = player_obj.battlefield.get(aa.source_id) if player_obj else None
        if not entry:
            result[player].append(self._make_error(Error.Code.ILLEGAL_ACTION, f"{aa.source_id} not on battlefield.", pdu))
            result[player].append(self._reissue_priority(holder))
            return result

        if aa.cost_payment.tap:
            if isinstance(entry.card, CreatureCard) and entry.summoning_sick:
                result[player].append(self._make_error(Error.Code.ILLEGAL_ACTION, f"{aa.source_id} has summoning sickness.", pdu))
                result[player].append(self._reissue_priority(holder))
                return result
            if entry.tapped:
                result[player].append(self._make_error(Error.Code.ILLEGAL_ACTION, f"{aa.source_id} is already tapped.", pdu))
                result[player].append(self._reissue_priority(holder))
                return result
            player_obj.tap(aa.source_id)

        if aa.cost_payment.mana:
            ok, to_tap = self._validate_and_pay_mana(player_obj, aa.cost_payment.mana, aa.cost_payment.mana)
            if not ok:
                result[player].append(self._make_error(Error.Code.INSUFFICIENT_MANA, "Insufficient mana.", pdu))
                result[player].append(self._reissue_priority(holder))
                return result
            for cid in to_tap:
                player_obj.tap(cid)

        self._stack_counter += 1
        sid = f"stk_{self._stack_counter:03d}"
        self._stack.append(
            _StackEntry(
                stack_item_id=sid,
                item_type=StackItem.ItemType.ABILITY,
                source=aa.source_id,
                targets=list(aa.targets),
                controller=player,
                card_obj=entry.card,
                is_permanent=False,
            )
        )

        self._seq_num += 1
        sp = StackPush(
            seq_num=self._seq_num,
            stack_item_id=sid,
            item_type=StackItem.ItemType.ABILITY,
            source=aa.source_id,
            targets=aa.targets,
            cotroller=player,
        )
        for p in self._players:
            result[p.id].append(sp)

        self._consecutive_passes = 0
        self._grant_priority_to(player_obj, result)
        return result

    def _handle_play_land(
        self: "ServerGame", pdu: PlayLand, player: PlayerID, holder: "ServerPlayer", result: dict
    ) -> dict:
        from packages.server.game import GamePhase

        pl: PlayLand = pdu
        ap = self._ap()
        player_obj = self._player_map.get(player)

        if player != ap.id:
            result[player].append(self._make_error(Error.Code.WRONG_PHASE, "Only the Active Player may play a land.", pdu))
            result[player].append(self._reissue_priority(holder))
            return result

        if pl.seq_num != self._priority_seq_num:
            result[player].append(self._make_error(Error.Code.STALE_ACTION, f"Stale. Expected {self._priority_seq_num}.", pdu))
            result[player].append(self._reissue_priority(holder))
            return result

        if self.state not in (GamePhase.PRECOMBAT_MAIN, GamePhase.POSTCOMBAT_MAIN):
            result[player].append(self._make_error(Error.Code.WRONG_PHASE, "Lands can only be played during Main Phase.", pdu))
            result[player].append(self._reissue_priority(holder))
            return result

        if self._land_played_this_turn:
            result[player].append(self._make_error(Error.Code.ILLEGAL_ACTION, "Already played a land this turn.", pdu))
            result[player].append(self._reissue_priority(holder))
            return result

        card = player_obj.card_in_hand(pl.card_id) if player_obj else None
        if not card:
            result[player].append(self._make_error(Error.Code.ILLEGAL_ACTION, f"Card {pl.card_id} not in hand.", pdu))
            result[player].append(self._reissue_priority(holder))
            return result

        if not isinstance(card, LandCard):
            result[player].append(self._make_error(Error.Code.ILLEGAL_ACTION, f"{pl.card_id} is not a land.", pdu))
            result[player].append(self._reissue_priority(holder))
            return result

        # Play the land (no stack)
        player_obj.remove_from_hand(card)
        player_obj.put_to_battlefield(card, summoning_sick=False)
        self._land_played_this_turn = True

        self._broadcast_gsu(result)
        # AP retains priority
        self._consecutive_passes = 0
        self._grant_priority_to(ap, result)
        return result

    def _handle_concede(self: "ServerGame", pdu: Concede, player: PlayerID) -> dict[PlayerID, list[PDU]]:
        result: dict[PlayerID, list[PDU]] = {p.id: [] for p in self._players}
        if len(self._players) < 2:
            return result

        loser = self._player_map.get(player)
        if not loser:
            return result
        winner = self._opponent_of(loser)

        self._seq_num += 1
        go = GameOver(
            seq_num=self._seq_num,
            winner_id=winner.id,
            loser_id=player,
            reason=GameOver.Reason.CONCEDE,
        )
        for p in self._players:
            result[p.id].append(go)

        self._reset_to_lobby()
        return result

    # -----------------------------------------------------------------------
    # Priority helpers
    # -----------------------------------------------------------------------

    def _open_priority(self: "ServerGame", result: dict) -> None:
        """Grant priority to the Active Player and reset consecutive-pass counter."""
        self._consecutive_passes = 0
        self._grant_priority_to(self._ap(), result)

    def _grant_priority_to(self: "ServerGame", player: "ServerPlayer", result: dict) -> None:
        """Issue a new PRIORITY_GRANT to *player*."""
        self._priority_holder_idx = self._players.index(player)
        self._seq_num += 1
        self._priority_seq_num = self._seq_num
        grant = PriorityGrant(
            player_id=player.id,
            seq_num=self._seq_num,
            time_limit_ms=60000,
        )
        result[player.id].append(grant)

    def _reissue_priority(self: "ServerGame", player: "ServerPlayer") -> PriorityGrant:
        """Return a PRIORITY_GRANT re-using the current seq_num (after error)."""
        return PriorityGrant(
            player_id=player.id,
            seq_num=self._priority_seq_num,
            time_limit_ms=60000,
        )
