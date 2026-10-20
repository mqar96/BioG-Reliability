"""Small synthetic fixtures are for engineering tests only."""

import pandas as pd
import pytest

from biog_reliability.validation import Provenance


@pytest.fixture
def truth():
    return pd.DataFrame(
        {
            "site_id": ["a", "b", "c", "d", "u"],
            "guide_id": ["g1", "g1", "g2", "g2", "g1"],
            "assembly": "hg38",
            "assay": "test",
            "context": "test",
            "status": [
                "positive",
                "measured_negative",
                "positive",
                "measured_negative",
                "untested",
            ],
            "measurement": [1.0, 0.0, 0.5, 0.0, None],
        }
    )


@pytest.fixture
def predictions():
    return pd.DataFrame(
        {
            "site_id": ["a", "b", "c", "d", "u"],
            "guide_id": ["g1", "g1", "g2", "g2", "g1"],
            "assembly": "hg38",
            "model": "A",
            "score": [0.9, 0.1, 0.8, 0.2, 0.95],
            "rank": [2, 3, 1, 2, 1],
        }
    )


@pytest.fixture
def provenance():
    return Provenance(
        "test",
        "1",
        "https://example.org/test",
        "test only",
        "hg38",
        "test",
        "test",
        "test",
        "test",
        "explicit site_id",
    )
