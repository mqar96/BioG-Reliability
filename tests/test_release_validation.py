import io
import json
from pathlib import Path

import pytest
from streamlit.delta_generator import DeltaGenerator
from streamlit.testing.v1 import AppTest

from biog_reliability.provenance import seal_directory, source_snapshot
from biog_reliability.reporting import sha256
from biog_reliability.validation import ValidationError, validate_predictions


@pytest.mark.parametrize(
    "start,end,strand",
    [
        (-1, 3, "+"),
        (4, 3, "+"),
        (3, 3, "+"),
        (0.5, 3, "+"),
        (0, float("nan"), "+"),
        (0, 3, "?"),
        (0, 3, None),
    ],
)
def test_canonical_prediction_coordinates(start, end, strand, truth, predictions):
    with pytest.raises(ValidationError):
        validate_predictions(predictions.assign(start=start, end=end, strand=strand), truth)


@pytest.mark.parametrize("invalid", [b"[]", b"null", b'"invalid"', b"{broken"])
def test_dashboard_malformed_provenance(monkeypatch, truth, predictions, invalid):
    files = {
        "Experimental sites CSV": truth.to_csv(index=False).encode(),
        "Precomputed predictions CSV": predictions.to_csv(index=False).encode(),
        "Provenance JSON": invalid,
    }
    monkeypatch.setattr(
        DeltaGenerator, "file_uploader", lambda self, label, **kwargs: io.BytesIO(files[label])
    )
    root = Path(__file__).resolve().parents[1]
    app = AppTest.from_file(str(root / "app.py"), default_timeout=30).run()
    app.sidebar.radio[0].set_value("Import CSV files").run()
    assert not app.exception
    assert any("Input validation failed" in e.value for e in app.error)


def test_source_snapshot_detects_change(tmp_path):
    p = tmp_path / "app.py"
    p.write_text("original")
    before = source_snapshot(tmp_path)
    p.write_text("changed")
    assert before != source_snapshot(tmp_path)


def test_manifest_includes_late_outputs(tmp_path):
    (tmp_path / "exact_budget_comparison.csv").write_text("k,expected\n50,0.5\n")
    (tmp_path / "analysis.html").write_text("report")
    seal_directory(tmp_path, {"seed": 3})
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert set(manifest["files_sha256"]) == {"exact_budget_comparison.csv", "analysis.html"}
    for name, digest in manifest["files_sha256"].items():
        assert sha256(tmp_path / name) == digest
