# Rainbow Register Backend - PowerShell启动脚本

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting Rainbow Register Backend" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (-Not (Test-Path "rainbowEnv\Scripts\Activate.ps1")) {
    Write-Host "[ERROR] Virtual environment 'rainbowEnv' not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please create it first:" -ForegroundColor Yellow
    Write-Host "    python -m venv rainbowEnv" -ForegroundColor White
    Write-Host "    .\rainbowEnv\Scripts\Activate.ps1" -ForegroundColor White
    Write-Host "    pip install -r requirements.txt" -ForegroundColor White
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Activate virtual environment
Write-Host "[INFO] Activating virtual environment..." -ForegroundColor Green
& ".\rainbowEnv\Scripts\Activate.ps1"

# Check if .env exists
if (-Not (Test-Path ".env")) {
    Write-Host "[WARNING] .env file not found!" -ForegroundColor Yellow
    Write-Host "[INFO] Copying .env.example to .env..." -ForegroundColor Green
    Copy-Item ".env.example" ".env"
    Write-Host ""
    Write-Host "Please edit .env file with your configuration:" -ForegroundColor Yellow
    Write-Host "    notepad .env" -ForegroundColor White
    Write-Host ""
    Read-Host "Press Enter to continue"
}

# Check if dependencies are installed
Write-Host "[INFO] Checking dependencies..." -ForegroundColor Green
try {
    python -c "import fastapi" 2>$null
} catch {
    Write-Host "[WARNING] Dependencies not installed!" -ForegroundColor Yellow
    Write-Host "[INFO] Installing from requirements.txt..." -ForegroundColor Green
    pip install -r requirements.txt
}

# Run the application
Write-Host ""
Write-Host "[INFO] Starting application..." -ForegroundColor Green
Write-Host ""

python run.py

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Application stopped" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Read-Host "Press Enter to exit"