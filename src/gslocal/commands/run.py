"""Run orchestration: dependency checks → config → submission → build → docker → results."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

from gslocal.log import log_error, log_info


def _check_dependencies() -> None:
    """Verify docker and git are installed and Docker daemon is running."""
    if shutil.which("docker") is None:
        log_error(
            "Docker is not installed or not in PATH.\n"
            "Please install Docker: https://docs.docker.com/get-docker/"
        )
        sys.exit(1)

    result = subprocess.run(
        ["docker", "info"],
        capture_output=True,
    )
    if result.returncode != 0:
        log_error(
            "Docker daemon is not running.\n"
            "Please start Docker and try again."
        )
        sys.exit(1)

    if shutil.which("git") is None:
        log_error(
            "Git is not installed or not in PATH.\n"
            "Please install Git: https://git-scm.com/downloads"
        )
        sys.exit(1)


def _resolve_timeout(args_timeout: int | None, config_timeout: int) -> int:
    """Resolve timeout from CLI flag > env var > config value > default."""
    if args_timeout is not None:
        return args_timeout
    env = os.environ.get("GSLOCAL_TIMEOUT")
    if env is not None:
        try:
            return int(env)
        except ValueError:
            log_error(f"GSLOCAL_TIMEOUT is not a valid integer: {env!r}")
            sys.exit(1)
    return config_timeout


def cmd_run(args) -> None:
    from gslocal.config import find_project_root, load_config, check_placeholders
    from gslocal.build import needs_build, run_build, check_no_build_zip, get_zip_path
    from gslocal.submission import prepare_submission, detect_submission_type
    from gslocal.docker import image_name, needs_image_build, build_image, run_container
    from gslocal.results import format_results

    _check_dependencies()

    # Locate project root and load config
    try:
        project_root = find_project_root()
    except FileNotFoundError:
        log_error(
            "No gslocal.toml found in current directory or any parent.\n"
            "Run `gslocal init` to set up gslocal in this project.\n"
            "To quickly scaffold a config for manual editing, run `gslocal init --placeholders`"
        )
        sys.exit(1)

    config = load_config(project_root)
    check_placeholders(config)

    # Resolve submission path (make absolute if it's a local path)
    submission = args.submission
    if not (submission.startswith("git@") or submission.startswith("https://")):
        sub_path = Path(submission)
        if not sub_path.is_absolute():
            submission = str(Path.cwd() / sub_path)

    sub_type = detect_submission_type(submission)
    if sub_type == "unknown":
        log_error(
            f"Unknown submission type: {submission}\n"
            "Must be a .zip file, directory, or GitHub URL."
        )
        sys.exit(1)

    # Prepare temp directories
    temp_base = project_root / ".gslocal" / "temp"
    submission_dir = temp_base / "submission"
    results_dir = temp_base / "results"
    autograder_dir = temp_base / "autograder"

    # Clean old temp state
    if temp_base.exists():
        shutil.rmtree(temp_base)
    submission_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)
    autograder_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Prepare submission
        prepare_submission(submission, submission_dir)

        # Build autograder
        do_build = needs_build(
            project_root,
            config,
            force_rebuild=args.rebuild,
            no_build=args.no_build,
        )

        if args.no_build:
            log_info("Skipping build (--no-build)")
            zip_path = check_no_build_zip(project_root, config.build.zip)
        elif do_build:
            run_build(project_root, config)
            zip_path = get_zip_path(project_root, config.build.zip)
        else:
            log_info("Source unchanged, skipping build.")
            zip_path = get_zip_path(project_root, config.build.zip)

        # Extract autograder zip for inspection
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(autograder_dir)
        log_info(f"Autograder extracted to: {autograder_dir}")

        # Docker image
        img_name = image_name(project_root)
        log_info(f"Docker image name: {img_name}")

        if needs_image_build(img_name, force_rebuild=args.rebuild, build_ran=do_build):
            build_image(project_root, config, img_name)
        else:
            log_info(f"Using existing Docker image: {img_name}")

        # Resolve timeout
        timeout = _resolve_timeout(args.timeout, config.run.timeout)

        # Run autograder
        success = run_container(
            img_name,
            submission_dir,
            results_dir,
            timeout=timeout,
            interactive=args.interactive,
        )

        # Print results if available
        results_json = results_dir / "results.json"
        if results_json.exists():
            format_results(results_json)
            log_info(f"Raw JSON: {results_json}")

        if not success:
            sys.exit(1)

    finally:
        if args.clean and temp_base.exists():
            shutil.rmtree(temp_base)
            log_info("Temp files cleaned up.")
