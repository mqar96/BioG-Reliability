"""Audit import-branch execution using file-like input injection, not browser uploads."""

import io
from pathlib import Path

import pytest
from streamlit.delta_generator import DeltaGenerator
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.realdata
def test_import_mode_all_pages_with_real_csv_files(monkeypatch):
    if not (ROOT / "data/processed/truth.csv").exists():
        pytest.skip("External research inputs not prepared; see docs/reproducibility.md")
    names = {
        "Experimental sites CSV": "truth.csv",
        "Precomputed predictions CSV": "predictions.csv",
        "Provenance JSON": "provenance.json",
    }

    def uploaded(self, label, *args, **kwargs):
        p = ROOT / "data/processed" / names[label]
        result = io.BytesIO(p.read_bytes())
        result.name = p.name
        return result

    monkeypatch.setattr(DeltaGenerator, "file_uploader", uploaded)
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
    app.sidebar.radio[0].set_value("Import CSV files").run()
    assert not app.exception
    for page in ["Model comparison", "Sensitivity", "Data audit", "Export"]:
        app.sidebar.radio[1].set_value(page).run()
        assert not app.exception, page
