param([int]$Port = 8501)
$ErrorActionPreference = 'Stop'
$project = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $project
& "$project/.venv/Scripts/python.exe" -m streamlit run app.py --server.address 127.0.0.1 --server.headless true --server.port $Port
