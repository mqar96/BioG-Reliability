"""Fetch only the pinned public inputs, with integrity and extraction checks."""

import argparse
import hashlib
import json
import subprocess
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import requests

from biog_reliability.benchmark import UPSTREAM_COMMIT
from biog_reliability.reporting import sha256, write_json

ROOT = Path(__file__).resolve().parents[1]
MD5 = "611cb28ab0516e471c5dc59ea44a330a"
SHA256 = "42c1b1c71c77494b3ab3a4cf5a3e54c500bf2eb2985a53c76a41dc08c3e6cda9"
URL = "https://zenodo.org/api/records/20627722/files/offtarget_prediction_benchmark_zenodo_artifacts_v1.zip/content"


def main():
    upstream = ROOT / "research/upstream"
    upstream.parent.mkdir(parents=True, exist_ok=True)
    if not upstream.exists():
        subprocess.run(
            [
                "git",
                "clone",
                "https://github.com/maren-ha/OffTargetPredictionBenchmark.git",
                str(upstream),
            ],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(upstream), "checkout", "--detach", UPSTREAM_COMMIT], check=True
        )
    head = subprocess.check_output(
        ["git", "-C", str(upstream), "rev-parse", "HEAD"], text=True
    ).strip()
    if head != UPSTREAM_COMMIT:
        raise ValueError("Existing reference checkout differs from pinned version; not modified")
    metadata = requests.get("https://zenodo.org/api/records/20627722", timeout=60)
    metadata.raise_for_status()
    record = metadata.json()
    if record["metadata"]["license"]["id"] != "cc-by-4.0":
        raise ValueError("Unexpected data license; review before download")
    write_json(ROOT / "research/zenodo_record.json", record)
    raw = ROOT / "data/raw"
    raw.mkdir(parents=True, exist_ok=True)
    archive = raw / "zenodo_artifacts.zip"
    if not archive.exists():
        partial = raw / "zenodo_artifacts.zip.partial"
        with requests.get(URL, stream=True, timeout=(30, 180)) as response:
            response.raise_for_status()
            with partial.open("wb") as stream:
                for chunk in response.iter_content(1024 * 1024):
                    stream.write(chunk)
        partial.replace(archive)
    digest = hashlib.file_digest(archive.open("rb"), "md5").hexdigest()
    if digest != MD5 or sha256(archive) != SHA256:
        raise ValueError("Archive checksum mismatch")
    destination = (raw / "zenodo").resolve()
    destination.mkdir(exist_ok=True)
    with zipfile.ZipFile(archive) as bundle:
        for member in bundle.infolist():
            if not (destination / member.filename).resolve().is_relative_to(destination):
                raise ValueError("Unsafe archive path")
        bundle.extractall(destination)
    write_json(
        ROOT / "research/download_manifest.json",
        {
            "url": URL,
            "md5": digest,
            "sha256": sha256(archive),
            "upstream_commit": head,
            "license": "CC-BY-4.0",
            "retrieved_date": datetime.now(UTC).isoformat(),
        },
    )
    print(json.dumps({"archive": str(archive), "sha256": sha256(archive)}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--acknowledge-data-terms", action="store_true")
    args = parser.parse_args()
    if not args.acknowledge_data_terms:
        parser.error(
            "Review docs/data-provenance.md and obtain applicable data rights. "
            "Then pass --acknowledge-data-terms. No data downloaded."
        )
    main()
