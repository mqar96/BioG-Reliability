"""Inspect every tracked distribution file and export only a reviewed clean Git tree."""

import argparse
import json
import re
import subprocess
import zipfile
from pathlib import Path

from biog_reliability.reporting import sha256

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = {"data", "research", "results", "reports", "presentation", "work", ".venv", ".git"}
PATTERNS = {
    "github_token": r"(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})",
    "aws_key": r"AKIA[0-9A-Z]{16}",
    "private_key": r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
    "slack_token": r"xox[baprs]-[0-9A-Za-z-]{20,}",
    "google_key": r"AIza[0-9A-Za-z_-]{30,}",
    "workstation_path": r"[A-Z]:[\\/](?:Users|Documents)[\\/]",
}


def main(check_only=False):
    paths = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
    records, findings = [], []
    for name in filter(None, paths):
        path = ROOT / name
        if not path.is_file() or path.is_symlink():
            findings.append({"path": name, "reason": "missing file or symbolic link"})
            continue
        if Path(name).parts[0] in FORBIDDEN or any(
            p.endswith(".egg-info") for p in Path(name).parts
        ):
            findings.append({"path": name, "reason": "excluded research/build content"})
        data = path.read_bytes()
        if len(data) > 5_000_000:
            findings.append({"path": name, "reason": "file larger than 5 MB"})
        if path.suffix == ".csv" and not name.startswith("examples/demo/"):
            findings.append({"path": name, "reason": "unreviewed tabular data"})
        if path.suffix == ".png":
            if name != "docs/assets/demo-dashboard.png":
                findings.append({"path": name, "reason": "unreviewed binary"})
            category = "synthetic demo screenshot; no research records"
        else:
            text = data.decode("utf-8-sig")
            for label, pattern in PATTERNS.items():
                if re.search(pattern, text):
                    findings.append({"path": name, "reason": label})
            if re.search(r"(?<![A-Z])[ACGT]{18,}(?![A-Z])", text):
                findings.append({"path": name, "reason": "possible literal biological sequence"})
            category = "original source/test/docs/config or attributed license metadata"
            if name.startswith("examples/demo/"):
                category = "original synthetic software fixture; MIT"
        records.append(
            {"path": name, "bytes": len(data), "sha256": sha256(path), "review_category": category}
        )
    output = ROOT / "work/release"
    output.mkdir(parents=True, exist_ok=True)
    report = {
        "files": records,
        "findings": findings,
        "scope": "Tracked files only; bounded scan plus separate human license review.",
    }
    (output / "file-review.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    if findings:
        raise SystemExit("Distribution review found blockers; see work/release/file-review.json")
    if not check_only:
        if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip():
            raise SystemExit("Commit the reviewed source before exporting")
        archive = output / "BioG-Reliability-v0.1.0-source.zip"
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
            for record in records:
                bundle.write(ROOT / record["path"], record["path"])
        report.update(
            archive_sha256=sha256(archive),
            commit=subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
        )
        (output / "export-receipt.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Reviewed {len(records)} tracked files; {len(findings)} findings")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-only", action="store_true")
    main(parser.parse_args().check_only)
