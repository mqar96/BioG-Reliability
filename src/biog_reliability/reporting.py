"""Portable exports with content hashes and machine-readable nulls."""

import hashlib
import html
import json
from pathlib import Path

import numpy as np


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def clean_json(value):
    if isinstance(value, dict):
        return {str(k): clean_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean_json(v) for v in value]
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def write_json(path, value):
    Path(path).write_text(
        json.dumps(clean_json(value), indent=2, allow_nan=False), encoding="utf-8"
    )


def export_analysis(directory, tables, metadata):
    output = Path(directory)
    output.mkdir(parents=True, exist_ok=True)
    content = [
        "<h1>BIOGIANT THERAPEUTICS · BioG-Reliability v0.1</h1>",
        "<p>Research evaluation only. Unknown candidates are excluded from classification.</p>",
    ]
    files = {}
    for name, frame in tables.items():
        path = output / f"{name}.csv"
        frame.to_csv(path, index=False)
        files[path.name] = sha256(path)
        content.append(f"<h2>{html.escape(name.replace('_', ' '))}</h2>")
        content.append(frame.head(100).to_html(index=False, na_rep="Undefined", escape=True))
    content.append(
        "<h2>Provenance and settings</h2><pre>"
        + html.escape(json.dumps(clean_json(metadata), indent=2))
        + "</pre>"
    )
    style = (
        "body{background:#091827;color:#e8f2f9;font:16px Segoe UI;margin:48px}"
        "h1,h2{color:#41d9df}td,th{padding:10px;border:1px solid #284257}"
        "table{border-collapse:collapse}pre{white-space:pre-wrap}"
    )
    (output / "analysis.html").write_text(
        '<!doctype html><html lang="en"><meta charset="utf-8"><title>BioG Reliability</title>'
        f"<style>{style}</style><body>{''.join(content)}</body></html>",
        encoding="utf-8",
    )
    write_json(output / "manifest.json", {"metadata": metadata, "files_sha256": files})
