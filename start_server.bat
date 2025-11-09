@echo off
echo ========================================
echo Starting Aventus HR Backend Server
echo ========================================
echo.

call venv\Scripts\activate.bat

echo Server starting at http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

python run.py

pause
