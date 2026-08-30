@echo off
setlocal enabledelayedexpansion

echo ============================================
echo   TetoMidi - Build Windows (.exe)
echo   FIXED: Them hidden imports, clean cache
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
    if errorlevel 1 (
        echo [ERROR] Failed to create venv.
        pause
        exit /b 1
    )
)

call venv\Scripts\activate.bat

echo Installing / upgrading dependencies...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo [ERROR] pip upgrade failed.
    pause
    exit /b 1
)

pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install requirements.
    pause
    exit /b 1
)

pip install pyinstaller pillow
if errorlevel 1 (
    echo [ERROR] Failed to install pyinstaller.
    pause
    exit /b 1
)

echo Cleaning previous build...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
del TetoMidi.spec 2>nul

echo Building .exe...
pyinstaller --noconfirm --onefile --windowed --clean ^
    --name TetoMidi ^
    --icon icon.ico ^
    --add-data "icon.ico;." ^
    --add-data "discord_avatar.png;." ^
    --add-data "teto-midi-logo.svg;." ^
    --hidden-import PyQt6.QtMultimedia ^
    --hidden-import PyQt6.QtCore ^
    --hidden-import PyQt6.QtGui ^
    --hidden-import PyQt6.QtWidgets ^
    --hidden-import mido ^
    --hidden-import mido.backends.backend ^
    --hidden-import numpy ^
    --hidden-import scipy ^
    --hidden-import scipy.signal ^
    --hidden-import librosa ^
    --hidden-import soundfile ^
    --hidden-import pynput ^
    --hidden-import pynput.keyboard._win32 ^
    --hidden-import pynput.mouse._win32 ^
    --hidden-import torch ^
    --hidden-import piano_transcription_inference ^
    --hidden-import pkg_resources ^
    --hidden-import pkg_resources.py2_warn ^
    --collect-submodules pkg_resources ^
    --collect-data setuptools ^
    --copy-metadata piano_transcription_inference ^
    --copy-metadata setuptools ^
    --collect-submodules PyQt6 ^
    --collect-submodules mido ^
    --noupx ^
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
