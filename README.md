
readme_content = """<div align="center">

# 🎹 Teto Midi Hub

**Auto MIDI Player for Roblox & Virtual Piano — with AI Transcription**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![PyQt6](https://img.shields.io/badge/PyQt6-6.0%2B-green)](https://riverbankcomputing.com/software/pyqt)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-3.4_beta-orange)](https://github.com/XibeoFlower/Tetomidi-hub/releases)

*Turn audio into MIDI. Turn MIDI into keyboard input. Play music your way.*

[Features](#-features) • [Installation](#-installation) • [Roblox Setup](#-roblox-setup-guide) • [Usage](#-usage) • [Troubleshooting](#-troubleshooting)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Requirements](#-requirements)
- [Installation](#-installation)
  - [Windows](#windows)
  - [Linux](#linux)
- [Roblox Setup Guide](#-roblox-setup-guide)
- [Usage](#-usage)
  - [Playing MIDI Files](#playing-midi-files)
  - [MP3 → MIDI Transcription](#mp3--midi-transcription)
  - [Guitar Mode](#guitar-mode)
  - [Humanization](#humanization)
  - [Smart Pedal](#smart-pedal)
  - [Visualizer](#visualizer)
  - [Sheet Music Translator](#sheet-music-translator)
  - [Global Hotkey](#global-hotkey)
- [Building Standalone App](#-building-standalone-application)
- [Updating](#-updating)
- [Troubleshooting](#-troubleshooting)
- [Project Structure](#-project-structure)
- [Credits](#-credits)

---

## 🎯 Overview

**Teto Midi Hub** is a desktop MIDI player and audio-to-MIDI transcription tool built with **Python** and **PyQt6**. It is specifically designed for **Roblox virtual piano/guitar games** and any software that receives keyboard input.

Whether you have a MIDI file, an MP3 song, or sheet music — Teto Midi can convert it into playable keyboard input and send it directly to your Roblox game.

**Current Version:** `3.4 beta`

---

## ✨ Features

### 🎹 Core Playback
- Load `.mid` / `.midi` files
- Auto-map MIDI notes to keyboard keys
- Support for **61-key** and **88-key** layouts
- Select individual MIDI tracks
- Adjustable tempo & transpose
- Play / Pause / Resume / Stop controls

### 🎸 Guitar Mode
- Guitar-specific MIDI mapping
- Interactive fretboard visualizer
- Guitar-oriented playback

### 🎵 MP3 → MIDI Transcriber *(New in v3.4)*
- Convert **MP3, WAV, FLAC, M4A, OGG, AAC, WMA** → MIDI
- Powered by **TransKun** transcription engine
- Auto-converts audio to mono 44.1 kHz

### 🧠 Humanization *(New in v3.4)*
Make playback sound natural, not robotic:
- Timing variation
- Chord rolling
- Velocity variation
- Articulation variation
- Tempo sway
- Mistake simulation
- Drift correction
- Hand simulation

### 🦶 Smart Pedal *(New in v3.4)*
- **Auto** — Automatic pedal behavior
- **PedalAI** — AI-assisted pedaling
- **Harmonic** — Harmonic-based pedaling
- **Rhythmic** — Rhythm-oriented pedaling
- **None** — Disable pedal

### 👁️ Visualizer
- Real-time piano keyboard display
- Piano-roll timeline
- Playback position tracking

### 📝 Sheet Music Translator
- Import and convert sheet music
- Translate to playable notes
- Export to supported formats

### 🎨 Customization
- **English / Vietnamese** interface
- Custom themes & window opacity
- Always-on-top mode
- Mini / collapsed mode
- Custom global playback hotkey

---

## 📥 Requirements

### Windows
- Windows 10 or newer (recommended)
- Python 3.10+
- Git
- Internet connection (for first-time setup)

### Linux
- Python 3.10+
- Git
- PyQt6 system libraries
- `pynput` permissions
- ⚠️ **Wayland users:** May need additional permissions for keyboard simulation (see [Troubleshooting](#-troubleshooting))

---

## 🚀 Installation

### Windows (Step-by-Step)

#### Step 1 — Install Python & Git
1. Download and install **Python 3.10+** from [python.org](https://python.org)
2. **IMPORTANT:** During installation, check ✅ **"Add Python to PATH"**
3. Download and install **Git** from [git-scm.com](https://git-scm.com)
4. Verify installation by opening **Command Prompt** or **PowerShell**:
   ```cmd
   python --version
   git --version
   ```

#### Step 2 — Clone the Repository
```cmd
git clone https://github.com/XibeoFlower/Tetomidi-hub.git
cd Tetomidi-hub
```

#### Step 3 — Create Virtual Environment
```cmd
python -m venv venv
venv\\Scripts\\activate
```

#### Step 4 — Install Dependencies
```cmd
python -m pip install --upgrade pip
pip install -r requirements.txt
```

#### Step 5 — Launch Teto Midi
```cmd
python main.py
```

---

### Linux (Step-by-Step)

#### Step 1 — Install System Dependencies

**Ubuntu / Debian:**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv git python3-pyqt6 python3-pynput
```

**Fedora / RHEL:**
```bash
sudo dnf install python3 python3-pip python3-virtualenv git python3-qt6 python3-pynput
```

**Arch Linux:**
```bash
sudo pacman -S python python-pip python-virtualenv git python-pyqt6 python-pynput
```

#### Step 2 — Clone the Repository
```bash
git clone https://github.com/XibeoFlower/Tetomidi-hub.git
cd Tetomidi-hub
```

#### Step 3 — Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

#### Step 4 — Install Dependencies
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

#### Step 5 — Launch Teto Midi
```bash
python3 main.py
```

---

## 🎮 Roblox Setup Guide

To use Teto Midi with **Roblox virtual piano/guitar games**, follow this setup:

### 1. Prepare Roblox
- Open **Roblox** and join a virtual piano/guitar game
- Make sure your character is seated at the instrument
- Ensure the game window is **focused** (click inside the game)

### 2. Configure Teto Midi
- Launch **Teto Midi**
- Go to **Settings** tab
- Set your preferred **keyboard layout** (61-key or 88-key)
- Configure **Language** (English/Vietnamese)
- Set **Always on Top** if you want to see Teto Midi while playing

### 3. Load Your Music
- Go to **Playback** tab
- Click **Browse...** and select your `.mid` file
- **OR** use the **Transcriber** to convert an MP3 to MIDI (see below)

### 4. Select Tracks
- After loading MIDI, check the tracks you want to play
- Example: ✅ Piano + Melody, ⬜ Bass + Drums

### 5. Configure Playback (Optional but Recommended)
- Adjust **Tempo** if the song is too fast/slow
- Set **Transpose** if needed
- Enable **Humanization** for natural sound
- Choose **Smart Pedal** mode (recommended: `Auto`)

### 6. Start Playing
- Click inside the **Roblox game window** to focus it
- Press your **Global Hotkey** (default can be set in Settings)
- **OR** click the **Play** button in Teto Midi
- Teto Midi will automatically send keyboard inputs to Roblox!

### 💡 Pro Tips for Roblox
- Use **Mini Mode** to keep Teto Midi small and non-intrusive
- Set **Window Opacity** to see through Teto Midi while watching the game
- Use **Visualizer** to see exactly which notes are being played
- Enable **Always on Top** so Teto Midi stays visible over Roblox

---

## 📖 Usage

### Playing MIDI Files

1. Open **Playback** tab
2. Click **Browse...** and select a `.mid` or `.midi` file
3. Select the tracks you want to play (e.g., Piano, Melody)
4. Adjust **Tempo**, **Transpose**, **Layout** as needed
5. Click **Play**

### MP3 → MIDI Transcription

1. Open **Transcriber** tab
2. Click **Select Audio File** and choose your audio (MP3/WAV/FLAC/M4A/OGG/AAC/WMA)
3. The app auto-converts audio to **mono 44.1 kHz** for the TransKun engine
4. Click **Start Transcription**
5. Wait for processing (depends on audio length)
6. The generated MIDI auto-loads into **Playback** tab
7. Select tracks and play!

**Tips for best transcription results:**
- Use **high-quality, clean audio**
- Prefer **isolated melodies** (single instrument)
- Avoid: vocals, drums, heavy reverb, distortion
- Complex songs may need editing in a DAW after transcription

### Guitar Mode

1. Open **Guitar** tab
2. Load a MIDI file
3. Select desired tracks
4. View the **fretboard visualizer**
5. Click **Play** — uses guitar-specific note mapping

### Humanization

1. In **Playback** tab, enable **Humanization**
2. Choose features:
   - **Timing Variation** — slight timing offsets
   - **Velocity Variation** — dynamic loudness changes
   - **Chord Roll** — realistic chord strumming
   - **Tempo Sway** — natural tempo fluctuations
   - **Mistake Simulation** — occasional small errors
   - **Hand Simulation** — realistic hand movement behavior
3. Click **Play** — each performance will be unique!

### Smart Pedal

1. In **Playback** tab, select **Pedal Mode**:
   - `Auto` — Best for beginners (recommended)
   - `PedalAI` — AI-powered pedaling
   - `Harmonic` — Based on harmonic structure
   - `Rhythmic` — Follows rhythm patterns
   - `None` — No pedal

### Visualizer

- Open **Visualizer** tab to see:
  - **Piano Keyboard** — active notes light up
  - **Timeline** — full song overview
  - **Playback Position** — follows current progress

### Sheet Music Translator

1. Open **Translator** tab
2. Paste or import sheet music
3. Select the appropriate format
4. Set **BPM**
5. Choose **Humanization** (optional)
6. Click **Play** or **Export**

### Global Hotkey

1. Go to **Settings** → **Hotkey**
2. Click the hotkey configuration button
3. Press your desired key (e.g., `F8`, `Insert`)
4. Save
5. Use this key anywhere (even in Roblox) to **Play/Pause/Resume**

---

## 🏗️ Building Standalone Application

### Linux
```bash
chmod +x build_linux.sh
./build_linux.sh
```
Run the built app:
```bash
./dist/TetoMidi
```

### Windows
```cmd
build_windows.bat
```
The executable will be in `dist/` folder.

---

## 🔄 Updating

```bash
cd Tetomidi-hub
git pull
```
Then reactivate your virtual environment and update dependencies:

**Windows:**
```cmd
venv\\Scripts\\activate
pip install -r requirements.txt
```

**Linux:**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

You can also use the built-in **Check for updates** button in Settings.

---

## 🔧 Troubleshooting

### Keyboard Input Not Working (Linux)
- Teto Midi uses `pynput` for keyboard simulation
- **Wayland** sessions may block synthetic input
- **Solution:** Switch to **X11** session, or:
  ```bash
  # Ubuntu/Debian
  sudo apt install python3-pynput
  
  # Fedora
  sudo dnf install python3-pynput
  ```

### MP3 Cannot Be Loaded
- Ensure file extension is: `.mp3`, `.wav`, `.flac`, `.m4a`, `.ogg`, `.aac`, `.wma`
- Try converting to WAV if the file is corrupted

### Transcription Fails
- Verify the audio plays normally in a media player
- Try a shorter audio file
- Convert to WAV format first
- Check the terminal/log output for specific errors

### MIDI Sounds Wrong in Roblox
- Audio-to-MIDI is an estimation, not perfect
- Complex songs (vocals, drums, multiple instruments) reduce accuracy
- Try cleaner, isolated recordings
- Edit the generated MIDI in a DAW if needed

### Roblox Not Receiving Input
- Make sure **Roblox window is focused** (click inside it)
- Disable any antivirus that may block keyboard simulation
- Run Teto Midi as **Administrator** (Windows) if needed
- Check that your keyboard layout in Teto Midi matches the Roblox game

---

## 📁 Project Structure

```
Tetomidi-hub/
├── .github/workflows/      # CI/CD workflows
├── backup/                 # Backup utilities
├── controllers/            # Input controllers
├── core/                   # Core playback engine
├── managers/               # State & resource managers
├── transcriber/            # Audio-to-MIDI system
│   ├── audio_loader.py     # Audio file loading
│   ├── spectral_engine.py  # Spectral analysis
│   └── transkun_engine.py  # TransKun AI engine
├── ui/                     # PyQt6 user interface
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── build_linux.sh          # Linux build script
├── build_windows.bat       # Windows build script
├── ruff.toml               # Code style config
├── icon.ico / icon.icns    # App icons
└── teto-midi-logo.svg      # Logo asset
```

---

## 🤝 Contributing

Contributions are welcome!

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

**Bug reports:** Please include your OS, Python version, Teto Midi version, and steps to reproduce.

---

## 💬 Support

- **GitHub Issues:** [github.com/XibeoFlower/Tetomidi-hub/issues](https://github.com/XibeoFlower/Tetomidi-hub/issues)
- **Discord:** `@xiunolove`

---

## 📄 License

This project is licensed under the MIT License — see the repository for details.

---

## ❤️ Credits

Made with ❤️ by **XibeoFlower**

If Teto Midi is useful to you, consider giving the project a ⭐ on GitHub!

**[⭐ Star this repo](https://github.com/XibeoFlower/Tetomidi-hub)**

---

<div align="center">

**🎹 Turn audio into MIDI. Turn MIDI into keyboard input. Play music your way.**

</div>
"""

with open('/mnt/agents/output/README.md', 'w', encoding='utf-8') as f:
    f.write(readme_content)

print("README.md created successfully!")
print(f"File size: {len(readme_content)} characters")
