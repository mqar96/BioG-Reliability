"""Engineering scaling on real deposited prediction rows, never new biological evidence."""

import argparse
import gc
import json
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd
import psutil

from biog_reliability.benchmark import prepare_predictions, prepare_truth
from biog_reliability.metrics import compare_models
from biog_reliability.provenance import run_context, seal_directory
from biog_reliability.reporting import export_analysis, sha256, write_json
from biog_reliability.validation import Provenance, ValidationError

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "work/stress"


def worker(n, repeat):
    source = WORK / f"input-{n}.csv"
    started = time.perf_counter()
    # Separately measure CSV ingestion; release this frame before adapter execution.
    frame = pd.read_csv(source, low_memory=False)
    ingestion = time.perf_counter() - started
    assert len(frame) == n
    del frame
    gc.collect()
    truth, _ = prepare_truth(
        pd.read_csv(ROOT / "research/upstream/data/manuscript/manuscript_primary.csv")
    )
    started = time.perf_counter()
    pred, qc = prepare_predictions(source, truth)
    table = compare_models(truth, pred)
    processing = time.perf_counter() - started
    started = time.perf_counter()
    export_analysis(
        WORK / f"report-{n}-{repeat}",
        {"performance_fixture_only": table},
        {
            "interpretation": "Source prefixes, NOT biological validation",
            "input_sha256": sha256(source),
        },
    )
    reporting = time.perf_counter() - started
    recovery = False
    try:
        Provenance.from_dict([])
    except ValidationError:
        recovery = len(compare_models(truth, pred)) > 0
    write_json(
        WORK / f"worker-{n}-{repeat}.json",
        {
            "records": n,
            "repeat": repeat,
            "csv_bytes": source.stat().st_size,
            "ingestion_seconds": ingestion,
            "processing_seconds": processing,
            "report_seconds": reporting,
            "ingestion_rows_per_second": n / ingestion,
            "processing_rows_per_second": n / processing,
            "invalid_then_valid_recovery": recovery,
            "identities_after_dedup": len(pred),
            "source_duplicate_rows_removed": qc["duplicate_identity_rows_removed"],
        },
    )


def main():
    WORK.mkdir(parents=True, exist_ok=True)
    out = ROOT / "results/stress"
    out.mkdir(parents=True, exist_ok=True)
    paths = [
        ROOT / f"data/raw/zenodo/standard_tool_predictions/prediction_contract_{m}.csv"
        for m in ("moff", "crisot")
    ]
    rows = []
    for n in (10000, 100000, 1000000):
        remaining = n
        target = WORK / f"input-{n}.csv"
        first = True
        # Prefixes of two real model contracts; no generated or repeated rows are added.
        for path in paths:
            for chunk in pd.read_csv(path, chunksize=100000, low_memory=False):
                chunk = chunk.iloc[:remaining]
                chunk.to_csv(target, index=False, header=first, mode="w" if first else "a")
                first = False
                remaining -= len(chunk)
                if not remaining:
                    break
            if not remaining:
                break
        assert remaining == 0
        for repeat in (1, 2):
            start = time.perf_counter()
            proc = subprocess.Popen(
                [sys.executable, __file__, "--worker", str(n), "--repeat", str(repeat)], cwd=ROOT
            )
            observer = psutil.Process(proc.pid)
            peak = cpu = 0
            while proc.poll() is None:
                try:
                    processes = [observer, *observer.children(recursive=True)]
                    peak = max(peak, sum(p.memory_info().rss for p in processes))
                    cpu = max(
                        cpu, sum(p.cpu_times().user + p.cpu_times().system for p in processes)
                    )
                except psutil.NoSuchProcess:
                    break
                time.sleep(0.02)
            elapsed = time.perf_counter() - start
            record = {
                "exit_code": proc.wait(),
                "wall_seconds": elapsed,
                "peak_rss_mib": peak / 2**20,
                "cpu_seconds": cpu,
                "cpu_percent_one_core": 100 * cpu / elapsed,
                "records": n,
                "repeat": repeat,
            }
            if record["exit_code"] == 0:
                record.update(json.loads((WORK / f"worker-{n}-{repeat}.json").read_text()))
            rows.append(record)
            print(json.dumps(record), flush=True)
    pd.DataFrame(rows).to_csv(out / "measurements.csv", index=False)
    context = {
        **run_context(ROOT),
        "fixture": "Real MOFF then CRISOT source prefixes",
        "interpretation": "Engineering only; correlated and duplicated source rows retained",
        "logical_cpus": psutil.cpu_count(),
        "ram_bytes": psutil.virtual_memory().total,
        "sampling_interval_seconds": 0.02,
        "cache": "OS cache not flushed; 2 fresh processes/size",
        "input_sha256": {p.name: sha256(p) for p in paths},
    }
    write_json(out / "summary.json", context)
    seal_directory(out, context)
    if any(row["exit_code"] for row in rows):
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", type=int)
    parser.add_argument("--repeat", type=int, default=1)
    args = parser.parse_args()
    worker(args.worker, args.repeat) if args.worker else main()
