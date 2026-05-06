"""Command-line interface for envpatch."""

import argparse
import sys

from envpatch.parser import parse
from envpatch.differ import diff
from envpatch.merger import merge
from envpatch.formatter import format_diff, format_merge_result
from envpatch.writer import write_env


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envpatch",
        description="Diff and safely merge .env files across environments.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    diff_cmd = sub.add_parser("diff", help="Show differences between two .env files.")
    diff_cmd.add_argument("base", help="Base .env file")
    diff_cmd.add_argument("target", help="Target .env file")
    diff_cmd.add_argument("--no-color", action="store_true", help="Disable color output")

    merge_cmd = sub.add_parser("merge", help="Merge target .env into base .env.")
    merge_cmd.add_argument("base", help="Base .env file")
    merge_cmd.add_argument("target", help="Target .env file")
    merge_cmd.add_argument("-o", "--output", help="Output file (default: stdout)")
    merge_cmd.add_argument("--overwrite", action="store_true", help="Overwrite modified keys without conflict")
    merge_cmd.add_argument("--no-color", action="store_true", help="Disable color output")

    return parser


def main(argv=None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    use_color = not getattr(args, "no_color", False)

    if args.command == "diff":
        base_env = parse(open(args.base).read())
        target_env = parse(open(args.target).read())
        result = diff(base_env, target_env)
        print(format_diff(result, use_color=use_color))
        return 0 if not result.has_changes() else 1

    if args.command == "merge":
        base_env = parse(open(args.base).read())
        target_env = parse(open(args.target).read())
        diff_result = diff(base_env, target_env)
        merge_result = merge(diff_result, base_env, overwrite=args.overwrite)
        if args.output:
            write_env(merge_result, args.output, include_conflicts=True)
            if merge_result.conflicts:
                print(format_merge_result(merge_result, use_color=use_color), file=sys.stderr)
        else:
            print(format_merge_result(merge_result, use_color=use_color))
        return 1 if merge_result.has_conflicts() else 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
