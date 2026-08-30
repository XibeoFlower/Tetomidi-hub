@echo off
setlocal enabledelayedexpansion
title TetoMidi Launcher

REM ============================================================
REM  TetoMidi Launcher - giam lag khi mo app va khi su dung app
REM ============================================================
REM  Vi sao lag:
REM   - torch / numpy / scipy mac dinh tu dong dung TAT CA nhan CPU
REM     de chay song song ngay khi khoi dong -> vua cham lucc mo app,
REM     vua giat UI khi phat nhac vi luong giao dien chinh (Qt) phai
REM     tranh CPU voi cac luong tinh toan nen.
REM   - Gioi han lai so luong thread hop ly (2-4) giup:
REM       + Mo app nhanh hon (it thread spin-up hon)
REM       + UI muot hon khi dang phat / transcribe vi CPU con "cho"
REM         cho luong ve giao dien.
REM  Script nay cung tang do uu tien tien trinh de UI phan hoi
REM  nhanh hon khi may dang chay nhieu app khac cung luc.
REM ============================================================

REM --- So luong thread cho cac thu vien tinh toan (chinh o day neu can) ---
REM     May yeu / nhieu app khac dang chay -> de 2
REM     May manh, chi dung TetoMidi -> co the tang len 4
set THREADS=2

set OMP_NUM_THREADS=%THREADS%
set MKL_NUM_THREADS=%THREADS%
set OPENBLAS_NUM_THREADS=%THREADS%
set NUMEXPR_NUM_THREADS=%THREADS%
set VECLIB_MAXIMUM_THREADS=%THREADS%
set TORCH_NUM_THREADS=%THREADS%

REM --- Tat animation/hieu ung DPI scaling gay giat tren man hinh nhieu DPI khac nhau ---
set QT_ENABLE_HIGHDPI_SCALING=1
set QT_SCALE_FACTOR_ROUNDING_POLICY=PassThrough

REM --- Tim file chay: uu tien ban .exe da build, neu khong co thi chay tu source ---
set SCRIPT_DIR=%~dp0
set EXE_PATH=%SCRIPT_DIR%dist\TetoMidi.exe

if exist "%EXE_PATH%" (
    echo [TetoMidi] Dang mo ban build: %EXE_PATH%
    echo [TetoMidi] Gioi han %THREADS% threads cho tinh toan nen, uu tien tien trinh: Above Normal
    start "" /ABOVENORMAL "%EXE_PATH%"
) else (
    echo [TetoMidi] Khong thay ban build, chay tu source (main.py)...
    if exist "%SCRIPT_DIR%venv\Scripts\python.exe" (
        set PYTHON_EXE=%SCRIPT_DIR%venv\Scripts\python.exe
    ) else (
        set PYTHON_EXE=python
    )
    echo [TetoMidi] Gioi han %THREADS% threads cho tinh toan nen, uu tien tien trinh: Above Normal
    start "" /ABOVENORMAL "!PYTHON_EXE!" "%SCRIPT_DIR%main.py"
)

REM --- Goi y them (khong tu dong lam, can quyen Admin) ---
echo.
echo [Meo them] Neu van con lag luc MO app (khong phai luc dang dung):
echo   Nguyen nhan thuong gap la Windows Defender quet lai file .exe
echo   moi lan mo (do build --onefile tu giai nen ra %%TEMP%% moi lan chay).
echo   Cach fix: Windows Security ^> Virus ^& threat protection ^> Manage
echo   settings ^> Add or remove exclusions ^> them thu muc chua TetoMidi.exe.
echo.

endlocal
