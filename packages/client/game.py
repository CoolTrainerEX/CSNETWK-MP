"""Client state."""

from pkgutil import ModuleInfo

from prompt_toolkit.formatted_text import ANSI, to_formatted_text
from prompt_toolkit.patch_stdout import patch_stdout
from questionary import checkbox, confirm, select, text
from rich import print
from rich.table import Table

from packages.client.input import Input, rich_parse
from packages.shared.cards import (
    BattlefieldCard,
    Card,
    CardID,
    CreatureCard,
    CreatureCardID,
    InstantCard,
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
    Error,
    GameStateUpdate,
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
        self.__land_played_this_turn = False

    @property
    def input(self):
        """Get game input."""
        return self.__input

    @property
    def concede(self):
        """Get concede PDU.

        Returns:
            Concede: Concede PDU
        """
        player_id = (
            self._players[0].id if hasattr(self, "_players") and self._players else ""
        )
        return Concede(seq_num=getattr(self, "_seq_num", 1), player_id=player_id)

    def _parse_phase(self, phase_value: str):
        for enum_type in (State, GamePhase, CombatStep):
            try:
                return enum_type(phase_value)
            except ValueError:
                continue

        return prompt

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
                    self.state = pdu.state.phase

                if hasattr(pdu.state, "active_player"):
                    self.active_player = pdu.state.active_player

                if hasattr(pdu.state, "priority_holder"):
                    self.priority_player = pdu.state.priority_holder

                if hasattr(pdu.state, "turn"):
                    self.turn = pdu.state.turn

                if hasattr(pdu.state, "stack"):
                    self.stack = pdu.state.stack

                if hasattr(pdu.state, "land_played_this_turn"):
                    self.__land_played_this_turn = pdu.state.land_played_this_turn

                self._update_players(pdu.state)

                if isinstance(pdu.state, GameStateUpdate.LobbyState):
                    print("[bold magenta]Waiting...[/]")

                    for player in pdu.state.waiting_for:
                        print(player)
                else:
                    data = Table("Turn", "Phase", "Active Player", "Priority Holder")

                    data.add_row(
                        str(self.turn),
                        self.state.title(),
                        self.active_player,
                        self.priority_player,
                    )
                    opponent = Table(
                        "Life Total",
                        "Library",
                        "Hand",
                        title=self.__get_opponent_player().id,
                    )
                    opponent.add_row(
                        str(self.__get_opponent_player().life_total),
                        str(self.__get_opponent_player().library_count),
                        str(self.__get_opponent_player().hand_count),
                    )
                    opponent_graveyard = Table(
                        title=f"{self.__get_opponent_player().id} Graveyard",
                        show_header=False,
                    )

                    opponent_graveyard.add_row(
                        *[f"{card}" for card in self.__get_opponent_player().graveyard]
                    )

                    opponent_battlefield = Table(
                        title=f"{self.__get_opponent_player().id} Battlefield",
                        show_header=False,
                    )

                    opponent_battlefield.add_row(
                        *[
                            f"{card}"
                            for card in self.__get_opponent_player().battlefield
                            if not isinstance(card, LandCard)
                        ]
                    )
                    opponent_battlefield.add_row(
                        *[
                            f"{card}"
                            for card in self.__get_opponent_player().battlefield
                            if isinstance(card, LandCard)
                        ]
                    )

                    current_battlefield = Table(
                        title=f"{self.__get_current_player().id} Battlefield",
                        show_header=False,
                    )

                    current_battlefield.add_row(
                        *[
                            f"{card}"
                            for card in self.__get_current_player().battlefield
                            if not isinstance(card, LandCard)
                        ],
                    )

                    current_battlefield.add_row(
                        *[
                            f"{card}"
                            for card in self.__get_current_player().battlefield
                            if isinstance(card, LandCard)
                        ],
                    )

                    hand = Table(title="Hand", show_header=False)

                    hand.add_row(
                        *[f"{card}" for card in self.__get_current_player().hand],
                    )

                    current = Table(
                        "Life Total",
                        "Library",
                        title=self.__get_current_player().id,
                    )

                    current.add_row(
                        str(self.__get_current_player().life_total),
                        str(self.__get_current_player().library_count),
                    )
                    current_graveyard = Table(
                        title=f"{self.__get_current_player().id} Graveyard",
                        show_header=False,
                    )

                    opponent_graveyard.add_row(
                        *[f"{card}" for card in self.__get_current_player().graveyard]
                    )

                    print(
                        data,
                        opponent,
                        opponent_graveyard,
                        opponent_battlefield,
                        current_battlefield,
                        hand,
                        current,
                        current_graveyard,
                    )
                if self.state == State.MULLIGAN and self.__mulligan_count != -1:
                    self.input.run(
                        self.__mulligan_prompt(
                            self._seq_num, self.__get_current_player().hand
                        )
                    )
            case Type.PHASE_TRANSITION:
                self.state = pdu.to_phase

                self.active_player = pdu.active_player
                self.turn = pdu.turn

                print(
                    f"[italic magenta]{pdu.from_phase.title()} \u2192 {pdu.to_phase.title()}[/]"
                )

                if self.active_player == self.__get_current_player().id:
                    if self.state == CombatStep.DECLARE_ATTACKERS:
                        self.input.run(
                            ClientGame.__declare_attackers(
                                self._seq_num,
                                self.__get_opponent_player().id,
                                {
                                    card
                                    for card in self.__get_current_player().battlefield
                                    if isinstance(card, CreatureCard)
                                    and not card.tapped
                                    and not card.summoning_sick
                                    and CreatureCard.Modifier.DEFENDER
                                    not in card.modifiers()
                                },
                            )
                        )
                elif self.state == CombatStep.DECLARE_BLOCKERS:
                    self.input.run(
                        ClientGame.__declare_blockers(
                            self._seq_num,
                            {
                                blocker: {
                                    attacker
                                    for attacker in self.__get_opponent_player().battlefield
                                    if isinstance(attacker, CreatureCard)
                                    and attacker.tapped
                                    and (
                                        CreatureCard.Modifier.FLYING
                                        not in attacker.modifiers()
                                        or CreatureCard.Modifier.FLYING
                                        in blocker.modifiers()
                                    )
                                }
                                for blocker in self.__get_current_player().battlefield
                                if isinstance(blocker, CreatureCard)
                                and not blocker.tapped
                                and not blocker.summoning_sick
                                and CreatureCard.Modifier.DEFENDER
                                not in blocker.modifiers()
                            },
                        )
                    )
            case Type.PRIORITY_GRANT:
                self.priority_player = pdu.player_id
                self.priority_seq_num = pdu.seq_num
                self.time_limit_ms = pdu.time_limit_ms

                targets = [
                    id
                    for player in self._players
                    for id in [player.id] + [card.id for card in player.battlefield]
                ] + self.stack

                self.input.run(
                    ClientGame.__priority(
                        self.priority_seq_num,
                        {
                            card: (0, targets)
                            for card in self.__get_current_player().hand
                            if self.state in (GamePhase.UPKEEP, GamePhase.END_STEP)
                            and isinstance(card, InstantCard)
                            or self.state
                            in (GamePhase.PRECOMBAT_MAIN, GamePhase.POSTCOMBAT_MAIN)
                            and self.active_player == self.__get_current_player().id
                            and not (
                                isinstance(card, LandCard)
                                and self.__land_played_this_turn
                            )
                        },
                        {
                            card: [(0, targets) for _ in card.abilities_details()]
                            for card in self.__get_current_player().battlefield
                            if card.abilities_details()
                            and not isinstance(card, LandCard)
                        },
                    )
                )

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
                print(f"""[bold dark_orange]
  ________                        ________                     
 /  _____/_____    _____   ____   \\_____  \\___  __ ___________ 
/   \\  ___\\__  \\  /     \\_/ __ \\   /   |   \\  \\/ // __ \\_  __ \\
\\    \\_\\  \\/ __ \\|  Y Y  \\  ___/  /    |    \\   /\\  ___/|  | \\/
 \\______  (____  /__|_|  /\\___  > \\_______  /\\_/  \\___  >__|   
        \\/     \\/      \\/     \\/          \\/          \\/       

[/][magenta]Winner: [bold]{self.game_over_data.winner_id}[/]
Loser: [bold]{self.game_over_data.loser_id}[/]

[italic]{self.game_over_data.reason.title()}[/][/]
""")
                self.ready()

            case Type.ERROR:
                self.error_msg = pdu.message
                print(f"[bold white on red]{self.error_msg}[/]")

                if pdu.code in (Error.Code.DUPLICATE_ID, Error.Code.ILLEGAL_DECK):
                    self.ready()

            case Type.COMBAT_DAMAGE_RESULT:
                self.last_combat_result = pdu

            case Type.TRIGGER_ORDER:
                self.pending_trigger_order = pdu

            case Type.TRIGGER_CHOICE:
                self.pending_trigger_choice = pdu

    def ready(self):
        """Initial player ready prompt."""
        self._player_ready_seq_num = getattr(self, "_player_ready_seq_num", 0) + 1
        self.__mulligan_count = 0
        self.input.run(ClientGame.__ready_prompt(self._player_ready_seq_num))

    def __get_current_player(self) -> CurrentClientPlayer:  # type: ignore
        for player in self._players:
            if isinstance(player, CurrentClientPlayer):
                return player

    def __get_opponent_player(self) -> OpponentClientPlayer:  # type: ignore
        for player in self._players:
            if isinstance(player, OpponentClientPlayer):
                return player

    @staticmethod
    def __ready_prompt(seq_num: int):
        async def prompt():
            print("""[bold dark_orange]
 _______  _______  _______ _________ _______                                                                  
(       )(  ___  )(  ____ \\__   __/(  ____ \\                                                                 
| () () || (   ) || (    \\/   ) (   | (    \\/                                                                 
| || || || (___) || |         | |   | |                                                                       
| |(_)| ||  ___  || | ____    | |   | |                                                                       
| |   | || (   ) || | \\_  )   | |   | |                                                                       
| )   ( || )   ( || (___) |___) (___| (____/\\                                                                 
|/     \\||/     \\|(_______)\\_______/(_______/                                                                 
                                                                                                              
_________          _______    _______  _______ _________          _______  _______ _________ _        _______ 
\\__   __/|\\     /|(  ____ \\  (  ____ \\(  ___  )\\__   __/|\\     /|(  ____ \\(  ____ )\\__   __/( (    /|(  ____ \\
   ) (   | )   ( || (    \\/  | (    \\/| (   ) |   ) (   | )   ( || (    \\/| (    )|   ) (   |  \\  ( || (    \\/
   | |   | (___) || (__      | |      | (___) |   | |   | (___) || (__    | (____)|   | |   |   \\ | || |      
   | |   |  ___  ||  __)     | | ____ |  ___  |   | |   |  ___  ||  __)   |     __)   | |   | (\\ \\) || | ____ 
   | |   | (   ) || (        | | \\_  )| (   ) |   | |   | (   ) || (      | (\\ (      | |   | | \\   || | \\_  )
   | |   | )   ( || (____/\\  | (___) || )   ( |   | |   | )   ( || (____/\\| ) \\ \\_____) (___| )  \\  || (___) |
   )_(   |/     \\|(_______/  (_______)|/     \\|   )_(   |/     \\|(_______/|/   \\__/\\_______/|/    )_)(_______)                                                                                                            
[/]""")
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

    def __mulligan_prompt(self, seq_num: int, cards: set[Card]):
        async def prompt():
            with patch_stdout():
                if await confirm("Redraw?").ask_async():
                    self.__mulligan_count += 1
                    return [MulliganChoice(seq_num=seq_num, keep=False)]
                else:
                    if self.__mulligan_count:
                        cards_to_bottom = set(
                            await checkbox(
                                "Mulligan",
                                [
                                    {
                                        "name": to_formatted_text(
                                            ANSI(rich_parse(f"\n{card}"))
                                        ),
                                        "value": card.id,
                                    }
                                    for card in cards
                                ],
                                instruction=f"Choose {self.__mulligan_count} cards to place on the bottom of the library.",
                                validate=lambda choices: (
                                    len(choices) == self.__mulligan_count
                                    or f"Choose {self.__mulligan_count}."
                                ),
                            ).ask_async()
                        )
                    else:
                        cards_to_bottom = set()

                    self.__mulligan_count = -1

                    return [
                        MulliganChoice(
                            seq_num=seq_num,
                            keep=True,
                            cards_to_bottom=cards_to_bottom,
                        )
                    ]

        return prompt

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
            with patch_stdout():
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
                                    # validate=lambda choices: (
                                    #     len(choices) == spells[spell][0]
                                    #     or f"Choose {spells[spell][0]} targets."
                                    # ),
                                ).ask_async()
                            )
                        else:
                            targets: set[ID] = set()

                        if isinstance(spell, LandCard):
                            return [PlayLand(seq_num=seq_num, card_id=spell.id)]

                        mana_payment = dict(spell.cast_details().mana_cost)
                        generic_cost = mana_payment.pop(Card.Color.C, 0)

                        for i in range(generic_cost):
                            color = await select(
                                f"Pay generic mana {i + 1}/{generic_cost} with:",
                                [
                                    {"name": "White", "value": Card.Color.W},
                                    {"name": "Blue", "value": Card.Color.U},
                                    {"name": "Black", "value": Card.Color.B},
                                    {"name": "Red", "value": Card.Color.R},
                                    {"name": "Green", "value": Card.Color.G},
                                ],
                            ).ask_async()
                            mana_payment[color] = mana_payment.get(color, 0) + 1

                        return [
                            CastSpell(
                                seq_num=seq_num,
                                card_id=spell.id,
                                targets=targets,
                                mana_payment=mana_payment,
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
                                for index, ability in enumerate(
                                    card.abilities_details()
                                )
                            ],
                        ).ask_async()

                        if abilities[card][ability][1]:
                            targets = set(
                                await checkbox(
                                    "Select target",
                                    list(abilities[card][ability][1]),
                                    instruction=f"Choose {abilities[card][ability][0]} targets.",
                                    # validate=lambda choices: (
                                    #     len(choices) == abilities[card][ability][0]
                                    #     or f"Choose {abilities[card][ability][0]} targets."
                                    # ),
                                ).ask_async()
                            )
                        else:
                            targets: set[ID] = set()

                        mana_payment = dict(card.abilities_details()[ability].mana_cost)
                        generic_cost = mana_payment.pop(Card.Color.C, 0)

                        for i in range(generic_cost):
                            color = await select(
                                f"Pay generic mana {i + 1}/{generic_cost} with:",
                                [
                                    {"name": "White", "value": Card.Color.W},
                                    {"name": "Blue", "value": Card.Color.U},
                                    {"name": "Black", "value": Card.Color.B},
                                    {"name": "Red", "value": Card.Color.R},
                                    {"name": "Green", "value": Card.Color.G},
                                ],
                            ).ask_async()
                            mana_payment[color] = mana_payment.get(color, 0) + 1

                        return [
                            ActivateAbility(
                                seq_num=seq_num,
                                source_id=card.id,
                                ability_index=ability,
                                targets=targets,
                                cost_payment=ActivateAbility.CostPayment(  # type: ignore
                                    tap=bool(
                                        card.abilities_details()[ability].tap_cost
                                    ),
                                    mana=mana_payment,
                                ),
                            )
                        ]
                    case _:
                        return [PriorityPass(seq_num=seq_num)]

        return prompt

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
            with patch_stdout():
                return [
                    DeclareAttackers(
                        seq_num=seq_num,
                        attackers={
                            DeclareAttackers.Attacker(
                                creature_id=attacker, target=opponent_id
                            )
                            for attacker in (
                                await checkbox(
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
                                if attackers
                                else []
                            )
                        },
                    )
                ]

        return prompt

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

            with patch_stdout():
                while blockers:
                    blocker = await select(
                        "Declare blockers",
                        [
                            {
                                "name": to_formatted_text(
                                    ANSI(rich_parse(f"\n{blocker}"))
                                ),
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

    @staticmethod
    def __assign_damage_order(
        seq_num: int, attackers: dict[CreatureCard, set[CreatureCard]] | None = None
    ):
        if attackers is None:
            attackers = {}

        async def prompt():
            damage_orders: list[AssignDamageOrder] = []

            with patch_stdout():
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
                            seq_num=seq_num,
                            attacker_id=attacker.id,
                            blocker_order=blockers,
                        )
                    )

                    del attackers[attacker]

            return damage_orders

        return prompt

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

            with patch_stdout():
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

    @staticmethod
    def __trigger_choice(
        seq_num: int, trigger: tuple[TriggerID, Trigger], targets: set[ID] = set()
    ):
        async def prompt():
            print(trigger[1].trigger_details())

            with patch_stdout():
                if await confirm("Activate trigger?").ask_async():
                    if targets:
                        target = await select(
                            "Select target", list(targets)
                        ).ask_async()
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

            return [
                TriggerChoiceResponse(
                    seq_num=seq_num, trigger_id=trigger[0], accept=False
                )
            ]

        return prompt

    @staticmethod
    def __discard(seq_num: int, hand: set[Card] | None = None):
        if hand is None:
            hand = set()

        async def prompt():
            discard_set: set[CardID] = set()

            with patch_stdout():
                while len(hand) > 7:
                    discard: Card = await select(
                        "Discard",
                        [
                            {
                                "name": to_formatted_text(
                                    ANSI(rich_parse(f"\n{card}"))
                                ),
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
                battlefield = set()

                for card_data in state.battlefield.get(our_id, p.battlefield):
                    card: BattlefieldCard = Card.from_id(card_data.id)(card_data.id)
                    card.tapped = card_data.tapped

                    if isinstance(card, CreatureCard):
                        card.damage = card_data.damage
                        card.power = card_data.power
                        card.toughness = card_data.toughness
                        card.summoning_sick = card_data.summoning_sick

                    battlefield.add(card)

                p.life_total = state.life_totals.get(our_id, p.life_total)
                p.graveyard = {
                    Card.from_id(id)(id)
                    for id in state.graveyard.get(our_id, p.graveyard)
                }
                p.hand = {Card.from_id(id)(id) for id in state.hand.get(our_id, p.hand)}
                p.library_count = state.library_counts.get(our_id, p.library_count)
                p.battlefield = battlefield
            elif isinstance(p, OpponentClientPlayer) and p.id == opponent_id:
                battlefield = set()

                for card_data in state.battlefield.get(opponent_id, p.battlefield):
                    card: BattlefieldCard = Card.from_id(card_data.id)(card_data.id)
                    card.tapped = card_data.tapped

                    if isinstance(card, CreatureCard):
                        card.damage = card_data.damage
                        card.power = card_data.power
                        card.toughness = card_data.toughness
                        card.summoning_sick = card_data.summoning_sick

                    battlefield.add(card)

                p.life_total = state.life_totals.get(opponent_id, p.life_total)
                p.graveyard = {
                    Card.from_id(id)(id)
                    for id in state.graveyard.get(opponent_id, p.graveyard)
                }
                p.hand_count = state.hand_counts.get(opponent_id, p.hand_count)
                p.library_count = state.library_counts.get(opponent_id, p.library_count)
                p.battlefield = battlefield
