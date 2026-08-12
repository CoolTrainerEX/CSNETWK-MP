# CSNETWK MP

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

## Limitations and Deviations

None as of the current version of this application.
