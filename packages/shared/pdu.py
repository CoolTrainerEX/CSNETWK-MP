"""PDU schemas."""

from enum import StrEnum, auto
from typing import Annotated, Literal

from pydantic import BaseModel, Field, TypeAdapter

from packages.shared.cards import Card, CardID, CreatureCardID, LandCardID
from packages.shared.game import ID, CombatStep, GamePhase, State
from packages.shared.player import PlayerID


class Type(StrEnum):
    """PDU Type."""

    PLAYER_READY = auto()
    """:class:`PlayerReady`"""

    GAME_STATE_UPDATE = auto()
    """:class:`GameStateUpdate`"""

    MULLIGAN_CHOICE = auto()
    """:class:`MulliganChoice`"""

    PHASE_TRANSITION = auto()
    """:class:`PhaseTransition`"""

    PRIORITY_GRANT = auto()
    """:class:`PriorityGrant`"""

    PRIORITY_PASS = auto()
    """:class:`PriorityPass`"""

    CAST_SPELL = auto()
    """:class:`CastSpell`"""

    ACTIVATE_ABILITY = auto()
    """:class:`ActivateAbility`"""

    STACK_PUSH = auto()
    """:class:`StackPush`"""

    TRIGGER_ORDER = auto()
    """:class:`TriggerOrder`"""

    TRIGGER_ORDER_RESPONSE = auto()
    """:class:`TriggerOrderResponse`"""

    TRIGGER_CHOICE = auto()
    """:class:`TriggerChoice`"""

    TRIGGER_CHOICE_RESPONSE = auto()
    """:class:`TriggerChoiceResponse`"""

    STACK_RESOLVE = auto()
    """:class:`StackResolve`"""

    DECLARE_ATTACKERS = auto()
    """:class:`DeclareAttackers`"""

    DECLARE_BLOCKERS = auto()
    """:class:`DeclareBlockers`"""

    ASSIGN_DAMAGE_ORDER = auto()
    """:class:`AssignDamageOrder`"""

    COMBAT_DAMAGE_RESULT = auto()
    """:class:`CombatDamageResult`"""

    PLAY_LAND = auto()
    """:class:`PlayLand`"""

    DISCARD = auto()
    """:class:`Discard`"""

    CONCEDE = auto()
    """:class:`Concede`"""

    GAME_OVER = auto()
    """:class:`GameOver`"""

    ERROR = auto()
    """:class:`Error`"""

    PING = auto()
    """:class:`Ping`"""

    PONG = auto()
    """:class:`Pong`"""


class PlayerReady(BaseModel):
    """**Dir**: C -> S; **Phase**: Lobby.

    Notes:
        1-50 cards; server rejects invalid decks with ILLEGAL_DECK

    Attributes:
        type (Literal[Type.PLAYER_READY]):
        seq_num (int): Monotonically increasing message counter
        player_id (PlayerID): Client-chosen non-empty string; must be unique in this lobby
        deck_list (set[str]): 1 to 50 card IDs
    """

    model_config = {"arbitrary_types_allowed": True}
    type: Literal[Type.PLAYER_READY] = Type.PLAYER_READY
    seq_num: int
    player_id: PlayerID
    deck_list: set[CardID]


class GameStateUpdate(BaseModel):
    """**Dir**: S -> C; **Phase**: All.

    Notes:
        Personalized per player; hidden info filtered out

    Attributes:
        type (Literal[Type.GAME_STATE_UPDATE]):
        seq_num (int):
        state (__LobbyState | __GameState):
    """

    class __LobbyState(BaseModel):
        """State in :attr:`Phase.LOBBY`.

        Attributes:
            phase (Literal[Phase.LOBBY]):
            players_ready (int): How many players have sent :class:`PlayerReady`
            waiting_for (set[PlayerID]): :attr:`PlayerReady.player_id`s not yet ready
        """

        model_config = {"arbitrary_types_allowed": True}
        phase: Literal[State.LOBBY]
        players_ready: int
        waiting_for: set[PlayerID]

    class __GameState(BaseModel):
        """State in all other phases.

        Attributes:
            turn (int):
            active_player (PlayerID):
            phase (Literal[State.MULLIGAN] | GamePhase | CombatStep):
            priority_holder (PlayerID | None): `None` during :attr:`CombatStep.UNTAP` and :attr:`CombatStep.CLEANUP` steps
            life_totals (dict[PlayerID, int]):
            battlefield (dict[PlayerID, set[__BattlefieldCard | __BattlefieldCreatureCard]]):
            graveyard (dict[PlayerID, set[CardID]]): Ordered by insertion: index 0 = first card placed, last = most recently added
            hand (dict[PlayerID, set[CardID]]):
            hand_counts (dict[PlayerID, int]):
            library_counts (dict[PlayerID, int]):
            land_played_this_turn (bool): `True` if AP has already played a land this turn
        """

        class __BattlefieldCard(BaseModel):
            """Card placed in :attr:`GameStateUpdate.state.battlefield`.

            Attributes:
                id (CardID):
                tapped (bool):
            """

            model_config = {"arbitrary_types_allowed": True}
            id: CardID
            tapped: bool

            def __eq__(self, value: object) -> bool:
                """Checks object equality.

                Args:
                    value (object): Object to compare

                Returns:
                    bool: Is equal
                """
                return (
                    isinstance(value, GameStateUpdate.__GameState.__BattlefieldCard)
                    and self.id == value.id
                )

            def __hash__(self) -> int:
                """Hashes the object.

                Returns:
                    int: Object hash
                """
                return hash(self.id)

        class __BattlefieldCreatureCard(__BattlefieldCard):
            """Creature card placed in :attr:`GameStateUpdate.state.battlefield.

            Attributes:
                id (CreatureCardID):
                damage (int):
                power (int):
                toughness (int):
                summoning_sick (bool):
            """

            model_config = {"arbitrary_types_allowed": True}
            id: CreatureCardID
            damage: int
            power: int
            toughness: int
            summoning_sick: bool

        model_config = {"arbitrary_types_allowed": True}
        turn: int
        active_player: PlayerID
        phase: Literal[State.MULLIGAN] | GamePhase | CombatStep
        priority_holder: PlayerID | None
        life_totals: dict[PlayerID, int]
        battlefield: dict[
            PlayerID, set[__BattlefieldCard | __BattlefieldCreatureCard]
        ]
        graveyard: dict[PlayerID, set[CardID]]
        hand: dict[PlayerID, set[CardID]]
        hand_counts: dict[PlayerID, int]
        library_counts: dict[PlayerID, int]
        land_played_this_turn: bool

    type: Literal[Type.GAME_STATE_UPDATE] = Type.GAME_STATE_UPDATE
    seq_num: int
    state: __LobbyState | __GameState


class MulliganChoice(BaseModel):
    """**Dir**: C -> S; **Phase**: Setup.

    Notes:
        Server redraws if :attr:`MulliganChoice.keep` is `False` (London Mulligan)

    Attributes:
        type (Literal[Type.MULLIGAN_CHOICE]):
        seq_num (int): Monotonically increasing message counter
        keep (bool): `False` = take a mulligan
        cards_to_bottom (set[CardID]): Must equal mulligan count when :attr:`MulliganChoice.keep` = `True`
    """

    model_config = {"arbitrary_types_allowed": True}
    type: Literal[Type.MULLIGAN_CHOICE] = Type.MULLIGAN_CHOICE
    seq_num: int
    keep: bool
    cards_to_bottom: set[CardID]


class PhaseTransition(BaseModel):
    """**Dir**: S -> ALL; **Phase**: All.

    Notes:
        Broadcast when server advances a step or phase

    Attributes:
        type (Literal[Type.PHASE_TRANSITION]):
        seq_num (int): Server-issued sequence number
        from_phase (GamePhase | CombatStep):
        to_phase (GamePhase | CombatStep):
        active_player (PlayerID):
        turn (int):
    """

    model_config = {"arbitrary_types_allowed": True}
    type: Literal[Type.PHASE_TRANSITION] = Type.PHASE_TRANSITION
    seq_num: int
    from_phase: GamePhase | CombatStep
    to_phase: GamePhase | CombatStep
    active_player: PlayerID
    turn: int


class PriorityGrant(BaseModel):
    """**Dir**: S -> C; **Phase**: Priority.

    Notes:
        Sent only to the player who now holds priority

    Attributes:
        type (Literal[Type.PRIORITY_GRANT]):
        player_id (PlayerID):
        seq_num (int):
        time_limit_ms (int): Server-enforced response deadline
    """

    model_config = {"arbitrary_types_allowed": True}
    type: Literal[Type.PRIORITY_GRANT] = Type.PRIORITY_GRANT
    player_id: PlayerID
    seq_num: int
    time_limit_ms: int


class PriorityPass(BaseModel):
    """**Dir**: C -> S; **Phase**: Priority.

    Notes:
        :attr:`PriorityPass.seq_num` must match current priority token

    Attributes:
        type (Literal[Type.PRIORITY_PASS]):
        seq_num (int): Must match current :attr:`PriorityGrant.seq_num`
    """

    type: Literal[Type.PRIORITY_PASS] = Type.PRIORITY_PASS
    seq_num: int


class CastSpell(BaseModel):
    """**Dir**: C -> S; **Phase**: Priority.

    Notes:
        Server validates; pushes to stack on success

    Attributes:
        type (Literal[Type.CAST_SPELL]):
        seq_num (int):
        card_id (CardID):
        targets (set[ID]): Empty array if spell has no targets
        mana_payment (dict[Card.Color, int]):
    """

    model_config = {"arbitrary_types_allowed": True}
    type: Literal[Type.CAST_SPELL] = Type.CAST_SPELL
    seq_num: int
    card_id: CardID
    targets: set[ID]
    mana_payment: dict[Card.Color, int]


class ActivateAbility(BaseModel):
    """**Dir**: C -> S; **Phase**: Priority.

    Notes:
        Mana abilities bypass the stack entirely
        Server rejects with :attr:`Error.Code.ILLEGAL_ACTION` if permanent is already tapped

    Attributes:
        type (Literal[Type.ACTIVATE_ABILITY]):
        seq_num (int):
        source_id (CardID):
        ability_index (int): 0-based index into permanent's ability list
        targets (set[ID]):
        cost_payment (__CostPayment):
    """

    class __CostPayment(BaseModel):
        """Ability cost.

        Attributes:
            tap (bool): True only if ability requires tapping
            mana (dict[Card.Color, int]):
        """

        tap: bool
        mana: dict[Card.Color, int]

    model_config = {"arbitrary_types_allowed": True}
    type: Literal[Type.ACTIVATE_ABILITY] = Type.ACTIVATE_ABILITY
    seq_num: int
    source_id: CardID
    ability_index: int
    targets: set[ID]
    cost_payment: __CostPayment


StackID = ID


class StackItem(BaseModel):
    """Stack item.

    Attributes:
        stack_item_id (ID):
        item_type (ItemType):
        source (CardID):
        targets (set[ID]):
        cotroller (PlayerID):
    """

    class ItemType(StrEnum):
        """Stack item type."""

        SPELL = auto()
        ABILITY = auto()
        TRIGGER_ABILITY = auto()

    model_config = {"arbitrary_types_allowed": True}
    stack_item_id: StackID
    item_type: ItemType
    source: CardID
    targets: set[ID]
    cotroller: PlayerID


class StackPush(StackItem):
    """**Dir**: S -> ALL; **Phase**: Stack.

    Attributes:
        type (Literal[Type.STACK_PUSH]):
        seq_num (int): Server-issued sequence number
    """

    type: Literal[Type.STACK_PUSH] = Type.STACK_PUSH
    seq_num: int


TriggerID = ID


class TriggerOrder(BaseModel):
    """**Dir**: S -> C; **Phase**: Stack.

    Notes:
        Player must specify order for their simultaneous triggers

    Attributes:
        type (Literal[Type.TRIGGER_ORDER]):
        seq_num (int): Server-issued sequence number
        player_id (PlayerID): Player must order these
        trigger_ids (set[TriggerID]):
    """

    model_config = {"arbitrary_types_allowed": True}
    type: Literal[Type.TRIGGER_ORDER] = Type.TRIGGER_ORDER
    seq_num: int
    player_id: PlayerID
    trigger_ids: set[TriggerID]


class TriggerOrderResponse(BaseModel):
    """**Dir**: C -> S; **Phase**: Stack.

    Notes:
        Triggers listed in desired stack placement order

    Attributes:
        type (Literal[Type.TRIGGER_ORDER_RESPONSE]):
        seq_num (int): Must match the corresponding :attr:`TriggerOrder.seq_num`
        ordered_trigger_ids (set[TriggerID]):
    """

    type: Literal[Type.TRIGGER_ORDER_RESPONSE] = Type.TRIGGER_ORDER_RESPONSE
    seq_num: int
    ordered_trigger_ids: set[TriggerID]


class TriggerChoice(BaseModel):
    """**Dir**: S -> C; **Phase**: Stack.

    Notes:
        Ask player to accept optional trigger or choose a target

    Attributes:
        type (Literal[Type.TRIGGER_CHOICE]):
        seq_num (int): Server-issued sequence number
        trigger_id (TriggerID):
        source_id (CardID):
        effect_summary (str):
        requires_target (bool): `True` if player must also pick a target
        legal_targets (ID): Elements are `player_id` strings or permanent id
    """

    model_config = {"arbitrary_types_allowed": True}
    type: Literal[Type.TRIGGER_CHOICE] = Type.TRIGGER_CHOICE
    seq_num: int
    trigger_id: TriggerID
    source_id: CardID
    effect_summary: str
    requires_target: bool
    legal_targets: ID


class TriggerChoiceResponse(BaseModel):
    """**Dir**: C -> S; **Phase**: Stack.

    Notes:
        :attr:`TriggerChoiceResponse.accept` = `False` discards the trigger with no effect

    Attributes:
        type (Literal[Type.TRIGGER_CHOICE_RESPONSE]):
        seq_num (int): Must match the corresponding :attr:`TriggerChoice.seq_num`
        trigger_id (TriggerID):
        accept (bool):
        chosen_target (ID | None): `ID` only when :attr:`TriggerChoiceResponse.accept` = `True` AND :attr:`TriggerChoice.requires_target` = `True`; `None` when :attr:`TriggerChoiceResponse.accept` = False or :attr:`TriggerChoice.requires_target` = `False`
    """

    type: Literal[Type.TRIGGER_CHOICE_RESPONSE] = Type.TRIGGER_CHOICE_RESPONSE
    seq_num: int
    trigger_id: TriggerID
    accept: bool
    chosen_target: ID | None


class StackResolve(BaseModel):
    """**Dir**: S -> ALL; **Phase**: Stack.

    Attributes:
        type (Literal[Type.STACK_RESOLVE]):
        seq_num (int): Server-issued sequence number
        stack_item_id (StackID):
        result (Result):
        state_changes (list[StateChange]):
    """

    class Result(StrEnum):
        """Resolution result."""

        RESOLVED = auto()
        FIZZLED = auto()

    class __StateChange(BaseModel):
        """Resolution state change.

        Attributes:
            change_type (ChangeType):
            target (ID):
            amount (int | None):
        """

        class ChangeType(StrEnum):
            """Change type."""

            DAMAGE = auto()
            LIFE_GAIN = auto()
            DESTROY = auto()

        change_type: ChangeType
        target: ID
        amount: int | None

    type: Literal[Type.STACK_RESOLVE] = Type.STACK_RESOLVE
    seq_num: int
    stack_item_id: StackID
    result: Result
    state_changes: list[__StateChange]


class DeclareAttackers(BaseModel):
    """**Dir**: C -> S; **Phase**: Combat.

    Notes:
        Empty array = no attack (still required)

    Attributes:
        type (Literal[Type.DECLARE_ATTACKERS]):
        seq_num (int):
        attackers (set[Attacker]): Send empty attackers array to declare no attack
    """

    class __Attacker(BaseModel):
        """Attacker.

        Attributes:
            creature_id (CreatureCardID):
            target (PlayerID):
        """

        model_config = {"arbitrary_types_allowed": True}
        creature_id: CreatureCardID
        target: PlayerID

        def __eq__(self, value: object) -> bool:
            """Checks object equality.

            Args:
                value (object): Object to compare

            Returns:
                bool: Is equal
            """
            return (
                isinstance(value, DeclareAttackers.__Attacker)
                and self.creature_id == value.creature_id
            )

        def __hash__(self) -> int:
            """Hashes the object.

            Returns:
                int: Object hash
            """
            return hash(self.creature_id)

    type: Literal[Type.DECLARE_ATTACKERS] = Type.DECLARE_ATTACKERS
    seq_num: int
    attackers: set[__Attacker]


class DeclareBlockers(BaseModel):
    """**Dir**: C -> S; **Phase**: Combat.

    Notes:
        Server validates legality of each block

    Attributes:
        type (Literal[Type.DECLARE_BLOCKERS]):
        seq_num (int):
        blockers (set[Blocker]): Send empty blockers array to not block
    """

    class __Blocker(BaseModel):
        """Bolcker.

        Attributes:
            creature_id (CreatureCardID):
            blocking_id (CreatureCardID):
        """

        model_config = {"arbitrary_types_allowed": True}
        creature_id: CreatureCardID
        blocking_id: CreatureCardID

        def __eq__(self, value: object) -> bool:
            """Checks object equality.

            Args:
                value (object): Object to compare

            Returns:
                bool: Is equal
            """
            return (
                isinstance(value, DeclareAttackers.__Attacker)
                and self.creature_id == value.creature_id
            )

        def __hash__(self) -> int:
            """Hashes the object.

            Returns:
                int: Object hash
            """
            return hash(self.creature_id)

    type: Literal[Type.DECLARE_BLOCKERS] = Type.DECLARE_BLOCKERS
    seq_num: int
    attackers: set[__Blocker]


class AssignDamageOrder(BaseModel):
    """**Dir**: C -> S; **Phase**: Combat.

    Notes:
        Required when multiple blockers on one attacker

    Attributes:
        type (Literal[Type.ASSIGN_DAMAGE_ORDER]):
        seq_num (int):
        attacker_id (CreatureCardID):
        blocker_order (set[CreatureCardID]):
    """

    model_config = {"arbitrary_types_allowed": True}
    type: Literal[Type.ASSIGN_DAMAGE_ORDER] = Type.ASSIGN_DAMAGE_ORDER
    seq_num: int
    attacker_id: CreatureCardID
    blocker_order: set[CreatureCardID]


class CombatDamageResult(BaseModel):
    """**Dir**: S -> ALL; **Phase**: Combat.

    Notes:
        Server computes all damage simultaneously

    Attributes:
        type (Literal[Type.COMBAT_DAMAGE_RESULT]):
        seq_num (int): Server-issued sequence number
        damage_events (set[DamageEvent]):
        life_totals (dict[PlayerID, int]):
        creatures_died (set[CreatureCardID]):
    """

    class __DamageEvent(BaseModel):
        """Combat damage event.

        Attributes:
            source (CreatureCardID):
            target (CreatureCardID | PlayerID):
            amount (int):
        """

        model_config = {"arbitrary_types_allowed": True}
        source: CreatureCardID
        target: CreatureCardID | PlayerID
        amount: int

    model_config = {"arbitrary_types_allowed": True}
    type: Literal[Type.COMBAT_DAMAGE_RESULT] = Type.COMBAT_DAMAGE_RESULT
    seq_num: int
    damage_events: set[__DamageEvent]
    life_totals: dict[PlayerID, int]
    creatures_died: set[CreatureCardID]


class PlayLand(BaseModel):
    """**Dir**: C -> S; **Phase**: Main.

    Notes:
        Does not use the stack; one per turn limit

    Attributes:
        type (Literal[Type.PLAY_LAND]):
        seq_num (int):
        card_id (LandCardID):
    """

    model_config = {"arbitrary_types_allowed": True}
    type: Literal[Type.PLAY_LAND] = Type.PLAY_LAND
    seq_num: int
    card_id: LandCardID


class Discard(BaseModel):
    """**Dir**: C -> S; **Phase**: Cleanup.

    Notes:
        Required when hand size > 7 at cleanup

    Attributes:
        type (Literal[Type.DISCARD]):
        seq_num (int):
        card_ids (set[CardID]):
    """

    model_config = {"arbitrary_types_allowed": True}
    type: Literal[Type.DISCARD] = Type.DISCARD
    seq_num: int
    card_ids: set[CardID]


class Concede(BaseModel):
    """**Dir**: C -> S; **Phase**: Any.

    Notes:
        Triggers immediate :attr:`State.GAME_OVER`

    Attributes:
        type (Literal[Type.CONCEDE]):
        seq_num (int):
        player_id (PlayerID):
    """

    model_config = {"arbitrary_types_allowed": True}
    type: Literal[Type.CONCEDE] = Type.CONCEDE
    seq_num: int
    player_id: PlayerID


class GameOver(BaseModel):
    """**Dir**: S -> ALL; **Phase**: End.

    Attributes:
        type (Literal[Type.GAME_OVER]):
        seq_num (int): Server-issued sequence number
        winner_id (PlayerID):
        loser_id (PlayerID):
        reason (Reason):
    """

    class Reason(StrEnum):
        """Game over reason."""

        LIFE_ZERO = auto()
        DECK_EMPTY = auto()
        CONCEDE = auto()
        DISCONNECT = auto()

    model_config = {"arbitrary_types_allowed": True}
    type: Literal[Type.GAME_OVER] = Type.GAME_OVER
    seq_num: int
    winner_id: PlayerID
    loser_id: PlayerID
    reason: Reason


class Error(BaseModel):
    """**Dir**: S -> C; **Phase**: Any.

    Notes:
        Game continues; rejected action is discarded

    Attributes:
        type (Literal[Type.ERROR]):
        seq_num (int):
        code (Code):
        message (str):
        rejected_action (PDU):
    """

    class Code(StrEnum):
        """Error code."""

        INVALID_JSON = auto()
        """The received bytes could not be parsed as valid UTF-8 JSON"""
        ILLEGAL_DECK = auto()
        """The submitted :attr:`PlayerReady.deck_list` is empty, contains more than 50 cards, or includes one or more cards not in the legal card set"""
        UNKNOWN_TYPE = auto()
        """The type field does not match any known PDU :class:`Type`"""
        STALE_ACTION = auto()
        """The `seq_num` does not match the current priority token"""
        NOT_YOUR_PRIORITY = auto()
        """The client submitted an action PDU when it does not hold priority"""
        ILLEGAL_ACTION = auto()
        """The action is syntactically valid but violates game rules (e.g., attacking with a tapped creature)"""
        ILLEGAL_TARGET = auto()
        """One or more targets in a :class:`CastSpell`, :class:`ActivateAbility`, or :class:`TriggerChoiceResponse` PDU are not legal targets"""
        TRIGGER_ORDER_INVALID = auto()
        """The :class:`TriggerOrderResponse` does not contain exactly the trigger IDs that were sent in the corresponding :class:`TriggerOrder` PDU"""
        TRIGGER_CHOICE_INVALID = auto()
        """The :class:`TriggerChoiceResponse` references an unknown :attr:`TriggerChoiceResponse.trigger_id`, or :class:`TriggerChoiceResponse.chosen_target` is absent when a target is required"""
        INSUFFICIENT_MANA = auto()
        """The :attr:`CastSpell.mana_payment` provided does not satisfy the spell's mana cost"""
        WRONG_PHASE = auto()
        """The action is not legal in the current phase (e.g., casting a sorcery outside a Main Phase)"""
        DUPLICATE_ID = auto()
        """The :attr:`PlayerReady.player_id` in a :class:`PlayerReady` PDU is already claimed by the other connected player in this lobby session"""

    type: Literal[Type.ERROR] = Type.ERROR
    seq_num: int
    code: Code
    message: str
    rejected_action: PDU


class Ping(BaseModel):
    """**Dir**: C -> S; **Phase**: Any.

    Notes:
        Heartbeat — server responds with :class:`Pong`

    Attributes:
        type (Literal[Type.PING]):
        seq_num (int):
        timestamp (float):
    """

    type: Literal[Type.PING] = Type.PING
    seq_num: int
    timestamp: float


class Pong(BaseModel):
    """**Dir**: S -> C; **Phase**: Any.

    Notes:
        Echo of the client's :class:`Ping` timestamp

    Attributes:
        type (Literal[Type.PONG]):
        seq_num (int):
        timestamp (float):
    """

    type: Literal[Type.PONG] = Type.PONG
    seq_num: int
    timestamp: float


PDU = Annotated[
    PlayerReady
    | GameStateUpdate
    | MulliganChoice
    | PhaseTransition
    | PriorityGrant
    | PriorityPass
    | CastSpell
    | ActivateAbility
    | StackPush
    | TriggerOrder
    | TriggerOrderResponse
    | TriggerChoice
    | TriggerChoiceResponse
    | StackResolve
    | DeclareAttackers
    | DeclareBlockers
    | AssignDamageOrder
    | CombatDamageResult
    | PlayLand
    | Discard
    | Concede
    | GameOver
    | Error
    | Ping
    | Pong,
    Field(discriminator="type"),
]

PDUValidator = TypeAdapter(PDU)
