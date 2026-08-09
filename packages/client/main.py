"""Main client module."""

from argparse import ArgumentParser
import asyncio
from packages.client.connection import ClientConnection
from packages.client.game import ClientGame


def main():
    """Main client function."""
    try:
        parser = ArgumentParser(description="CSNETWK-MP Client")
        game = ClientGame()

        parser.add_argument("-v", "--verbose", action="store_true", help="Verbose mode")
        asyncio.run(ClientConnection(game, parser.parse_args().verbose).connect())
    except KeyboardInterrupt:
        game.concede()


if __name__ == "__main__":
    main()
