"""Submission preparation: zip extraction, dir copy, git clone."""

from __future__ import annotations

import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

from gslocal.log import log_error, log_info


def detect_submission_type(submission: str) -> str:
    """Return 'github', 'zip', 'directory', or 'unknown'."""
    if submission.startswith("git@github.com:") or submission.startswith("https://github.com"):
        return "github"
    p = Path(submission)
    if p.is_file() and submission.endswith(".zip"):
        return "zip"
    if p.is_dir():
        return "directory"
    return "unknown"


def prepare_submission(submission: str, dest: Path) -> None:
    """Dispatch to the appropriate preparation function."""
    sub_type = detect_submission_type(submission)
    log_info(f"Detected submission type: {sub_type}")

    if sub_type == "github":
        _from_github(submission, dest)
    elif sub_type == "zip":
        _from_zip(submission, dest)
    elif sub_type == "directory":
        _from_directory(submission, dest)
    else:
        log_error(
            f"Unknown submission type: {submission}\n"
            "Must be a .zip file, directory, or GitHub URL."
        )
        sys.exit(1)


def _from_zip(zip_path: str, dest: Path) -> None:
    log_info(f"Extracting zip: {zip_path}")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(dest)


def _from_directory(dir_path: str, dest: Path) -> None:
    log_info(f"Copying from directory: {dir_path}")
    src = Path(dir_path)
    for item in src.iterdir():
        target = dest / item.name
        if item.is_dir():
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)


def _from_github(url: str, dest: Path) -> None:
    log_info(f"Cloning from GitHub: {url}")
    result = subprocess.run(
        ["git", "clone", "--depth", "1", url, str(dest)],
        capture_output=True,
    )
    if result.returncode != 0:
        log_error(f"Failed to clone repository: {url}\n{result.stderr.decode()}")
        sys.exit(1)
    # Strip .git directory
    git_dir = dest / ".git"
    if git_dir.exists():
        shutil.rmtree(git_dir)
