@echo off
setlocal

echo ============================================
echo   TetoMidi - Build Windows (.exe)
echo ============================================

REM --- Check Python ---
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install Python 3.10+ and add it to PATH.
    pause
    exit /b 1
)

REM --- Create virtual environment if missing ---
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat

echo Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller pillow

echo Cleaning previous build...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
del TetoMidi.spec 2>nul

echo Building .exe...
pyinstaller --noconfirm --onefile --windowed ^
    --name TetoMidi ^
    --icon icon.ico ^
    --add-data "icon.ico;." ^
    --add-data "discord_avatar.png;." ^
    --add-data "teto-midi-logo.svg;." ^
    --hidden-import PyQt6.QtMultimedia ^
    --hidden-import PyQt6.QtCore ^
    --hidden-import PyQt6.QtGui ^
    --hidden-import PyQt6.QtWidgets ^
    --collect-submodules PyQt6 ^
    main.py

if errorlevel 1 (
    echo [ERROR] Build failed. Check the log above.
    pause
    exit /b 1
)

echo ============================================
echo   Build done! File: dist\TetoMidi.exe
echo ============================================
pause
