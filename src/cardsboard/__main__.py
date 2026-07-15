import argparse

from os.path import expanduser

import cardsboard.config as config
from cardsboard.cardsboard import TUI


def main():
    """
    Main script entry point.
    """
    parser = argparse.ArgumentParser(
        description="Terminal Kanban board for cards-based project management."
    )

    parser.add_argument(
        "-d",
        "--datadir",
        type=str,
        required=False,
        help="File path to a directory containing the subdirectories with the cards.",
    )

    args = vars(parser.parse_args())
    if args["datadir"] is not None:
        config.DATADIR = expanduser(args["datadir"])

    tui = TUI()
    tui.run()


if __name__ == "__main__":
    main()
