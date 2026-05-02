"""Build command invocation and hash-based caching."""

from __future__ import annotations

import glob
import hashlib
import shlex
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from gslocal.log import log_error, log_info, log_success

if TYPE_CHECKING:
    from gslocal.config import Config

BUILD_HASH_FILE = ".build_hash"


def _compute_source_hash(project_root: Path, watch_patterns: list[str]) -> str:
    """SHA-256 over sorted contents of all files matched by watch patterns."""
    files: list[Path] = []
    for pattern in watch_patterns:
        matched = glob.glob(str(project_root / pattern), recursive=True)
        for m in matched:
            p = Path(m)
            if p.is_file():
                files.append(p)

    files = sorted(set(files))

    h = hashlib.sha256()
    for f in files:
        try:
            h.update(f.read_bytes())
        except OSError:
            pass
    return h.hexdigest()


def _find_zip(project_root: Path, zip_pattern: str) -> Path | None:
    """Return the first file matching the zip glob pattern, or None."""
    matches = glob.glob(str(project_root / zip_pattern), recursive=True)
    if matches:
        return Path(matches[0])
    return None


def needs_build(
    project_root: Path,
    config: "Config",
    *,
    force_rebuild: bool,
    no_build: bool,
) -> bool:
    """Return True if the build command should be executed."""
    if no_build:
        return False
    if force_rebuild:
        return True

    # No zip → must build
    if _find_zip(project_root, config.build.zip) is None:
        return True

    hash_file = project_root / ".gslocal" / BUILD_HASH_FILE
    if not hash_file.exists():
        return True

    current = _compute_source_hash(project_root, config.build.watch)
    stored = hash_file.read_text().strip()
    return current != stored


def run_build(project_root: Path, config: "Config") -> None:
    """Invoke the build command. Exits on failure."""
    log_info(f"Building autograder: {config.build.cmd}")

    cmd = shlex.split(config.build.cmd)
    result = subprocess.run(cmd, cwd=project_root)

    if result.returncode != 0:
        log_error("Build command failed.")
        sys.exit(1)

    log_success("Autograder built successfully.")

    # Store hash after successful build
    new_hash = _compute_source_hash(project_root, config.build.watch)
    hash_file = project_root / ".gslocal" / BUILD_HASH_FILE
    hash_file.parent.mkdir(parents=True, exist_ok=True)
    hash_file.write_text(new_hash)


def check_no_build_zip(project_root: Path, zip_pattern: str) -> Path:
    """Return zip path when --no-build is set; exit with error if not found."""
    zip_path = _find_zip(project_root, zip_pattern)
    if zip_path is None:
        log_error(
            f"--no-build specified but no zip found matching: {zip_pattern}\n"
            "Run without --no-build to build first."
        )
        sys.exit(1)
    return zip_path


def get_zip_path(project_root: Path, zip_pattern: str) -> Path:
    """Return zip path; exit with error if not found."""
    zip_path = _find_zip(project_root, zip_pattern)
    if zip_path is None:
        log_error(f"No zip found matching: {zip_pattern}")
        sys.exit(1)
    return zip_path
