#!/usr/bin/env bash
set -e

echo "============================================"
echo "  TetoMidi - Build Linux (binary)"
echo "  FIXED: Them hidden imports, clean cache"
echo "============================================"

# --- Check Python ---
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] python3 not found. Install Python 3.10+ first."
    exit 1
fi

# --- Create virtual environment if missing ---
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

echo "Installing / upgrading dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

echo "Cleaning previous build..."
rm -rf build dist TetoMidi.spec

echo "Building binary..."
pyinstaller --noconfirm --onefile --clean \
    --name TetoMidi \
    --add-data "icon.ico:." \
    --add-data "discord_avatar.png:." \
    --add-data "teto-midi-logo.svg:." \
    --hidden-import PyQt6.QtMultimedia \
    --hidden-import PyQt6.QtCore \
    --hidden-import PyQt6.QtGui \
    --hidden-import PyQt6.QtWidgets \
    --hidden-import mido \
    --hidden-import mido.backends.backend \
    --hidden-import numpy \
    --hidden-import scipy \
    --hidden-import scipy.signal \
    --hidden-import librosa \
    --hidden-import soundfile \
    --hidden-import pynput \
    --hidden-import pynput.keyboard._xorg \
    --hidden-import pynput.keyboard._uinput \
    --hidden-import pynput.mouse._xorg \
    --hidden-import torch \
    --hidden-import transkun \
    --hidden-import transkun.transcribe \
    --collect-submodules PyQt6 \
    --collect-submodules mido \
    main.py

if [ -f "dist/TetoMidi" ]; then
    chmod +x dist/TetoMidi
    echo "============================================"
    echo "  Build done! Binary: dist/TetoMidi"
    echo "  Run with: ./dist/TetoMidi"
    echo "============================================"
else
    echo "[ERROR] Build failed. Binary not found."
    exit 1
fi
