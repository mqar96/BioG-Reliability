"""Archive executions must never claim a parent repository's commit."""

import hashlib
import importlib.util
import json
import subprocess
import sys
import zipfile
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


def test_release_export_uses_committed_bytes(tmp_path, monkeypatch):
    """Git newline conversion must not change a source archive's committed bytes."""

    def git(*args):
        return subprocess.run(["git", "-C", str(tmp_path), *args], check=True, capture_output=True)

    git("init")
    git("config", "core.autocrlf", "true")
    (tmp_path / ".gitattributes").write_bytes(b"README.md text eol=crlf\n")
    (tmp_path / "README.md").write_bytes(b"fixture\n")
    git("add", ".gitattributes", "README.md")
    git(
        "-c",
        "user.name=Fixture",
        "-c",
        "user.email=fixture@example.invalid",
        "commit",
        "-m",
        "Fixture",
    )
    (tmp_path / "README.md").write_bytes(b"fixture\r\n")
    git("add", "README.md")
    assert not git("status", "--porcelain").stdout.strip()
    source = Path(__file__).resolve().parents[1] / "scripts/check_release.py"
    spec = importlib.util.spec_from_file_location("release_export_fixture", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "ROOT", tmp_path)
    module.main()
    output = tmp_path / "work/release"
    with zipfile.ZipFile(output / "BioG-Reliability-v0.1.0-source.zip") as archive:
        assert archive.read("README.md") == b"fixture\n"
    receipt = json.loads((output / "export-receipt.json").read_text())
    record = next(f for f in receipt["files"] if f["path"] == "README.md")
    assert record["sha256"] == hashlib.sha256(b"fixture\n").hexdigest()
