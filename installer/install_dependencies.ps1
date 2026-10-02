# Development dependency bootstrapper.
# This is intentionally separate from the PyInstaller build so developers can
# install dependencies without building the executable.

$ErrorActionPreference = "Stop"

$python = Get-Command py -ErrorAction SilentlyContinue
if (-not $python) {
    throw "Python 3.13 or newer is required."
}

$versionText = & py -3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"
$version = [version]$versionText

if ($version -lt [version]"3.13.0") {
    throw "Python 3.13 or newer is required. Detected $versionText."
}

$root = Split-Path -Parent $PSScriptRoot
$venv = Join-Path $root ".venv"

if (-not (Test-Path $venv)) {
    & py -3 -m venv $venv
}

$venvPython = Join-Path $venv "Scripts\python.exe"

& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r (Join-Path $root "requirements-runtime.txt")

Write-Host "Dependencies installed successfully." -ForegroundColor Green
Write-Host "Activate with: .venv\Scripts\Activate.ps1"
