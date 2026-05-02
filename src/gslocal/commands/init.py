"""gslocal init — interactive config generation."""

from __future__ import annotations

import sys
from pathlib import Path

from gslocal.log import log_error, log_info, log_success

_PLACEHOLDERS = {
    "build.cmd": "<your-build-command>",
    "build.zip": "<glob/to/*.zip>",
    "build.watch": "<glob/to/watch>",
    "docker.setup": "<path/to/setup.sh>",
}


def _prompt(msg: str, hint: str = "") -> str:
    """Prompt the user with an optional hint on its own line; return stripped input."""
    if hint:
        print(f"  {hint}")
    try:
        return input(f"{msg}: ").strip()
    except EOFError:
        return ""


def _write_toml(
    dest: Path,
    cmd: str,
    zip_: str,
    watch: list[str],
    setup: str,
    timeout: int,
) -> None:
    watch_toml = "[" + ", ".join(f'"{w}"' for w in watch) + "]"
    content = (
        "[build]\n"
        f'cmd = "{cmd}"\n'
        f'zip = "{zip_}"\n'
        f"watch = {watch_toml}\n"
        "\n"
        "[docker]\n"
        f'setup = "{setup}"\n'
        "\n"
        "[run]\n"
        f"timeout = {timeout}\n"
    )
    dest.write_text(content)


def cmd_init(args) -> None:
    target = Path.cwd() / "gslocal.toml"

    if target.exists():
        log_error(
            "gslocal.toml already exists in this directory.\n"
            "Delete it manually before running `gslocal init` again."
        )
        sys.exit(1)

    if args.placeholders:
        _write_toml(
            target,
            cmd=_PLACEHOLDERS["build.cmd"],
            zip_=_PLACEHOLDERS["build.zip"],
            watch=[_PLACEHOLDERS["build.watch"]],
            setup=_PLACEHOLDERS["docker.setup"],
            timeout=60,
        )
        log_success("gslocal.toml written with placeholder values. Edit it before running.")
        return

    # Interactive mode
    print()
    print("Setting up gslocal for this project.")
    print("Required fields will use a placeholder if skipped.")
    print()

    cmd = _prompt('Build command', 'e.g. "mvn clean package"')
    if not cmd:
        cmd = _PLACEHOLDERS["build.cmd"]

    zip_ = _prompt('Zip output', 'e.g. "target/*.zip"')
    if not zip_:
        zip_ = _PLACEHOLDERS["build.zip"]

    watch_raw = _prompt('Watch patterns, comma-separated', 'e.g. "src/**/*,pom.xml"')
    if watch_raw:
        watch = [w.strip() for w in watch_raw.split(",") if w.strip()]
    else:
        watch = [_PLACEHOLDERS["build.watch"]]

    setup = _prompt('Path to setup.sh', 'e.g. "src/main/resources/setup.sh"')
    if not setup:
        setup = _PLACEHOLDERS["docker.setup"]

    timeout_raw = _prompt("Autograder timeout in seconds [60]")
    try:
        timeout = int(timeout_raw) if timeout_raw else 60
    except ValueError:
        log_error(f"Invalid timeout value: {timeout_raw!r}. Using 60.")
        timeout = 60

    print()
    print(
        "[INFO] To use mock submission metadata, add to gslocal.toml:\n"
        "         [docker]\n"
        "         metadata = \"path/to/mock_submission_metadata.json\""
    )
    print()

    # .gitignore prompt
    gi_answer = _prompt("Add .gslocal/ to .gitignore? [Y/n]")
    if gi_answer.lower() not in ("n", "no"):
        gitignore = Path.cwd() / ".gitignore"
        if gitignore.exists():
            content = gitignore.read_text()
            if ".gslocal/" not in content:
                gitignore.write_text(content.rstrip("\n") + "\n.gslocal/\n")
            log_success("Added .gslocal/ to .gitignore")
        else:
            log_info("No .gitignore found — skipping (create one and add .gslocal/ manually)")

    _write_toml(target, cmd=cmd, zip_=zip_, watch=watch, setup=setup, timeout=timeout)
    log_success("gslocal is ready. Run `gslocal run <submission>` to test a submission.")
