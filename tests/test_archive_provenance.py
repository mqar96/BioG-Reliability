"""Archive executions must never claim a parent repository's commit."""

import subprocess
import sys
from pathlib import Path

from biog_reliability.provenance import run_context


def test_archive_does_not_inherit_parent_git(tmp_path):
    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    (tmp_path / "unrelated.txt").write_text("unrelated", encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp_path), "add", "."], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(tmp_path),
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "commit",
            "-m",
            "Unrelated fixture",
        ],
        check=True,
        capture_output=True,
    )
    child = tmp_path / "archive"
    child.mkdir()
    (child / "app.py").write_text("original source", encoding="utf-8")
    context = run_context(child)
    assert context["git_commit"] is None
    assert "app.py" in context["source_sha256"]


def test_archive_without_git_metadata_records_source(tmp_path):
    (tmp_path / "app.py").write_text("source", encoding="utf-8")
    context = run_context(tmp_path)
    assert context["git_commit"] is None
    assert context["python"] and context["source_sha256"]


def test_release_export_rejects_parent_checkout(tmp_path):
    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    source = Path(__file__).resolve().parents[1] / "scripts/check_release.py"
    script = tmp_path / "archive/scripts/check_release.py"
    script.parent.mkdir(parents=True)
    script.write_bytes(source.read_bytes())
    result = subprocess.run(
        [sys.executable, str(script), "--check-only"],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "own project-root Git repository" in result.stderr
    assert not (tmp_path / "archive/work/release").exists()
