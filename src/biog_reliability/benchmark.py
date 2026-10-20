"""Independent adapter for Kaufmann et al. (2026), pinned public artifacts.

Sequence/chromosome identity is an explicit reproduction convention, not a
general genomic locus identifier. No upstream source code is bundled.
"""

from pathlib import Path

import numpy as np
import pandas as pd

from .validation import (
    Provenance,
    ValidationError,
    validate_coordinates,
    validate_predictions,
    validate_truth,
)

UPSTREAM_COMMIT = "e82954897a77e95df46370923e9a5213ed7b1e19"
PROVENANCE = dict(
    dataset_id="kaufmann2026_manuscript_primary",
    version=UPSTREAM_COMMIT,
    source_url="https://github.com/maren-ha/OffTargetPredictionBenchmark",
    license="Repository pyproject declares MIT; original database rights not independently cleared",
    assembly="hg38",
    species="Homo sapiens",
    nuclease="SpCas9",
    assay="deep_sequencing_pooled",
    context="pooled_as_published",
    identity_policy="guide_sequence::offtarget_sequence::chromosome; conflicts excluded",
)


def prepare_truth(raw, threshold=0.1, no_bulge=False, policy="exclude_conflicts"):
    if not np.isfinite(threshold) or threshold < 0:
        raise ValidationError("Indel threshold must be a finite nonnegative percentage")
    if policy not in {"exclude_conflicts", "first_record"}:
        raise ValidationError("Unknown repeated-observation policy")
    required = {"guide_seq", "offtarget_seq", "chromosome", "delta_indels", "genome"}
    if not required.issubset(raw):
        raise ValidationError(f"Missing upstream truth fields: {required - set(raw.columns)}")
    frame = raw.copy()
    if set(frame.genome) != {"hg38"} or frame[list(required)].isna().any().any():
        raise ValidationError("Unexpected build or incomplete upstream truth")
    for name in ("guide_seq", "offtarget_seq"):
        if not frame[name].str.fullmatch("[ACGTN]+").all():
            raise ValidationError("Unexpected sequence alphabet; no silent character deletion")
    frame["site_id"] = frame.guide_seq + "::" + frame.offtarget_seq + "::" + frame.chromosome
    frame["measurement"] = pd.to_numeric(frame.delta_indels, errors="raise")
    if not np.isfinite(frame.measurement).all():
        raise ValidationError("Non-finite indel measurements")
    frame["status"] = np.where(frame.measurement.ge(threshold), "positive", "measured_negative")
    if no_bulge:
        frame = frame[frame.offtarget_seq.str.len().eq(23) & frame.guide_seq.str.len().eq(23)]
    conflicts = frame.groupby("site_id").status.nunique()
    conflict_ids = set(conflicts[conflicts.gt(1)].index)
    counts = {
        "raw_observations": len(raw),
        "observations_in_scope": len(frame),
        "unique_before_conflicts": frame.site_id.nunique(),
        "conflicting_site_ids": len(conflict_ids),
        "extra_repeated_rows": len(frame) - frame.site_id.nunique(),
        "threshold_percent": threshold,
        "policy": policy,
        "no_bulge": no_bulge,
    }
    # Count collisions where the reproduction key conflates genomic starts.
    counts["keys_with_multiple_starts"] = (
        int(frame.groupby("site_id").start.nunique().gt(1).sum()) if "start" in frame else None
    )
    if policy == "exclude_conflicts":
        frame = frame[~frame.site_id.isin(conflict_ids)]
        out = (
            frame.groupby("site_id", sort=True)
            .agg(
                guide_id=("guide_seq", "first"),
                status=("status", "first"),
                measurement=("measurement", "median"),
                observations=("measurement", "size"),
            )
            .reset_index()
        )
    else:
        out = frame.drop_duplicates("site_id").rename(columns={"guide_seq": "guide_id"})[
            ["site_id", "guide_id", "status", "measurement"]
        ]
    out = out.assign(assembly="hg38", assay=PROVENANCE["assay"], context=PROVENANCE["context"])
    counts.update(
        unique_sites=len(out),
        positives=int(out.status.eq("positive").sum()),
        guides=out.guide_id.nunique(),
    )
    return validate_truth(out, Provenance.from_dict(PROVENANCE)), counts


def prepare_predictions(path, truth, no_bulge=False):
    cols = [
        "tool",
        "guide_key",
        "off_target_seq",
        "chromosome",
        "start",
        "end",
        "strand",
        "raw_score",
        "score_direction",
        "rank",
        "genome_build",
    ]
    frame = pd.read_csv(path, usecols=cols, low_memory=False)
    # Deposited contracts annotate pseudoautosomal regions in the strand field.
    # Recognize only these explicit source tokens; arbitrary malformed strands still fail.
    par_strands = frame.strand.isin(["+ PAR1", "- PAR1", "+ PAR2", "- PAR2"])
    par_strand_rows = int(par_strands.sum())
    frame.loc[par_strands, "strand"] = frame.loc[par_strands, "strand"].str[0]
    validate_coordinates(frame)
    input_rows = len(frame)
    if set(frame.score_direction.dropna()) != {"higher_is_riskier"}:
        raise ValidationError("Adapter requires declared higher-is-riskier scores")
    for name in ("guide_key", "off_target_seq"):
        if not frame[name].dropna().str.fullmatch("[ACGTN]+").all():
            raise ValidationError("Unexpected prediction sequence alphabet")
    frame = frame[frame.genome_build.eq("hg38")].copy()
    for name in ("raw_score", "rank", "start", "end"):
        frame[name] = pd.to_numeric(frame[name], errors="coerce")
    valid = (
        frame[["guide_key", "off_target_seq", "chromosome", "start", "strand", "raw_score", "rank"]]
        .notna()
        .all(axis=1)
    )
    valid &= np.isfinite(frame.raw_score) & np.isfinite(frame["rank"]) & frame["rank"].gt(0)
    frame = frame[valid].copy()
    after_clean = len(frame)
    frame = frame.sort_values(
        [
            "guide_key",
            "rank",
            "raw_score",
            "chromosome",
            "start",
            "end",
            "strand",
            "off_target_seq",
        ],
        ascending=[True, True, False, True, True, True, True, True],
    )
    frame["site_id"] = frame.guide_key + "::" + frame.off_target_seq + "::" + frame.chromosome
    frame = frame.drop_duplicates(["tool", "site_id"])
    after_dedup = len(frame)
    if no_bulge:
        frame = frame[frame.off_target_seq.str.len().eq(23) & frame.guide_key.str.len().eq(23)]
    # Preserve deposited ranks. Do not compress ranks after filtering candidates.
    frame = frame.rename(
        columns={
            "tool": "model",
            "guide_key": "guide_id",
            "raw_score": "score",
            "genome_build": "assembly",
        }
    )
    out = frame[["site_id", "guide_id", "assembly", "model", "score", "rank"]].copy()
    qc = {
        "source_par_strand_annotations_normalized": par_strand_rows,
        "file": str(Path(path).name),
        "input_rows": input_rows,
        "invalid_or_other_build_rows": input_rows - after_clean,
        "duplicate_identity_rows_removed": after_clean - after_dedup,
        "candidate_identities_in_scope": len(out),
        "no_bulge": no_bulge,
        "rank_policy": "original deposited per-guide rank",
    }
    return validate_predictions(out, truth), qc
