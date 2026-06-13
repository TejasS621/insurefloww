$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$venvPython = Join-Path $root "venv\Scripts\python.exe"
if (Test-Path $venvPython) {
    & $venvPython "backend\main_backend\main.py"
    exit $LASTEXITCODE
}

python "backend\main_backend\main.py"
