import argparse

from .version import VERSION


def generate_cli() -> argparse.ArgumentParser:
    """
    Generates the argument parsers for the game7dev command-line tool.
    """
    parser = argparse.ArgumentParser(
        description="Development tools for Game7 smart contracts"
    )
    parser.add_argument(
        "-v", "--version", action="version", version=VERSION, help="Print version"
    )
    parser.set_defaults(func=lambda _: parser.print_help())

    return parser


def main() -> None:
    """
    Executes the game7dev command line tool
    """
    parser = generate_cli()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
