"""Main client module."""

from packages.client.connection import connect
from packages.client.state import run


def main():
    """Main client function."""
    connect(run)


if __name__ == "__main__":
    main()
