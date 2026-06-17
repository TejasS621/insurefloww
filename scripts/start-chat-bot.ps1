param()

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

if (Test-Path ".\.venv312\Scripts\Activate.ps1") {
    . .\.venv312\Scripts\Activate.ps1
}
elseif (Test-Path ".\venv\Scripts\Activate.ps1") {
    . .\venv\Scripts\Activate.ps1
}

$env:PYTHONIOENCODING = "utf-8"
python -m chat_bot
