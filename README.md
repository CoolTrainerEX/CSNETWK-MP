# CSNETWK MP

## Build and Run

1. Install [uv](https://docs.astral.sh/uv/).
2. Go to the project directory.

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

## Limitations and Deviations

TODO
