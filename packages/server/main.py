"""Main server module."""

from argparse import ArgumentParser

from packages.server.connection import connect
from packages.server.state import run


def main():
    """Main server function."""
    parser = ArgumentParser(description="CSNETWK-MP Client")

    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose mode")
    connect(run, parser.parse_args().verbose)


if __name__ == "__main__":
    main()
