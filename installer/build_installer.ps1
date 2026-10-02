# Py Diffuser 02 build script
# Run from the repository root:
# powershell -ExecutionPolicy Bypass -File .\installer\build_installer.ps1

$ErrorActionPreference = "Stop"

function Test-Admin {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-Admin)) {
    Write-Host "Administrator permission is required. Relaunching..." -ForegroundColor Yellow
    $args = "-ExecutionPolicy Bypass -File `"$PSCommandPath`""
    Start-Process powershell.exe -Verb RunAs -ArgumentList $args
    exit
}

Write-Host "=== Py Diffuser 02 Build ===" -ForegroundColor Cyan

$python = Get-Command py -ErrorAction SilentlyContinue

if (-not $python) {
    throw "Python launcher 'py' was not found. Install Python 3.13 or newer from python.org, then run this script again."
}

$versionText = & py -3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"
$version = [version]$versionText

if ($version -lt [version]"3.13.0") {
    throw "Python 3.13 or newer is required. Detected Python $versionText."
}

Write-Host "Python $versionText detected." -ForegroundColor Green

$root = Split-Path -Parent $PSScriptRoot
$venv = Join-Path $root ".build-venv"

if (-not (Test-Path $venv)) {
    Write-Host "Creating build environment..."
    & py -3 -m venv $venv
}

$venvPython = Join-Path $venv "Scripts\python.exe"

Write-Host "Upgrading pip..."
& $venvPython -m pip install --upgrade pip

Write-Host "Installing dependencies..."
& $venvPython -m pip install -r (Join-Path $root "requirements.txt")

$dist = Join-Path $root "dist"
$build = Join-Path $root "build"

if (Test-Path $dist) {
    Remove-Item $dist -Recurse -Force
}

if (Test-Path $build) {
    Remove-Item $build -Recurse -Force
}

Write-Host "Building py-diffuser-02.exe..."
Set-Location $root

& $venvPython -m PyInstaller `
    --noconfirm `
    --clean `
    --name "py-diffuser-02" `
    --windowed `
    --collect-all "diffusers" `
    --collect-all "transformers" `
    --collect-all "accelerate" `
    --collect-all "safetensors" `
    --collect-all "torch" `
    --collect-all "imageio" `
    --collect-all "imageio_ffmpeg" `
    "launcher.py"

Write-Host ""
Write-Host "Build complete." -ForegroundColor Green
Write-Host "Executable: $dist\py-diffuser-02.exe"
Write-Host ""
Write-Host "Note: the Stable Diffusion model is downloaded separately on first use."
