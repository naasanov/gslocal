"""CLI entry point — argparse subcommand dispatch."""

import argparse
import sys
from importlib.metadata import PackageNotFoundError, version

import colorama


def _get_version() -> str:
    try:
        return version("gslocal")
    except PackageNotFoundError:
        return "0.0.0-dev"


def main() -> None:
    colorama.init()

    parser = argparse.ArgumentParser(
        prog="gslocal",
        description="Local Gradescope autograder runner.",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"gslocal {_get_version()}",
    )

    subparsers = parser.add_subparsers(dest="subcommand")

    # --- run subcommand ---
    run_parser = subparsers.add_parser(
        "run",
        help="Run the autograder against a submission (default subcommand)",
    )
    run_parser.add_argument("submission", help="Zip file, directory, or GitHub URL")
    run_parser.add_argument(
        "-r",
        "--rebuild",
        action="store_true",
        help="Force rebuild of build command and Docker image",
    )
    run_parser.add_argument(
        "-n",
        "--no-build",
        action="store_true",
        help="Skip build command entirely, use existing zip",
    )
    run_parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="Drop into container shell instead of running autograder",
    )
    run_parser.add_argument(
        "-c", "--clean", action="store_true", help="Delete temp files after run"
    )
    run_parser.add_argument(
        "-t",
        "--timeout",
        type=int,
        metavar="SECS",
        help="Autograder timeout in seconds (default: 60)",
    )
    run_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show full build output instead of a spinner",
    )

    # --- init subcommand ---
    init_parser = subparsers.add_parser(
        "init",
        help="Generate a gslocal.toml in the current directory",
    )
    init_parser.add_argument(
        "--placeholders",
        action="store_true",
        help="Write config with all sentinel values, no prompts",
    )

    # --- clean subcommand ---
    clean_parser = subparsers.add_parser(
        "clean",
        help="Clean up local gslocal state",
    )
    clean_parser.add_argument(
        "--image",
        action="store_true",
        help="Also remove the Docker image for this project",
    )
    clean_parser.add_argument(
        "--all",
        action="store_true",
        help="Remove temp files, Docker image, and build hash (full reset)",
    )

    args = parser.parse_args()

    if args.subcommand is None:
        parser.print_help()
        sys.exit(0)

    try:
        if args.subcommand == "run":
            from gslocal.commands.run import cmd_run

            cmd_run(args)
        elif args.subcommand == "init":
            from gslocal.commands.init import cmd_init

            cmd_init(args)
        elif args.subcommand == "clean":
            from gslocal.commands.clean import cmd_clean

            cmd_clean(args)
    except KeyboardInterrupt:
        sys.exit(130)
