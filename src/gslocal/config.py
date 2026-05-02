"""Config loading, validation, project root resolution."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[no-reuse-of-import]

from gslocal.ui.log import log_error

_PLACEHOLDER_RE = re.compile(r"^<.+>$")


@dataclass
class BuildConfig:
    cmd: str
    zip: str
    watch: List[str]


@dataclass
class DockerConfig:
    setup: str
    metadata: Optional[str] = None


@dataclass
class RunConfig:
    timeout: int = 60
    verbose: bool = False


@dataclass
class Config:
    build: BuildConfig
    docker: DockerConfig
    run: RunConfig = field(default_factory=RunConfig)
    project_root: Path = field(default_factory=Path.cwd)


def find_project_root() -> Path:
    for directory in [Path.cwd(), *Path.cwd().parents]:
        if (directory / "gslocal.toml").exists():
            return directory
    raise FileNotFoundError(
        "No gslocal.toml found in current directory or any parent. "
        "Are you inside a gslocal-configured project?"
    )


def load_config(project_root: Path) -> Config:
    toml_path = project_root / "gslocal.toml"
    try:
        with open(toml_path, "rb") as f:
            data = tomllib.load(f)
    except OSError as e:
        log_error(f"Cannot read gslocal.toml: {e}")
        sys.exit(1)
    except tomllib.TOMLDecodeError as e:
        log_error(f"Invalid TOML in {toml_path}: {e}")
        sys.exit(1)

    # Validate required sections/fields
    errors: list[str] = []

    build_data = data.get("build", {})
    for key in ("cmd", "zip", "watch"):
        if key not in build_data:
            errors.append(f"build.{key}")

    docker_data = data.get("docker", {})
    if "setup" not in docker_data:
        errors.append("docker.setup")

    if errors:
        log_error(
            "gslocal.toml is missing required fields:\n"
            + "\n".join(f"  {e}" for e in errors)
        )
        sys.exit(1)

    run_data = data.get("run", {})
    return Config(
        build=BuildConfig(
            cmd=build_data["cmd"],
            zip=build_data["zip"],
            watch=build_data["watch"],
        ),
        docker=DockerConfig(
            setup=docker_data["setup"],
            metadata=docker_data.get("metadata"),
        ),
        run=RunConfig(
            timeout=run_data.get("timeout", 60),
            verbose=run_data.get("verbose", False),
        ),
        project_root=project_root,
    )


def check_placeholders(config: Config) -> None:
    """Abort with an error if any string config value is an unfilled placeholder."""
    offenders: list[str] = []

    checks = [
        ("build.cmd", config.build.cmd),
        ("build.zip", config.build.zip),
        ("docker.setup", config.docker.setup),
    ]
    for key, value in checks:
        if isinstance(value, str) and _PLACEHOLDER_RE.match(value):
            offenders.append(f'  {key} = "{value}"')

    for i, pattern in enumerate(config.build.watch):
        if isinstance(pattern, str) and _PLACEHOLDER_RE.match(pattern):
            offenders.append(f'  build.watch[{i}] = "{pattern}"')

    if offenders:
        log_error(
            "gslocal.toml contains unfilled placeholders:\n"
            + "\n".join(offenders)
            + "\nEdit gslocal.toml or run `gslocal init` to reconfigure."
        )
        sys.exit(1)
