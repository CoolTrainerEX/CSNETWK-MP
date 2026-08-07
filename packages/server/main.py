"""Main server module."""

from argparse import ArgumentParser
import asyncio

from packages.server.connection import ServerConnection
from packages.server.state import ServerGame


def main():
    """Main server function."""
    parser = ArgumentParser(description="CSNETWK-MP Client")

    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose mode")
    asyncio.run(ServerConnection(ServerGame(), parser.parse_args().verbose).run())


if __name__ == "__main__":
    main()
