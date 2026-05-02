"""Terminal formatting of results.json."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from colorama import Fore, Style

from gslocal.log import log_error, log_warn


def format_results(results_file: Path) -> None:
    try:
        with open(results_file, "r") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        log_error(f"Failed to parse results: {e}")
        sys.exit(1)

    tests = data.get("tests", [])
    if not tests:
        log_warn("No tests found in results")
        return

    print()

    total_score = 0.0
    total_max = 0.0
    passed = 0
    failed = 0

    for test in tests:
        score = test.get("score", 0)
        max_score = test.get("max_score", 0)
        name = test.get("name", "Unknown")
        status = test.get("status", "")
        output = test.get("output", "") or ""

        total_score += score
        total_max += max_score

        is_failed = status == "failed" or score < max_score
        score_str = f"{score}/{max_score}".ljust(12)

        if is_failed:
            failed += 1
            print(f"  {Fore.RED}FAIL{Style.RESET_ALL}  {score_str}  {name}")
            if output:
                reason = output.replace("FAILED/ABORTED:: ", "").strip()
                print(f"                      {Fore.YELLOW}-> {reason}{Style.RESET_ALL}")
        else:
            passed += 1
            print(f"  {Fore.GREEN}PASS{Style.RESET_ALL}  {score_str}  {name}")

    print()
    print("=" * 60)
    summary = f"  {Fore.BLUE}Score:{Style.RESET_ALL} {total_score:.2f} / {total_max:.2f}"
    if failed > 0:
        summary += (
            f"  ({Fore.GREEN}{passed} passed{Style.RESET_ALL}, "
            f"{Fore.RED}{failed} failed{Style.RESET_ALL})"
        )
    else:
        summary += f"  ({Fore.GREEN}{passed} passed{Style.RESET_ALL})"
    print(summary)
    print("=" * 60)
