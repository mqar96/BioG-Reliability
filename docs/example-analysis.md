# Worked synthetic software example

Run scripts/setup.ps1, then:
    .venv\Scripts\python.exe -m biog_reliability.cli examples/demo/truth.csv examples/demo/predictions.csv examples/demo/provenance.json --output work/demo

Inspect work/demo/analysis.html and its manifest. There are five artificial site IDs:
two positive placeholders, two negative placeholders and one unknown. Each model has
four scored measured placeholders. The unknown affects rankings but never classification.
These are software fixtures, not experimental findings.

Import the same three files using Import CSV files or use Synthetic demonstration.
All pages preserve provenance and export interpretation. Public benchmark mode needs
separately acquired authorized data; see reproducibility.md. Historical research facts
are summarized separately in README and research-summary.json.
