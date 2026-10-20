"""Small composable command line surface for BioG-X1.0 integration."""

import argparse
import json
import logging
from pathlib import Path

import pandas as pd

from .metrics import compare_models, recall_at_k, summarize_recall
from .reporting import export_analysis, sha256
from .validation import Provenance, audit_table, validate_predictions, validate_truth


def run(truth_path, predictions_path, provenance_path, output):
    provenance = Provenance.from_dict(
        json.loads(Path(provenance_path).read_text(encoding="utf-8-sig"))
    )
    truth = validate_truth(pd.read_csv(truth_path), provenance)
    predictions = validate_predictions(pd.read_csv(predictions_path), truth)
    tables = {
        "model_scored": compare_models(truth, predictions),
        "common_scored": compare_models(truth, predictions, common=True),
        "recall": summarize_recall(recall_at_k(truth, predictions)),
    }
    export_analysis(
        output,
        tables,
        {
            "provenance": provenance.__dict__,
            "truth_audit": audit_table(truth),
            "input_sha256": {
                str(p): sha256(p) for p in (truth_path, predictions_path, provenance_path)
            },
        },
    )
    return tables


def main():
    parser = argparse.ArgumentParser(description="Evaluate precomputed off-target predictions")
    parser.add_argument("truth", type=Path)
    parser.add_argument("predictions", type=Path)
    parser.add_argument("provenance", type=Path)
    parser.add_argument("--output", type=Path, default=Path("results/custom"))
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    try:
        run(args.truth, args.predictions, args.provenance, args.output)
    except (ValueError, OSError, KeyError) as error:
        logging.error("Evaluation failed: %s", error)
        raise SystemExit(2) from error
    logging.info("Report saved to %s", args.output.resolve())


if __name__ == "__main__":
    main()
