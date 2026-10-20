"""Previously failing audit cases, retained as release regressions."""

from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from biog_reliability.benchmark import prepare_predictions
from biog_reliability.validation import Provenance, ValidationError, validate_predictions

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("value", [[], None, "text", 3, True])
def test_non_object_provenance_rejected_as_validation_error(value):
    with pytest.raises(ValidationError):
        Provenance.from_dict(value)


def test_adapter_rejects_invalid_genomic_coordinates(tmp_path, truth):
    row = {
        "tool": "AuditFixture",
        "guide_key": "A" * 23,
        "off_target_seq": "C" * 23,
        "chromosome": "chr1",
        "start": -2,
        "end": -3,
        "strand": "?",
        "raw_score": 1.0,
        "score_direction": "higher_is_riskier",
        "rank": 1,
        "genome_build": "hg38",
    }
    source = tmp_path / "invalid_contract.csv"
    pd.DataFrame([row]).to_csv(source, index=False)
    with pytest.raises(ValidationError):
        prepare_predictions(source, truth)


@pytest.mark.parametrize("strand", ["+ PAR1", "- PAR1", "+ PAR2", "- PAR2"])
def test_adapter_explicit_par_annotations(tmp_path, truth, strand):
    row = {
        "tool": "fixture",
        "guide_key": "A" * 23,
        "off_target_seq": "C" * 23,
        "chromosome": "chrX",
        "start": 1,
        "end": 24,
        "strand": strand,
        "raw_score": 1,
        "rank": 1,
        "genome_build": "hg38",
        "score_direction": "higher_is_riskier",
    }
    path = tmp_path / "par.csv"
    pd.DataFrame([row]).to_csv(path, index=False)
    pred, qc = prepare_predictions(path, truth)
    assert len(pred) == 1 and qc["source_par_strand_annotations_normalized"] == 1


@pytest.mark.realdata
def test_sensitivity_page_handles_valid_zero_overlap(tmp_path):
    if not (ROOT / "data/processed/truth.csv").exists():
        pytest.skip("External research inputs not prepared; see docs/reproducibility.md")
    truth = pd.read_csv(ROOT / "data/processed/truth.csv")
    pred = pd.read_csv(ROOT / "data/processed/predictions.csv")
    pred = pred.assign(site_id="unmatched::" + pred.site_id)
    validate_predictions(pred, truth)
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    source = source.replace("ROOT = Path(__file__).resolve().parent", f"ROOT = Path({str(ROOT)!r})")
    source = source.replace(
        "truth, predictions, provenance, metadata = bundled()",
        "truth, predictions, provenance, metadata = bundled()\n"
        "        predictions = predictions.assign(site_id='unmatched::'+predictions.site_id)",
    )
    appfile = tmp_path / "zero_overlap_app.py"
    appfile.write_text(source, encoding="utf-8")
    app = AppTest.from_file(str(appfile), default_timeout=30).run()
    assert not app.exception
    app.sidebar.radio[1].set_value("Sensitivity").run()
    assert not app.exception
