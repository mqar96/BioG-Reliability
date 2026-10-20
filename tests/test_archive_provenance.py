"""Archive executions must never claim a parent repository's commit."""

import subprocess

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
