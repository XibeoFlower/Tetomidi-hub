#!/usr/bin/env bash
set -e

echo "============================================"
echo "  TetoMidi - Build Linux (binary)"
echo "============================================"

# --- Kiem tra Python ---
if ! command -v python3 &> /dev/null; then
    echo "[LOI] Khong tim thay python3. Hay cai Python 3.10+ truoc."
    exit 1
fi

# --- Tao virtual environment neu chua co ---
if [ ! -d "venv" ]; then
    echo "Dang tao virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

echo "Dang cai dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

echo "Dang don dep build cu..."
rm -rf build dist TetoMidi.spec

echo "Dang build binary..."
pyinstaller --noconfirm --onefile \
    --name TetoMidi \
    --add-data "icon.ico:." \
    main.py

chmod +x dist/TetoMidi

echo "============================================"
echo "  Build xong! File nam o: dist/TetoMidi"
echo "  Chay bang: ./dist/TetoMidi"
echo "============================================"
