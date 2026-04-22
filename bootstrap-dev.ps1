Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $projectRoot "backend"
$frontendDir = Join-Path $projectRoot "frontend"
$backendVenv = Join-Path $backendDir ".venv"
$backendPython = Join-Path $backendVenv "Scripts\python.exe"
$backendRequirements = Join-Path $backendDir "requirements.txt"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Require-Command {
    param(
        [string]$Name,
        [string]$InstallHint
    )

    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "$Name is required. $InstallHint"
    }
}

function Get-PythonLauncher {
    $candidates = @(
        @{ Command = "py"; Launch = @("-3.12") },
        @{ Command = "py"; Launch = @("-3.11") },
        @{ Command = "py"; Launch = @("-3.10") },
        @{ Command = "python"; Launch = @() }
    )

    foreach ($candidate in $candidates) {
        if (-not (Get-Command $candidate.Command -ErrorAction SilentlyContinue)) {
            continue
        }

        $args = @()
        $args += $candidate.Launch
        $args += @("-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")

        try {
            $version = (& $candidate.Command @args).Trim()
        } catch {
            continue
        }

        if ($version -match "^3\.(10|11|12|13)$") {
            return $candidate
        }
    }

    throw "Python 3.10-3.13 was not found. Install a compatible Python version first."
}

Write-Step "Check required commands"
Require-Command -Name "docker" -InstallHint "Install Docker Desktop first."
Require-Command -Name "npm" -InstallHint "Install Node.js and npm first."

$pythonLauncher = Get-PythonLauncher

Write-Step "Prepare backend/.venv"
if (-not (Test-Path -LiteralPath $backendVenv)) {
    $venvArgs = @()
    $venvArgs += $pythonLauncher.Launch
    $venvArgs += @("-m", "venv", $backendVenv)
    & $pythonLauncher.Command @venvArgs
}

if (-not (Test-Path -LiteralPath $backendPython)) {
    throw "Virtual environment creation failed. Missing file: $backendPython"
}

Write-Step "Upgrade pip in backend/.venv"
& $backendPython -m pip install --upgrade pip

Write-Step "Install backend dependencies into backend/.venv"
if (Test-Path -LiteralPath $backendRequirements) {
    & $backendPython -m pip install -r $backendRequirements
} else {
    & $backendPython -m pip install -e $backendDir
    & $backendPython -m pip install pytest mypy ruff coverage
}

Write-Step "Update backend/requirements.txt"
& $backendPython -m pip freeze | Out-File -LiteralPath $backendRequirements -Encoding utf8

Write-Step "Install frontend dependencies"
Push-Location $projectRoot
try {
    npm install
} finally {
    Pop-Location
}

Write-Step "Install Playwright Chromium browser"
Push-Location $frontendDir
try {
    npx playwright install chromium
} finally {
    Pop-Location
}

Write-Step "Bootstrap complete"
Write-Host "Run the project:" -ForegroundColor Green
Write-Host "  docker compose watch"
Write-Host ""
Write-Host "Backend virtual environment:" -ForegroundColor Green
Write-Host "  $backendVenv"
Write-Host ""
Write-Host "Common commands:" -ForegroundColor Green
Write-Host "  Backend tests:  $backendPython -m pytest"
Write-Host "  Frontend tests: cd frontend; npx playwright test --reporter=line"
