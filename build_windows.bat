@echo off
setlocal

echo ============================================
echo   TetoMidi - Build Windows (.exe)
echo ============================================

REM --- Kiem tra Python ---
where python >nul 2>&1
if errorlevel 1 (
    echo [LOI] Khong tim thay Python. Hay cai Python 3.10+ va them vao PATH.
    pause
    exit /b 1
)

REM --- Tao virtual environment neu chua co ---
if not exist venv (
    echo Dang tao virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat

echo Dang cai dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller pillow

echo Dang don dep build cu...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
del TetoMidi.spec 2>nul

echo Dang build file .exe...
pyinstaller --noconfirm --onefile --windowed ^
    --name TetoMidi ^
    --icon icon.ico ^
    --add-data "icon.ico;." ^
    main.py

if errorlevel 1 (
    echo [LOI] Build that bai. Xem log o tren.
    pause
    exit /b 1
)

echo ============================================
echo   Build xong! File nam o: dist\TetoMidi.exe
echo ============================================
pause
