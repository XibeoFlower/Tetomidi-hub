# Teto Midi v3.0

**Teto Midi** is a MIDI playback and auto-play tool built around a Kasane Teto–themed interface. It can load and play MIDI files, translate sheet-music text into playable input, and visualize notes in real time on a piano roll — with optional **humanized playback**, making it well suited for auto-playing virtual piano games such as those found on **Roblox**.

---

## ✨ Features

![Teto Midi — Playback tab](https://raw.githubusercontent.com/XibeoFlower/Tetomidi-hub/main/assets/screenshots/playback.jpeg)

### 🎹 Playback
- **Load MIDI files** via `Browse…`, or restore a previous session with `Load Save`
- **Tempo control** — adjustable BPM slider (default `100.0`)
- **Pedal mode** — `Auto (Default)` or manual sustain pedal handling
- **Transpose** — shift the whole track up/down in semitones (`st`)
- **88-Key Layout** toggle for full-range keyboards
- **Countdown** before playback starts, so you have time to switch to the target window (e.g. a Roblox piano game)
- **Debug Output** toggle for troubleshooting playback issues
- Playback progress bar with elapsed / total time
- `Save`, `Reset`, and `Collapse` (compact mode) controls

### 🎵 Visualizer

![Teto Midi — Visualizer tab](https://raw.githubusercontent.com/XibeoFlower/Tetomidi-hub/main/assets/screenshots/visualizer.jpeg)

- Real-time **falling-note piano roll**
- Interactive **virtual keyboard** that highlights keys as they're played
- **Two-hand color coding** (green/red) to visually separate left-hand and right-hand parts
- **Sustain pedal bar** shown beneath the note roll

### 🔀 Translator

![Teto Midi — Translator tab](https://raw.githubusercontent.com/XibeoFlower/Tetomidi-hub/main/assets/screenshots/translator.jpeg)

- Convert between sheet-music formats — currently supports **Virtual Piano** notation
- **Import** tab: paste raw sheet text directly into the app
- **Export** tab: convert a loaded MIDI/session back into sheet text
- Adjustable **BPM** for the translated sheet
- **Humanize** toggle
- One-click **▶ Play Sheet**

### 🤖 Humanization
Makes auto-played input feel less robotic and more like a real performance:

| Option | Description |
|---|---|
| **All** | Master switch — enables every humanization option below |
| **Simulate Hands** | Mimics natural hand movement between notes |
| **Chord Roll** | Slightly staggers notes in a chord instead of hitting them perfectly together |
| **Vary Timing** | Randomizes note timing within a set range (seconds) |
| **Vary Articulation** | Randomizes note length/velocity (%) |
| **Hand Drift** | Simulates small positional drift of the hand over time (%) |
| **Mistakes** | Occasionally introduces small human-like errors (%) |
| **Tempo Sway** | Gently speeds up/slows down tempo over time (seconds) |
| **Invert Sway** | Reverses the direction of the tempo sway |

### ⚙️ Settings & Debug
- App-wide configuration options
- Built-in debug console for diagnosing playback or input issues

### 🎨 Themes
Multiple built-in color themes to choose from in Settings:
`Dark` · `Light` · `Midnight` · `Mocha` · **`Teto Red` (default)** · `Sakura` · `Emerald` · `Royal Purple`

---

## 🕹️ Auto-Playing Piano on Roblox

Teto Midi can send simulated key presses to auto-play a loaded track or translated sheet inside a virtual piano game window (such as the piano games found on Roblox).

1. Open the Roblox piano game and get to the point where the on-screen/virtual piano is active.
2. In Teto Midi, either:
   - go to **Playback** and load a `.mid` file via `Browse…`, **or**
   - go to **Translator**, set **Format** to `Virtual Piano`, and paste your sheet text into the Import box.
3. (Recommended) Enable **Humanization** options — `Simulate Hands`, `Vary Timing`, `Chord Roll`, etc. — so the input looks and sounds like a real performance rather than a perfectly robotic one.
4. Set your desired **Tempo** and, if needed, **Transpose**.
5. Click **▶ Play (F6)**, then quickly switch focus to the Roblox game window during the **Countdown**.
6. Teto Midi will send key presses automatically to play the track in-game.

> ⚠️ **Note:** Auto-play tools may violate the terms of service of some games or platforms. Use at your own discretion and risk.

**Keyboard shortcut:** `F6` — Play / Pause playback.

---

## 📦 Installation

### Windows
1. Download `TetoMidi.exe` from the [Releases](../../releases) page (or from the CI build artifacts).
2. Double-click to run.
3. If Windows SmartScreen shows a warning (the build isn't code-signed), click **More info → Run anyway**.

### Linux (via terminal)

Download the latest Linux build and run it directly:

```bash
# Download the binary (replace the URL with your actual release asset link)
curl -L -o TetoMidi https://github.com/XibeoFlower/Tetomidi-hub/releases/latest/download/TetoMidi

# Make it executable
chmod +x TetoMidi

# Run it
./TetoMidi
```

If you're running a minimal Linux distro, install the required GUI libraries first:

```bash
sudo apt-get update
sudo apt-get install -y \
    libgl1 libegl1 libxkbcommon0 libxkbcommon-x11-0 \
    libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \
    libxcb-randr0 libxcb-render-util0 libxcb-shape0 libxcb-xfixes0 \
    libdbus-1-3 libfontconfig1
```

#### Build from source instead

```bash
git clone https://github.com/XibeoFlower/Tetomidi-hub.git
cd Tetomidi-hub
chmod +x build_linux.sh
./build_linux.sh
./dist/TetoMidi
```

---

## 🖥️ Requirements

- **Windows:** Windows 10/11 (64-bit)
- **Linux:** A modern desktop distro with Qt6-compatible GUI libraries installed (see above)
- A `.mid` file or Virtual Piano sheet text to play

---

## 📁 Project Structure (relevant folders)

```
Tetomidi-hub/
├── controllers/     # App control logic
├── core/            # Core playback / MIDI engine
├── managers/        # State & settings managers
├── ui/              # Interface + theme.py (color themes & stylesheet engine)
├── main.py          # App entry point
├── requirements.txt
└── build_windows.bat / build_linux.sh
```

---

## 📝 License / Credits

Add your license and credits here.
