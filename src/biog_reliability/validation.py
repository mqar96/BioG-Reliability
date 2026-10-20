"""Strict public contracts. Unknown observations never become negatives."""

from dataclasses import dataclass

import numpy as np
import pandas as pd

STATUSES = {"positive", "measured_negative", "untested"}
TRUTH = {"site_id", "guide_id", "assembly", "assay", "context", "status", "measurement"}
PRED = {"site_id", "guide_id", "assembly", "model", "score", "rank"}


class ValidationError(ValueError):
    """An input would make the evaluation ambiguous or invalid."""


@dataclass(frozen=True)
class Provenance:
    dataset_id: str
    version: str
    source_url: str
    license: str
    assembly: str
    species: str
    nuclease: str
    assay: str
    context: str
    identity_policy: str

    @classmethod
    def from_dict(cls, value: dict):
        if not isinstance(value, dict):
            raise ValidationError("Provenance JSON must be an object, not an array or scalar")
        fields = cls.__dataclass_fields__
        missing = [
            key for key in fields if not isinstance(value.get(key), str) or not value[key].strip()
        ]
        if missing:
            raise ValidationError(f"Missing provenance fields: {', '.join(missing)}")
        if not value["source_url"].startswith("https://"):
            raise ValidationError("Provenance source_url must use HTTPS")
        return cls(**{key: value[key] for key in fields})


def _required(df, columns):
    missing = columns - set(df.columns)
    if missing:
        raise ValidationError(f"Missing columns: {sorted(missing)}")
    for col in columns - {"measurement", "score", "rank"}:
        if df[col].isna().any() or df[col].astype(str).str.strip().eq("").any():
            raise ValidationError(f"Empty identifier/annotation: {col}")


def validate_coordinates(df):
    """Validate supplied 0-based, half-open genomic intervals before dropping fields."""
    for col in ("start", "end"):
        if col in df:
            values = pd.to_numeric(df[col], errors="coerce")
            if not np.isfinite(values).all() or (values < 0).any() or (values % 1 != 0).any():
                raise ValidationError(f"Invalid genomic coordinates: {col}")
    if {"start", "end"}.issubset(df):
        if (pd.to_numeric(df.end) <= pd.to_numeric(df.start)).any():
            raise ValidationError("end precedes start or is equal (0-based, half-open)")
    if "strand" in df and not df.strand.isin(["+", "-"]).all():
        raise ValidationError("Invalid strand: expected + or -")
    if "chromosome" in df and (
        df.chromosome.isna().any() or df.chromosome.astype(str).str.strip().eq("").any()
    ):
        raise ValidationError("Empty chromosome")


def validate_truth(df: pd.DataFrame, provenance: Provenance) -> pd.DataFrame:
    _required(df, TRUTH)
    validate_coordinates(df)
    if df.empty:
        raise ValidationError("Truth table is empty")
    if not set(df.status).issubset(STATUSES):
        raise ValidationError("status must be positive, measured_negative, or untested")
    if df.site_id.duplicated().any():
        raise ValidationError("Duplicate site_id: resolve repeated observations explicitly")
    for col in ("assembly", "assay", "context"):
        if set(df[col]) != {getattr(provenance, col)}:
            raise ValidationError(f"Incompatible {col}; partition cohorts before evaluation")
    out = df.copy()
    out["measurement"] = pd.to_numeric(out.measurement, errors="raise")
    measured = out.status.ne("untested")
    if not np.isfinite(out.loc[measured, "measurement"]).all():
        raise ValidationError("Measured labels require finite experimental measurements")
    if out.loc[~measured, "measurement"].notna().any():
        raise ValidationError("Untested sites must not carry a measured outcome")
    for col in ("start", "end"):
        if col in out:
            values = pd.to_numeric(out[col], errors="raise")
            if not np.isfinite(values).all() or (values < 0).any() or (values % 1 != 0).any():
                raise ValidationError(f"Invalid genomic coordinates: {col}")
            out[col] = values
    if {"start", "end"}.issubset(out) and (out.end < out.start).any():
        raise ValidationError("end precedes start")
    if "strand" in out and not set(out.strand).issubset({"+", "-"}):
        raise ValidationError("Invalid strand")
    return out


def validate_predictions(df: pd.DataFrame, truth: pd.DataFrame) -> pd.DataFrame:
    _required(df, PRED)
    validate_coordinates(df)
    out = df.copy()
    if df.empty:
        raise ValidationError("Prediction table is empty")
    if not set(out.assembly).issubset(set(truth.assembly)):
        raise ValidationError("Prediction genome assembly differs from truth")
    if out.duplicated(["model", "site_id"]).any():
        raise ValidationError("Duplicate model/site_id scores")
    for col in ("score", "rank"):
        out[col] = pd.to_numeric(out[col], errors="raise")
        if not np.isfinite(out[col]).all():
            raise ValidationError(f"Non-finite {col}")
    if (out["rank"] <= 0).any() or (out["rank"] % 1 != 0).any():
        raise ValidationError("rank must be a positive integer within each guide")
    merged = out.merge(truth[["site_id", "guide_id"]], on="site_id", suffixes=("", "_truth"))
    if merged.guide_id.ne(merged.guide_id_truth).any():
        raise ValidationError("Same site_id has inconsistent guide identities")
    return out


def audit_table(df: pd.DataFrame) -> dict:
    """Non-destructive diagnostics, also usable before strict validation."""
    return {
        "rows": len(df),
        "exact_duplicate_rows": int(df.duplicated().sum()),
        "duplicate_site_ids": int(df.site_id.duplicated().sum()) if "site_id" in df else None,
        "missing_by_column": {c: int(v) for c, v in df.isna().sum().items()},
        "coordinate_checks_available": {"chromosome", "start", "end", "strand"}.issubset(df),
    }


def overlap_audit(train: pd.DataFrame, test: pd.DataFrame) -> dict:
    """Flag known overlap, not a certificate that unknown training sets are clean."""
    return {
        f"shared_{col}": len(set(train[col].dropna()) & set(test[col].dropna()))
        for col in ("site_id", "guide_id")
        if col in train and col in test
    }
