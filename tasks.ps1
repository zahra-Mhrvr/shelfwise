param(
    [string]$Task = "test"
)

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$ruff = Join-Path $PSScriptRoot ".venv\Scripts\ruff.exe"

if ($Task -eq "test") {
    & $python -m pytest
}
elseif ($Task -eq "coverage") {
    & $python -m pytest --cov=library --cov-report=term-missing
}
elseif ($Task -eq "lint") {
    & $ruff check .
}
elseif ($Task -eq "format") {
    & $ruff format .
}
else {
    Write-Error "Unknown task: $Task"
    exit 1
}
