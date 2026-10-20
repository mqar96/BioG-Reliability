from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.realdata
def test_dashboard_pages():
    if not (ROOT / "data/processed/truth.csv").exists():
        pytest.skip("Public benchmark not prepared")
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
    assert not app.exception
    for page in ["Model comparison", "Sensitivity", "Data audit", "Export"]:
        app.sidebar.radio[1].set_value(page).run()
        assert not app.exception, page
