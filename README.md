# CSNETWK MP

## Demo Link

- https://drive.google.com/file/d/1whb85PdQ-5eQQNUWYEa5QfJHuZKK7wtK/view?usp=sharing

## Build and Run

1. Install [uv](https://docs.astral.sh/uv/).
2. Go to the project directory.
3. `uv sync --all-packages`

### Server

```sh
uv run server
```

### Client

```sh
uv run client
```

## Verbose Mode

### Server

```sh
uv run server -v # or
uv run server --verbose
```

### Client

```sh
uv run client -v # or
uv run client --verbose
```

## Work Distribution

| Task/Feature                                              | Justin Ryan Uy | Adrian Nathaniel Co | Jayhan Charlizze Esparas | Ethan Jude Reyes |
| --------------------------------------------------------- | -------------- | ------------------- | ------------------------ | ---------------- |
| TCP Server: connection handling, framing, dispatch        | ✅             | ✅                  | ✅                       | ✅               |
| Game lifecycle: LOBBY, GAME_SETUP, MULLIGAN logic         | ✅             | ✅                  | ✅                       | ✅               |
| Turn & phase engine (all phases/steps, transitions)       | ✅             | ✅                  | ✅                       | ✅               |
| Priority & Stack logic, spell/ability resolution          | ✅             | ✅                  | ✅                       | ✅               |
| Combat system (attackers, blockers, damage)               | ✅             | ✅                  | ✅                       | ✅               |
| Client implementation & state rendering                   | ✅             | ✅                  | ✅                       | ✅               |
| PDU serialisation/deserialisation (all 25 PDU types)      | ✅             | ✅                  | ✅                       | ✅               |
| Error handling, PING/PONG heartbeat, disconnect logic     | ✅             | ✅                  | ✅                       | ✅               |
| Verbose mode (client + server PDU logging, toggle on/off) | ✅             | ✅                  | ✅                       | ✅               |
| Testing & interoperability                                | ✅             | ✅                  | ✅                       | ✅               |
| README / documentation / AI disclosure                    | ✅             | ✅                  | ✅                       | ✅               |

## AI Usage

- NotebookLM was used to understand the game rules and flow.
- Used Google AI Studio as an additional reference to get ideas when figuring out and understanding the logic.
- Gemini AI was used to verify consistency and documentation (comments). Also, used to help identifying certain logic in code-writing.

## Libraries

- Rich – terminal coloring/UI (both client & server)
- Pydantic – PDU validation and serialization
- Prompt-toolkit – CLI interaction framework
- Questionary – dropdown/checkbox prompts for game actions

| Library                                                       | Version Requirement | Purpose                                                 |
| :------------------------------------------------------------ | :------------------ | :------------------------------------------------------ |
| **[Rich](https://rich.readthedocs.io/)**                      | `>= 15.0.0`         | Terminal coloring/UI (both client & server)             |
| **[Pydantic](https://pydantic-docs.helpmanual.io/)**          | `>= 2.13.4`         | PDU validation and serialization.                       |
| **[Prompt Toolkit](https://docs.python-prompt-toolkit.org/)** | `>= 3.0.53`         | Prevents terminal display corruption during user input. |
| **[Questionary](https://questionary.readthedocs.io/)**        | `>= 2.1.1`          | Dropdown/checkbox prompts for game actions              |

## Implemented Card Abilities and Effects

- Deal damage to target(s) (e.g., Lightning Bolt 3 damage, Shock 2 damage, Lava Spike 3 damage)
- Destroy target creature/artifact (e.g., Terror, Doom Blade, Naturalize)
- Exile target creature (e.g., Swords to Plowshares, Path to Exile, Graveyard Return)
- Draw cards (e.g., Ponder, Merfolk Looter)
- Discard cards (e.g., Mind Rot)
- Mill cards (e.g., Millstone)
- Gain life (e.g., Healing Salve, Gray Merchant of Asphodel)
- Counter target spell (e.g., Counterspell, Cancel, Negate, Mana Leak)
- Return target creature to hand (e.g., Raise Dead, Gravedigger)
- Pump power/toughness (e.g., Giant Growth +3/+3, Vines of Vastwood +4/+4)
- Search library (e.g., Rampant Growth, Path to Exile)
- Special triggered abilities (e.g., Goblin Guide reveal land on attack, Monastery Swiftspear prowess, White/Black Knight protection, Gravekeeper's Discipline
- First Strike (White Knight, Black Knight)
- Flying (Air Elemental, Serra Angel)
- Hexproof (Troll Ascetic)
- Defender (Wall of Stone)
- Haste (Goblin Guide, Monastery Swiftspear
- Trample (Reckless Wurm)
- Madness (Reckless Wurm discard for reduce
- Cast details text defines the effect (e.g., "Deal 3 damage to target", "Exile target creature", "Put top 2 cards of library into hand")

## Limitations and Deviations

None as of the current version of this application.
