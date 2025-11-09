@echo off
echo ========================================
echo Aventus HR Backend - Quick Setup
echo ========================================
echo.

echo Step 1: Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)
echo ✓ Virtual environment created
echo.

echo Step 2: Activating virtual environment...
call venv\Scripts\activate.bat
echo ✓ Virtual environment activated
echo.

echo Step 3: Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo ✓ Dependencies installed
echo.

echo Step 4: Checking environment configuration...
python check_env.py
if errorlevel 1 (
    echo.
    echo ⚠️  Please update your .env file with:
    echo    1. Supabase database password
    echo    2. Resend API key
    echo    3. Secure SECRET_KEY
    echo.
    echo See SETUP_GUIDE.md for detailed instructions
    pause
    exit /b 1
)
echo.

echo Step 5: Initializing database...
python seed_db.py
if errorlevel 1 (
    echo ERROR: Failed to initialize database
    echo Make sure your DATABASE_URL in .env is correct
    pause
    exit /b 1
)
echo.

echo ========================================
echo ✅ Setup completed successfully!
echo ========================================
echo.
echo Your backend is ready to run!
echo.
echo To start the server, run: python run.py
echo Or double-click: start_server.bat
echo.
echo API will be available at: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
pause
