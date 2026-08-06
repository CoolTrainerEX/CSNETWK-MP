"""Main server module."""

from packages.server.connection import connect
from packages.server.state import run


def main():
    """Main server function."""
    connect(run)


if __name__ == "__main__":
    main()
