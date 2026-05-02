"""gslocal clean — remove temp files, Docker image, build hash."""

from __future__ import annotations

import shutil
import sys

from gslocal.config import find_project_root
from gslocal.docker import image_name, remove_image
from gslocal.ui.log import log_error, log_info, log_warn


def cmd_clean(args) -> None:
    try:
        project_root = find_project_root()
    except FileNotFoundError:
        log_error(
            "No gslocal.toml found in current directory or any parent.\n"
            "Nothing to clean."
        )
        sys.exit(1)

    gslocal_dir = project_root / ".gslocal"

    if not gslocal_dir.exists():
        log_info("No .gslocal/ directory found — nothing to clean.")
        return

    do_all = getattr(args, "all", False)
    do_image = args.image or do_all

    if do_all:
        # Remove entire .gslocal/ directory
        shutil.rmtree(gslocal_dir)
        log_info("Removed .gslocal/ (temp files and build hash).")
    else:
        # Remove only temp/
        temp_dir = gslocal_dir / "temp"
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
            log_info("Removed .gslocal/temp/")
        else:
            log_info("No .gslocal/temp/ to remove.")

    if do_image:
        img_name = image_name(project_root)
        removed = remove_image(img_name)
        if removed:
            log_info(f"Removed Docker image: {img_name}")
        else:
            log_warn(f"Docker image not found: {img_name}")
