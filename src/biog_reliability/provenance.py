"""Source snapshots bind tests and experiments to executable inputs, even on dirty trees."""

import importlib.metadata
import platform
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from .reporting import sha256, write_json


def source_snapshot(root):
    root = Path(root)
    paths = [root / n for n in ("app.py", "pyproject.toml", "requirements.lock")]
    for folder in ("src", "scripts", "tests"):
        paths.extend((root / folder).rglob("*.py"))
        paths.extend((root / folder).glob("*.ps1"))
    return {p.relative_to(root).as_posix(): sha256(p) for p in sorted(paths) if p.is_file()}


def run_context(root):
    root = Path(root).resolve()
    commit = None
    try:
        top = subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        if Path(top).resolve() == root:
            commit = subprocess.check_output(
                ["git", "-C", str(root), "rev-parse", "HEAD"],
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
    except (OSError, subprocess.CalledProcessError):
        # Source ZIPs have no Git metadata. Never inherit an unrelated parent checkout.
        pass
    return {
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "git_commit": commit,
        "source_sha256": source_snapshot(root),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "dependencies": {d.metadata["Name"]: d.version for d in importlib.metadata.distributions()},
    }


def seal_directory(directory, metadata):
    directory = Path(directory)
    files = {
        p.relative_to(directory).as_posix(): sha256(p)
        for p in sorted(directory.rglob("*"))
        if p.is_file() and p.name != "manifest.json"
    }
    write_json(directory / "manifest.json", {"metadata": metadata, "files_sha256": files})
