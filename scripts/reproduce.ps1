param([switch]$Research, [switch]$DataTermsAccepted, [switch]$SkipDownload)
$ErrorActionPreference = 'Stop'
$project = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $project
if ($Research -and -not $DataTermsAccepted) { throw 'Review docs/data-provenance.md and confirm rights with -DataTermsAccepted before research execution.' }
& "$PSScriptRoot/setup.ps1"
if (-not $Research) {
    & .venv/Scripts/python.exe -m biog_reliability.cli examples/demo/truth.csv examples/demo/predictions.csv examples/demo/provenance.json --output work/demo
    if ($LASTEXITCODE -ne 0) { throw 'Synthetic demo failed' }
    & .venv/Scripts/python.exe scripts/verify.py --software-only
    if ($LASTEXITCODE -ne 0) { throw 'Software verification failed' }
    return
}
if (-not $SkipDownload) {
    & .venv/Scripts/python.exe scripts/fetch_data.py --acknowledge-data-terms
    if ($LASTEXITCODE -ne 0) { throw 'Primary acquisition failed' }
    & .venv/Scripts/python.exe scripts/fetch_external.py --acknowledge-data-terms
    if ($LASTEXITCODE -ne 0) { throw 'External acquisition failed' }
}
foreach ($script in @('run_experiments.py','diagnose_ties.py','external_validation.py','profile_large_data.py','stress_test.py','investigate_cctop.py','verify.py','generate_report.py')) {
    & .venv/Scripts/python.exe "scripts/$script"
    if ($LASTEXITCODE -ne 0) { throw "Failed: $script" }
}
