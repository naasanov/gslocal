"""Docker image naming, Dockerfile generation, image build, container run."""

from __future__ import annotations

import hashlib
import importlib.resources
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from gslocal.log import log_error, log_info, log_success

if TYPE_CHECKING:
    from gslocal.config import Config


def image_name(project_root: Path) -> str:
    """Derive a deterministic Docker image name from the project root path."""
    abs_path = str(project_root.resolve())

    raw_slug = project_root.resolve().name.lower()
    slug = re.sub(r"[^a-z0-9._-]", "-", raw_slug)
    slug = slug.strip("-")
    if not slug:
        slug = "autograder"

    path_hash = hashlib.sha256(abs_path.encode()).hexdigest()[:12]
    return f"gslocal-{slug}-{path_hash}"


def generate_dockerfile(config: "Config") -> str:
    """Generate a Dockerfile string from config values."""
    lines = [
        "FROM gradescope/autograder-base:ubuntu-22.04",
        "",
        "RUN mkdir -p /autograder/source /autograder/submission /autograder/results",
        "",
        f"COPY {config.docker.setup} /autograder/source/setup.sh",
        "RUN apt-get update && \\",
        "    bash /autograder/source/setup.sh && \\",
        "    rm -rf /var/lib/apt/lists/*",
        "",
        f"COPY {config.build.zip} /tmp/autograder.zip",
        "RUN unzip -oq /tmp/autograder.zip -d /autograder/source && \\",
        "    rm /tmp/autograder.zip",
        "",
        "RUN cp /autograder/source/run_autograder /autograder/run_autograder && \\",
        "    chmod +x /autograder/run_autograder",
    ]

    if config.docker.metadata:
        lines += [
            "",
            f"COPY {config.docker.metadata} /autograder/submission_metadata.json",
        ]

    lines += [
        "",
        "WORKDIR /autograder",
        "",
        'CMD ["/autograder/run_autograder"]',
    ]

    return "\n".join(lines) + "\n"


def image_exists(name: str) -> bool:
    result = subprocess.run(
        ["docker", "image", "inspect", name],
        capture_output=True,
    )
    return result.returncode == 0


def needs_image_build(
    name: str,
    *,
    force_rebuild: bool,
    build_ran: bool,
) -> bool:
    if force_rebuild:
        return True
    if not image_exists(name):
        return True
    if build_ran:
        return True
    return False


def _stage_default_metadata(gslocal_dir: Path) -> str:
    """Copy the bundled default metadata into .gslocal/ and return its project-relative path."""
    dest = gslocal_dir / "default_submission_metadata.json"
    src = importlib.resources.files("gslocal.data").joinpath("default_submission_metadata.json")
    with importlib.resources.as_file(src) as src_path:
        shutil.copy2(src_path, dest)
    # Return path relative to project root (one level up from .gslocal/)
    return ".gslocal/default_submission_metadata.json"


def build_image(project_root: Path, config: "Config", name: str) -> None:
    """Write a temporary Dockerfile and build the Docker image."""
    gslocal_dir = project_root / ".gslocal"
    gslocal_dir.mkdir(parents=True, exist_ok=True)

    # Resolve metadata path — use bundled default if not configured
    if not config.docker.metadata:
        metadata_path = _stage_default_metadata(gslocal_dir)
        log_info("No metadata configured — using bundled default submission metadata.")
    else:
        metadata_path = config.docker.metadata

    # Temporarily override metadata for Dockerfile generation
    from gslocal.config import DockerConfig
    docker_with_metadata = DockerConfig(setup=config.docker.setup, metadata=metadata_path)

    from dataclasses import replace
    effective_config = replace(config, docker=docker_with_metadata)

    dockerfile_content = generate_dockerfile(effective_config)
    dockerfile_path = gslocal_dir / "Dockerfile"
    dockerfile_path.write_text(dockerfile_content)

    log_info("Building Docker image...")
    result = subprocess.run(
        ["docker", "build", "-t", name, "-f", str(dockerfile_path), str(project_root)],
    )
    if result.returncode != 0:
        log_error("Docker image build failed.")
        sys.exit(1)
    log_success(f"Docker image built: {name}")


def run_container(
    name: str,
    submission_dir: Path,
    results_dir: Path,
    *,
    timeout: int,
    interactive: bool,
) -> bool:
    """
    Run the autograder container.
    Returns True on success, False on failure.
    In interactive mode, drops into a shell and returns True.
    """
    if interactive:
        log_info("Starting interactive container...")
        log_info("Run './run_autograder' to execute the autograder manually")
        subprocess.run(
            [
                "docker", "run", "-it", "--rm",
                "-v", f"{submission_dir}:/autograder/submission:ro",
                "-v", f"{results_dir}:/autograder/results",
                name,
                "/bin/bash",
            ],
        )
        return True

    # Start detached container
    result = subprocess.run(
        [
            "docker", "run", "-d",
            "-v", f"{submission_dir}:/autograder/submission:ro",
            "-v", f"{results_dir}:/autograder/results",
            name,
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        log_error(f"Failed to start container:\n{result.stderr}")
        return False

    container_id = result.stdout.strip()
    log_info("Running autograder...")

    # Poll for completion with timeout
    import time
    elapsed = 0
    try:
        while True:
            inspect = subprocess.run(
                ["docker", "inspect", "-f", "{{.State.Running}}", container_id],
                capture_output=True,
                text=True,
            )
            if inspect.returncode != 0 or inspect.stdout.strip() != "true":
                break

            if elapsed >= timeout:
                subprocess.run(["docker", "kill", container_id], capture_output=True)
                subprocess.run(["docker", "rm", container_id], capture_output=True)
                log_error(
                    f"Autograder timed out after {timeout} seconds.\n"
                    "  To increase the timeout:\n"
                    "    gslocal run -t SECS <submission>"
                )
                return False

            time.sleep(1)
            elapsed += 1
    except KeyboardInterrupt:
        log_info("Interrupted — stopping container...")
        subprocess.run(["docker", "kill", container_id], capture_output=True)
        subprocess.run(["docker", "rm", container_id], capture_output=True)
        sys.exit(130)

    # Show logs
    subprocess.run(["docker", "logs", container_id])

    # Get exit code
    exit_result = subprocess.run(
        ["docker", "inspect", "-f", "{{.State.ExitCode}}", container_id],
        capture_output=True,
        text=True,
    )
    exit_code = int(exit_result.stdout.strip()) if exit_result.returncode == 0 else 1

    subprocess.run(["docker", "rm", container_id], capture_output=True)

    if exit_code != 0:
        log_error(f"Autograder container exited with code {exit_code}")
        return False

    if not (results_dir / "results.json").exists():
        log_error("No results.json generated")
        return False

    log_success("Autograder completed successfully")
    return True


def remove_image(name: str) -> bool:
    """Remove a Docker image. Returns True if removed, False if not found."""
    if not image_exists(name):
        return False
    result = subprocess.run(["docker", "rmi", name], capture_output=True)
    return result.returncode == 0
