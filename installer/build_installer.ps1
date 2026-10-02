# Py Diffuser 02 - Windows executable build script
#
# Run from the repository root:
# powershell -ExecutionPolicy Bypass -File .\installer\build_installer.ps1

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "       Py Diffuser 02 Build" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

function Test-IsAdministrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)

    return $principal.IsInRole(
        [Security.Principal.WindowsBuiltInRole]::Administrator
    )
}

try {

    # ---------------------------------------------------------
    # Administrator check
    # ---------------------------------------------------------

    if (-not (Test-IsAdministrator)) {

        Write-Host "Administrator permission is required." -ForegroundColor Yellow
        Write-Host "Requesting Administrator access..." -ForegroundColor Yellow
        Write-Host ""

        $arguments = "-ExecutionPolicy Bypass -File `"$PSCommandPath`""

        Start-Process `
            -FilePath "powershell.exe" `
            -Verb RunAs `
            -ArgumentList $arguments

        exit
    }

    Write-Host "Administrator access confirmed." -ForegroundColor Green

    # ---------------------------------------------------------
    # Locate project root
    # ---------------------------------------------------------

    $projectRoot = Split-Path -Parent $PSScriptRoot

    Set-Location $projectRoot

    Write-Host ""
    Write-Host "Project root:" -ForegroundColor Gray
    Write-Host $projectRoot -ForegroundColor White

    # ---------------------------------------------------------
    # Check Python
    # ---------------------------------------------------------

    Write-Host ""
    Write-Host "Checking Python version..." -ForegroundColor Cyan

    $pythonLauncher = Get-Command py -ErrorAction SilentlyContinue

    if (-not $pythonLauncher) {
        throw "Python launcher 'py' was not found. Install Python 3.13 or newer."
    }

    $pythonVersionText = & py -3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"

    if ($LASTEXITCODE -ne 0) {
        throw "Unable to determine the installed Python version."
    }

    $pythonVersion = [version]$pythonVersionText

    Write-Host "Detected Python $pythonVersionText" -ForegroundColor Green

    if ($pythonVersion -lt [version]"3.13.0") {
        throw "Python 3.13 or newer is required. Detected Python $pythonVersionText."
    }

    # ---------------------------------------------------------
    # Build environment
    # ---------------------------------------------------------

    $buildEnvironment = Join-Path $projectRoot ".build-venv"
    $venvPython = Join-Path $buildEnvironment "Scripts\python.exe"

    Write-Host ""
    Write-Host "Checking build environment..." -ForegroundColor Cyan

    if (-not (Test-Path $buildEnvironment)) {

        Write-Host "Creating .build-venv..." -ForegroundColor Yellow

        & py -3 -m venv $buildEnvironment

        if ($LASTEXITCODE -ne 0) {
            throw "Failed to create the build virtual environment."
        }
    }
    else {
        Write-Host ".build-venv already exists." -ForegroundColor Green
    }

    if (-not (Test-Path $venvPython)) {
        throw "Build environment Python executable was not found at $venvPython"
    }

    # ---------------------------------------------------------
    # Upgrade pip
    # ---------------------------------------------------------

    Write-Host ""
    Write-Host "Upgrading pip..." -ForegroundColor Cyan

    & $venvPython -m pip install --upgrade pip

    if ($LASTEXITCODE -ne 0) {
        throw "Failed to upgrade pip."
    }

    # ---------------------------------------------------------
    # Install dependencies
    # ---------------------------------------------------------

    $requirementsFile = Join-Path $projectRoot "requirements.txt"

    if (-not (Test-Path $requirementsFile)) {
        throw "requirements.txt was not found."
    }

    Write-Host ""
    Write-Host "Installing project dependencies..." -ForegroundColor Cyan
    Write-Host "This may take a while because PyTorch and Diffusers are large." -ForegroundColor Gray
    Write-Host ""

    & $venvPython -m pip install -r $requirementsFile

    if ($LASTEXITCODE -ne 0) {
        throw "Failed to install project dependencies."
    }

    # ---------------------------------------------------------
    # Verify important packages
    # ---------------------------------------------------------

    Write-Host ""
    Write-Host "Verifying required packages..." -ForegroundColor Cyan

    & $venvPython -c "import requests; print('requests:', requests.__version__)"

    if ($LASTEXITCODE -ne 0) {
        throw "The requests package could not be imported."
    }

    & $venvPython -c "import diffusers; print('diffusers:', diffusers.__version__)"

    if ($LASTEXITCODE -ne 0) {
        throw "The diffusers package could not be imported."
    }

    & $venvPython -c "import torch; print('torch:', torch.__version__)"

    if ($LASTEXITCODE -ne 0) {
        throw "The torch package could not be imported."
    }

    # ---------------------------------------------------------
    # Clean previous build
    # ---------------------------------------------------------

    $buildDirectory = Join-Path $projectRoot "build"
    $distDirectory = Join-Path $projectRoot "dist"

    Write-Host ""
    Write-Host "Cleaning previous PyInstaller builds..." -ForegroundColor Cyan

    if (Test-Path $buildDirectory) {
        Remove-Item $buildDirectory -Recurse -Force
    }

    if (Test-Path $distDirectory) {
        Remove-Item $distDirectory -Recurse -Force
    }

    # ---------------------------------------------------------
    # Verify launcher
    # ---------------------------------------------------------

    $launcher = Join-Path $projectRoot "launcher.py"

    if (-not (Test-Path $launcher)) {
        throw "launcher.py was not found in the project root."
    }

    # ---------------------------------------------------------
    # Build with PyInstaller
    # ---------------------------------------------------------

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "       Building Windows executable" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""

    & $venvPython -m PyInstaller `
        --noconfirm `
        --clean `
        --windowed `
        --name "py-diffuser-02" `
        --collect-all "diffusers" `
        --collect-all "transformers" `
        --collect-all "accelerate" `
        --collect-all "safetensors" `
        --collect-all "torch" `
        --collect-all "imageio" `
        --collect-all "imageio_ffmpeg" `
        --copy-metadata "requests" `
        --copy-metadata "huggingface-hub" `
        --copy-metadata "filelock" `
        --copy-metadata "numpy" `
        --copy-metadata "safetensors" `
        --copy-metadata "Pillow" `
        --copy-metadata "torch" `
        --copy-metadata "accelerate" `
        --copy-metadata "transformers" `
        --copy-metadata "diffusers" `
        $launcher

    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller failed with exit code $LASTEXITCODE."
    }

    # ---------------------------------------------------------
    # Verify executable
    # ---------------------------------------------------------

    $executable = Join-Path `
        $distDirectory `
        "py-diffuser-02\py-diffuser-02.exe"

    Write-Host ""
    Write-Host "Checking generated executable..." -ForegroundColor Cyan

    if (-not (Test-Path $executable)) {
        throw "PyInstaller reported success, but the executable was not found at:`n$executable"
    }

    # ---------------------------------------------------------
    # Build complete
    # ---------------------------------------------------------

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "          BUILD SUCCESSFUL" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""

    Write-Host "Executable:" -ForegroundColor White
    Write-Host $executable -ForegroundColor Cyan

    Write-Host ""
    Write-Host "The application is a one-folder PyInstaller build." -ForegroundColor Gray
    Write-Host "The executable is located inside the dist directory." -ForegroundColor Gray

    Write-Host ""
    Write-Host "Stable Diffusion model weights are NOT included." -ForegroundColor Yellow
    Write-Host "They will be downloaded separately when the application loads the model." -ForegroundColor Gray

    Write-Host ""

}
catch {

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "             BUILD FAILED" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""

    Write-Host $_.Exception.Message -ForegroundColor Red

    Write-Host ""
    Write-Host "The build window will remain open so you can read the error." -ForegroundColor Yellow
}
finally {

    Write-Host ""
    Read-Host "Press ENTER to close this window"
}