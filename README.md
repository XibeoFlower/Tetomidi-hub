# Teto Midi

**Teto Midi** (v3.3) — A MIDI player that simulates keyboard input. Optimized for virtual piano/guitar games (especially on Roblox) and similar applications.

![Teto Midi Logo](teto-midi-logo.svg)

## ✨ Features

- 🎹 **MIDI → Keyboard**: Automatically maps MIDI notes to QWERTY keys (supports 61-key & 88-key layouts)
- 🎸 **Guitar Mode**: Dedicated fretboard visualizer + guitar-specific mapping
- 👁️ **Visualizer**: Piano keys + Timeline (piano-roll)
- 🧠 **Humanization**: Realistic playing simulation (chord roll, timing variation, mistakes, tempo sway…)
- 🦶 **Smart Pedal**: Auto / PedalAI / Harmonic / Rhythmic / None
- 📝 **Translator**: Import/export sheet music in multiple formats
- 💾 **Save / Load** humanized performances
- ⌨️ **Custom Hotkey** (Play / Pause / Resume)
- 🌐 **Multi-language**: English & Vietnamese
- 🎨 Custom themes, Always-on-top, Opacity, Mini mode

---

## 🐧 Installation on Linux (from GitHub repo)

### 1. System Requirements

- Python **3.10+**
- `git`
- System libraries for PyQt6 (usually pre-installed on most distros)

### 2. Clone the repository

```bash
git clone https://github.com/XibeoFlower/Tetomidi-hub.git
cd Tetomidi-hub
```

### 3. Create virtual environment & install dependencies

```bash
python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Run the application

```bash
python3 main.py
```

### 5. (Optional) Build standalone binary

To create a single executable that doesn’t require Python:

```bash
chmod +x build_linux.sh
./build_linux.sh
```

After building, the binary will be located at:

```
dist/TetoMidi
```

Run it with:

```bash
./dist/TetoMidi
```

---

## 🚀 Quick Start

1. Open the app → go to the **Playback** tab
2. Click **Browse…** and select a `.mid` / `.midi` file
3. Choose the tracks you want to play in the dialog
4. Adjust Tempo, Transpose, Humanization, Pedal if needed
5. Click **Play** (or use the Hotkey)
6. The app will simulate key presses → your game/software will receive them as real keyboard input

### Useful Tabs

| Tab            | Purpose                                           |
|----------------|---------------------------------------------------|
| **Playback**   | Load MIDI, configure playback & humanization      |
| **Guitar**     | Guitar mode + fretboard visualizer                |
| **Visualizer** | Piano keys + timeline view                        |
| **Translator** | Paste sheet music → play or export to other formats |
| **Settings**   | Hotkey, language, theme, always-on-top…           |

---

## 📦 Main Dependencies

```
PyQt6 >= 6.7.0
mido >= 1.3.0
numpy >= 1.26.0
pynput >= 1.7.0
```

---

## ⚠️ Important Notes for Linux

- The app uses `pynput` to simulate keyboard input. On some distros (especially Wayland) you may need extra permissions or an X11 session.
- If keys are not being sent, try installing the system package:
  ```bash
  # Fedora / RHEL
  sudo dnf install python3-pynput

  # Ubuntu / Debian
  sudo apt install python3-pynput
  ```
- Some Wayland environments restrict key injection. Using an **X11 session** is recommended if you encounter issues.

---

## 🛠 Updating the App

```bash
cd Tetomidi-hub
git pull
source venv/bin/activate
pip install -r requirements.txt
```

Or simply use the **Check for updates** button inside the app.

---

## 📄 License

See the license file in the repository (if available).

---

**Discord support**: `@xiunolove`

Made with ❤️ by **XibeoFlower**
