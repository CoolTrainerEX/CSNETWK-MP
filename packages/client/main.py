"""Main client module."""

from argparse import ArgumentParser
import asyncio

from packages.client.connection import connect


def main():
    """Main client function."""
    parser = ArgumentParser(description="CSNETWK-MP Client")

    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose mode")
    asyncio.run(connect(parser.parse_args().verbose))


if __name__ == "__main__":
    main()
