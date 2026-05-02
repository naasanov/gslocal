"""Simple terminal spinner using a background thread."""

from __future__ import annotations

import itertools
import sys
import threading
import time

from colorama import Fore, Style

_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]


class Spinner:
    """Context manager that shows an animated spinner while work is in progress.

    Disabled automatically when stdout is not a TTY (CI, piped output).
    Pass enabled=False to suppress it unconditionally (verbose mode).
    """

    def __init__(self, message: str, *, enabled: bool = True) -> None:
        self._message = message
        self._enabled = enabled and sys.stdout.isatty()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._spin, daemon=True)

    def _spin(self) -> None:
        for frame in itertools.cycle(_FRAMES):
            if self._stop.is_set():
                break
            sys.stdout.write(f"\r{Fore.BLUE}{frame}{Style.RESET_ALL} {self._message}")
            sys.stdout.flush()
            time.sleep(0.08)

    def __enter__(self) -> "Spinner":
        if self._enabled:
            self._thread.start()
        return self

    def __exit__(self, *_: object) -> None:
        if self._enabled:
            self._stop.set()
            self._thread.join()
            # Clear the spinner line
            sys.stdout.write("\r" + " " * (len(self._message) + 4) + "\r")
            sys.stdout.flush()
