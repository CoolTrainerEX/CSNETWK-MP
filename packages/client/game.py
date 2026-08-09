"""Client state."""

from prompt_toolkit.formatted_text import ANSI, to_formatted_text
from prompt_toolkit.patch_stdout import patch_stdout
from questionary import checkbox, confirm, select, text
from rich import print

from packages.client.input import Input, rich_parse
from packages.shared.cards import (
    BattlefieldCard,
    Card,
    CardID,
    CreatureCard,
    CreatureCardID,
    LandCard,
    Trigger,
)
from packages.shared.game import CombatStep, Game, GamePhase, State
from packages.shared.pdu import (
    PDU,
    ActivateAbility,
    AssignDamageOrder,
    CastSpell,
    Concede,
    DeclareAttackers,
    DeclareBlockers,
    Discard,
    MulliganChoice,
    PlayLand,
    PlayerReady,
    PriorityPass,
    TriggerChoiceResponse,
    TriggerID,
    TriggerOrderResponse,
    Type,
)
from packages.shared.player import Player, PlayerID
from packages.shared.types import ID


class ClientPlayer(Player):
    """Client player view."""

    def __init__(self, id: PlayerID, library_count: int) -> None:
        """Creates a client player.

        Args:
            id (PlayerID): Player ID
            library_count (int): Library count
        """
        super().__init__(id)
        self._library_count = library_count
        self._life_total = 20
        self._battlefield = set()
        self._graveyard = set()

    @property
    def library_count(self):
        """Player library count.

        Returns:
            int: Player library count
        """
        return self._library_count

    @library_count.setter
    def library_count(self, value):
        self._library_count = value

    @property
    def life_total(self):
        """Player life total."""
        return self._life_total

    @life_total.setter
    def life_total(self, value):
        self._life_total = value

    @property
    def battlefield(self):
        """Player battlefield."""
        return self._battlefield

    @battlefield.setter
    def battlefield(self, value):
        self._battlefield = value

    @property
    def graveyard(self):
        """Player graveyard."""
        return self._graveyard

    @graveyard.setter
    def graveyard(self, value):
        self._graveyard = value


class CurrentClientPlayer(ClientPlayer):
    """Current player."""

    def __init__(self, id: PlayerID, library_count: int) -> None:  # noqa: D107
        super().__init__(id, library_count)
        self._hand: set[Card] = set()

    @property
    def hand(self):
        """Player hand.

        Returns:
            set[Card]: Player hand.
        """
        return self._hand

    @hand.setter
    def hand(self, value):
        self._hand = value


class OpponentClientPlayer(ClientPlayer):
    """Opponent player."""

    def __init__(self, id: PlayerID, library_count: int) -> None:  # noqa: D107
        super().__init__(id, library_count)
        self._hand_count = 0

    @property
    def hand_count(self):
        """Player hand count.

        Returns:
            int: Player hand count.
        """
        return self._hand_count

    @hand_count.setter
    def hand_count(self, value):
        self._hand_count = value


class ClientGame(Game):
    """Client-side game."""

    def __init__(self) -> None:
        """Creates a client game instance."""
        super().__init__()
        self.__input = Input()

        # state tracking
        self.game_state_data = None
        self.priority_player = None
        self.priority_seq_num = 0
        self.time_limit_ms = 0
        self.stack = []
        self.error_msg = None
        self.active_player = None
        self.turn = 0
        self.game_over_data = None
        self.last_combat_result = None
        self.pending_trigger_order = None
        self.pending_trigger_choice = None

    @property
    def input(self):
        """Get game input."""
        return self.__input

    def concede(self):
        """Runs the concede input."""
        # TODO
        self.input.run(ClientGame.__concede())

    @staticmethod
    def __concede(seq_num: int, player_id: PlayerID):
        async def prompt():
            return Concede(seq_num=seq_num, player_id=player_id)

        return prompt

    def _parse_phase(self, phase_value: str):
        for enum_type in (State, GamePhase, CombatStep):
            try:
                return enum_type(phase_value)
            except ValueError:
                continue

        return None

    def run(self, pdu: PDU):
        """Run on receive.

        Args:
            pdu (PDU): PDU received
        """
        if hasattr(pdu, "seq_num"):
            self._seq_num = pdu.seq_num

        match pdu.type:
            case Type.GAME_STATE_UPDATE:
                self.game_state_data = pdu.state

                if hasattr(pdu.state, "phase"):
                    parsed_phase = self._parse_phase(pdu.state.phase)

                    if parsed_phase:
                        self.state = parsed_phase

                if hasattr(pdu.state, "active_player"):
                    self.active_player = pdu.state.active_player

                if hasattr(pdu.state, "turn"):
                    self.turn = pdu.state.turn

                if hasattr(pdu.state, "stack"):
                    self.stack = pdu.state.stack

                self._update_players(pdu.state)

            case Type.PHASE_TRANSITION:
                parsed_phase = self._parse_phase(pdu.to_phase)

                if parsed_phase:
                    self.state = parsed_phase

                self.active_player = pdu.active_player
                self.turn = pdu.turn

            case Type.PRIORITY_GRANT:
                self.priority_player = pdu.player_id
                self.priority_seq_num = pdu.seq_num
                self.time_limit_ms = pdu.time_limit_ms

            case Type.STACK_PUSH:
                self.stack.append(pdu)

            case Type.STACK_RESOLVE:
                self.stack = [
                    item
                    for item in self.stack
                    if getattr(item, "stack_item_id", None) != pdu.stack_item_id
                ]

            case Type.GAME_OVER:
                self.state = State.GAME_OVER
                self.game_over_data = pdu

            case Type.ERROR:
                self.error_msg = pdu.message

            case Type.COMBAT_DAMAGE_RESULT:
                self.last_combat_result = pdu

            case Type.TRIGGER_ORDER:
                self.pending_trigger_order = pdu

            case Type.TRIGGER_CHOICE:
                self.pending_trigger_choice = pdu

    def ready(self):
        """Initial player ready prompt."""
        # TODO Set seq_num
        self.input.run(ClientGame.__ready_prompt(1))

    # TODO
    @staticmethod
    def __ready_prompt(seq_num: int):
        async def prompt():
            player_id = ""
            deck_list = None

            with patch_stdout():
                player_id = await text(
                    "Player ID",
                    validate=lambda text: text != "" or "Must not be empty.",  # type: ignore
                ).ask_async()

                deck_list = await checkbox(
                    "Cards",
                    [
                        {
                            "name": to_formatted_text(
                                ANSI(rich_parse(f"\n{card(id)}"))
                            ),
                            "value": id,
                        }
                        for id, card in Card.registry().items()
                    ],
                    instruction="Select cards for the deck.",
                    validate=lambda choices: (
                        len(choices) != 0 or "Choose at least one."
                    ),
                ).ask_async()

            return [
                PlayerReady(seq_num=1, player_id=player_id, deck_list=set(deck_list))
            ]

        return prompt

    # TODO
    @staticmethod
    def __mulligan_prompt(seq_num: int, cards: set[Card], num_bottom: int):
        async def prompt():
            with patch_stdout():
                cards_to_bottom = await checkbox(
                    "Mulligan",
                    [
                        {
                            "name": to_formatted_text(ANSI(rich_parse(f"\n{card}"))),
                            "value": card.id,
                        }
                        for card in cards
                    ],
                    instruction=f"Choose {num_bottom} cards to place on the bottom of the library or choose none to keep.",
                    validate=lambda choices: (
                        len(choices) == 0
                        or len(choices) == num_bottom
                        or f"Choose {num_bottom} or none."
                    ),
                ).ask_async()

            return [
                MulliganChoice(
                    seq_num=seq_num,
                    keep=len(cards_to_bottom) == 0,
                    cards_to_bottom=cards_to_bottom,
                )
            ]

        return prompt

    # TODO
    @staticmethod
    def __priority(
        seq_num: int,
        spells: dict[Card, tuple[int, set[ID]]] = {},
        abilities: dict[BattlefieldCard, list[tuple[int, set[ID]]]] = {},
    ):
        """Priority action.

        Args:
            seq_num (int): Sequence number
            spells (dict[Card, tuple[int, set[ID]]]): Cards to cast (including land) and number of targets to choose with set of available targets. Empty if no targets.
            abilities (dict[BattlefieldCard, list[tuple[int, set[ID]]]]): Cards with available abilities and number of targets with set of available targets indexed to the ability index.
        """

        async def prompt():
            match await select(
                "Gained priority.",
                [
                    choice
                    for choice in [
                        "Cast spell" if spells else None,
                        "Activate ability" if abilities else None,
                        "Pass",
                    ]
                    if choice
                ],
            ).ask_async():
                case "Cast spell":
                    spell: Card = await select(
                        "Cast spell",
                        [
                            {
                                "name": to_formatted_text(
                                    ANSI(rich_parse(f"\n{card}"))
                                ),
                                "value": card,
                            }
                            for card in spells.keys()
                        ],
                    ).ask_async()

                    if spells[spell][1]:
                        targets = set(
                            await checkbox(
                                "Select target",
                                list(spells[spell][1]),
                                instruction=f"Choose {spells[spell][0]} targets.",
                                validate=lambda choices: (
                                    len(choices) == spells[spell][0]
                                    or f"Choose {spells[spell][0]} targets."
                                ),
                            ).ask_async()
                        )
                    else:
                        targets: set[ID] = set()

                    if isinstance(spell, LandCard):
                        return [PlayLand(seq_num=seq_num, card_id=spell.id)]

                    return [
                        CastSpell(
                            seq_num=seq_num,
                            card_id=spell.id,
                            targets=targets,
                            mana_payment=spell.cast_details().mana_cost,
                        )
                    ]
                case "Activate ability":
                    card: BattlefieldCard = await select(
                        "Activate ability",
                        [
                            {
                                "name": to_formatted_text(
                                    ANSI(rich_parse(f"\n{card}"))
                                ),
                                "value": card,
                            }
                            for card in abilities.keys()
                        ],
                    ).ask_async()

                    ability: int = await select(
                        "Select ability",
                        [
                            {
                                "name": to_formatted_text(
                                    ANSI(rich_parse(ability.text))
                                ),
                                "value": index,
                            }
                            for index, ability in enumerate(card.abilities_details())
                        ],
                    ).ask_async()

                    if abilities[card][ability][1]:
                        targets = set(
                            await checkbox(
                                "Select target",
                                list(abilities[card][ability][1]),
                                instruction=f"Choose {abilities[card][ability][0]} targets.",
                                validate=lambda choices: (
                                    len(choices) == abilities[card][ability][0]
                                    or f"Choose {abilities[card][ability][0]} targets."
                                ),
                            ).ask_async()
                        )
                    else:
                        targets: set[ID] = set()

                    return [
                        ActivateAbility(
                            seq_num=seq_num,
                            source_id=card.id,
                            ability_index=ability,
                            targets=targets,
                            cost_payment=ActivateAbility.CostPayment(  # type: ignore
                                tap=bool(card.abilities_details()[ability].tap_cost),
                                mana=card.abilities_details()[ability].mana_cost,
                            ),
                        )
                    ]
                case _:
                    return [PriorityPass(seq_num=seq_num)]

        return prompt

    # TODO
    @staticmethod
    def __declare_attackers(
        seq_num: int, opponent_id: PlayerID, attackers: set[CreatureCard] = set()
    ):
        """Declare attackers prompt.

        Args:
            seq_num (int): Sequence number
            attackers (set[CreatureCard]): Set of available attacker choices
            opponent_id (PlayerID): Target player ID
        """

        async def prompt():
            return (
                [
                    DeclareAttackers(
                        seq_num=seq_num,
                        attackers={
                            DeclareAttackers.Attacker(
                                creature_id=attacker, target=opponent_id
                            )
                            for attacker in await checkbox(
                                "Declare attackers",
                                [
                                    {
                                        "name": to_formatted_text(
                                            ANSI(rich_parse(f"\n{attacker}"))
                                        ),
                                        "value": attacker.id,
                                    }
                                    for attacker in attackers
                                ],
                            ).ask_async()
                        },
                    )
                ]
                if attackers
                else []
            )

        return prompt

    # TODO
    @staticmethod
    def __declare_blockers(
        seq_num: int, blockers: dict[CreatureCard, set[CreatureCard]] | None = None
    ):
        """Declare blockers prompt.

        Args:
            seq_num (int): Sequence number
            blockers (dict[CreatureCard, set[CreatureCard]] | None): Available blockers and set of blockable attackers
        """
        if blockers is None:
            blockers = {}

        async def prompt():
            blockers_set: set[DeclareBlockers.Blocker] = set()

            while blockers:
                blocker = await select(
                    "Declare blockers",
                    [
                        {
                            "name": to_formatted_text(ANSI(rich_parse(f"\n{blocker}"))),
                            "value": blocker,
                        }
                        for blocker in blockers.keys()
                    ]
                    + ["Done"],
                ).ask_async()

                if not isinstance(blocker, CreatureCard):
                    break

                blockers_set.add(
                    DeclareBlockers.Blocker(
                        creature_id=blocker.id,
                        blocking_id=await select(
                            "Select attacker",
                            [
                                {
                                    "name": to_formatted_text(
                                        ANSI(rich_parse(f"\n{attacker}"))
                                    ),
                                    "value": attacker.id,
                                }
                                for attacker in blockers[blocker]
                            ],
                        ).ask_async(),
                    )
                )

                del blockers[blocker]

            return [
                DeclareBlockers(
                    seq_num=seq_num,
                    blockers=blockers_set,
                )
            ]

        return prompt

    # TODO
    @staticmethod
    def __assign_damage_order(
        seq_num: int, attackers: dict[CreatureCard, set[CreatureCard]] | None = None
    ):
        if attackers is None:
            attackers = {}

        async def prompt():
            damage_orders: list[AssignDamageOrder] = []

            while attackers:
                attacker = await select(
                    "Assign damage order",
                    [
                        {
                            "name": to_formatted_text(
                                ANSI(rich_parse(f"\n{attacker}"))
                            ),
                            "value": attacker,
                        }
                        for attacker in attackers.keys()
                    ],
                ).ask_async()

                blockers: list[CreatureCardID] = []

                while attackers[attacker]:
                    blocker = await select(
                        "Select blocker",
                        [
                            {
                                "name": to_formatted_text(
                                    ANSI(rich_parse(f"\n{blocker}"))
                                ),
                                "value": blocker,
                            }
                            for blocker in attackers[attacker]
                        ],
                        instruction="Select the next blocker.",
                    ).ask_async()

                    blockers.append(blocker.id)

                    attackers[attacker].remove(blocker)

                damage_orders.append(
                    AssignDamageOrder(
                        seq_num=seq_num, attacker_id=attacker.id, blocker_order=blockers
                    )
                )

                del attackers[attacker]

            return damage_orders

        return prompt

    # TODO
    @staticmethod
    def __trigger_order(seq_num: int, triggers: dict[TriggerID, Trigger] | None = None):
        """Assign trigger order.

        Args:
            seq_num (int): Sequence number
            triggers (dict[TriggerID,Trigger] | None): List of triggers and card origins
        """
        if triggers is None:
            triggers = {}

        async def prompt():
            trigger_order: list[TriggerID] = []
            while triggers:
                trigger = await select(
                    "Trigger order",
                    [
                        {
                            "name": to_formatted_text(
                                ANSI(rich_parse(card.trigger_details()))
                            ),
                            "value": id,
                        }
                        for id, card in triggers.items()
                    ],
                    instruction="Select the next trigger.",
                ).ask_async()

                trigger_order.append(trigger)

                del triggers[trigger]

            return [
                TriggerOrderResponse(seq_num=seq_num, ordered_trigger_ids=trigger_order)
            ]

        return prompt

    # TODO
    @staticmethod
    def __trigger_choice(
        seq_num: int, trigger: tuple[TriggerID, Trigger], targets: set[ID] = set()
    ):
        async def prompt():
            print(trigger[1].trigger_details())
            if await confirm("Activate trigger?").ask_async():
                if targets:
                    target = await select("Select target", list(targets)).ask_async()
                else:
                    target = None

                return [
                    TriggerChoiceResponse(
                        seq_num=seq_num,
                        trigger_id=trigger[0],
                        accept=True,
                        chosen_target=target,
                    )
                ]
            else:
                return [
                    TriggerChoiceResponse(
                        seq_num=seq_num, trigger_id=trigger[0], accept=False
                    )
                ]

        return prompt

    # TODO
    @staticmethod
    def __discard(seq_num: int, hand: set[Card] | None = None):
        if hand is None:
            hand = set()

        async def prompt():
            discard_set: set[CardID] = set()

            while len(hand) > 7:
                discard: Card = await select(
                    "Discard",
                    [
                        {
                            "name": to_formatted_text(ANSI(rich_parse(f"\n{card}"))),
                            "value": card,
                        }
                        for card in hand
                    ],
                    instruction="Discard until you have seven cards.",
                ).ask_async()

                discard_set.add(discard.id)
                hand.remove(discard)

            return [Discard(seq_num=seq_num, card_ids=discard_set)]

        return prompt

    def _update_players(self, state):
        if not hasattr(state, "life_totals"):
            return  # lobby state

        our_id = None
        opponent_id = None

        for pid in getattr(state, "hand", {}).keys():
            our_id = pid

        for pid in getattr(state, "hand_counts", {}).keys():
            if pid != our_id:
                opponent_id = pid

        if not self._players and our_id and opponent_id:
            self._players = [
                CurrentClientPlayer(our_id, state.library_counts.get(our_id, 0)),
                OpponentClientPlayer(
                    opponent_id, state.library_counts.get(opponent_id, 0)
                ),
            ]

        for p in self._players:
            if isinstance(p, CurrentClientPlayer) and p.id == our_id:
                p.life_total = state.life_totals.get(our_id, p.life_total)
                p.graveyard = state.graveyard.get(our_id, p.graveyard)
                p.hand = state.hand.get(our_id, p.hand)
                p.library_count = state.library_counts.get(our_id, p.library_count)
                p.battlefield = state.battlefield.get(our_id, p.battlefield)
            elif isinstance(p, OpponentClientPlayer) and p.id == opponent_id:
                p.life_total = state.life_totals.get(opponent_id, p.life_total)
                p.graveyard = state.graveyard.get(opponent_id, p.graveyard)
                p.hand_count = state.hand_counts.get(opponent_id, p.hand_count)
                p.library_count = state.library_counts.get(opponent_id, p.library_count)
                p.battlefield = state.battlefield.get(opponent_id, p.battlefield)
