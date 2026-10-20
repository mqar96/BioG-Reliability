"""Stream independent assay candidate data; undetected candidates remain unknown."""

import zipfile
from pathlib import Path

import pandas as pd

from biog_reliability.provenance import run_context, seal_directory
from biog_reliability.reporting import sha256, write_json
from biog_reliability.validation import validate_coordinates

ROOT = Path(__file__).resolve().parents[1]


def main():
    archive = ROOT / "data/raw/external/crispr-bulge-datasets.zip"
    digest = sha256(archive)
    if digest != "f892f70ba4ac3b05b03b2171b4ad38746630de08ad630e650f355dd61203eab0":
        raise ValueError("CRISPR-Bulge archive hash mismatch")
    out = ROOT / "results/large-data"
    out.mkdir(parents=True, exist_ok=True)
    rows, guide_rows = [], []
    with zipfile.ZipFile(archive) as bundle:
        for assay in ["CHANGEseq", "FullGUIDEseq"]:
            member = f"datasets/{assay}/include_on_targets/{assay}_CR_Lazzarotto_2020_dataset.csv"
            counts = {}
            totals = {
                "rows": 0,
                "detected_rows": 0,
                "zero_read_unknown": 0,
                "bulged_detected_rows": 0,
                "on_target_rows": 0,
            }
            with bundle.open(member) as stream:
                for frame in pd.read_csv(stream, chunksize=100000):
                    validate_coordinates(
                        frame.rename(
                            columns={
                                "Align.chromStart": "start",
                                "Align.chromEnd": "end",
                                "Align.strand": "strand",
                                "chrom": "chromosome",
                            }
                        )
                    )
                    if frame.reads.isna().any() or frame.reads.lt(0).any():
                        raise ValueError("Missing or negative read count")
                    detected = frame.reads.gt(0)
                    totals["rows"] += len(frame)
                    totals["detected_rows"] += int(detected.sum())
                    totals["zero_read_unknown"] += int(frame.reads.eq(0).sum())
                    totals["bulged_detected_rows"] += int(
                        (detected & frame["Align.#Bulges"].gt(0)).sum()
                    )
                    totals["on_target_rows"] += int(
                        (frame["Align.#Mismatches"].eq(0) & frame["Align.#Bulges"].eq(0)).sum()
                    )
                    for guide, group in frame.assign(detected=detected).groupby("sgRNA"):
                        previous = counts.setdefault(guide, [0, 0])
                        previous[0] += len(group)
                        previous[1] += int(group.detected.sum())
            rows.append(
                {
                    "assay": assay,
                    **totals,
                    "guides": len(counts),
                    "uncompressed_bytes": bundle.getinfo(member).file_size,
                    "crc32": bundle.getinfo(member).CRC,
                }
            )
            # Release aggregates only; guide sequences stay in the local source archive.
            guide_rows.extend(
                {"assay": assay, "guide_index": i, "candidate_rows": v[0], "detected_rows": v[1]}
                for i, (_, v) in enumerate(sorted(counts.items()))
            )
            print(rows[-1], flush=True)
    pd.DataFrame(rows).to_csv(out / "assay_inventory.csv", index=False)
    pd.DataFrame(guide_rows).to_csv(out / "guide_counts.csv", index=False)
    context = {
        **run_context(ROOT),
        "archive_sha256": digest,
        "repository_commit": "3eddcd5bfcaff00b2bdf29425116ec9756ace870",
        "publication": "https://doi.org/10.1093/nar/gkae428",
        "source_study": "https://doi.org/10.1038/s41587-020-0555-7",
        "assembly": "hg38",
        "interpretation": "Candidate/assay integrity audit only",
        "limitations": [
            "Detection read counts are not editing percentages",
            "Zero reads are unknown, not measured negatives",
            "Includes on-targets, duplicate loci/alignments may occur",
            "CHANGE and GUIDE are not independent studies or interchangeable assays",
            "No compatible scores evaluated here; no predictive accuracy claimed",
        ],
    }
    write_json(out / "summary.json", context)
    seal_directory(out, context)


if __name__ == "__main__":
    main()
