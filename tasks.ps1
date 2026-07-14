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
elseif ($Task -eq "check") {
    & $python manage.py check
}
elseif ($Task -eq "makemigrations") {
    & $python manage.py makemigrations
}
elseif ($Task -eq "migrate") {
    & $python manage.py migrate
}
elseif ($Task -eq "runserver") {
    & $python manage.py runserver
}
elseif ($Task -eq "ci") {
    & $ruff check .
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    & $python -m pytest
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    & $python -m pytest --cov=library --cov-report=term-missing
}
else {
    Write-Error "Unknown task: $Task"
    exit 1
}