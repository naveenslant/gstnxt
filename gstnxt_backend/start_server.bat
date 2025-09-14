@echo off
echo Starting GST Next Backend Server...
cd /d "%~dp0"

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Start the FastAPI server
echo Starting FastAPI server on http://localhost:8000
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

pause
