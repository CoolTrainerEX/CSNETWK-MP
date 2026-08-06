"""PDU schemas."""

from enum import StrEnum, auto
from time import time
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from cards import Card, CardModel, CreatureCardModel, LandCardModel
from game import ID
from player import PlayerModel


class State(StrEnum):
    """Game states."""

    LOBBY = auto()
    GAME_SETUP = auto()
    MULLIGAN = auto()
    IN_GAME = auto()
    GAME_OVER = auto()


class GamePhase(StrEnum):
    """:attr:`State.IN_GAME` phases."""

    UNTAP = auto()

    UPKEEP = auto()
    """Priority window"""

    DRAW = auto()
    """Priority window"""

    PRECOMBAT_MAIN = auto()
    """Priority window (sorcery speed for AP)"""

    COMBAT = auto()
    """See :class:`CombatStep` for sub-steps"""

    POSTCOMBAT_MAIN = auto()
    """Priority window (sorcery speed for AP)"""

    END_STEP = auto()
    """Priority window"""

    CLEANUP = auto()


class CombatStep(StrEnum):
    """:attr:`GamePhase.COMBAT` steps."""

    BEGIN_COMBAT = auto()

    DECLARE_ATTACKERS = auto()
    """AP declares; priority window follows"""

    DECLARE_BLOCKERS = auto()
    """NAP assigns blockers; priority window follows"""

    ASSIGN_DAMAGE_ORDER = auto()
    """AP orders multi-blockers; priority window"""

    FIRST_STRIKE_DAMAGE = auto()
    """OPTIONAL: only if first/double strike present"""
    COMBAT_DAMAGE = auto()
    """Server resolves damage; priority window"""

    END_OF_COMBAT = auto()
    """Priority window; combat concludes"""


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
        player_id (PlayerModel): Client-chosen non-empty string; must be unique in this lobby
        deck_list (set[str]): 1 to 50 card IDs
    """

    type: Literal[Type.PLAYER_READY]
    seq_num: int
    player_id: PlayerModel
    deck_list: set[CardModel]


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
            waiting_for (set[PlayerModel]): :attr:`PlayerReady.player_id`s not yet ready
        """

        phase: Literal[State.LOBBY]
        players_ready: int
        waiting_for: set[PlayerModel]

    class __GameState(BaseModel):
        """State in all other phases.

        Attributes:
            turn (int):
            active_player (PlayerModel):
            phase (Literal[State.MULLIGAN] | GamePhase | CombatStep):
            priority_holder (PlayerModel | None): `None` during :attr:`CombatStep.UNTAP` and :attr:`CombatStep.CLEANUP` steps
            life_totals (dict[PlayerModel, int]):
            battlefield (dict[PlayerModel, set[__BattlefieldCard | __BattlefieldCreatureCard]]):
            graveyard (dict[PlayerModel, set[CardModel]]): Ordered by insertion: index 0 = first card placed, last = most recently added
            hand (dict[PlayerModel, set[CardModel]]):
            hand_counts (dict[PlayerModel, int]):
            library_counts (dict[PlayerModel, int]):
            land_played_this_turn (bool): `True` if AP has already played a land this turn
        """

        class __BattlefieldCard(BaseModel):
            """Card placed in :attr:`GameStateUpdate.state.battlefield`.

            Attributes:
                id (CardModel):
                tapped (bool):
            """

            id: CardModel
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
                id (CreatureCardModel):
                damage (int):
                power (int):
                toughness (int):
                summoning_sick (bool):
            """

            id: CreatureCardModel
            damage: int
            power: int
            toughness: int
            summoning_sick: bool

        turn: int
        active_player: PlayerModel
        phase: Literal[State.MULLIGAN] | GamePhase | CombatStep
        priority_holder: PlayerModel | None
        life_totals: dict[PlayerModel, int]
        battlefield: dict[
            PlayerModel, set[__BattlefieldCard | __BattlefieldCreatureCard]
        ]
        graveyard: dict[PlayerModel, set[CardModel]]
        hand: dict[PlayerModel, set[CardModel]]
        hand_counts: dict[PlayerModel, int]
        library_counts: dict[PlayerModel, int]
        land_played_this_turn: bool

    type: Literal[Type.GAME_STATE_UPDATE]
    seq_num: int
    state: __LobbyState | __GameState = Field(discriminator="phase")


class MulliganChoice(BaseModel):
    """**Dir**: C -> S; **Phase**: Setup.

    Notes:
        Server redraws if :attr:`MulliganChoice.keep` is `False` (London Mulligan)

    Attributes:
        type (Literal[Type.MULLIGAN_CHOICE]):
        seq_num (int): Monotonically increasing message counter
        keep (bool): `False` = take a mulligan
        cards_to_bottom (set[CardModel]): Must equal mulligan count when :attr:`MulliganChoice.keep` = `True`
    """

    type: Literal[Type.MULLIGAN_CHOICE]
    seq_num: int
    keep: bool
    cards_to_bottom: set[CardModel]


class PhaseTransition(BaseModel):
    """**Dir**: S -> ALL; **Phase**: All.

    Notes:
        Broadcast when server advances a step or phase

    Attributes:
        type (Literal[Type.PHASE_TRANSITION]):
        seq_num (int): Server-issued sequence number
        from_phase (GamePhase | CombatStep):
        to_phase (GamePhase | CombatStep):
        active_player (PlayerModel):
        turn (int):
    """

    type: Literal[Type.PHASE_TRANSITION]
    seq_num: int
    from_phase: GamePhase | CombatStep
    to_phase: GamePhase | CombatStep
    active_player: PlayerModel
    turn: int


class PriorityGrant(BaseModel):
    """**Dir**: S -> C; **Phase**: Priority.

    Notes:
        Sent only to the player who now holds priority

    Attributes:
        type (Literal[Type.PRIORITY_GRANT]):
        player_id (PlayerModel):
        seq_num (int): Server-enforced response deadline
        time_limit_ms (int):
    """

    type: Literal[Type.PRIORITY_GRANT]
    player_id: PlayerModel
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

    type: Literal[Type.PRIORITY_PASS]
    seq_num: int


class CastSpell(BaseModel):
    """**Dir**: C -> S; **Phase**: Priority.

    Notes:
        Server validates; pushes to stack on success

    Attributes:
        type (Literal[Type.CAST_SPELL]):
        seq_num (int):
        card_id (CardModel):
        targets (set[ID]): Empty array if spell has no targets
        mana_payment (dict[Card.Color, int]):
    """

    type: Literal[Type.CAST_SPELL]
    seq_num: int
    card_id: CardModel
    targets: set[ID]
    mana_payment: dict[Card.Color, int]


class ActivateAbility(BaseModel):
    """**Dir**: C -> S; **Phase**: Priority.

    Notes:
        Mana abilities bypass the stack entirely
        Server rejects with :attr:`Error.ILLEGAL_ACTION` if permanent is already tapped

    Attributes:
        type (Literal[Type.ACTIVATE_ABILITY]):
        seq_num (int):
        source_id (CardModel):
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

    type: Literal[Type.ACTIVATE_ABILITY]
    seq_num: int
    source_id: CardModel
    ability_index: int
    targets: set[ID]
    cost_payment: __CostPayment


StackID = ID


class StackItem(BaseModel):
    """Stack item.

    Attributes:
        stack_item_id (ID):
        item_type (ItemType):
        source (CardModel):
        targets (set[ID]):
        cotroller (PlayerModel):
    """

    class ItemType(StrEnum):
        """Stack item type."""

        SPELL = auto()
        ABILITY = auto()
        TRIGGER_ABILITY = auto()

    stack_item_id: StackID
    item_type: ItemType
    source: CardModel
    targets: set[ID]
    cotroller: PlayerModel


class StackPush(StackItem):
    """**Dir**: S -> ALL; **Phase**: Stack.

    Attributes:
        type (Literal[Type.STACK_PUSH]):
        seq_num (int): Server-issued sequence number
    """

    type: Literal[Type.STACK_PUSH]
    seq_num: int


TriggerID = ID


class TriggerOrder(BaseModel):
    """**Dir**: S -> C; **Phase**: Stack.

    Notes:
        Player must specify order for their simultaneous triggers

    Attributes:
        type (Literal[Type.TRIGGER_ORDER]):
        seq_num (int): Server-issued sequence number
        player_id (PlayerModel): Player must order these
        trigger_ids (set[TriggerID]):
    """

    type: Literal[Type.TRIGGER_ORDER]
    seq_num: int
    player_id: PlayerModel
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

    type: Literal[Type.TRIGGER_ORDER_RESPONSE]
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
        source_id (CardModel):
        effect_summary (str):
        requires_target (bool): `True` if player must also pick a target
        legal_targets (ID): Elements are `player_id` strings or permanent id
    """

    type: Literal[Type.TRIGGER_CHOICE]
    seq_num: int
    trigger_id: TriggerID
    source_id: CardModel
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

    type: Literal[Type.TRIGGER_CHOICE_RESPONSE]
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

    type: Literal[Type.STACK_RESOLVE]
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
            creature_id (CreatureCardModel):
            target (PlayerModel):
        """

        creature_id: CreatureCardModel
        target: PlayerModel

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

    type: Literal[Type.DECLARE_ATTACKERS]
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
            creature_id (CreatureCardModel):
            blocking_id (CreatureCardModel):
        """

        creature_id: CreatureCardModel
        blocking_id: CreatureCardModel

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

    type: Literal[Type.DECLARE_BLOCKERS]
    seq_num: int
    attackers: set[__Blocker]


class AssignDamageOrder(BaseModel):
    """**Dir**:C -> S; **Phase**: Combat.

    Notes:
        Required when multiple blockers on one attacker

    Attributes:
        type (Literal[Type.ASSIGN_DAMAGE_ORDER]):
        seq_num (int):
        attacker_id (CreatureCardModel):
        blocker_order (set[CreatureCardModel]):
    """

    type: Literal[Type.ASSIGN_DAMAGE_ORDER]
    seq_num: int
    attacker_id: CreatureCardModel
    blocker_order: set[CreatureCardModel]


class CombatDamageResult(BaseModel):
    """**Dir**: S -> ALL; **Phase**: Combat.

    Notes:
        Server computes all damage simultaneously

    Attributes:
        type (Literal[Type.COMBAT_DAMAGE_RESULT]):
        seq_num (int): Server-issued sequence number
        damage_events (set[DamageEvent]):
        life_totals (dict[PlayerModel, int]):
        creatures_died (set[CreatureCardModel]):
    """

    class __DamageEvent(BaseModel):
        """Combat damage event.

        Attributes:
            source (CreatureCardModel):
            target (CreatureCardModel | PlayerModel):
            amount (int):
        """

        source: CreatureCardModel
        target: CreatureCardModel | PlayerModel
        amount: int

    type: Literal[Type.COMBAT_DAMAGE_RESULT]
    seq_num: int
    damage_events: set[__DamageEvent]
    life_totals: dict[PlayerModel, int]
    creatures_died: set[CreatureCardModel]


class PlayLand(BaseModel):
    """**Dir**: C -> S; **Phase**: Main.

    Notes:
        Does not use the stack; one per turn limit

    Attributes:
        type (Literal[Type.PLAY_LAND]):
        seq_num (int):
        card_id (LandCardModel):
    """

    type: Literal[Type.PLAY_LAND]
    seq_num: int
    card_id: LandCardModel


class Discard(BaseModel):
    """**Dir**: C -> S; **Phase**: Cleanup.

    Notes:
        Required when hand size > 7 at cleanup

    Attributes:
        type (Literal[Type.DISCARD]):
        seq_num (int):
        card_ids (set[CardModel]):
    """

    type: Literal[Type.DISCARD]
    seq_num: int
    card_ids: set[CardModel]


class Concede(BaseModel):
    """**Dir**: C -> S; **Phase**: Any.

    Notes:
        Triggers immediate :attr:`State.GAME_OVER`

    Attributes:
        type (Literal[Type.CONCEDE]):
        seq_num (int):
        player_id (PlayerModel):
    """

    type: Literal[Type.CONCEDE]
    seq_num: int
    player_id: PlayerModel


class GameOver(BaseModel):
    """**Dir**: S -> ALL; **Phase**: End.

    Attributes:
        type (Literal[Type.GAME_OVER]):
        seq_num (int): Server-issued sequence number
        winner_id (PlayerModel):
        loser_id (PlayerModel):
        reason (Reason):
    """

    class Reason(StrEnum):
        """Game over reason."""

        LIFE_ZERO = auto()
        DECK_EMPTY = auto()
        CONCEDE = auto()
        DISCONNECT = auto()

    type: Literal[Type.GAME_OVER]
    seq_num: int
    winner_id: PlayerModel
    loser_id: PlayerModel
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

    type: Literal[Type.ERROR]
    seq_num: int
    code: Code
    message: str
    rejected_action: PDU


class Ping(BaseModel):
    """**Dir**:c C -> S; **Phase**: Any.

    Notes:
        Heartbeat — server responds with :class:`Pong`

    Attributes:
        type (Literal[Type.PING]):
        seq_num (int):
        timestamp (float):
    """

    type: Literal[Type.PING]
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

    type: Literal[Type.PONG]
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
