"""Download pinned external observations and training inventories without redistributing them."""

import argparse
import json
from pathlib import Path

import requests

from biog_reliability.provenance import run_context
from biog_reliability.reporting import sha256, write_json

ROOT = Path(__file__).resolve().parents[1]
COMMIT = "4ff0ccd2493de3dc658747d05fa6bb4fe12ea2c7"
BASE = f"https://raw.githubusercontent.com/baolab-rice/CRISPR_OT_scoring/{COMMIT}/"
PATHS = [
    "Algorithms/pairwise_evaluation/TrueOT_v1_1_allscores.xlsx",
    "Algorithms/pairwise_evaluation/TrueOT_v1_1_gRNA_overlap.xlsx",
    "Supplementary_tables/Table_S1_TrueOT_dataset_summary.xlsx",
    "Supplementary_tables/Table_S2_TrueOT_v1_1.xlsx",
    "Algorithms/pairwise_evaluation/training_sets/CRISPR-NET/CIRCLE_seq_10gRNA_wholeDataset.csv",
    "Algorithms/pairwise_evaluation/training_sets/CRISPR-NET/SITE-Seq_offTarget_wholeDataset.csv",
]


def main():
    output = ROOT / "data/raw/external"
    output.mkdir(parents=True, exist_ok=True)
    expected_path = ROOT / "docs/external-input-hashes.json"
    expected = json.loads(expected_path.read_text()) if expected_path.exists() else {}
    records = []
    for relative in PATHS:
        path = output / Path(relative).name
        if not path.exists():
            response = requests.get(BASE + relative, timeout=180)
            response.raise_for_status()
            path.write_bytes(response.content)
        digest = sha256(path)
        if path.name in expected and digest != expected[path.name]:
            raise ValueError(f"External checksum mismatch: {path.name}")
        records.append(
            {
                "filename": path.name,
                "url": BASE + relative,
                "sha256": digest,
                "bytes": path.stat().st_size,
            }
        )
    write_json(
        output / "download-manifest.json",
        {
            **run_context(ROOT),
            "repository_commit": COMMIT,
            "inputs": records,
            "license": (
                "No standalone repository license found. Local analysis only; no redistribution."
            ),
            "publication": "https://doi.org/10.1101/2021.08.28.457846",
        },
    )
    archive = output / "crispr-bulge-datasets.zip"
    archive_url = (
        "https://media.githubusercontent.com/media/OrensteinLab/CRISPR-Bulge/"
        "3eddcd5bfcaff00b2bdf29425116ec9756ace870/files/datasets.zip"
    )
    if not archive.exists():
        partial = archive.with_suffix(".partial")
        with requests.get(archive_url, stream=True, timeout=(30, 180)) as response:
            response.raise_for_status()
            with partial.open("wb") as stream:
                for chunk in response.iter_content(1024 * 1024):
                    stream.write(chunk)
        partial.replace(archive)
    if sha256(archive) != "f892f70ba4ac3b05b03b2171b4ad38746630de08ad630e650f355dd61203eab0":
        raise ValueError("CRISPR-Bulge archive hash mismatch")
    write_json(
        output / "large-download-manifest.json",
        {
            **run_context(ROOT),
            "url": archive_url,
            "sha256": sha256(archive),
            "bytes": archive.stat().st_size,
            "license": "Repository MIT; primary data rights separate",
        },
    )


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
