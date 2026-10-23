import argparse
import sys
from pathlib import Path

from . import build as build_mod
from .inspect_cli import run


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="atlas_pipeline")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("inspect", help="verify a candidate map (path or http(s) URL)")
    p.add_argument("target")
    b = sub.add_parser("build", help="fetch, verify and write the site data files")
    b.add_argument("--deploy", action="store_true", help="also fail on TODO text and unreviewed lessons")
    b.add_argument("--out", type=Path, default=build_mod.DEFAULT_OUT)
    b.add_argument("--cache", type=Path, default=build_mod.DEFAULT_CACHE)
    b.add_argument("--sources", type=Path, default=build_mod.DEFAULT_SOURCES)
    b.add_argument("--lessons", type=Path, default=build_mod.DEFAULT_LESSONS)
    args = parser.parse_args(argv)
    if args.command == "inspect":
        return run(args.target)
    if args.command == "build":
        return build_mod.run(args.deploy, args.out, args.cache, args.sources, args.lessons)
    return 2


if __name__ == "__main__":
    sys.exit(main())
