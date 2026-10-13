<#
.SYNOPSIS
  One-command launcher for the Nozama demo (backend + frontend).

.DESCRIPTION
  - Creates backend\.venv if it does not exist
  - Installs Python requirements (only when requirements.txt changed)
  - Installs frontend packages if node_modules is missing
  - Creates .env from .env.example if you do not have one yet
  - Opens the backend (port 8000) and frontend (port 5173) in their own windows

  Close those two windows (or press Ctrl+C in them) to stop the demo.
  The browser opens automatically on the Control page.

.EXAMPLE
  .\run.ps1
  .\run.ps1 -Setup      # only install/prepare, do not start anything
#>
param(
    [switch]$Setup
)

$ErrorActionPreference = "Stop"

$Root       = $PSScriptRoot
$BackendDir = Join-Path $Root "backend"
$FrontDir   = Join-Path $Root "frontend"
$VenvDir    = Join-Path $BackendDir ".venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
$ReqFile    = Join-Path $BackendDir "requirements.txt"
$ReqStamp   = Join-Path $VenvDir ".requirements.sha256"
$EnvFile    = Join-Path $Root ".env"
$EnvExample = Join-Path $Root ".env.example"

function Write-Step($text) { Write-Host "==> $text" -ForegroundColor Cyan }

function Test-PortInUse([int]$Port) {
    $null -ne (Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue)
}

function Find-Python {
    foreach ($candidate in @("py", "python", "python3")) {
        $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($cmd) { return $cmd.Source }
    }
    throw "Python was not found. Install Python 3.10+ from https://www.python.org and re-run."
}

# --- Prerequisites ---------------------------------------------------------
if (-not (Get-Command node -ErrorAction SilentlyContinue) -or -not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw "Node.js / npm was not found. Install Node 18+ from https://nodejs.org and re-run."
}

# --- .env ------------------------------------------------------------------
if (-not (Test-Path $EnvFile) -and -not (Test-Path (Join-Path $BackendDir ".env"))) {
    if (Test-Path $EnvExample) {
        Write-Step "Creating .env from .env.example (mock mode; add GEMINI_API_KEY to use Gemini)"
        Copy-Item $EnvExample $EnvFile
    }
}

# --- Python environment ----------------------------------------------------
if (-not (Test-Path $VenvPython)) {
    Write-Step "Creating Python virtual environment (backend\.venv)"
    $python = Find-Python
    if ((Split-Path $python -Leaf) -ieq "py.exe") {
        & $python -3 -m venv $VenvDir
    } else {
        & $python -m venv $VenvDir
    }
    if ($LASTEXITCODE -ne 0) { throw "Could not create the virtual environment." }
}

$reqHash = (Get-FileHash $ReqFile -Algorithm SHA256).Hash
$installedHash = if (Test-Path $ReqStamp) { (Get-Content $ReqStamp -Raw).Trim() } else { "" }
if ($reqHash -ne $installedHash) {
    Write-Step "Installing Python requirements"
    & $VenvPython -m pip install --disable-pip-version-check -r $ReqFile
    if ($LASTEXITCODE -ne 0) { throw "pip install failed." }
    Set-Content -Path $ReqStamp -Value $reqHash
}

# --- Frontend packages -----------------------------------------------------
if (-not (Test-Path (Join-Path $FrontDir "node_modules"))) {
    Write-Step "Installing frontend packages (npm install)"
    Push-Location $FrontDir
    try {
        npm install
        if ($LASTEXITCODE -ne 0) { throw "npm install failed." }
    } finally {
        Pop-Location
    }
}

if ($Setup) {
    Write-Step "Setup complete. Run .\run.ps1 to start the demo."
    return
}

# --- Start servers ---------------------------------------------------------
if (Test-PortInUse 8000) {
    Write-Warning "Port 8000 is already in use - the backend may already be running. Skipping backend start."
} else {
    Write-Step "Starting backend on http://127.0.0.1:8000"
    $backendCmd = "`$Host.UI.RawUI.WindowTitle = 'Nozama backend'; & '$VenvPython' -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
    Start-Process powershell.exe -WorkingDirectory $BackendDir `
        -ArgumentList @("-NoLogo", "-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $backendCmd)
}

if (Test-PortInUse 5173) {
    Write-Warning "Port 5173 is already in use - the frontend may already be running. Skipping frontend start."
} else {
    Write-Step "Starting frontend on http://localhost:5173 (browser opens automatically)"
    $frontendCmd = "`$Host.UI.RawUI.WindowTitle = 'Nozama frontend'; npm run dev"
    Start-Process powershell.exe -WorkingDirectory $FrontDir `
        -ArgumentList @("-NoLogo", "-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $frontendCmd)
}

Write-Host ""
Write-Host "Nozama demo is starting." -ForegroundColor Green
Write-Host "  Shop:     http://localhost:5173/"
Write-Host "  Control:  http://localhost:5173/control"
Write-Host "  X-Ray:    http://localhost:5173/xray"
Write-Host "  API docs: http://127.0.0.1:8000/docs"
Write-Host "Close the 'Nozama backend' and 'Nozama frontend' windows to stop."
