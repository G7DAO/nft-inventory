import argparse

from .core import generate_cli as core_generate_cli
from .InventoryFacet import generate_cli as inventory_generate_cli
from .version import VERSION


def generate_cli() -> argparse.ArgumentParser:
    """
    Generates the argument parsers for the game7ctl command-line tool.
    """
    parser = argparse.ArgumentParser(
        description="Development tools for Game7 smart contracts"
    )
    parser.add_argument(
        "-v", "--version", action="version", version=VERSION, help="Print version"
    )
    parser.set_defaults(func=lambda _: parser.print_help())

    subparsers = parser.add_subparsers()

    core_parser = core_generate_cli()
    subparsers.add_parser("core", parents=[core_parser], add_help=False)

    inventory_parser = inventory_generate_cli()
    subparsers.add_parser("inventory", parents=[inventory_parser], add_help=False)

    return parser


def main() -> None:
    """
    Executes the game7ctl command line tool
    """
    parser = generate_cli()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
