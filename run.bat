@echo off
echo ========================================
echo Starting Rainbow Register Backend
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "rainbowEnv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment 'rainbowEnv' not found!
    echo.
    echo Please create it first:
    echo     python -m venv rainbowEnv
    echo     rainbowEnv\Scripts\activate
    echo     pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call rainbowEnv\Scripts\activate.bat

REM Check if .env exists
if not exist ".env" (
    echo [WARNING] .env file not found!
    echo [INFO] Copying .env.example to .env...
    copy .env.example .env
    echo.
    echo Please edit .env file with your configuration:
    echo     notepad .env
    echo.
    pause
)

REM Check if dependencies are installed
echo [INFO] Checking dependencies...
python -c "import fastapi" 2>nul
if errorlevel 1 (
    echo [WARNING] Dependencies not installed!
    echo [INFO] Installing from requirements.txt...
    pip install -r requirements.txt
)

REM Run the application
echo.
echo [INFO] Starting application...
echo.
python run.py

echo.
echo ========================================
echo Application stopped
echo ========================================
pause