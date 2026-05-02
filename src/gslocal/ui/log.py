"""Colored log helpers."""

import sys

from colorama import Fore, Style


def log_info(msg: str) -> None:
    print(f"{Fore.BLUE}[INFO]{Style.RESET_ALL} {msg}")


def log_success(msg: str) -> None:
    print(f"{Fore.GREEN}[SUCCESS]{Style.RESET_ALL} {msg}")


def log_warn(msg: str) -> None:
    print(f"{Fore.YELLOW}[WARN]{Style.RESET_ALL} {msg}")


def log_error(msg: str) -> None:
    print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} {msg}", file=sys.stderr)
