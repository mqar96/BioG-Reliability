"""The redistributable demonstration exercises UI and exports without research inputs."""

import json
from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

from biog_reliability.cli import run
from biog_reliability.reporting import sha256

ROOT = Path(__file__).resolve().parents[1]


def test_synthetic_demo_all_pages_and_export():
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
    app.sidebar.radio[0].set_value("Synthetic demonstration").run()
    assert not app.exception
    assert any("SYNTHETIC SOFTWARE DEMONSTRATION" in w.value for w in app.warning)
    for page in ["Model comparison", "Sensitivity", "Data audit", "Export"]:
        app.sidebar.radio[1].set_value(page).run()
        assert not app.exception, page
    # Export metadata is rendered, retaining the synthetic label and exact input hashes.
    metadata = json.loads(app.json[0].value)
    assert metadata["synthetic_demonstration"] is True
    assert metadata["input_sha256"]["truth.csv"] == sha256(ROOT / "examples/demo/truth.csv")


def test_demo_cli_exports_unknown_semantics(tmp_path):
    d = ROOT / "examples/demo"
    tables = run(d / "truth.csv", d / "predictions.csv", d / "provenance.json", tmp_path)
    assert set(tables["common_scored"].n) == {4}
    assert set(tables["common_scored"].positives) == {2}
    assert set(tables["common_scored"].unlabeled_in_cohort_predictions) == {1}
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert manifest["metadata"]["provenance"]["dataset_id"].startswith("synthetic_")


def test_demo_contains_no_biological_sequences():
    d = ROOT / "examples/demo"
    truth = pd.read_csv(d / "truth.csv")
    assert set(truth.assembly) == {"synthetic"}
    assert truth.site_id.str.startswith("demo-").all()
    # All CSV identifiers are explicit artificial names, not sequence-level research records.
    assert not truth.site_id.str.fullmatch("[ACGTN]+", case=False).any()
