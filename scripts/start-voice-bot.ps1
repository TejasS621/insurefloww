param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$PipecatArgs
)

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

if (Test-Path ".\venv\Scripts\Activate.ps1") {
    . .\venv\Scripts\Activate.ps1
}

python -m voice_bot @PipecatArgs
