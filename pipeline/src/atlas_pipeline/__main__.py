import argparse
import sys

from .inspect_cli import run


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="atlas_pipeline")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("inspect", help="verify a candidate map (path or http(s) URL)")
    p.add_argument("target")
    args = parser.parse_args(argv)
    if args.command == "inspect":
        return run(args.target)
    return 2


if __name__ == "__main__":
    sys.exit(main())
